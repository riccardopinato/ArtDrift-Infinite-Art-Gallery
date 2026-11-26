#!/usr/bin/env python3
"""Art Drift dark-area A/B threshold policy on original raster-derived evidence.

Retroactively compare the 10%, 15%, 20% limits from stored per-image metrics.
No image pixels modified; no historical catalog/report rewritten; no runtime
asset publication. Commons held records were capped at 100 per batch, so
recovery numbers are measured *minimums* and not claims of exhaustive search.
"""
from __future__ import annotations
import argparse
import json
from collections import defaultdict, Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
EVIDENCE=ROOT/".artdrift_dark_ab_evidence"
OUTPUT=ROOT/"research/experiments/20261126/dark_threshold_10_15_20.json"
THRESHOLDS=(.10,.15,.20)
LUMINANCE_MIN=.55
SATURATION_MIN=.18
VIVID_MIN=.18
SECOND_TIER_SAT_MIN=.24
SECOND_TIER_VIVID_MIN=.30

def pixel_eligible(c,limit):
    """Color pass under requested dark ratio; never trust prior bright_pass flag."""
    return (
        isinstance(c,dict)
        and all(isinstance(c.get(k),(float,int)) for k in (
            "luminance","saturation","vivid_fraction","dark_fraction"))
        and c["luminance"]>=LUMINANCE_MIN
        and c["saturation"]>=SATURATION_MIN
        and c["vivid_fraction"]>=VIVID_MIN
        and c["dark_fraction"]<=limit
    )

def color_tier(c):
    if not pixel_eligible(c,.20):
        return "HOLD_DARK_OR_MUTED"
    if c["dark_fraction"]<=.15:
        return "PREFERRED_AT_MOST_15_PERCENT_DARK"
    if c["saturation"]>=SECOND_TIER_SAT_MIN and c["vivid_fraction"]>=SECOND_TIER_VIVID_MIN:
        return "CONDITIONAL_15_TO_20_PERCENT__HIGH_CHROMA"
    return "HOLD_15_TO_20_PERCENT__NOT_VIVID_ENOUGH"

def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))

def observations(folder):
    """Read item metrics, deduplicating by official source ID across shard results."""
    files=sorted(folder.rglob("review.json"))
    if not files:raise RuntimeError(f"No shard evidence: {folder}")
    records={}; omitted=0; available=0; extracted=[]; errors=0
    for p in files:
        raw=read_json(p)
        available+=int(raw.get("images_probed") or 0)
        works=raw.get("works") or []
        holds=raw.get("holds") or []
        for item in works:
            ident=str(item.get("museum_native_id") or item.get("file_pageid") or "")
            metric=item.get("color_metrics")
            if not ident or not metric:continue
            records.setdefault(ident,{"id":ident,"metric":metric,"baseline":"pass",
                                      "title":item.get("title"),"source_file":str(p)})
        for item in holds:
            ident=str(item.get("native_id") or item.get("id") or "")
            c=item.get("color_metrics") or item.get("metrics")
            if not ident or not c:continue
            if ident not in records:
                records[ident]={"id":ident,"metric":c,"baseline":"hold",
                                "title":item.get("title"),"source_file":str(p)}
        # Report may cap hold details to 100 items; the remaining are unmeasurable.
        # Cannot subtract blindly: duplicates and fetch failures need explicit status.
        extracted.append({"path":str(p.relative_to(EVIDENCE)),
                          "probed":raw.get("images_probed"),
                          "held_reported":raw.get("dark_or_media_holds") or raw.get("hold_count"),
                          "held_metrics_available":sum(bool(x.get("metrics") or x.get("color_metrics"))
                                                       for x in holds),
                          "works":len(works)})
    return records,extracted

def eligible_count(records,threshold):
    return sum(pixel_eligible(v["metric"],threshold) for v in records.values())

def new_candidates(records,threshold):
    return sorted([
        {"id":x["id"],
         "title":x["title"],
         "dark_fraction":x["metric"]["dark_fraction"],
         "luminance":x["metric"]["luminance"],
         "saturation":x["metric"]["saturation"],
         "vivid_fraction":x["metric"]["vivid_fraction"],
         "tier":color_tier(x["metric"]),
         "source_file":x["source_file"],
         "metadata_not_carried_in_rejected_shard":x["title"] is None}
        for x in records.values()
        if x["baseline"]=="hold" and pixel_eligible(x["metric"],threshold)
    ],key=lambda x:(x["dark_fraction"],x["id"]))

def source_report(name,folder,baseline_count=None):
    rec,shards=observations(folder)
    stats={str(round(th*100)):eligible_count(rec,th) for th in THRESHOLDS}
    rec15=new_candidates(rec,.15)
    rec20=new_candidates(rec,.20)
    # Old data may contain same id in multiple shards; count unique IDs only.
    strong20=[v for v in rec20 if v["tier"]=="CONDITIONAL_15_TO_20_PERCENT__HIGH_CHROMA"]
    return {"source":name,"batch_shards_available":len(shards),
            "unique_image_ids_with_pixels":len(rec),
            "old_total_pixel_verified_pass_from_published_summary":baseline_count,
            "pixel_eligible_counts":stats,
            "measurable_new_at_15_vs_10":[v for v in rec15 if .10<v["dark_fraction"]<=.15],
            "measurable_new_at_20_vs_10":[v for v in rec20 if .10<v["dark_fraction"]<=.20],
            "measurable_new_only_between_15_and_20":[v for v in rec20
                if .15<v["dark_fraction"]<=.20],
            "strong_color_between_15_and_20":strong20,
            "batch_evidence":shards}

def nga_reinstate():
    p=ROOT/"research/nga/20261126/nga_bright_combined_shortlist.json"
    j=read_json(p)
    dark=j["wave1_hold_dark"]
    return {"baseline_preferred_10_percent":j["total_aesthetically_eligible_candidates"],
            "previously_held_only_for_dark_area":[
                {**v,"reinstated_at_15_percent":v["dark_fraction"]<=.15,
                 "reinstated_at_20_percent":v["dark_fraction"]<=.20}
                for v in dark],
            "reinstated_at_15":sum(v["dark_fraction"]<=.15 for v in dark),
            "reinstated_at_20":sum(v["dark_fraction"]<=.20 for v in dark),
            "not_a_global_recalculation":True}

def main(evidence,out):
    global EVIDENCE
    EVIDENCE=evidence
    source_data={}
    for provider,sub in (("commons","commons"),("smk","smk"),("cma","cma")):
        source_data[provider]=source_report(provider,evidence/sub)
    # MET verification held items only saved statuses, not pixel metrics.
    # A new network probe would be needed to recover its dark-but-colorful cases.
    report={
        "schema_version":1,
        "date":"2026-11-26",
        "repository":"riccardopinato/ArtDrift-Infinite-Art-Gallery",
        "comparison":"10% baseline vs 15% preferred vs 20% experimental",
        "pixel_dark_definition":"Fraction of sampled inner image with luminance < 0.31",
        "other_filters_unchanged":{
            "luminance_min":LUMINANCE_MIN,
            "saturation_min":SATURATION_MIN,
            "vivid_fraction_min":VIVID_MIN},
        "new_policy":{
            "preferred_dark_fraction_max":.15,
            "conditional_dark_fraction_max":.20,
            "conditional_saturation_min":SECOND_TIER_SAT_MIN,
            "conditional_vivid_fraction_min":SECOND_TIER_VIVID_MIN,
            "dark_above_20_percent":"REJECT",
            "all_new_candidates":"HOLD_DUPLICATES_ATTRIBUTION_VISUAL_AND_TERRITORY_RIGHTS"},
        "source_evidence":{
            "commons":{"workflow_run_id":45815982003,
                       "artifact_pattern":"Commons-PD-Bright-*",
                       "historical_10_percent_unique_pass":113},
            "cma":{"workflow_run_id":45813706451,
                   "artifact_pattern":"ArtDrift-BrightMass-cma-*",
                   "historical_10_percent_unique_pass":8},
            "smk":{"workflow_run_id":45814424944,
                   "artifact_pattern":"SMK-Bright-Art-*",
                   "historical_10_percent_unique_pass":7},
            "nga":{"manifest":"research/nga/20261126/nga_bright_combined_shortlist.json",
                   "historical_10_percent_editorial_candidates":27},
            "met":{"artifact_limitation":"Most 257 rejected images have no stored numeric metrics",
                   "status":"NOT_RECOMPUTABLE_OFFLINE"}},
        "source_comparisons":source_data,
        "nga_dark_held":nga_reinstate(),
        "met_rejected_without_metrics_count":257,
        "met_dark_15_20_delta":"NOT_MEASURED",
        "user_visible_warning":"Measured lower bounds for Commons due to capped held records; "
        "pixel-eligible does not mean a new distinct painting or cleared copyright.",
        "runtime_imported":0,"commercially_cleared":0}
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    summary={
        "commons":{k:report["source_comparisons"]["commons"][k] for k in
                   ("unique_image_ids_with_pixels","pixel_eligible_counts")},
        "cma":report["source_comparisons"]["cma"]["pixel_eligible_counts"],
        "smk":report["source_comparisons"]["smk"]["pixel_eligible_counts"],
        "nga_restore_at_15":report["nga_dark_held"]["reinstated_at_15"],
        "nga_restore_at_20":report["nga_dark_held"]["reinstated_at_20"],
        "met_delta":"NOT_MEASURED","runtime_imported":0}
    print(json.dumps(summary,ensure_ascii=False,sort_keys=True))
    assert report["source_comparisons"]["commons"]["pixel_eligible_counts"]["10"]>=113
    assert report["source_comparisons"]["commons"]["pixel_eligible_counts"]["15"]>=120
    assert report["source_comparisons"]["commons"]["pixel_eligible_counts"]["20"]>=127
    assert report["nga_dark_held"]["reinstated_at_15"]==2
    return report

if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("--evidence-root",type=Path,default=EVIDENCE)
    a.add_argument("--output",type=Path,default=OUTPUT)
    args=a.parse_args()
    main(args.evidence_root,args.output)
