#!/usr/bin/env python3
"""Generate a source-ID-bound manifest of the *actual bundled WebP frame sizes*.

Metadata API thumbnail width/height is sometimes a crop or display record,
not the dimensions of the compact local WebP shipped to Art Drift. Those
differences made BoxFit.contain show black gaps. This script reads the real
WebP headers without extra dependencies, and creates the deterministic,
reviewable, cross-platform source-aspect manifest.
"""
import base64
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = [
    "assets/gallery/catalog.json",
    "assets/museums/catalog.json",
    "assets/museums/catalog_global.json",
]
OUTPUT = ROOT / "assets/museums/canvas_real_webp_dimensions_v1.json"

def frame_size(path):
    with path.open("rb") as handle:
        chunk = handle.read(64)
    if len(chunk) < 30 or chunk[:4] != b"RIFF" or chunk[8:12] != b"WEBP":
        raise ValueError("Not a valid WebP header: " + str(path))
    codec = chunk[12:16]
    if codec == b"VP8X":
        w = 1 + int.from_bytes(chunk[24:27], "little")
        h = 1 + int.from_bytes(chunk[27:30], "little")
    elif codec == b"VP8 ":
        if chunk[23:26] != b"\x9d\x01\x2a":
            raise ValueError("Missing VP8 frame marker: " + str(path))
        w = int.from_bytes(chunk[26:28], "little") & 0x3fff
        h = int.from_bytes(chunk[28:30], "little") & 0x3fff
    elif codec == b"VP8L":
        if chunk[20] != 0x2f:
            raise ValueError("Missing VP8L frame marker: " + str(path))
        w = 1 + (chunk[21] | ((chunk[22] & 0x3f) << 8))
        h = 1 + ((chunk[22] >> 6) | (chunk[23] << 2) |
                  ((chunk[24] & 0x0f) << 10))
    else:
        raise ValueError("Unrecognized WebP codec: " + str(path))
    if not (0 < w <= 65535 and 0 < h <= 65535):
        raise ValueError("Invalid WebP dimensions: " + str(path))
    return w, h

def source_rows():
    rows = {}
    for source in SOURCES:
        entries = json.loads((ROOT / source).read_text(encoding="utf-8"))
        if not isinstance(entries, list):
            raise ValueError("Invalid catalog: " + source)
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            key = str(entry.get("museum_source") or "aic") + ":" + str(entry["id"])
            rows.setdefault(key, entry)
    if len(rows) != 4500:
        raise ValueError("Source catalog identity drift: " + str(len(rows)))
    return rows

def fnv(keys):
    h = 0x811c9dc5
    for key in keys:
        for byte in (key + "\x00").encode("utf-8"):
            h = ((h ^ byte) * 0x01000193) & 0xffffffff
    return h

def main():
    catalog = source_rows()
    keys = sorted(catalog)
    expected_fingerprint = 2742452096
    if fnv(keys) != expected_fingerprint:
        raise ValueError("Catalog fingerprint differs from color manifest")
    output = bytearray()
    found = 0
    by_codec = {}
    for key in keys:
        item = catalog[key]
        asset = item.get("bootstrap_asset") or ""
        museum = item.get("museum_source") or "aic"
        ident = str(item["id"])
        candidates = [ROOT / asset] if asset else []
        candidates.append(ROOT / ("web/museum_thumbs/" + museum + "_" +
                                  ident + ".webp"))
        candidates.append(ROOT / ("assets/museums/thumbs/" + museum + "_" +
                                  ident + ".webp"))
        size = (0, 0)
        for path in candidates:
            if path.is_file():
                size = frame_size(path)
                by_codec[path.read_bytes()[12:16].decode("ascii")] = (
                    by_codec.get(path.read_bytes()[12:16].decode("ascii"), 0) + 1)
                break
        if size[0] and size[1]:
            found += 1
        output.extend(struct.pack(">HH", *size))
    if found < 1000:
        raise ValueError("Too few packaged WebPs to trust dimensions: " +
                         str(found))
    payload = {
        "schema_version": 1,
        "basis": "actual RIFF WebP frame dimensions; no museum meta inference",
        "catalog_key_count": len(keys),
        "catalog_fingerprint_fnv1a32": expected_fingerprint,
        "available_preview_count": found,
        "missing_preview_count": len(keys) - found,
        "format": "big-endian uint16 width, uint16 height, sorted catalogKey",
        "dimensions_base64": base64.b64encode(output).decode("ascii"),
        "commercial_release_cleared": False,
    }
    OUTPUT.write_text(json.dumps(payload, separators=(",", ":")) + "\n",
                      encoding="utf-8")
    print("REAL_WEBP_DIMENSIONS_PASS", found, len(keys),
          "bytes", len(output), "codecs", by_codec, "manifest", OUTPUT)

if __name__ == "__main__":
    main()
