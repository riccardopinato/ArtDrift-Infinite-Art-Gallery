#!/usr/bin/env python3
"""Merge independently acquired Art Drift museum stages into one rights-gated D1 batch.

No web requests, media downloads or D1 writes. Every input is canonicalized
through the same provider policies used during initial acquisition.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from artdrift_museum_ingest import FIELDS, export, record


def combine(paths: list[Path]) -> tuple[list[dict], dict]:
    if not paths:
        raise ValueError("No input stages supplied")
    works: dict[str, dict] = {}
    provider_counts: Counter[str] = Counter()
    duplicates = 0
    for path in paths:
        if not path.is_file():
            raise FileNotFoundError(path)
        content = path.read_text(encoding="utf-8")
        if not content.strip():
            raise ValueError(f"Empty stage file: {path}")
        for line_no, raw in enumerate(content.splitlines(), start=1):
            try:
                incoming = json.loads(raw)
            except ValueError as exc:
                raise ValueError(f"Bad JSONL: {path}:{line_no}") from exc
            if not isinstance(incoming, dict) or set(incoming) != set(FIELDS):
                raise ValueError(f"Invalid canonical fields: {path}:{line_no}")
            fresh = record(
                provider=incoming["provider"], native_id=incoming["native_id"],
                museum=incoming["museum"], title=incoming["title"],
                artist=incoming["artist"], year=incoming["year_text"],
                medium=incoming["medium"], metadata_url=incoming["metadata_url"],
                image_url=incoming["image_url"], full_image_url=incoming["full_image_url"],
                rights_license=incoming["rights_license"],
                rights_evidence_url=incoming["rights_evidence_url"],
                rights_status=incoming["rights_status"],
            )
            if incoming != fresh:
                raise ValueError(f"Modified/fingerprint-mismatched record: {path}:{line_no}")
            key = fresh["source_key"]
            if key in works:
                if works[key] != fresh:
                    raise ValueError(f"Conflicting staged record: {key}")
                duplicates += 1
                continue
            works[key] = fresh
            provider_counts[fresh["provider"]] += 1
    return list(works.values()), {
        "providers": dict(sorted(provider_counts.items())),
        "identical_duplicates_dropped": duplicates,
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("inputs", nargs="+", type=Path, help="Individually approved JSONL stages")
    p.add_argument("--jsonl", type=Path, default=Path(".artdrift_ingest/modern_art.jsonl"))
    p.add_argument("--sql", type=Path, default=Path(".artdrift_ingest/modern_art.sql"))
    args = p.parse_args()
    works, details = combine(args.inputs)
    if not works:
        raise SystemExit("FAIL CLOSED: empty combined catalog")
    totals = export(works, args.jsonl, args.sql)
    print(json.dumps({**totals, **details}, sort_keys=True))


if __name__ == "__main__":
    main()
