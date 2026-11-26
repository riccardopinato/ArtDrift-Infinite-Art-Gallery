#!/usr/bin/env python3
"""Lossless, idempotent research reconciliation for independent museum lanes.

Inputs are limited discovery samples. A 429/timeout must never delete a
previously saved candidate or convert an incomplete sample to a museum zero.
The curated queue is only a human review aid: NOT a release manifest.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

OUTROOT = Path(__file__).resolve().parents[1] / "research/museums/20261126/lanes"
EMPTY = (None, "", [], {})
EXCLUDES = re.compile(r"\b(?:portrait|self.portrait|dolls?|puppets?|toys?|"
                      r"battles?|nocturne|book|catalogue|catalog|"
                      r"gardeners.? chronicle)\b", re.I)


def load(path: Path | None) -> dict | None:
    if path is None or not path.is_file():
        return None
    content = path.read_text(encoding="utf-8").strip()
    if not content:
        raise ValueError(f"Existing inventory empty, do not overwrite: {path}")
    obj = json.loads(content)
    if not isinstance(obj, dict):
        raise ValueError(f"Inventory must be object: {path}")
    return obj


def score(item: dict) -> int:
    return (90*bool(item.get("image_sha256")) +
            20*bool(item.get("color_metrics")) +
            18*bool(item.get("institutional_origin_confirmed")) +
            16*bool(item.get("image_license_checked")) +
            10*bool(item.get("remote_preview_url")) +
             8*bool(item.get("artist")) +
             5*bool(item.get("year")))


def record_key(item: dict, provider: str) -> str:
    if item.get("source") != provider:
        raise ValueError("Cross-source input in museum-only inventory")
    key = str(item.get("museum_native_id") or "").strip()
    if not key:
        raise ValueError("Missing stable museum_native_id")
    return key


def safest_record(old: dict, new: dict) -> dict:
    winner, other = (old, new) if score(old) >= score(new) else (new, old)
    merged = dict(winner)
    # Copy extra, independently collected evidence; never erase an image's
    # successful hash/measurements because a later server request failed.
    for field in ("image_sha256", "color_metrics", "color_tier",
                  "source_file_sha1", "file_sha1", "artist", "year",
                  "remote_preview_url", "remote_full_url", "original_media_url",
                  "image_mime", "institutional_provenance",
                  "rights_evidence_url", "source_item_rights_text",
                  "image_license_per_item", "museum_url"):
        if merged.get(field) in EMPTY and other.get(field) not in EMPTY:
            merged[field] = other[field]
    # Do NOT upgrade approval from another report, even one containing a
    # mistaken flag. Per-object commercial permission is a separate process.
    merged["runtime_visible"] = False
    merged["commercially_approved"] = False
    claims = {str(r.get("image_license_per_item", "")) for r in (old, new)
              if r.get("image_license_per_item")}
    if len(claims) > 1:
        merged["license_claims_to_reconcile"] = sorted(claims)
        merged["review_status"] = "HOLD_CONFLICTING_LICENSE_EVIDENCE"
    if other.get("institutional_origin_confirmed") and not merged.get(
            "institutional_origin_confirmed"):
        merged["institutional_origin_confirmed"] = True
        merged["institutional_provenance"] = other.get(
            "institutional_provenance", "SEARCH_RECORD_MUSEUM_MATCH")
    return merged


def reconcile(latest: dict, previous: dict | None,
              snapshot: dict | None) -> dict:
    provider = latest.get("provider")
    if not isinstance(provider, str) or not provider:
        raise ValueError("Missing latest provider")
    sources = [("snapshot", snapshot), ("previous", previous), ("latest", latest)]
    inventory: dict[str, dict] = {}
    raw_ids = set()
    observations = []
    observed_keys = set()
    for tag, source in sources:
        if source is None:
            continue
        if source.get("provider") != provider:
            raise ValueError(f"Wrong museum provider in {tag}")
        if source.get("runtime_imported", 0) != 0 or source.get(
                "commercially_approved", 0) != 0:
            raise ValueError(f"Release-gate violation in {tag}")
        for ident in source.get("source_identifier_sample") or []:
            if isinstance(ident, str) and ident.strip():
                raw_ids.add(ident.strip())
        for item in source.get("review_candidates") or []:
            if not isinstance(item, dict):
                raise ValueError(f"Invalid record in {tag}")
            k = record_key(item, provider)
            inventory[k] = (safest_record(inventory[k], item)
                            if k in inventory else dict(item))
            inventory[k]["runtime_visible"] = False
            inventory[k]["commercially_approved"] = False
        for obs in source.get("run_history") or []:
            marker = (obs.get("date_utc"), obs.get("candidate_count"),
                      obs.get("identifiers_discovered_or_scanned"))
            if marker not in observed_keys:
                observed_keys.add(marker)
                observations.append(obs)
    latest_marker = (latest.get("date_utc"),
                     latest.get("latest_run_candidates_in_report",
                                latest.get("candidates_in_report")),
                     latest.get("metadata_identifiers_discovered_or_scanned"))
    if latest_marker not in observed_keys:
        observations.append({
            "date_utc": latest.get("date_utc"),
            "candidate_count": latest_marker[1],
            "identifiers_discovered_or_scanned": latest_marker[2],
            "source_errors": (latest.get("errors") or [])[:8],
            "pixel_checked": (latest.get("stats") or {}).get("pixel_checked", 0),
        })
    # Explicitly record that we can only merge IDs present in retained files.
    # An API's estimated total is not an enumerated identifier inventory.
    result = dict(latest)
    result["schema_version"] = 2
    result["latest_run_candidates_in_report"] = latest_marker[1]
    result["latest_run_metadata_identifiers_discovered_or_scanned"] = (
        latest.get("metadata_identifiers_discovered_or_scanned"))
    result["review_candidates"] = [inventory[k] for k in sorted(inventory)]
    result["candidates_in_report"] = len(inventory)
    result["cumulative_distinct_candidate_records"] = len(inventory)
    result["cumulative_retained_source_identifiers"] = len(raw_ids)
    result["source_identifier_sample"] = sorted(raw_ids)
    result["run_history"] = observations[-40:]
    result["union_not_exhaustive"] = True
    result["catalog_exhaustively_searched"] = False
    result["source_zero_artworks_proven"] = False
    result["per_image_commercial_rights"] = "HOLD"
    result["cross_museum_dedupe"] = "PENDING_GLOBAL_ARTWORK_AND_FILE_HASH"
    result["runtime_imported"] = 0
    result["commercially_approved"] = 0
    result["cumulative_technical_color_pass_records"] = sum(
        1 for item in inventory.values()
        if item.get("color_tier") and
        not str(item["color_tier"]).startswith("HOLD"))
    return result


def review_priority(item: dict) -> tuple[int, str]:
    title = str(item.get("title") or "")
    remote = bool(item.get("remote_preview_url"))
    format_ok = item.get("supported_image_format") is not False and not (
        str(item.get("image_mime", "")).lower().endswith("pdf"))
    origin_ok = item.get("institutional_origin_confirmed") is not False
    license_ok = item.get("image_license_checked") is not False
    scene_ok = item.get("scenic_title_indicator") is not False
    subject_ok = not EXCLUDES.search(title) and scene_ok
    year = item.get("year")
    period_ok = not isinstance(year, int) or 1850 <= year <= 1960
    passed = item.get("color_tier") and not str(
        item["color_tier"]).startswith("HOLD")
    if not format_ok or not subject_ok or not origin_ok or not period_ok:
        return (3, title)
    if passed and remote and license_ok:
        return (0, title)
    if item.get("review_status") == "HOLD_HIGH_CHROMA_VISUAL" and remote:
        return (1, title)
    if remote and license_ok:
        return (2, title)
    return (3, title)


def queue(report: dict, limit: int = 100) -> dict:
    rows = sorted(report["review_candidates"], key=lambda r:
                  (review_priority(r)[0],
                   str(r.get("title") or "").casefold(),
                   str(r.get("museum_native_id") or "")))
    count = Counter(review_priority(r)[0] for r in rows)
    shortlisted = []
    for item in rows[:limit]:
        priority = review_priority(item)[0]
        if priority == 3:
            continue
        shortlisted.append({
            "source": report["provider"],
            "museum_native_id": item["museum_native_id"],
            "title": item.get("title"),
            "artist": item.get("artist"),
            "year": item.get("year"),
            "creation_date_raw": item.get("creation_date_raw"),
            "record_url": item.get("museum_url"),
            "preview_url": item.get("remote_preview_url"),
            "image_sha256": item.get("image_sha256"),
            "technical_color_tier": item.get("color_tier"),
            "color_metrics": item.get("color_metrics"),
            "license_statement": item.get("image_license_per_item"),
            "rights_evidence_url": item.get("rights_evidence_url"),
            "institutional_origin_confirmed":
                item.get("institutional_origin_confirmed"),
            "curatorial_priority": ["VISUAL_REVIEW_PRIORITY",
                                   "HIGH_CHROMA_NEAR_MISS",
                                   "METADATA_AND_IMAGE_REVIEW"][priority],
            "decision": "HOLD_HUMAN_VISUAL_AUTHOR_RIGHTS_DEDUP",
            "commercially_approved": False,
            "runtime_visible": False,
        })
    return {
        "schema_version": 1,
        "provider": report["provider"],
        "cumulative_inventory_records": report["candidates_in_report"],
        "ready_to_import": 0,
        "priority_counts": {str(k): v for k, v in sorted(count.items())},
        "queue_limit": limit,
        "items_for_review": shortlisted,
        "visual_approval": "PENDING",
        "copyright_review": "PENDING",
        "cross_museum_duplicates": "PENDING",
        "runtime_imported": 0,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", required=True)
    parser.add_argument("--prior", type=Path)
    parser.add_argument("--snapshot", type=Path)
    parser.add_argument("--max-review", type=int, default=100)
    args = parser.parse_args()
    if args.max_review < 1 or args.max_review > 300:
        parser.error("--max-review 1..300")
    path = OUTROOT / "results" / f"{args.provider}.json"
    current = load(path)
    if current is None:
        raise SystemExit("Latest research result missing: no replacement")
    reconciled = reconcile(current, load(args.prior), load(args.snapshot))
    result_queue = queue(reconciled, args.max_review)
    path.parent.mkdir(parents=True, exist_ok=True)
    target = OUTROOT / "reviews" / f"{args.provider}_visual_shortlist.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(reconciled, ensure_ascii=False, indent=2)+"\n",
                    encoding="utf-8")
    target.write_text(json.dumps(result_queue, ensure_ascii=False, indent=2)+"\n",
                      encoding="utf-8")
    print(json.dumps({
        "provider": args.provider,
        "latest_run_candidates": reconciled["latest_run_candidates_in_report"],
        "cumulative_distinct_candidates":
            reconciled["cumulative_distinct_candidate_records"],
        "source_identifiers_retained":
            reconciled["cumulative_retained_source_identifiers"],
        "color_pass_retained":
            reconciled["cumulative_technical_color_pass_records"],
        "visual_queue_count": len(result_queue["items_for_review"]),
        "commercially_approved": 0, "runtime_imported": 0,
    }, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
