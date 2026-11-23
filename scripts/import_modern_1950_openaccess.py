#!/usr/bin/env python3
"""Import independently licensed artworks created from 1950 onward.

Only the museum's *item-specific* CC0 media flag admits a record. Metadata
may be open when a modern image is not: never fabricate or hotlink those.
The importer is deterministic, idempotent, bounded, and does not change any
existing Art Drift catalog or user-owned favorites.
"""
from __future__ import annotations

import json
import os
import re
import time
from collections import Counter
from pathlib import Path
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "museums"
DEST = OUT / "catalog_modern_1950.json"
REPORT = OUT / "modern_1950_report.json"
SOURCE = "cleveland"
MUSEUM = "Cleveland Museum of Art"
RIGHTS = "https://www.clevelandart.org/open-access"
API = "https://openaccess-api.clevelandart.org/api/artworks/"
LICENSE = "CC0"
PREFIX = 20_000_000
MAX_RECORDS = 750
PAGE_SIZE = 100
MAX_PAGES = 40
MAX_OUTPUT_BYTES = 1_000_000
YEAR_PATTERN = re.compile(r"(?<!\d)(?:1[0-9]{3}|20[0-9]{2})(?!\d)")
TYPE_KEYWORDS = (
    "paint", "draw", "print", "photo", "sculpt", "ceramic",
    "textile", "mixed media", "poster", "design", "graphic",
    "collage", "assemblage", "installation",
)
HOSTS = {"openaccess-cdn.clevelandart.org"}
MUSEUM_HOSTS = {"www.clevelandart.org", "clevelandart.org"}


def text(value: object, limit: int) -> str:
    return value.strip()[:limit] if isinstance(value, str) else ""


def creation_year(date: str) -> int | None:
    """Use the *earliest* explicit year; do not infer from centuries or ages."""
    years = [int(y) for y in YEAR_PATTERN.findall(date)]
    if not years or min(years) < 1950 or max(years) > 2026:
        return None
    return min(years)


def official(url: str, hosts: set[str]) -> bool:
    try:
        uri = urlparse(url)
        return (uri.scheme == "https" and uri.hostname in hosts
                and uri.username is None and uri.password is None
                and uri.port in (None, 443))
    except (ValueError, TypeError):
        return False


def acceptable_type(kind: str) -> bool:
    kind = kind.strip().lower()
    return bool(kind and any(word in kind for word in TYPE_KEYWORDS))


def existing_identifiers(root: Path = ROOT) -> set[tuple[str, str]]:
    keys = set()
    for path in (
        root / "assets/gallery/catalog.json",
        root / "assets/museums/catalog.json",
        root / "assets/museums/catalog_global.json",
    ):
        if not path.is_file():
            continue
        for item in json.loads(path.read_text(encoding="utf-8")):
            if not isinstance(item, dict):
                continue
            src = item.get("museum_source") or "aic"
            native = item.get("museum_native_id")
            ident = item.get("id")
            if src == SOURCE:
                if native not in (None, ""):
                    keys.add((SOURCE, str(native)))
                if isinstance(ident, int):
                    keys.add((SOURCE, "id:" + str(ident)))
    return keys


def normalize(raw: dict) -> dict | None:
    if raw.get("share_license_status") != "CC0":
        return None
    art_id = raw.get("id")
    if type(art_id) is not int or not (0 < art_id < 950_000_000):
        return None
    title = text(raw.get("title"), 230)
    kind = text(raw.get("type"), 90)
    date = text(raw.get("creation_date"), 80)
    if not title or not acceptable_type(kind) or creation_year(date) is None:
        return None
    images = raw.get("images") or {}
    web = (images.get("web") or {}) if isinstance(images, dict) else {}
    preview = text(web.get("url"), 1800) if isinstance(web, dict) else ""
    if not official(preview, HOSTS):
        return None

    creators = raw.get("creators") or []
    artist = next(
        (text(a.get("description"), 190) for a in creators
         if isinstance(a, dict) and text(a.get("description"), 190)), ""
    )
    url = text(raw.get("url"), 700)
    if not official(url, MUSEUM_HOSTS):
        url = RIGHTS
    terms = []
    for value in raw.get("keywords") or []:
        term = text(value if isinstance(value, str)
                    else value.get("name") if isinstance(value, dict) else "", 70)
        if term and term not in terms:
            terms.append(term)
    return {
        "id": PREFIX + art_id,
        "museum_source": SOURCE,
        "museum_native_id": str(art_id),
        "museum_name": MUSEUM,
        "title": title,
        "artist_title": artist,
        "date_display": date,
        "creation_year_verified": creation_year(date),
        "artwork_type_title": kind,
        "image_id": "",
        "is_public_domain": True,
        "rights_license": LICENSE,
        "rights_evidence_url": RIGHTS,
        "remote_preview_url": preview,
        "remote_museum_url": url,
        "medium_display": text(raw.get("technique"), 160),
        "credit_line": text(raw.get("creditline"), 180),
        "place_of_origin": text(raw.get("culture"), 125),
        "subject_terms": terms[:12],
    }


def get_page(skip: int, retries: int = 3) -> dict:
    params = urlencode({
        "created_after": "1949",
        "cc0": "1",
        "has_image": "1",
        "limit": str(PAGE_SIZE),
        "skip": str(skip),
    })
    url = API + "?" + params
    for attempt in range(retries):
        try:
            req = Request(url, headers={
                "User-Agent": "ArtDrift-CC0-Modern-Catalog/1.0 (museum attribution)",
                "Accept": "application/json",
            })
            with urlopen(req, timeout=28) as response:
                if response.status != 200:
                    raise RuntimeError(f"Provider status {response.status}")
                payload = response.read(2_500_001)
                if len(payload) > 2_500_000:
                    raise ValueError("Oversized provider response")
            data = json.loads(payload)
            if not isinstance(data, dict) or not isinstance(data.get("data"), list):
                raise ValueError("Malformed provider response")
            return data
        except (HTTPError, URLError, TimeoutError) as err:
            if attempt + 1 >= retries:
                raise RuntimeError(f"Provider fetch failed, skip={skip}") from err
            time.sleep(1.5 * (attempt + 1))
    raise AssertionError("unreachable")


def import_catalog(fetch=get_page, root: Path = ROOT) -> dict:
    already = existing_identifiers(root)
    rows: dict[int, dict] = {}
    fetched = 0
    held_rights_or_quality = 0
    existing_skipped = 0
    pages = 0
    for page in range(MAX_PAGES):
        data = fetch(page * PAGE_SIZE)
        source_rows = data["data"]
        pages += 1
        fetched += len(source_rows)
        for raw in source_rows:
            record = normalize(raw) if isinstance(raw, dict) else None
            if record is None:
                held_rights_or_quality += 1
                continue
            key = (SOURCE, record["museum_native_id"])
            if key in already or (SOURCE, "id:" + str(record["id"])) in already:
                existing_skipped += 1
                continue
            rows.setdefault(record["id"], record)
            if len(rows) >= MAX_RECORDS:
                break
        info = data.get("info") or {}
        total = info.get("total") if isinstance(info, dict) else None
        if (len(rows) >= MAX_RECORDS or not source_rows
                or (isinstance(total, int) and (page + 1) * PAGE_SIZE >= total)
                or len(source_rows) < PAGE_SIZE):
            break
        # Keep provider load bounded. No scraping or asset download.
        time.sleep(0.22)

    result = list(rows.values())
    result.sort(key=lambda entry: (entry["creation_year_verified"], entry["id"]))
    if not result:
        raise RuntimeError("NO_NEW_VERIFIED_MODERN_ARTWORKS: no catalog replacement")
    encoded = (json.dumps(result, ensure_ascii=False, separators=(",", ":")) + "\n").encode()
    if len(encoded) > MAX_OUTPUT_BYTES:
        raise RuntimeError("MODERN_CATALOG_SIZE_EXCEEDED")
    if len({(r["museum_source"], r["museum_native_id"]) for r in result}) != len(result):
        raise RuntimeError("MODERN_DUPLICATE_SOURCE_ID")

    report = {
        "schema_version": 1,
        "status": "GENERATED_LICENSE_GATED_NOT_IMAGE_DELIVERY_CERTIFIED",
        "source": API,
        "scope": "modern artworks from 1950 with explicit CC0 license and CDN image",
        "first_year": 1950,
        "min_record_year": min(r["creation_year_verified"] for r in result),
        "max_record_year": max(r["creation_year_verified"] for r in result),
        "provider_pages": pages,
        "provider_rows_inspected": fetched,
        "held_rights_or_quality": held_rights_or_quality,
        "already_in_existing_catalog": existing_skipped,
        "new_unique_records": len(result),
        "by_type": dict(sorted(Counter(r["artwork_type_title"] for r in result).items())),
        "catalog_bytes": len(encoded),
        "images_bundled": 0,
        "rights": "Per-record API CC0 media flag, official HTTPS CDN, source open-access policy",
        "network_image_delivery": "UNVERIFIED",
        "store_commercial_rights_acceptance": "PENDING",
    }
    output = root / "assets/museums"
    output.mkdir(parents=True, exist_ok=True)
    (output / DEST.name).write_bytes(encoded)
    (output / REPORT.name).write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    report = import_catalog()
    print("MODERN_CATALOG_GENERATED", json.dumps(report, ensure_ascii=False))
