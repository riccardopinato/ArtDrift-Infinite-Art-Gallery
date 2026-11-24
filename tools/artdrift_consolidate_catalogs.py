#!/usr/bin/env python3
"""Reconcile PR42/43 curated museum catalog with PR44 independent D1 stage.

This command reads bundled manifests and a same-run, validated staging JSONL.
No Cloudflare network, SQL writes, image downloads or publication decisions.
"""
from __future__ import annotations
import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "cloudflare/art-catalog/scripts"))
from make_museum_d1_import import SOURCES, normalize as normalize_museum
from artdrift_museum_ingest import FIELDS, fingerprint, record

def normalized_title(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value or "").casefold())

def canonical_stage(row: dict) -> dict:
    if not isinstance(row, dict) or set(row) != set(FIELDS):
        raise ValueError("Stage record fields mismatch")
    restored = record(
        provider=row["provider"], native_id=row["native_id"],
        museum=row["museum"], title=row["title"], artist=row["artist"],
        year=row["year_text"], medium=row["medium"],
        metadata_url=row["metadata_url"], image_url=row["image_url"],
        full_image_url=row["full_image_url"],
        rights_license=row["rights_license"],
        rights_evidence_url=row["rights_evidence_url"],
        rights_status=row["rights_status"],
    )
    if restored != row or fingerprint(row) != row["fingerprint"]:
        raise ValueError("Unvalidated or modified stage data")
    return restored

def reconcile(museum_rows: list[dict], stage_rows: list[dict]) -> dict:
    by_work = {}
    seen_keys = set()
    for row in museum_rows:
        source = row["museum_source"]
        native = row["museum_native_id"]
        key = (source, native)
        if key in by_work or row["source_key"] in seen_keys:
            raise ValueError("Duplicate museum identity or source key")
        by_work[key] = row
        seen_keys.add(row["source_key"])
    overlap = []
    new = []
    seen_staged = set()
    for incoming in stage_rows:
        row = canonical_stage(incoming)
        if row["source_key"] in seen_staged:
            raise ValueError("Duplicate staged identity")
        seen_staged.add(row["source_key"])
        identity = (row["provider"], row["native_id"])
        old = by_work.get(identity)
        if old is None:
            new.append(row)
            continue
        if normalized_title(old["title"]) != normalized_title(row["title"]):
            raise ValueError(f"Conflicting primary-source title: {identity}")
        overlap.append({
            "provider": row["provider"],
            "museum_native_id": row["native_id"],
            "existing_source_key": old["source_key"],
            "staged_source_key": row["source_key"],
            "title": row["title"],
        })
    counts = dict(sorted(Counter(r["provider"] for r in stage_rows).items()))
    new_counts = dict(sorted(Counter(r["provider"] for r in new).items()))
    # Treat identical source/native ID as same physical collection entry.
    # Never deduplicate on title+artist alone (e.g. many distinct "Untitled").
    return {
        "museum_catalog_records": len(museum_rows),
        "museum_catalog_distinct_source_native": len(by_work),
        "new_stage_records": len(stage_rows),
        "stage_provider_counts": counts,
        "already_present": len(overlap),
        "new_stage_distinct_records": len(new),
        "new_stage_provider_counts": new_counts,
        "hypothetical_distinct_records": len(by_work) + len(new),
        "overlap": sorted(overlap, key=lambda r: r["staged_source_key"]),
        "merging_strategy": "source and museum-native identity, not internal numeric ID",
        "title_only_cross_source_collisions": "not automatically deduplicated",
        "all_stage_publication_status": "HOLD",
        "automatic_approvals": 0,
        "remote_D1_writes": 0,
        "new_images_bundled": 0,
    }

def bundled_museum_rows(root: Path) -> list[dict]:
    works = []
    for path in SOURCES:
        full = root / path
        if not full.is_file():
            raise FileNotFoundError(full)
        contents = json.loads(full.read_text(encoding="utf-8"))
        if not isinstance(contents, list):
            raise ValueError(f"Not a museum catalog: {path}")
        for original in contents:
            normalized = normalize_museum(original)
            if normalized is None:
                raise ValueError(f"Invalid rights, URL, or identity: {path}")
            works.append(normalized)
    return works

def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--stage", required=True, type=Path)
    p.add_argument("--out", default=Path(".artdrift_ingest/consolidation_report.json"), type=Path)
    args = p.parse_args()
    original = bundled_museum_rows(ROOT)
    staged = [json.loads(line) for line in args.stage.read_text(encoding="utf-8").splitlines()]
    report = reconcile(original, staged)
    expected = {
        "museum_catalog_records": 5084,
        "new_stage_records": 535,
        "already_present": 49,
        "new_stage_distinct_records": 486,
        "hypothetical_distinct_records": 5570,
        "new_stage_provider_counts": {"moma": 253, "tate": 233},
        "stage_provider_counts": {"cleveland": 49, "moma": 253, "tate": 233},
    }
    for key, value in expected.items():
        if report[key] != value:
            raise ValueError(f"Expected {key}={value}, found {report[key]}")
    if any(r["provider"] != "cleveland" for r in report["overlap"]):
        raise ValueError("Unexpected overlap outside Cleveland source")
    if any(r["rights_status"] != "METADATA_ONLY" for r in staged if r["provider"] in ("moma", "tate")):
        raise ValueError("No rights evidence for Tate/MoMA images; metadata only")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print("ARTDRIFT_PR42_43_44_CONSOLIDATION_PASS",
          report["museum_catalog_records"], report["new_stage_records"],
          report["already_present"], report["hypothetical_distinct_records"])

if __name__ == "__main__":
    main()
