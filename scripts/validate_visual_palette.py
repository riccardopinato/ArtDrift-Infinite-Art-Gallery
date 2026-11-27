#!/usr/bin/env python3
"""Fail-closed integrity check for source-bound measured WebP color scores.

This does not certify the image licenses or substitute for visual review.
The Flutter consumer independently validates the exact catalog key fingerprint.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
from pathlib import Path

MANIFEST = Path("assets/museums/canvas_joyful_pixel_scores_v2.json")


def validate(path: Path = MANIFEST) -> tuple[int, int]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema_version") != 2:
        raise ValueError("Unexpected measured-palette schema")
    count = data.get("catalog_key_count")
    available = data.get("available_image_count")
    encoded = data.get("score_bytes_base64")
    expected = data.get("score_bytes_sha256")
    if type(count) is not int or count != 4500:
        raise ValueError("Unexpected pinned catalog length")
    if type(available) is not int or available != 4499:
        raise ValueError("Unexpected source-backed image count")
    if data.get("score_byte_count") != count:
        raise ValueError("Score count does not equal source-ID count")
    if type(data.get("catalog_fingerprint_fnv1a32")) is not int:
        raise ValueError("Missing canonical ID fingerprint")
    if not isinstance(encoded, str) or not isinstance(expected, str):
        raise ValueError("Missing encoded scores/digest")
    if len(expected) != 64 or any(c not in "0123456789abcdef" for c in expected):
        raise ValueError("Invalid lowercase SHA256 digest")
    payload = base64.b64decode(encoded, validate=True)
    if len(payload) != count:
        raise ValueError("Wrong number of color-score bytes")
    actual = hashlib.sha256(payload).hexdigest()
    if not hmac.compare_digest(actual, expected):
        raise ValueError("Color-score payload differs from the declared SHA256")
    # Pixel analysis and source IDs are distinct from image copyright review.
    if data.get("commercial_release_cleared") is not False:
        raise ValueError("Measured scores must not imply commercial clearance")
    if type(data.get("manual_visual_review_complete")) is not bool:
        raise ValueError("Visual review metadata must be explicit")
    return count, available


if __name__ == "__main__":
    total, image_backed = validate()
    print(f"PALETTE_SCORE_INTEGRITY_OK catalog={total} images={image_backed}")
