#!/usr/bin/env python3
"""Offline, lossless triage of all Art Drift user-favourite-painter candidates.

Never converts a source "public domain" string or a favorable image metric
into commercial approval. Results are ordered research/curatorial queues, not
gallery imports. Optionally checks current MAIN runtime catalog for collisions.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from artdrift_user_artist_pipeline import BASE, norm

SOURCE=BASE/"user_artist_visual_qa.json"
PIXELS=BASE/"artist_pixel_visual_evidence.json"
CURATION=BASE/"curatorial_triage_verified.json"
SEEDS=BASE/"user_palette_artist_seeds.json"
OUTPUT=BASE/"artist_bulk_486_triage.json"
RUNTIME_FILES=(
    "assets/gallery/catalog.json",
    "assets/museums/catalog.json",
    "assets/museums/catalog_global.json",
    "assets/museums/catalog_modern_1950.json",
    "assets/museums/catalog_new_museums.json",
)
IMAGE_EXTENSIONS=(".jpg",".jpeg",".png",".webp",".tiff",".tif")
NON_ART_RE=re.compile(
    r"\b(?:trichromogravure|lithograph|lithographie|engraving|etching|"
    r"facsimile|replica|exhibition poster|postcard|poster|"
    r"catalogue|catalog|print reproduction|print of|bookplate|"
    r"auction catalog|photograph of painting|scanned book)\b",re.I)
SUBJECT_RE=re.compile(
    r"\b(?:portrait|self.portrait|nude|naked|peasant|"
    r"full.length portrait|girl|girls|boy|boys|female figure)\b",re.I)
FRAME_RE=re.compile(r"\b(?:with frame|in frame|framed)\b",re.I)
LANDSCAPE_RE=re.compile(
    r"\b(?:landscape|landskap|landschap|landschaft|landskab|"
    r"flowers?|flowering|blomster|blumen|garden|garten|"
    r"river|rivier|lake|sea|beach|water|waterlilies|water lilies|"
    r"bridge|ponte|pont|boating|boats?|forest|woods?|"
    r"meadow|field|summer|sunset|sky|moor|village|mountains?|"
    r"wiesen?|fjord|winter|spring|autumn|shore|soleil|nympheas)\b",re.I)


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def artist_hint(s):
    """Match only selected artists; no arbitrary similarity across surnames."""
    seed=load(SEEDS)
    return {x["id"] for x in seed["artists"]}


def runtime_catalog_index(root: Path):
    seen={}
    totals={}
    skipped=[]
    for rel in RUNTIME_FILES:
        path=root/rel
        if not path.exists():
            skipped.append(rel)
            continue
        obj=load(path)
        if not isinstance(obj,list):
            raise ValueError(f"Unexpected runtime catalog shape: {rel}")
        totals[rel]=len(obj)
        for r in obj:
            if not isinstance(r,dict):
                continue
            title=norm(r.get("title"))
            author=norm(r.get("artist_title") or r.get("artist_display"))
            if not title or not author:
                continue
            sig=(title,author)
            seen.setdefault(title,[]).append({
                "museum_source":r.get("museum_source") or "gallery",
                "runtime_id":r.get("id"),"runtime_title":r.get("title"),
                "runtime_artist":r.get("artist_title"),
                "catalog":rel,
                "normalized_artist":author,
            })
    return seen,totals,skipped


def runtime_collision(row, index, artists):
    """Conservative title+artist signal, not automatic same-artwork proof."""
    t=norm(row.get("title"))
    if not t:
        return []
    aid=row.get("artist_id")
    names=[norm(x) for x in artists.get(aid,[])]
    if not names:
        return []
    out=[]
    for r in index.get(t,[]):
        author=r["normalized_artist"]
        if any(name and (
                author==name or author.startswith(name+" ") or
                " "+name+" " in " "+author+" ") for name in names):
            out.append({k:r.get(k) for k in (
                "catalog","runtime_id","museum_source","runtime_title",
                "runtime_artist")})
    return out[:10]


def prioritize(row, pix, decision):
    issues=[]
    title=str(row.get("title") or "")
    lower=title.lower()
    if NON_ART_RE.search(title):
        issues.append("POSSIBLE_PRINT_OR_NON_ART_REPRODUCTION")
    if FRAME_RE.search(title):
        issues.append("FRAMED_REPRODUCTION_ARTIFACT")
    if SUBJECT_RE.search(title):
        issues.append("POSSIBLE_PEOPLE_CENTERED_SUBJECT")
    if not LANDSCAPE_RE.search(title) and not row.get(
            "explicit_work_target"):
        issues.append("SUBJECT_NOT_IDENTIFIED_FROM_TITLE")
    if row.get("image_mime") and row["image_mime"].lower() not in {
            "image/jpeg","image/png","image/webp","image/tiff"}:
        issues.append("UNSUPPORTED_MEDIA_FORMAT")
    # Keep rights separate from metadata. Public-domain declarations
    # are not sufficient for item-level attribution/territory checks.
    license_text=str(row.get("source_license_claim") or "").strip()
    if not license_text or "unverified" in license_text.lower():
        issues.append("IMAGE_LICENSE_NOT_EVIDENCED")
    if row.get("institutional_origin_confirmed") is False:
        issues.append("MUSEUM_CUSTODY_NOT_EVIDENCED")
    if not row.get("work_year") and not row.get("creation_date_raw"):
        issues.append("CREATION_DATE_MISSING")
    if row.get("image_sha256") is None and pix is None:
        issues.append("NO_REAL_PIXEL_CHECK_YET")
    if decision:
        category=decision["decision"]
        if category.startswith(("REJECT_","HOLD_")):
            lane="CURATORIAL_REJECT_OR_HOLD"
        elif category.startswith(("PRIORITY_","REVIEW_NAMED_ARTWORK")):
            lane="USER_PALETTE_PRIORITY_VISUAL_RIGHTS_REVIEW"
        else:
            lane="CURATORIAL_OTHER"
        issues.append("EXISTING_14_IMAGE_CURATORIAL_DISPOSITION")
    elif row.get("explicit_work_target"):
        lane="USER_EXACT_WORK_IDENTITY_AND_RIGHTS_CHECK"
    elif pix and pix.get("color_tier") and not str(
            pix["color_tier"]).startswith("HOLD"):
        lane="BRIGHT_PIXELS_REVIEW_SUBJECT_AND_LICENSE"
    elif pix:
        lane="PIXEL_CHECKED_DIM_REVIEW_VARIANTS"
    elif any(x in issues for x in (
            "POSSIBLE_PRINT_OR_NON_ART_REPRODUCTION",
            "UNSUPPORTED_MEDIA_FORMAT",
            "FRAMED_REPRODUCTION_ARTIFACT",
            "POSSIBLE_PEOPLE_CENTERED_SUBJECT")):
        lane="SOURCE_REFERENCE_NOT_PRIORITY"
    else:
        lane="SCENIC_OR_STYLE_VISUAL_CHECK_PENDING"
    return lane,sorted(set(issues))


def build(source, pixel_source, curation, runtime_index=None, runtime_totals=None,
          runtime_missing=None, seed=None):
    rows=source.get("priority_shortlist")
    if not isinstance(rows,list):
        raise ValueError("Missing complete artist candidate inventory")
    painters={a["id"]:a["aliases"] for a in seed["artists"]}
    permitted=set(painters)
    px={x["identity"]:x for x in pixel_source.get("records") or []}
    decisions={x["identity"]:x for x in curation.get("individual_decisions") or []}
    result=[]
    seen=set()
    counts=Counter()
    per_artist=defaultdict(Counter)
    for row in rows:
        identity=row.get("identity")
        aid=row.get("artist_id")
        if not identity or identity in seen:
            raise ValueError("Missing or repeated source identity in artist inventory")
        if aid not in permitted:
            raise ValueError("Unregistered artist in source evidence")
        if row.get("commercially_approved") is not False or row.get(
                "runtime_visible") is not False:
            raise ValueError("Research-only candidate invariant violated")
        seen.add(identity)
        pix=px.get(identity)
        decision=decisions.get(identity)
        lane,issues=prioritize(row,pix,decision)
        linked=runtime_collision(row,runtime_index or {},painters)
        if linked:
            issues.append("POSSIBLE_RUNTIME_DUPLICATE_EXACT_TITLE_ARTIST")
        record={
            "source_identity":identity,"artist_id":aid,
            "title":row.get("title"),
            "source":row.get("source"),
            "record_url":row.get("record_url"),
            "preview_url":row.get("preview_url"),
            "explicit_work_target":row.get("explicit_work_target"),
            "raw_year":row.get("work_year") or row.get("creation_date_raw"),
            "image_license_claim":row.get("source_license_claim"),
            "artist_attribution":row.get("artist_attribution"),
            "origin_confirmed":row.get("institutional_origin_confirmed"),
            "technical_color_tier":pix.get("color_tier") if pix else row.get("color_tier"),
            "pixel_checked":bool(pix and pix.get("status")=="PIXELS_CHECKED_HOLD"),
            "pixel_sha256":pix.get("pixel_sha256") if pix else row.get("image_sha256"),
            "preliminary_curator_decision":decision.get("decision") if decision else None,
            "review_lane":lane,
            "risk_codes":sorted(issues),
            "possible_existing_runtime_matches":linked,
            "visual_review":"HOLD",
            "work_and_image_licenses":"HOLD_PER_ITEM_TERRITORY",
            "commercially_approved":False,"runtime_visible":False,
        }
        result.append(record)
        counts[lane]+=1
        per_artist[aid][lane]+=1
    # Ensure no one can accidentally use absence of review as approval.
    order={
        "USER_PALETTE_PRIORITY_VISUAL_RIGHTS_REVIEW":0,
        "USER_EXACT_WORK_IDENTITY_AND_RIGHTS_CHECK":1,
        "BRIGHT_PIXELS_REVIEW_SUBJECT_AND_LICENSE":2,
        "SCENIC_OR_STYLE_VISUAL_CHECK_PENDING":3,
        "PIXEL_CHECKED_DIM_REVIEW_VARIANTS":4,
        "CURATORIAL_REJECT_OR_HOLD":5,
        "SOURCE_REFERENCE_NOT_PRIORITY":6,
    }
    result.sort(key=lambda r:(order.get(r["review_lane"],9),
                              r["artist_id"],norm(r["title"]),
                              r["source_identity"]))
    return {
        "schema_version":1,
        "as_of_utc":datetime.now(timezone.utc).isoformat(),
        "scope":"USER_SELECTED_SEVEN_PAINTERS_OFFLINE_RESEARCH_TRIAGE",
        "source_artist_matches":source.get("artist_matched_distinct_files"),
        "all_candidate_records_retained":len(result),
        "processed_without_new_museum_or_commons_requests":True,
        "review_lanes":dict(counts),
        "artist_lanes":{a:dict(v) for a,v in sorted(per_artist.items())},
        "pixel_qa_records_available":sum(r["pixel_checked"] for r in result),
        "exact_user_work_records":sum(bool(r["explicit_work_target"]) for r in result),
        "runtime_catalog_row_counts":runtime_totals or {},
        "runtime_catalogs_not_available":runtime_missing or [],
        "possible_runtime_collision_candidates":sum(bool(
            r["possible_existing_runtime_matches"]) for r in result),
        "complete_queue":result,
        "not_proven_unique_paintings":True,
        "commercially_approved":0,
        "runtime_imported":0,
        "main_modified":False,
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--runtime-root",type=Path)
    args=parser.parse_args()
    idx,tot,skips=({}, {}, list(RUNTIME_FILES))
    if args.runtime_root:
        idx,tot,skips=runtime_catalog_index(args.runtime_root)
    data=build(load(SOURCE),load(PIXELS),load(CURATION),
               idx,tot,skips,load(SEEDS))
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",
                      encoding="utf-8")
    print(json.dumps({k:v for k,v in data.items() if k!="complete_queue"},
                     ensure_ascii=False),flush=True)


if __name__=="__main__":
    main()
