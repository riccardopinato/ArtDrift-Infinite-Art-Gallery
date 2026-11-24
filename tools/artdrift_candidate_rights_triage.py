#!/usr/bin/env python3
"""Per-item rights/media triage. Source metadata only; no publishing or network."""
import argparse
import json
import re
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit

RISK_FLAGS = {
    "MEDIA_LICENSE_ITEM_NOT_REVIEWED",
    "MEDIA_DELIVERY_NOT_VERIFIED",
}

def safe_https(raw):
    if not isinstance(raw, str):
        return False
    try:
        uri = urlsplit(raw)
    except ValueError:
        return False
    return uri.scheme == "https" and bool(uri.hostname) and not uri.username and not uri.password and uri.port in (None, 443)

def triage(items, expected=585):
    if not isinstance(items, list) or len(items) != expected:
        raise ValueError("Candidate source count mismatch")
    seen = set()
    records = []
    for src in items:
        if not isinstance(src, dict):
            raise ValueError("Unexpected source record")
        ident = src.get("source_key")
        if not isinstance(ident, str) or not re.fullmatch(r"[a-z]+:[0-9]+", ident):
            raise ValueError("Invalid source identity")
        if ident in seen:
            raise ValueError("Duplicate source identity: " + ident)
        seen.add(ident)
        if src.get("publication_status") != "HOLD":
            raise ValueError("Unexpected candidate publication status " + ident)
        provider = src.get("museum_source")
        if provider not in ("smithsonian", "commons"):
            raise ValueError("New provider requires individual policy: " + ident)
        kind = str(src.get("type") or "").strip()
        painting = kind.casefold() == "painting"
        lic = str(src.get("license") or "")
        source_url = src.get("source_url") or ""
        preview_url = src.get("preview_url") or ""
        rights_url = src.get("rights_evidence_url") or ""
        title = str(src.get("title") or "")
        flags = set(RISK_FLAGS)
        if not painting:
            flags.add("NOT_PAINTING_DO_NOT_AUTO_PLACE_IN_PAINTING_CANVAS")
        if not src.get("artist"):
            flags.add("CREATOR_MISSING")
        if not safe_https(source_url):
            flags.add("OFFICIAL_OBJECT_DETAIL_MISSING")
        if not safe_https(preview_url):
            flags.add("PREVIEW_URL_MISSING_OR_INVALID")
        if not safe_https(rights_url):
            flags.add("RIGHTS_EVIDENCE_URL_MISSING_OR_INVALID")
        if "QS:" in title:
            flags.add("TITLE_CONTAINS_QS_METADATA")
        if re.search(r"<[^>]{1,64}>", title):
            flags.add("TITLE_CONTAINS_HTML_MARKUP")
        if lic.startswith("CC BY"):
            flags.add("ATTRIBUTION_REQUIRED_REVIEW_LICENSE_TERMS")
            if "SA" in lic:
                flags.add("SHARE_ALIKE_CONDITIONS_REVIEW")
        if provider == "smithsonian" and lic != "CC0":
            flags.add("SMITHSONIAN_SOURCE_LICENSE_MISMATCH")
        if provider == "commons" and not lic.startswith("CC BY"):
            flags.add("COMMONS_SOURCE_LICENSE_REVIEW")
        source_specific_rights = False  # Never infer image rights from a generic provider URL.
        media_delivery_verified = False
        records.append({
            "source_key": ident,
            "museum_source": provider,
            "museum_native_id": src.get("museum_native_id"),
            "title_original": title,
            "artist_original": src.get("artist"),
            "type_original": kind,
            "license_claim_original": lic,
            "source_url": source_url,
            "rights_evidence_url": rights_url,
            "preview_url": preview_url,
            "publication_status": "HOLD",
            "canvas_classification": "PAINTING_CANDIDATE" if painting else "ARCHIVE_ONLY_PENDING_PRODUCT_SCOPE",
            "source_specific_media_rights_verified": source_specific_rights,
            "media_delivery_verified": media_delivery_verified,
            "commercial_release_cleared": False,
            "flags": sorted(flags),
        })
    records.sort(key=lambda r: r["source_key"])
    for i, rec in enumerate(records):
        rec["catalog_review_wave"] = i // 100 + 1
    by_type = Counter(x["type_original"] for x in records)
    by_license = Counter(x["license_claim_original"] for x in records)
    by_flag = Counter(f for x in records for f in x["flags"])
    painting = [x for x in records if x["canvas_classification"] == "PAINTING_CANDIDATE"]
    archive = [x for x in records if x["canvas_classification"] == "ARCHIVE_ONLY_PENDING_PRODUCT_SCOPE"]
    summary = {
        "candidate_records": len(records),
        "paintings_to_prioritize_for_canvas_review": len(painting),
        "non_paintings_preserved_for_separate_archive_review": len(archive),
        "rights_media_item_specific_cleared": 0,
        "published_or_unheld": 0,
        "image_delivery_network_checks_performed": 0,
        "catalog_waves": (len(records) + 99) // 100,
        "by_type": dict(sorted(by_type.items())),
        "by_license": dict(sorted(by_license.items())),
        "by_flag": dict(sorted(by_flag.items())),
        "source_rights_review_status": "ALL_HOLD_NO_AUTO_APPROVAL",
    }
    return summary, records, painting, archive

def write_report(review_path, out, expected=585):
    review = json.loads(Path(review_path).read_text(encoding="utf-8"))
    summary, records, painting, archive = triage(review, expected=expected)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    for name, data in (("summary.json", summary), ("triage-all.json", records),
                       ("paintings-priority.json", painting),
                       ("separate-archive-review.json", archive)):
        (out / name).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for i in range(0, len(records), 100):
        (out / ("wave-%02d.json" % (i // 100 + 1))).write_text(
            json.dumps(records[i:i + 100], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("ARTDRIFT_RIGHTS_TRIAGE_PASS", summary["candidate_records"],
          summary["paintings_to_prioritize_for_canvas_review"],
          summary["non_paintings_preserved_for_separate_archive_review"],
          summary["catalog_waves"], "CLEARED", 0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--review", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--expected", type=int, default=585)
    args = parser.parse_args()
    write_report(args.review, args.out, args.expected)
