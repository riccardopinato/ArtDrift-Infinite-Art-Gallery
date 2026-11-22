#!/usr/bin/env python3
"""Fail-closed per-object metadata/image audit for the Art Drift global catalog.

IMPORTANT: This is a deterministic provenance + integrity screen, NOT legal
clearance for commercial redistribution. An image is NEVER marked licensed
for commercial release merely because the source catalog says public domain.
"""
import collections
import hashlib
import json
from pathlib import Path

from PIL import Image
from build_museum_thumbnail_pack import eligible, eligible_new_download

CATALOG = Path("assets/museums/catalog_global.json")
ROOT = Path("web/museum_thumbs")
MANIFEST = ROOT / "manifest.json"
REPORT = Path("docs/generated/ART_IMAGE_ITEM_RIGHTS_AUDIT.json")
SUMMARY = Path("docs/ART_IMAGE_RIGHTS_AUDIT_2026-11-23.md")
MIN_WEBP = 250
MAX_WEBP = 24000


def key(row):
    return f"{row['museum_source']}:{int(row['id'])}"


def inspect_asset(path):
    """Check the bytes for the EXACT museum-native ID, not another painting."""
    if not path.is_file():
        return {"state": "ABSENT"}
    raw = path.read_bytes()
    result = {"state": "INVALID", "size_bytes": len(raw),
              "sha256": hashlib.sha256(raw).hexdigest()}
    if not MIN_WEBP <= len(raw) <= MAX_WEBP:
        result["reason"] = "SIZE_OUT_OF_BOUNDS"
        return result
    try:
        with Image.open(path) as image:
            if image.format != "WEBP":
                result["reason"] = "NOT_WEBP"
                return result
            image.verify()
        with Image.open(path) as image:
            image.load()
            if min(image.size) < 1 or max(image.size) > 256:
                result["reason"] = "INVALID_DIMENSIONS"
                return result
            result.update({"state": "VERIFIED_BYTES", "width": image.width,
                           "height": image.height})
            if min(image.size) < 36:
                # Real narrow-aspect source images can legitimately downsample
                # below 36 px on one dimension at the 256 px long-side cap.
                # The codec is valid; record a visual review, not corruption.
                result["visual_review"] = "VERY_THIN_ASPECT_OR_SMALL_PREVIEW"
    except (OSError, ValueError, SyntaxError) as exc:
        result["reason"] = type(exc).__name__
    return result


def audit():
    rows = json.loads(CATALOG.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if not isinstance(rows, list) or not rows:
        raise ValueError("Catalog missing or not a nonempty list")
    if manifest.get("schema_version") != 1 or not isinstance(manifest.get("keys"), list):
        raise ValueError("Bad manifest schema")
    keys = manifest["keys"]
    if len(keys) != len(set(keys)):
        raise ValueError("Duplicate manifest identity")
    indexed = {}
    for row in rows:
        k = key(row)
        if k in indexed:
            raise ValueError("Duplicate catalog identity: " + k)
        indexed[k] = row
    if set(keys) - set(indexed):
        raise ValueError("Manifest contains unknown catalog identity")
    items = []
    counts = collections.Counter()
    by_source = collections.defaultdict(collections.Counter)
    for k in sorted(indexed):
        row = indexed[k]
        source = str(row.get("museum_source", ""))
        on_manifest = k in keys
        path = ROOT / f"{source}_{int(row['id'])}.webp"
        file = inspect_asset(path) if on_manifest else {"state": "ABSENT"}
        eligible_base = eligible(row)
        policy = eligible_new_download(row)
        if on_manifest and file["state"] != "VERIFIED_BYTES":
            verdict = "INVALID_IMAGE_HOLD"
        elif not eligible_base:
            verdict = "INVALID_OR_INCOMPLETE_SOURCE_RIGHTS_HOLD"
        elif not policy:
            verdict = "IMAGE_SPECIFIC_COMMERCIAL_RIGHTS_REVIEW"
        elif on_manifest:
            verdict = "SOURCE_POLICY_SCREENED_NOT_LEGALLY_CERTIFIED"
        else:
            verdict = "SOURCE_POLICY_ELIGIBLE_IMAGE_MISSING"
        # No row is legally certified by this static check. The evidence URL
        # is provenance, NOT proof that an unrelated image carries CC0.
        obj = {
            "key": k, "museum_native_id": row.get("museum_native_id"),
            "source": source, "title": row.get("title"),
            "rights_license_declared": row.get("rights_license"),
            "rights_evidence_url": row.get("rights_evidence_url"),
            "official_image_url": row.get("remote_preview_url"),
            "provider_policy_gate": bool(policy),
            "in_thumbnail_manifest": on_manifest,
            "asset": file,
            "review_verdict": verdict,
            "commercial_release_cleared": False,
        }
        items.append(obj)
        counts[verdict] += 1
        by_source[source][verdict] += 1
    summary = {
        "schema_version": 1,
        "catalog_total": len(rows),
        "manifest_total": len(keys),
        "manifest_global_sha256": hashlib.sha256(MANIFEST.read_bytes()).hexdigest(),
        "missing_total": sum(not i["in_thumbnail_manifest"] for i in items),
        "policy_eligible_missing": counts["SOURCE_POLICY_ELIGIBLE_IMAGE_MISSING"],
        "policy_hold_missing": sum(
            not i["in_thumbnail_manifest"] and not i["provider_policy_gate"] for i in items),
        "packaged_policy_hold": sum(
            i["in_thumbnail_manifest"] and not i["provider_policy_gate"] for i in items),
        "invalid_packaged": counts["INVALID_IMAGE_HOLD"],
        "packaged_very_thin_visual_review": sum(
            i["in_thumbnail_manifest"] and
            i["asset"].get("visual_review") == "VERY_THIN_ASPECT_OR_SMALL_PREVIEW"
            for i in items),
        "verdicts": dict(sorted(counts.items())),
        "by_source": {k: dict(sorted(v.items())) for k, v in sorted(by_source.items())},
        "legally_certified_images": 0,
        "method": "Local file integrity, exact museum ID, catalog licence metadata, and provider policy host gate. No live object-specific copyright adjudication.",
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps({"summary": summary, "artworks": items},
                                 ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                      encoding="utf-8")
    notes = [
        "# Art Drift — deterministic rights and coverage screen (23 November 2026)",
        "",
        "**NOT a commercial legal certification.** Every artwork still has",
        "`commercial_release_cleared=false` pending image-specific rights review.",
        "",
        f"- Global catalog records: **{len(rows)}**",
        f"- Actual manifest entries: **{len(keys)}**",
        f"- Missing real image assets: **{summary['missing_total']}**",
        f"- Missing from source-policy-eligible providers: **{summary['policy_eligible_missing']}**",
        f"- Missing behind source/image-rights HOLD: **{summary['policy_hold_missing']}**",
        f"- Already packaged requiring image-specific rights review: **{summary['packaged_policy_hold']}**",
        f"- Manifest image bytes invalid: **{summary['invalid_packaged']}**",
        f"- Valid but very thin previews needing visual review: **{summary['packaged_very_thin_visual_review']}**",
        "",
        "## Per-object evidence",
        "",
        "Full itemized entries, identity, declared license, official image/evidence",
        "URLs, SHA-256 of verified WebP bytes, gate verdict and explicit commercial",
        "release status: `docs/generated/ART_IMAGE_ITEM_RIGHTS_AUDIT.json`.",
        "",
        "Source-policy-eligible means **allowed for bounded download**, not legal",
        "approval of a product. A CC0 metadata declaration does not by itself",
        "clear artwork-specific photographs or provider trademarks.",
        "",
        "## Remaining gates",
        "",
        "1. Retry the policy-eligible missing images with safe official URLs; keep",
        "   HTTP/403/404, tiny or invalid images as actual failures, never substitutes.",
        "2. For source-policy HOLD rows, record explicit object/image license evidence",
        "   from official museum pages before any new media file is downloaded.",
        "3. Human/legal image-specific review before commercial distribution, plus",
        "   device benchmarks, stable signing and Play disclosures.",
        "",
    ]
    SUMMARY.write_text("\n".join(notes), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if summary["invalid_packaged"]:
        raise SystemExit("INVALID_PACKAGED_IMAGE: image-integrity gate failed")
    return summary


if __name__ == "__main__":
    audit()
