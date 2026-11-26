#!/usr/bin/env python3
"""Merge official Städel staged LIDO details into existing museum HOLD inventory.

No OAI requests, image downloads, commercial approvals or runtime import.
"""
from __future__ import annotations

import json
from pathlib import Path
from artdrift_parallel_museum_reconcile import reconcile,queue

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"research/museums/20261126/lanes"
RESULT=BASE/"results/staedel.json"
DETAIL=BASE/"staedel_lido_detail_sample.json"
SHORTLIST=BASE/"reviews/staedel_visual_shortlist.json"


def merge(previous:dict,detail:dict):
    if detail.get("provider")!="staedel":
        raise ValueError("Wrong official detail source")
    if detail.get("commercially_approved",0)!=0 or detail.get("runtime_imported",0)!=0:
        raise ValueError("Unsafe detail manifest")
    latest={
        "provider":"staedel",
        "date_utc":detail.get("as_of_utc"),
        "review_candidates":detail.get("review_candidates") or [],
        "candidates_in_report":len(detail.get("review_candidates") or []),
        "metadata_identifiers_discovered_or_scanned":detail.get(
            "total_new_metadata_processed",0),
        "source_identifier_sample":detail.get("processed_oai_identifiers") or [],
        "stats":detail.get("stats") or {},
        "errors":detail.get("errors") or [],
        "runtime_imported":0,
        "commercially_approved":0,
        "source_approach":"OFFICIAL_OAI_LIDO_STAGED_DETAILS",
        "stage2_source_429_stopped":bool(detail.get("source_429_stopped")),
    }
    combined=reconcile(latest,previous,None)
    combined["stage2_details_metadata_processed"]=detail.get(
        "total_new_metadata_processed",0)
    combined["stage2_source_429_stopped"]=bool(detail.get("source_429_stopped"))
    combined["rights_status"]="HOLD_CC_BY_SA_OFFICIAL_IMAGE_AND_PER_OBJECT"
    return combined


def main():
    before=json.loads(RESULT.read_text(encoding="utf-8"))
    detail=json.loads(DETAIL.read_text(encoding="utf-8"))
    result=merge(before,detail)
    shortlist=queue(result,limit=120)
    RESULT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",
                      encoding="utf-8")
    SHORTLIST.parent.mkdir(parents=True,exist_ok=True)
    SHORTLIST.write_text(json.dumps(shortlist,ensure_ascii=False,indent=2)+"\n",
                         encoding="utf-8")
    print(json.dumps({"provider":"staedel",
          "cumulative_records":result["cumulative_distinct_candidate_records"],
          "stage2_records_processed":result["stage2_details_metadata_processed"],
          "visual_review_queue":len(shortlist["items_for_review"]),
          "commercially_approved":0,"runtime_imported":0}),flush=True)


if __name__=="__main__":
    main()
