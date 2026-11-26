#!/usr/bin/env python3
"""Recheck Commons page IDs recovered by 15/20% dark-area expansion.

Official Commons page API, item-level PD/CC0 rights, independently fetched
raster SHA and color metrics. Only stages research candidates, never app assets.
"""
from __future__ import annotations
import hashlib,io,json,re,time
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request,urlopen
from PIL import Image,ImageDraw
from artdrift_commons_pd_bright import (
    API,UA,host_ok,licenses,safe_thumb,thumb_probe,strip_html
)
from artdrift_dark_threshold_ab import pixel_eligible,color_tier
from artdrift_bright_mass import cleaned

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/"research/experiments/20261126/dark_threshold_10_15_20.json"
OUT=ROOT/"research/experiments/20261126/commons_dark15_20_recovered.json"
PICTURES=ROOT/".artdrift_dark_ab_evidence/recovered_sheets"
BANNED=("portrait","self portrait","study","sketch","photograph","drawing",
        "woman","women","men","nude","figure","figures","woman with")

def official_pages(ids):
    if not ids or any(not str(v).isdigit() for v in ids):
        raise ValueError("untrusted page IDs")
    p=urlencode({"action":"query","format":"json","formatversion":"2",
        "pageids":"|".join(str(v) for v in ids),
        "prop":"imageinfo","iiprop":"url|mime|extmetadata|sha1|size",
        "iiurlwidth":320,"iilimit":1})
    req=Request(API+"?"+p,headers={"User-Agent":UA,"Accept":"application/json"})
    with urlopen(req,timeout=30) as response:
        if not host_ok(response.url,"commons.wikimedia.org"):
            raise ValueError("untrusted Commons redirect")
        raw=response.read(5_000_001)
    if len(raw)>5_000_000:raise ValueError("oversized response")
    return {str(p["pageid"]):p for p in (json.loads(raw).get("query") or {}).get("pages") or []}

def recheck(rec,page):
    if not page or page.get("ns")!=6:return None,"NOT_IMAGE_PAGE"
    title=str(page.get("title") or "")
    if not title.startswith("File:"):return None,"NOT_COMMONS_FILE"
    short=cleaned(title)
    if any(re.search(r"\b"+re.escape(t)+r"\b",short) for t in BANNED):
        return None,"PORTRAIT_OR_NON_PAINTING_TITLE"
    info=(page.get("imageinfo") or [{}])[0]
    if info.get("mime") not in ("image/jpeg","image/png","image/webp"):
        return None,"NOT_SUPPORTED_RASTER"
    is_pd,lic=licenses(info.get("extmetadata") or {})
    if not is_pd:return None,"FILE_NOT_EXPLICIT_PD_OR_CC0"
    thumb=str(info.get("thumburl") or "")
    if not safe_thumb(thumb):return None,"UNSAFE_OR_MISSING_COMMONS_THUMB"
    w={"remote_preview_url":thumb}
    try:
        color,sha,picture=thumb_probe(w)
    except Exception as ex:
        return None,"MEDIA_CHECK_"+str(ex)[:130]
    if not pixel_eligible(color,.20):
        return None,"NO_LONGER_PIXELS_20_ELIGIBLE"
    old=rec
    # Ensure a changed image, crop or thumbnail does not silently swap content.
    if abs(old["dark_fraction"]-color["dark_fraction"])>.05 or (
       abs(old["luminance"]-color["luminance"])>.06):
        return None,"IMAGE_METRICS_CHANGED_NEEDS_MANUAL_REVIEW"
    tier=color_tier(color)
    meta=info.get("extmetadata") or {}
    artist=strip_html((meta.get("Artist") or {}).get("value"))[:180]
    # Collector catalog may store author as a photograper; never certify.
    result={"commons_page_id":int(old["id"]),"file_name":title,
            "artist_metadata_unverified":artist,
            "file_metadata_license":lic,"file_sha1":info.get("sha1"),
            "rights":lic["license_name"],
            "source_link":"https://commons.wikimedia.org/w/index.php?curid="+str(old["id"]),
            "image_url":thumb,"image_sha256":sha,
            "dark_fraction":color["dark_fraction"],
            "luminance":color["luminance"],
            "saturation":color["saturation"],
            "vivid_fraction":color["vivid_fraction"],
            "tier":tier,
            "enough_color_for_research":tier in
               ("PREFERRED_AT_MOST_15_PERCENT_DARK",
                "CONDITIONAL_15_TO_20_PERCENT__HIGH_CHROMA"),
            "publication_status":"HOLD_ARTIST_WORK_DEDUP_AND_TERRITORIAL_RIGHTS",
            "runtime_visible":False}
    return (result,picture),"VERIFIED_PIXEL_AND_FILE_RIGHTS"

def main():
    j=json.loads(REPORT.read_text(encoding="utf-8"))
    records=j["source_comparisons"]["commons"]["measurable_new_at_20_vs_10"]
    if not 10<=len(records)<=30:raise RuntimeError("unexpected historical candidates")
    originals={str(w["id"]):w for w in records}
    pages=official_pages(list(originals))
    rows=[];holds=[];images={}
    with ThreadPoolExecutor(max_workers=2) as exe:
        futures={exe.submit(recheck,r,pages.get(str(r["id"]))):r for r in records}
        for f in as_completed(futures):
            old=futures[f]
            got,status=f.result()
            if got:
                item,picture=got
                rows.append(item);images[item["commons_page_id"]]=picture
            else:
                holds.append({"id":old["id"],"reason":status})
    rows.sort(key=lambda x:(not x["enough_color_for_research"],
                     x["dark_fraction"],x["commons_page_id"]))
    accepted=[w for w in rows if w["enough_color_for_research"]]
    OUT.parent.mkdir(parents=True,exist_ok=True)
    manifest={"schema_version":1,"as_of":"2026-11-26",
              "original_source":"Wikimedia Commons explicit PD/CC0 page API",
              "historical_new_dark10_to_20_pixel_candidates":len(records),
              "source_page_verified_again":len(rows),
              "strong_chroma_accepted_for_further_research":len(accepted),
              "out_of_scope_or_failed":len(holds)+len(rows)-len(accepted),
              "publication_ready":0,"runtime_imported":0,
              "rights_country_by_country":"HOLD",
              "accepted_for_curation":accepted,
              "not_selected_for_color": [w for w in rows if not w["enough_color_for_research"]],
              "media_holds":holds}
    OUT.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    if accepted:
        W=200;H=200;cols=4;data=accepted[:24]
        sheet=Image.new("RGB",(cols*W,((len(data)+cols-1)//cols)*H),"white")
        draw=ImageDraw.Draw(sheet)
        for i,w in enumerate(data):
            im=images.get(w["commons_page_id"])
            if im is None:continue
            x=(i%cols)*W;y=(i//cols)*H
            sheet.paste(im,(x+(W-im.width)//2,y+(150-im.height)//2))
            draw.text((x+3,y+154),w["file_name"][:26],fill="black")
            draw.text((x+3,y+172),f"dark {w['dark_fraction']*100:.1f}%  {w['tier'][:12]}",fill="black")
        PICTURES.mkdir(parents=True,exist_ok=True)
        sheet.save(PICTURES/"bright_dark15_20_candidates.jpg",quality=88,optimize=True)
    print(json.dumps({k:v for k,v in manifest.items()
                      if k not in ("accepted_for_curation","not_selected_for_color","media_holds")},
                     ensure_ascii=False,sort_keys=True))
if __name__=="__main__":main()
