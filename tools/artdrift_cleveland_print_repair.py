#!/usr/bin/env python3
"""Propose (never execute) D1 HOLD-only repair for Cleveland print image fallbacks.

Consumes a same-run official CMA item audit and validated original JSONL.
The generated SQL is a fingerprint-guarded, inspectable review artifact.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from artdrift_museum_ingest import (
    FIELDS, fingerprint, record, safe_https, sql_literal,
)


def prepare(audit: dict, originals: list[dict]) -> tuple[list[dict], str]:
    if audit.get("total") != 49 or audit.get("all_publication_status") != "HOLD":
        raise ValueError("Invalid or incomplete rights audit")
    if audit.get("editorial_approved") != 0 or audit.get("published") != 0:
        raise ValueError("A rights review is not approval")
    if len(audit.get("works") or []) != 49:
        raise ValueError("Missing per-object audit evidence")
    by_key = {r.get("source_key"): r for r in originals}
    if len(by_key) != len(originals):
        raise ValueError("Repeated stage identities")
    proposals, statements = [], []
    for row in audit["works"]:
        if row.get("source_check") != "SOURCE_MATCH_PREVIEW_FALLBACK":
            continue
        if row.get("review_flags") != ["preview_used_as_full_image"]:
            raise ValueError("Unexpected source warning; fail closed")
        key = row.get("source_key")
        existing = by_key.get(key)
        if not existing or set(existing) != set(FIELDS):
            raise ValueError(f"No canonical stage for {key}")
        if existing.get("provider") != "cleveland":
            raise ValueError("Only Cleveland print-image changes permitted")
        if row.get("fingerprint") != existing.get("fingerprint") or fingerprint(existing) != existing["fingerprint"]:
            raise ValueError("Staging fingerprint no longer matches API evidence")
        if existing["image_url"] != existing["full_image_url"] or existing["rights_status"] != "IMAGE_RIGHTS_VERIFIED":
            raise ValueError("Not an image fallback")
        if row.get("current_share_license_status") != "CC0":
            raise ValueError("CMA license no longer CC0")
        current = row.get("current_official_print_url") or ""
        if not safe_https(current, {"openaccess-cdn.clevelandart.org"}):
            raise ValueError("Untrusted official image URL")
        if current == existing["image_url"] or not current.endswith("_print.jpg"):
            raise ValueError("Unexpected official print-image format")
        changed = record(
            provider=existing["provider"], native_id=existing["native_id"],
            museum=existing["museum"], title=existing["title"],
            artist=existing["artist"], year=existing["year_text"],
            medium=existing["medium"], metadata_url=existing["metadata_url"],
            image_url=existing["image_url"], full_image_url=current,
            rights_license=existing["rights_license"],
            rights_evidence_url=existing["rights_evidence_url"],
            rights_status=existing["rights_status"])
        if changed["source_key"] != key:
            raise ValueError("Source identity changed")
        # Explicit HOLD invariant, source fingerprint prevents stale writes.
        sql = (
            "UPDATE artdrift_museum_ingest SET "
            f"full_image_url={sql_literal(current)}, "
            f"fingerprint={sql_literal(changed['fingerprint'])}, "
            "publication_status='HOLD', updated_at=CURRENT_TIMESTAMP "
            f"WHERE source_key={sql_literal(key)} "
            f"AND fingerprint={sql_literal(existing['fingerprint'])} "
            f"AND full_image_url={sql_literal(existing['full_image_url'])} "
            "AND rights_status='IMAGE_RIGHTS_VERIFIED' "
            "AND publication_status='HOLD';"
        )
        statements.append(sql)
        proposals.append({
            "source_key": key, "title": existing["title"], "artist": existing["artist"],
            "previous_fingerprint": existing["fingerprint"],
            "new_fingerprint": changed["fingerprint"],
            "source_api": row["source_api"],
            "previous_full_image_url": existing["full_image_url"],
            "verified_print_url": current,
            "publication_status_after": "HOLD",
        })
    if len(proposals) != 28:
        raise ValueError(f"Expected 28 evidence-complete corrections, found {len(proposals)}")
    if len({x["source_key"] for x in proposals}) != 28:
        raise ValueError("Duplicate corrected work")
    return proposals, "-- Review only; do not auto-deploy. All corrections remain HOLD.\n" + "\n".join(statements) + "\n"


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--audit", type=Path, required=True)
    p.add_argument("--stage", type=Path, required=True)
    p.add_argument("--out", type=Path, default=Path(".artdrift_ingest/cleveland-print-repair.sql"))
    args = p.parse_args()
    audit = json.loads(args.audit.read_text(encoding="utf-8"))
    originals = [json.loads(line) for line in args.stage.read_text(encoding="utf-8").splitlines()]
    changes, sql = prepare(audit, originals)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(sql, encoding="utf-8")
    args.out.with_suffix(".json").write_text(json.dumps(changes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("CLEVELAND_REPAIR_PROPOSALS_HOLD_ONLY", len(changes))


if __name__ == "__main__":
    main()
