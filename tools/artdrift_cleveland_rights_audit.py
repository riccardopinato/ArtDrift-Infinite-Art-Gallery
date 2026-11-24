#!/usr/bin/env python3
"""Read-only per-object Cleveland Open Access audit of staged Art Drift images.

This does not publish or approve anything. Any uncertain field fails closed.
See https://openaccess-api.clevelandart.org/ for official API semantics.
"""
from __future__ import annotations

import argparse
import json
import re
import time
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError

from artdrift_museum_ingest import (
    collect_verified_catalog, request_json, safe_https,
)

API_ROOT = "https://openaccess-api.clevelandart.org/api/artworks/"
IMAGE_HOST = {"openaccess-cdn.clevelandart.org"}


def normalize(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s)).casefold()
    return re.sub(r"[^a-z0-9]", "", "".join(c for c in s if not unicodedata.combining(c)))


def assess(staged: dict, payload: dict) -> tuple[str, list[str]]:
    """Every positive assessment requires current, item-level primary source data."""
    notes = []
    if staged.get("provider") != "cleveland":
        return "SOURCE_REVIEW", ["unsupported_provider"]
    data = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(data, dict):
        return "SOURCE_REVIEW", ["missing_artwork_data"]
    if not str(staged["native_id"]).isdigit() or str(data.get("id")) != staged["native_id"]:
        notes.append("identity_mismatch")
    if normalize(data.get("title", "")) != normalize(staged.get("title", "")):
        notes.append("title_mismatch")
    if data.get("share_license_status") != "CC0":
        notes.append("not_current_cc0")
    if str(data.get("type", "")).casefold() != "painting":
        notes.append("not_current_painting")
    images = data.get("images") or {}
    web = (images.get("web") or {}) if isinstance(images, dict) else {}
    print_image = (images.get("print") or {}) if isinstance(images, dict) else {}
    if web.get("url") != staged.get("image_url") or not safe_https(
            str(web.get("url") or ""), IMAGE_HOST):
        notes.append("web_image_changed_or_untrusted")
    if print_image.get("url") != staged.get("full_image_url") or not safe_https(
            str(print_image.get("url") or ""), IMAGE_HOST):
        notes.append("print_image_changed_or_untrusted")
    if normalize(data.get("url", "")) != normalize(staged.get("metadata_url", "")):
        notes.append("detail_url_changed")
    # Source may name multiple authors or role assignments. No automatic
    # conclusion for copyright status of additional creators or third parties.
    creators = data.get("creators") or []
    if not isinstance(creators, list) or not creators:
        notes.append("author_death_not_independently_verified")
    else:
        names = [str(c.get("description") or "") for c in creators if isinstance(c, dict)]
        def author_pd(name: str) -> bool:
            pairs = re.findall(r"(?<!\d)(1[6789]\d{2}|20\d{2})\s*[-–—]\s*(1[789]\d{2}|20\d{2})(?!\d)", name)
            return len(pairs) == 1 and int(pairs[0][1]) <= 1955
        if len(names) != 1 or not author_pd(names[0]):
            notes.append("complex_or_unverified_author_copyright")
    if notes:
        return "NEEDS_REVIEW", notes
    return "PRIMARY_SOURCE_MATCH", ["editorial_and_legal_review_pending"]


def audit(max_records: int = 5000, delay: float = 0.45) -> dict:
    records = [r for r in collect_verified_catalog(max_records)
               if r["provider"] == "cleveland"]
    if len(records) != 49:
        raise ValueError(f"Expected 49 stable Cleveland candidates, got {len(records)}")
    out = []
    for record in records:
        url = API_ROOT + record["native_id"]
        entry = {
            "source_key": record["source_key"],
            "title": record["title"],
            "artist": record["artist"],
            "museum_detail": record["metadata_url"],
            "source_api": url,
            "rights_evidence": record["rights_evidence_url"],
            "fingerprint": record["fingerprint"],
            "publication_status": "HOLD",
        }
        try:
            payload = request_json(url, max_bytes=3_000_000)
            status, reasons = assess(record, payload)
        except (ValueError, TimeoutError, OSError, HTTPError, URLError) as exc:
            status, reasons = "SOURCE_UNAVAILABLE", [type(exc).__name__]
        entry["source_check"] = status
        entry["review_flags"] = reasons
        out.append(entry)
        time.sleep(delay)
    counts = Counter(x["source_check"] for x in out)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "Cleveland Museum of Art Open Access API (live per artwork)",
        "source_policy": "https://www.clevelandart.org/terms-and-conditions",
        "all_publication_status": "HOLD",
        "total": len(out),
        "source_checks": dict(sorted(counts.items())),
        "works": out,
        "editorial_approved": 0,
        "published": 0,
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", type=Path, default=Path(".artdrift_ingest/cleveland-rights-audit.json"))
    p.add_argument("--delay", type=float, default=.45)
    args = p.parse_args()
    if not .35 <= args.delay <= 3.0:
        p.error("delay must be between .35 and 3 seconds")
    result = audit(delay=args.delay)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in
        ("total","source_checks","editorial_approved","published")}, sort_keys=True))


if __name__ == "__main__":
    main()
