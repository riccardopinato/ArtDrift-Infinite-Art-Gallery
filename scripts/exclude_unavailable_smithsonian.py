#!/usr/bin/env python3
"""Exclude one user-rejected metadata-only Smithsonian artwork; retain its audit trail.

Only smithsonian:6452594389 / npg:npg_NPG.2007.11 is excluded.
All other 4,042 museum identities and their original image bytes remain intact.
This action prepares a *source candidate*, not commercial rights certification.
"""
import collections
import json
from pathlib import Path

TARGET_SOURCE = "smithsonian"
TARGET_ID = "6452594389"
TARGET_NATIVE = "npg:npg_NPG.2007.11"
ROOT = Path(".")
CATALOG = ROOT / "assets/museums/catalog_global.json"
REPORT = ROOT / "assets/museums/global_report.json"
COVERAGE = ROOT / "docs/generated/MUSEUM_THUMBNAIL_COVERAGE.json"
MANIFEST = ROOT / "web/museum_thumbs/manifest.json"
TEST = ROOT / "test/museum_catalog_test.dart"
IMPORT = ROOT / "scripts/import_global_museum_catalog.py"
SANITIZE = ROOT / "scripts/sanitize_global_museums.py"
WORKFLOW = ROOT / ".github/workflows/web-thumbnail-pack.yml"
POLICY = ROOT / "docs/ART_IMAGE_RIGHTS_PROVIDER_GATES_2026-11-22.md"
LEDGER = ROOT / "docs/ARTDRIFT_MAXI_STEP_INTEGRATION_2026-11-22.md"

def write_json(path, data, *, compact=False):
    path.write_text(json.dumps(data, ensure_ascii=False,
        separators=(",", ":") if compact else None,
        indent=None if compact else 2,
        sort_keys=not compact) + "\n", encoding="utf-8")

def update_once(path, old, new):
    raw = path.read_text(encoding="utf-8")
    if old in raw:
        raw = raw.replace(old, new, 1)
        path.write_text(raw, encoding="utf-8")
    elif new not in raw:
        raise AssertionError(f"Expected patch anchor missing: {path}")

def main():
    data = json.loads(CATALOG.read_text(encoding="utf-8"))
    matches = [r for r in data if r.get("museum_source") == TARGET_SOURCE
               and str(r.get("id")) == TARGET_ID]
    if matches:
        assert len(data) == 4043, len(data)
        assert len(matches) == 1, matches
        assert matches[0].get("museum_native_id") == TARGET_NATIVE, matches[0]
        assert matches[0].get("title") == "William Linn"
        data = [r for r in data if not (
            r.get("museum_source") == TARGET_SOURCE
            and str(r.get("id")) == TARGET_ID)]
        write_json(CATALOG, data, compact=True)
    assert len(data) == 4042, len(data)
    assert not any(r.get("museum_source") == TARGET_SOURCE and
                   str(r.get("id")) == TARGET_ID for r in data)
    identities = [f"{r['museum_source']}:{int(r['id'])}" for r in data]
    assert len(identities) == len(set(identities)) == 4042

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    thumb_ids = manifest["keys"]
    assert len(thumb_ids) == len(set(thumb_ids)) == 4042, len(thumb_ids)
    assert set(identities) == set(thumb_ids), "Global catalog ≠ packed artworks"
    assert f"{TARGET_SOURCE}:{TARGET_ID}" not in thumb_ids
    assert not (ROOT / f"web/museum_thumbs/{TARGET_SOURCE}_{TARGET_ID}.webp").exists()

    report = json.loads(REPORT.read_text(encoding="utf-8"))
    assert report["records_bundled_existing"] == 457
    report.update(records_global=4042, records_total=4499,
                  catalog_bytes=CATALOG.stat().st_size,
                  remote_images_only=4042)
    report["institutions"] = dict(sorted(collections.Counter(
        r["museum_name"] for r in data).items()))
    report["excluded_metadata_only_smithsonian"] = {
        "museum_source": TARGET_SOURCE, "id": int(TARGET_ID),
        "museum_native_id": TARGET_NATIVE,
        "reason": "User-excluded unavailable preview; no alternate image substituted",
        "catalog_record_removed": True
    }
    write_json(REPORT, report)

    cover = json.loads(COVERAGE.read_text(encoding="utf-8"))
    assert cover["web_thumbnails_available"] == 4042
    assert sum(cover["available_by_source"].values()) == 4042
    cover.update(catalog_total=4042, license_eligible=4042,
                 new_download_policy_eligible=4042,
                 new_download_policy_hold=0, web_thumbnails_missing=0,
                 status_counts={}, batch_requested=0)
    write_json(COVERAGE, cover)

    # Never re-admit the intentionally excluded item in later imports.
    update_once(IMPORT,
        "    # Entropy interleaving gives worldwide variety at first viewport.",
        "    # User-excluded metadata-only item (Smithsonian NPG.2007.11): do not reimport.\n"
        "    data = {k: v for k, v in data.items() if not (\n"
        "        v.get('museum_source') == 'smithsonian' and\n"
        "        str(v.get('id')) == '6452594389')}\n"
        "    # Entropy interleaving gives worldwide variety at first viewport.")
    update_once(SANITIZE,
        "keep=[row for row in original if row.get(\"museum_source\")!=\"aic\"]",
        "keep=[row for row in original if row.get(\"museum_source\")!=\"aic\" "
        "and not (row.get(\"museum_source\")==\"smithsonian\" and "
        "str(row.get(\"id\"))==\"6452594389\")]")
    update_once(TEST, "expect(all.length, 4500);",
        "expect(all.length, 4499);\n"
        "    expect(all.where((a) => a.catalogKey == 'smithsonian:6452594389'), isEmpty);")

    # Delete the recovery pathway, which would otherwise fail when the item
    # is deliberately no longer in the catalog.
    update_once(WORKFLOW,
        "      - name: Recover the single verified public-domain NPG object if its original IDS media is unavailable\n"
        "        run: python3 scripts/recover_npg_linn_exact_image.py\n", "")
    for obsolete in [
        ROOT / "scripts/recover_npg_linn_exact_image.py",
        ROOT / "docs/generated/NPG_2007_11_COMMONS_EXCEPTION_EVIDENCE.json",
    ]:
        obsolete.unlink(missing_ok=True)

    existing = POLICY.read_text(encoding="utf-8")
    oldheading = "## Strictly limited NPG NPG.2007.11 exception (23 Nov 2026)"
    newsection = (
        "## Explicit catalog exclusion: NPG.2007.11 (23 Nov 2026)\n\n"
        "At the user's request, the metadata-only **William Linn** item "
        "(\`smithsonian:6452594389\`, NPG.2007.11) has been removed from "
        "\`catalog_global.json\`. The original Smithsonian IDS media was 404, "
        "and the exact Wikimedia alternative could not be transferred (HTTP 429). "
        "No substitute or Commons-sourced image was inserted. The earlier "
        "unavailable-media record is preserved in Git history/issue #31. "
        "All remaining 4,042 museum records match existing local WebP identities. "
        "This is a content decision, **not commercial rights certification**.\n"
    )
    if oldheading in existing:
        POLICY.write_text(existing.split(oldheading)[0] + newsection,
                          encoding="utf-8")
    elif "## Explicit catalog exclusion: NPG.2007.11" not in existing:
        raise AssertionError("Policy note heading changed unexpectedly")

    addition = (
        "\n## Consolidation update — 23 Nov 2026\n\n"
        "Final catalog: **4,499 works** = 457 original with previews + "
        "4,042 global museum works with **4,042 matching WebPs**. "
        "The last metadata-only Smithsonian NPG.2007.11 was explicitly removed. "
        "The previously published 4,500 and 1,142 numbers above are historical "
        "checkpoints, not the final state. "
        "The shared drift_core matches Art main (PR #30) and GalleryDrift #13. "
        "Commercial rights and physical-device acceptance are separate gates.\n"
    )
    text = LEDGER.read_text(encoding="utf-8")
    if "## Consolidation update — 23 Nov 2026" not in text:
        LEDGER.write_text(text + addition, encoding="utf-8")
    print("EXCLUDED_EXACT_NPG_ARTWORK", TARGET_SOURCE, TARGET_ID, flush=True)
    print("CATALOG_4499_REAL_IMAGES_4499", flush=True)

if __name__ == "__main__":
    main()
