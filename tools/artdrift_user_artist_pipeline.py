#!/usr/bin/env python3
"""Art Drift: user-selected artist discovery, pre-existing museum reuse, no deploy.

Two phases:
  discover: one polite, resumable public Commons artist-category scan;
  shortlist: offline matching/dedupe against retained reports from nine lanes.
No requests to excluded NGA/Met/SMK museum APIs. No auto licensing or import.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "research/artists/20261126"
SOURCE = BASE / "user_palette_artist_seeds.json"
REMOTE = BASE / "artist_commons_source_evidence.json"
SHORTLIST = BASE / "user_artist_visual_qa.json"
MUSEUM_REPORTS = ROOT / "research/museums/20261126/lanes/imports"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
PROVIDERS = ("rijks","nationalmuseum_se","staedel",
             "finnish_national_gallery","birmingham","belvedere",
             "paris_musees","te_papa","nasjonalmuseet")
MIME = {"image/jpeg","image/png","image/webp","image/tiff"}
MAX_BODY = 4_000_000


def norm(value):
    clean = unicodedata.normalize("NFKD", str(value or "")).casefold()
    clean = clean.translate(str.maketrans({
        "ø":"o","æ":"ae","œ":"oe","ł":"l","đ":"d","ð":"d",
        "þ":"th","ß":"ss","ı":"i","ŋ":"n",
    }))
    clean = "".join(c for c in clean if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", clean).strip()


def unwrap(value):
    return html.unescape(re.sub(r"<[^>]*>", " ",
        str(value.get("value", "") if isinstance(value, dict) else value or ""))).strip()


def safe_url(url):
    u = urllib.parse.urlsplit(str(url))
    return u.scheme == "https" and u.hostname in {
        "commons.wikimedia.org","upload.wikimedia.org","thumb.wikimedia.org"
    } and not u.username and not u.password and u.port in (None, 443)


def commons_get(params):
    url = COMMONS_API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url,headers={
        "User-Agent":"ArtDrift-ArtResearch/1.0 (metadata-only; non-commercial-preview; contact: GitHub riccardopinato)",
        "Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=22) as response:
        if not safe_url(response.url):
            raise ValueError("Unsafe Commons redirect host")
        raw=response.read(MAX_BODY+1)
        if len(raw)>MAX_BODY:
            raise ValueError("Oversize Commons metadata response")
        return json.loads(raw)


def public_license(text):
    t = norm(text)
    return t in {"cc0","cc 0","cc0 1 0","public domain","public domain mark",
                 "pdm","pd old","pd art","pd us","no known copyright restrictions"}


def parse_commons(page, artist_id, category):
    info=(page.get("imageinfo") or [{}])[0]
    ext=info.get("extmetadata") or {}
    title=str(page.get("title") or "")
    pid=page.get("pageid")
    if not isinstance(pid,int) or not title.startswith("File:"):
        return None
    mime=str(info.get("mime") or "")
    if mime not in MIME:
        return None
    preview=info.get("thumburl") or info.get("url") or ""
    if not safe_url(preview):
        preview=None
    rights=unwrap(ext.get("LicenseShortName")) or unwrap(ext.get("UsageTerms"))
    return {
        "source":"wikimedia_artist_category",
        "artist_id":artist_id,
        "museum_native_id":str(pid),
        "file_title":title,
        "title":title.removeprefix("File:")[:280],
        "artist_label_source":unwrap(ext.get("Artist"))[:160],
        "creation_date_raw":unwrap(ext.get("DateTimeOriginal"))[:120],
        "category_evidence":category,
        "museum_url":"https://commons.wikimedia.org/w/index.php?curid="+str(pid),
        "remote_preview_url":preview,
        "remote_full_url":str(info.get("url") or "") if safe_url(info.get("url") or "") else None,
        "file_sha1":str(info.get("sha1") or ""),
        "image_mime":mime,
        "image_license_per_item":rights or "UNVERIFIED",
        "public_domain_statement_present":public_license(rights),
        "rights_file_source":"Commons extmetadata",
        "artist_attribution_status":"HOLD_CATEGORY_MEMBERSHIP_NOT_AUTHOR_PROOF",
        "institutional_origin_confirmed":False,
        "copyright_review":"HOLD_VERIFY_AUTHOR_ORIGINAL_SOURCE_TERRITORY",
        "visual_status":"HOLD",
        "runtime_visible":False,
        "commercially_approved":False,
    }


def discover(seed, old, max_pages, caller=commons_get, pause=time.sleep):
    """Round-robin category scheduling, stop on first 429/503 for whole host."""
    existing=dict(old.get("records_by_commons_pageid") or {})
    progress=dict(old.get("query_progress") or {})
    errors=[]
    count=0
    throttled=False
    tasks=[(a["id"],cat) for a in seed["artists"]
           for cat in a["commons_categories"]]
    active=list(tasks)
    while active and count<max_pages and not throttled:
        pending=[]
        made_progress=False
        for artist_id,category in active:
            if count>=max_pages or throttled:
                pending.append((artist_id,category))
                continue
            key=artist_id+"|"+category
            state=progress.get(key) or {}
            if state.get("exhausted"):
                continue
            params={"action":"query","format":"json","formatversion":2,
                    "generator":"categorymembers","gcmtitle":category,
                    "gcmtype":"file","gcmlimit":50,"prop":"imageinfo",
                    "iiprop":"url|mime|extmetadata|sha1","iiurlwidth":340}
            if state.get("continuation"):
                params.update(state["continuation"])
            try:
                payload=caller(params)
            except Exception as e:
                msg=str(e)
                if getattr(e,"code",None) in (429,503) or re.search(
                        r"\b(?:429|503)\b",msg):
                    throttled=True
                    errors.append({"artist":artist_id,"category":category,
                                   "error":"REMOTE_THROTTLED_STOP__"+msg[:130]})
                else:
                    errors.append({"artist":artist_id,"category":category,
                                   "error":msg[:150]})
                pending.append((artist_id,category))
                continue
            if payload.get("error"):
                value=payload["error"]
                msg=str(value)[:150]
                code=str(value.get("code","")).lower() if isinstance(value,dict) else ""
                if code in ("ratelimited","maxlag"):
                    throttled=True
                errors.append({"artist":artist_id,"category":category,
                               "error":msg})
                pending.append((artist_id,category))
                continue
            count+=1
            made_progress=True
            for page in (payload.get("query") or {}).get("pages") or []:
                r=parse_commons(page,artist_id,category)
                if r:
                    key_id=r["museum_native_id"]
                    if key_id not in existing:
                        existing[key_id]=r
                    else:
                        v=existing[key_id]
                        v["also_seen_in_artist_categories"]=sorted(set(
                            v.get("also_seen_in_artist_categories",[]) + [category]))
            cursor=payload.get("continue") or None
            progress[key]={"continuation":cursor,
                           "exhausted":not bool(cursor),
                           "pages_completed":int(state.get("pages_completed",0))+1}
            if cursor:
                pending.append((artist_id,category))
            pause(0.7)
        if not made_progress:
            break
        active=pending
    return {
        "schema_version":1,
        "provider":"wikimedia_artist_categories",
        "as_of_utc":datetime.now(timezone.utc).isoformat(),
        "pages_retrieved_this_run":count,
        "total_distinct_commons_files":len(existing),
        "records_by_commons_pageid":existing,
        "query_progress":progress,
        "errors":errors[:50],
        "source_host_throttled":throttled,
        "source_catalog_exhaustively_searched":False,
        "license_gate":"HOLD_EACH_FILE",
        "source_evidence_is_not_artwork_ownership":True,
        "runtime_imported":0,
        "commercially_approved":0,
    }


def artist_id(row, seed):
    label=norm(row.get("artist") or row.get("artist_label_source"))
    title=norm(row.get("title") or "")
    for artist in seed["artists"]:
        for name in artist["aliases"]:
            alias=norm(name)
            if alias and (
                (label and (label==alias or label.startswith(alias+" ") or
                            " "+alias+" " in " "+label+" ")) or
                title.startswith(alias+" ") or
                (" "+alias+" " in " "+title+" " and not label)):
                return artist["id"]
    return None


def target_id(row, seed, artist):
    title=norm(row.get("title") or "")
    raw=str(row.get("title") or "").casefold()
    for target in seed["explicit_works"]:
        if target["artist_id"]!=artist:
            continue
        if any(str(code).casefold() in raw for code in target.get("work_reference_ids",[])):
            return target["id"]
        # a title may include the artist plus the painting name
        if any(norm(alias) in title for alias in target["title_aliases"]):
            return target["id"]
    return None


def commons_identity(row):
    link=str(row.get("museum_url") or "")
    found=re.search(r"(?:\?|&)curid=(\d+)(?:&|$)",link)
    if found:
        return "commons:"+found.group(1)
    if row.get("source")=="wikimedia_artist_category":
        return "commons:"+str(row["museum_native_id"])
    if row.get("source") not in ("rijks","staedel"):
        return "commons:"+str(row["museum_native_id"])
    return str(row.get("source") or "")+":"+str(row.get("museum_native_id") or "")


def confidence(row, exact):
    reason=[]
    score=0
    if exact:
        score+=100
        reason.append("USER_EXACT_WORK_FAMILY")
    else:
        score+=20
        reason.append("USER_NAMED_ARTIST")
    if row.get("image_sha256"):
        score+=45
        reason.append("PIXEL_INSPECTED")
    if row.get("color_tier") and not str(row["color_tier"]).startswith("HOLD"):
        score+=35
        reason.append("TECHNICAL_BRIGHTNESS_PASS")
    if row.get("remote_preview_url") and safe_url(row["remote_preview_url"]):
        score+=12
        reason.append("COMMONS_PREVIEW_AVAILABLE")
    elif row.get("remote_preview_url"):
        score+=5
        reason.append("SOURCE_PREVIEW_AVAILABLE_HOLD")
    if row.get("public_domain_statement_present") or row.get("image_license_checked"):
        score+=12
        reason.append("SOURCE_RIGHTS_STATEMENT_PRESENT_NOT_CLEARED")
    if row.get("institutional_origin_confirmed"):
        score+=10
        reason.append("SOURCE_PROVENANCE_CLAIM_TO_CHECK")
    if row.get("image_mime") and row["image_mime"] not in MIME:
        score-=50
        reason.append("NON_IMAGE_OR_UNSUPPORTED_FORMAT")
    return score,reason


def build(seed, museum_reports, sourced):
    if set(museum_reports)!=set(PROVIDERS):
        raise ValueError("All nine museum reports required")
    by_identity={}
    duplicates=[]
    raw=Counter()
    for provider in PROVIDERS:
        report=museum_reports[provider]
        if report.get("provider")!=provider:
            raise ValueError("Museum provider mismatch")
        if report.get("runtime_imported",0)!=0 or report.get("commercially_approved",0)!=0:
            raise ValueError("Unapproved museum report")
        for r in report.get("review_candidates") or []:
            raw[provider]+=1
            if r.get("runtime_visible") is not False or r.get("commercially_approved") is not False:
                raise ValueError("Unapproved candidate record")
            key=commons_identity(r)
            existing=by_identity.get(key)
            if existing is None or bool(r.get("image_sha256")) and not existing.get("image_sha256"):
                by_identity[key]=dict(r, source=provider)
            elif existing:
                duplicates.append(key)
    for r in (sourced.get("records_by_commons_pageid") or {}).values():
        key=commons_identity(r)
        if key in by_identity:
            duplicates.append(key)
            # Preserve established institutional source when category echoes it.
            if not by_identity[key].get("image_license_per_item"):
                by_identity[key]["image_license_per_item"]=r.get("image_license_per_item")
        else:
            by_identity[key]=r
    matches=[]
    matched=Counter()
    explicit=Counter()
    for key,r in by_identity.items():
        aid=r.get("artist_id") if r.get("source")=="wikimedia_artist_category" else artist_id(r,seed)
        if not aid or aid not in {a["id"] for a in seed["artists"]}:
            continue
        target=target_id(r,seed,aid)
        score,reasons=confidence(r,target)
        matched[aid]+=1
        if target:
            explicit[target]+=1
        matches.append({
            "source":r.get("source"),"source_native_id":r.get("museum_native_id"),
            "identity":key,"artist_id":aid,"title":r.get("title"),
            "artist_metadata":r.get("artist") or r.get("artist_label_source"),
            "explicit_work_target":target,
            "curatorial_score":score,"curatorial_reasons":reasons,
            "work_year":r.get("year"),"creation_date_raw":r.get("creation_date_raw"),
            "record_url":r.get("museum_url"),
            "preview_url":r.get("remote_preview_url"),
            "image_mime":r.get("image_mime"),"image_sha256":r.get("image_sha256"),
            "image_file_sha1":r.get("file_sha1") or r.get("source_file_sha1"),
            "color_tier":r.get("color_tier"),"color_metrics":r.get("color_metrics"),
            "source_license_claim":r.get("image_license_per_item"),
            "source_rights_evidence":r.get("rights_evidence_url") or r.get("rights_file_source"),
            "institutional_origin_confirmed":r.get("institutional_origin_confirmed"),
            "human_visual_review":"HOLD",
            "source_object_rights":"HOLD_VERIFY_PER_IMAGE",
            "artist_attribution":"HOLD_SOURCE_VS_CATEGORY_CLAIM",
            "dedup_status":"HOLD_CROSS_PROVIDER_WORK_MATCH",
            "runtime_visible":False,"commercially_approved":False,
        })
    matches.sort(key=lambda x:(-x["curatorial_score"],x["artist_id"],x["identity"]))
    return {
        "schema_version":1,
        "as_of_utc":datetime.now(timezone.utc).isoformat(),
        "artist_count":len(seed["artists"]),
        "named_works_count":len(seed["explicit_works"]),
        "museum_reports_read":len(museum_reports),
        "museum_records_examined":sum(raw.values()),
        "commons_artist_files_discovered":sourced.get("total_distinct_commons_files",0),
        "artist_matched_distinct_files":len(matches),
        "matches_by_artist":dict(matched),
        "exact_work_family_matches":dict(explicit),
        "duplicate_source_file_links":len(set(duplicates)),
        "priority_shortlist":matches[:600],
        "not_all_catalogs_exhaustively_searched":True,
        "rights_review_required":True,
        "visual_review_required":True,
        "commercially_approved":0,
        "runtime_imported":0,
        "note":"Artist-category membership and technical color are not artwork provenance or commercial image authorization. Explicit works may have distinct versions.",
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--phase",choices=["discover","shortlist"],required=True)
    parser.add_argument("--max-pages",type=int,default=12)
    args=parser.parse_args()
    seed=json.loads(SOURCE.read_text(encoding="utf-8"))
    if args.phase=="discover":
        if not 1<=args.max_pages<=22:
            parser.error("--max-pages 1..22")
        old=json.loads(REMOTE.read_text(encoding="utf-8")) if REMOTE.is_file() else {}
        result=discover(seed,old,args.max_pages)
        REMOTE.parent.mkdir(parents=True,exist_ok=True)
        REMOTE.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print(json.dumps({k:v for k,v in result.items() if k not in
                          ("records_by_commons_pageid","query_progress")},
                         ensure_ascii=False),flush=True)
    else:
        sources={p:json.loads((MUSEUM_REPORTS/f"{p}.json").read_text(
            encoding="utf-8")) for p in PROVIDERS}
        artist_source=json.loads(REMOTE.read_text(encoding="utf-8")) if REMOTE.is_file() else {}
        result=build(seed,sources,artist_source)
        SHORTLIST.parent.mkdir(parents=True,exist_ok=True)
        SHORTLIST.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",
                             encoding="utf-8")
        print(json.dumps({k:v for k,v in result.items() if k!="priority_shortlist"},
                         ensure_ascii=False),flush=True)


if __name__=="__main__":
    main()
