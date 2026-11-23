#!/usr/bin/env python3
"""Offline, deterministic mobile thumbnail-pack gate. No network or rights certification."""
import json
from collections import Counter
from pathlib import Path

ROOT = Path("web/museum_thumbs")
MANIFEST = ROOT / "manifest.json"
CATALOG = Path("assets/museums/catalog_global.json")

def main():
    packed = json.loads(MANIFEST.read_text(encoding="utf-8"))
    records = json.loads(CATALOG.read_text(encoding="utf-8"))
    assert packed.get("schema_version") == 1
    keys = packed.get("keys")
    assert isinstance(keys, list) and len(keys) >= 1000
    assert len(keys) == len(set(keys)), "duplicate image identities"
    artworks = {}
    for row in records:
        if not isinstance(row, dict):
            continue
        source = row.get("museum_source")
        ident = row.get("id")
        if isinstance(source, str) and source.isalpha() and type(ident) is int:
            artworks[f"{source}:{ident}"] = row
    counts = Counter()
    total_bytes = 0
    for key in keys:
        assert isinstance(key, str) and key.count(":") == 1
        source, value = key.split(":")
        assert source.isalpha() and value.isdecimal() and value == str(int(value))
        row = artworks.get(key)
        assert row is not None, f"orphan thumbnail: {key}"
        assert row.get("is_public_domain") is True
        assert str(row.get("artwork_type_title", "")).lower() == "painting"
        license_text = str(row.get("rights_license", "")).lower()
        assert "cc0" in license_text or "public domain" in license_text
        assert str(row.get("rights_evidence_url", "")).startswith("https://")
        path = ROOT / f"{source}_{value}.webp"
        assert path.is_file(), f"missing Flutter asset: {path}"
        size = path.stat().st_size
        assert 250 <= size <= 24000, f"oversized/invalid WebP: {path}"
        with path.open("rb") as handle:
            header = handle.read(12)
        assert header[:4] == b"RIFF" and header[8:12] == b"WEBP", str(path)
        counts[source] += 1
        total_bytes += size
    actual = {p.name for p in ROOT.glob("*.webp")}
    expected = {key.replace(":", "_") + ".webp" for key in keys}
    assert actual == expected, "unmanifested or missing WebPs"
    print(json.dumps({
        "gate": "MOBILE_THUMBNAILS_STATIC_PASS",
        "packaged": len(keys),
        "bytes": total_bytes,
        "by_source": dict(sorted(counts.items())),
        "catalog_records": len(records),
        "legal_release_status": "NOT_CERTIFIED"
    }, sort_keys=True))

if __name__ == "__main__":
    main()
