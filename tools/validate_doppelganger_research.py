#!/usr/bin/env python3
"""Read-only deterministic admissibility check for the ArtDrift research index.
A source link or a social editorial match is NOT proof of legal/visual release.
"""
import json
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "research" / "doppelgangers" / "candidates_index_20261124.json"

def validate(path=INDEX):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("schemaVersion") != 1 or data.get("status") != "RESEARCH_ONLY_NOT_RUNTIME":
        raise ValueError("Research index cannot be promoted implicitly")
    rows = data.get("pairs")
    sources = data.get("sourceRegistry")
    if not isinstance(rows, list) or len(rows) != 37 or not isinstance(sources, dict):
        raise ValueError("Expected exactly 37 candidate pairs plus sources")
    ids = [row.get("id") for row in rows]
    if len(set(ids)) != len(rows):
        raise ValueError("Duplicate candidate ID")
    for src, url in sources.items():
        parsed = urlparse(url)
        if not src or parsed.scheme != "https" or not parsed.hostname:
            raise ValueError("Unsafe source registry")
    for row in rows:
        if not (isinstance(row.get("celebrity"), str) and
                isinstance(row.get("artworkTitle"), str) and
                isinstance(row.get("artistCreditAsResearched"), str)):
            raise ValueError("Incomplete editorial provenance")
        if row.get("reviewStatus") not in (
                "INTERNAL_QA_MEDIA_DOCUMENTED", "HOLD_SOURCE_AND_RIGHTS"):
            raise ValueError("Unreviewed content accidentally activated")
        if row.get("commercialReleaseCleared") is not False or (
                row.get("independentSourceImagePairReviewed") is not False):
            raise ValueError("Rights or visual certification cannot be fabricated")
        if row.get("paintingStatus") not in (
                "CLAIMED_BY_EDITORIAL", "UNCERTAIN"):
            raise ValueError("Painting-type status unknown")
        refs = row.get("evidence")
        if not isinstance(refs, list) or not refs or any(k not in sources for k in refs):
            raise ValueError("Missing actual editorial evidence")
    types = Counter(row["paintingStatus"] for row in rows)
    rights = Counter(row["reviewStatus"] for row in rows)
    expected = data["counts"]
    if (types["CLAIMED_BY_EDITORIAL"], types["UNCERTAIN"]) != (29, 8):
        raise ValueError("Artwork-type counts differ")
    if rights["INTERNAL_QA_MEDIA_DOCUMENTED"] != 2:
        raise ValueError("Two inherited QA pairs not matched")
    if expected != dict(all=37, paintingsClaimed=29, paintingTypeUncertain=8,
            pairsWithBothMediaLicensesDocumented=2, commercialCleared=0):
        raise ValueError("Summary misrepresents dataset")
    print("RESEARCH_INDEX_PASS 37 pairs / 29 editorial paintings / 8 uncertain / "
          "2 photo-licensed QA / 0 public")
    return True

if __name__ == "__main__":
    validate()
