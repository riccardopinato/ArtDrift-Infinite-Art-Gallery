#!/usr/bin/env python3
"""Verify the preliminary 14-image visual triage against actual raster evidence.

No new HTTP requests. Does not publish artwork, approve rights or modify app.
"""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"research/artists/20261126"
DECISIONS=BASE/"preliminary_visual_triage.json"
PIXELS=BASE/"artist_pixel_visual_evidence.json"
OUTPUT=BASE/"curatorial_triage_verified.json"

CATEGORIES={
    "PRIORITY_MAIN_LUMINOUS",
    "PRIORITY_MAIN_NEAR_MISS",
    "PRIORITY_ACCENT_INTERIOR_USER_CHOICE",
    "REVIEW_NAMED_ARTWORK_VARIANT",
    "REJECT_SAMPLE_FRAMED_REPRODUCTION",
    "REJECT_SUBJECT_PEOPLE_CENTRED",
    "REJECT_SOURCE_IS_PRINT_REPRODUCTION",
    "HOLD_TOO_DARK",
    "HOLD_TOO_DARK_OR_MUTED",
    "HOLD_SEMANTIC_DUPLICATE_AND_DARK",
    "HOLD_TOO_DARK_AND_PROVENANCE",
    "HOLD_DIM_MOORLAND_STUDY",
}
PRIORITY_PREFIXES=("PRIORITY_", "REVIEW_NAMED_ARTWORK")


def verify(decisions,pixels):
    if decisions.get("runtime_imported",0)!=0 or decisions.get("commercially_approved",0)!=0:
        raise ValueError("Unsafe curatorial approvals")
    raw=[x for x in pixels.get("records") or [] if x.get("status")=="PIXELS_CHECKED_HOLD"]
    record_map={x["identity"]:x for x in raw}
    if len(record_map)!=len(raw):
        raise ValueError("Duplicate pixel identity")
    items={}
    for entry in decisions["works"]:
        ident=entry["identity"]
        if ident in items:
            raise ValueError("Duplicate decision identity")
        if ident not in record_map:
            raise ValueError("Decision without measured source pixels: "+ident)
        source=record_map[ident]
        if not source.get("pixel_sha256") or not source.get("color_metrics"):
            raise ValueError("Missing real raster measurement")
        category=entry["decision"]
        if category not in CATEGORIES:
            raise ValueError("Unknown decision category")
        if category.startswith("PRIORITY_MAIN_") and source.get(
                "explicit_work_target") == "karsten_blue_kitchen":
            raise ValueError("Interior cannot automatically enter bright main feed")
        if category=="PRIORITY_MAIN_LUMINOUS" and not source[
                "color_metrics"].get("bright_pass"):
            raise ValueError("Main luminous work must meet raster gate")
        if category=="PRIORITY_MAIN_NEAR_MISS" and (
                source["color_metrics"].get("dark_fraction",1)>.15 or
                source["color_metrics"].get("luminance",0)<.5):
            raise ValueError("Near miss needs evidence of near-bright painting")
        if category=="PRIORITY_ACCENT_INTERIOR_USER_CHOICE" and source.get(
                "explicit_work_target")!="karsten_blue_kitchen":
            raise ValueError("User accent exception only for named Karsten artwork")
        row={
            "identity":ident,
            "source_painter":source.get("artist_id"),
            "title":source.get("title"),
            "record_url":source.get("record_url"),
            "source_image_license":source.get("source_license_claim"),
            "image_sha256":source.get("pixel_sha256"),
            "pixel_metrics":source.get("color_metrics"),
            "decision":category,
            "reason":entry.get("rationale"),
            "reference_url":entry.get("reference_url"),
            "next_step":entry.get("required_next_step"),
            "human_user_acceptance":False,
            "commercially_approved":False,
            "runtime_visible":False,
        }
        items[ident]=row
    if len(items)!=len(record_map):
        raise ValueError("Missing individual preliminary decisions")
    count=Counter(x["decision"] for x in items.values())
    priority=[x for x in items.values()
              if x["decision"].startswith(PRIORITY_PREFIXES)]
    return {
        "schema_version":1,
        "as_of_utc":datetime.now(timezone.utc).isoformat(),
        "reviewed_raster_samples":len(items),
        "categories":dict(count),
        "user_palette_priority_candidates":[x["identity"] for x in priority],
        "priority_candidate_count":len(priority),
        "technical_color_pass_count":sum(1 for x in items.values()
                if x["pixel_metrics"].get("bright_pass") is True),
        "rights_source_still_requires_approval":True,
        "visual_decisions_are_not_user_acceptance":True,
        "individual_decisions":[items[k] for k in sorted(items)],
        "commercially_approved":0,
        "runtime_imported":0,
    }


def main():
    decisions=json.loads(DECISIONS.read_text(encoding="utf-8"))
    pixels=json.loads(PIXELS.read_text(encoding="utf-8"))
    result=verify(decisions,pixels)
    OUTPUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",
                      encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k!="individual_decisions"},
                     ensure_ascii=False),flush=True)


if __name__=="__main__":
    main()
