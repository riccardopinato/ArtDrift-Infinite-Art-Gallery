#!/usr/bin/env python3
"""One-time source-controlled, rights-filtered tiny WebP bootstrap catalog.

Fetches AIC Open Access museum records, independently verifies images through
official IIIF, and commits ONLY metadata and tiny previews. Never embeds
hi-resolution originals in the APK. Run manually from GitHub Actions on a
development branch. Do not run this during normal Android builds.
"""
from __future__ import annotations

import io
import json
import random
import re
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from PIL import Image, ImageOps, UnidentifiedImageError

BASE = Path(__file__).resolve().parents[1]
DEST = BASE / "assets/gallery"
THUMBS = DEST / "thumbs"
TARGET = 72
MINIMUM = 28
UUID = re.compile(r"^[0-9a-fA-F-]{16,64}$")
FIELDS = ",".join((
    "id", "title", "artist_title", "artist_display", "date_display", "image_id",
    "is_public_domain", "artwork_type_title", "medium_display", "credit_line",
    "place_of_origin", "thumbnail",
))
SUBJECTS = (
    "landscape", "flowers", "portrait", "seascape", "still life",
    "Monet", "impressionism", "Renoir", "Cassatt", "Cezanne", "painting",
    "nature", "Van Gogh",
)
HEADERS = {
    "User-Agent": "ArtDrift-Seed-Build/1.0 (open-access art application)",
    "AIC-User-Agent": "ArtDrift-Seed-Build/1.0 (GitHub riccardopinato/ArtDrift-Infinite-Art-Gallery)",
    "Accept": "application/json,image/jpeg,*/*",
}


def fetch(url: str, *, max_bytes: int = 4_000_000, attempts: int = 2) -> bytes:
    for attempt in range(attempts):
        try:
            with urlopen(Request(url, headers=HEADERS), timeout=25) as response:
                if response.status != 200:
                    raise RuntimeError(f"HTTP {response.status}")
                body = response.read(max_bytes + 1)
                if not body or len(body) > max_bytes:
                    raise RuntimeError("empty or oversized response")
                return body
        except (URLError, HTTPError, TimeoutError, RuntimeError) as error:
            if attempt + 1 == attempts:
                raise
            print(f"Retry {attempt + 1} {type(error).__name__}: {str(error)[:120]}", flush=True)
            time.sleep(2.0 + attempt * 2.0)
    raise RuntimeError("Unreachable")


def normalize(row: dict) -> dict | None:
    if not isinstance(row, dict):
        return None
    if row.get("is_public_domain") is not True:
        return None
    if (row.get("artwork_type_title") or "").lower() != "painting":
        return None
    image_id = row.get("image_id")
    if not isinstance(image_id, str) or not UUID.fullmatch(image_id):
        return None
    if not isinstance(row.get("id"), int) or row["id"] <= 0:
        return None
    result = {key: row.get(key) for key in FIELDS.split(",")}
    return result


def fetch_candidates() -> list[dict]:
    by_id = {}
    for subject in SUBJECTS:
        query = {
            "q": subject,
            "query[term][is_public_domain]": "true",
            "fields": FIELDS,
            "limit": "100",
        }
        url = "https://api.artic.edu/api/v1/artworks/search?" + urlencode(query)
        try:
            payload = json.loads(fetch(url, max_bytes=2_000_000))
            rows = payload.get("data", [])
            valid = 0
            for row in rows:
                artwork = normalize(row)
                if artwork is not None:
                    by_id[artwork["id"]] = artwork
                    valid += 1
            print(f"query {subject}: {len(rows)} items, {valid} eligible, {len(by_id)} distinct", flush=True)
        except Exception as error:
            print(f"query {subject}: {type(error).__name__} {str(error)[:180]}", flush=True)
        if len(by_id) >= TARGET * 4:
            break
        time.sleep(1.1)
    # deterministic shuffle: avoid all first search-results showing similar art
    output = list(by_id.values())
    random.Random(20261121).shuffle(output)
    return output


def make_preview(image_id: str) -> bytes:
    # Cached AIC IIIF variant. Single-threaded; never batch images in parallel.
    uri = f"https://www.artic.edu/iiif/2/{image_id}/full/200,/0/default.jpg"
    raw = fetch(uri, max_bytes=2_000_000, attempts=2)
    with Image.open(io.BytesIO(raw)) as painting:
        image = ImageOps.exif_transpose(painting)
        if image.width < 32 or image.height < 32:
            raise RuntimeError("image too small")
        image = image.convert("RGB")
        image.thumbnail((200, 250), Image.Resampling.LANCZOS)
        output = io.BytesIO()
        image.save(output, "WEBP", quality=65, method=6)
        return output.getvalue()


def main() -> None:
    candidates = fetch_candidates()
    if len(candidates) < MINIMUM:
        raise SystemExit(f"Only {len(candidates)} eligible AIC works. Asset build aborted.")
    THUMBS.mkdir(parents=True, exist_ok=True)
    records = []
    total = 0
    for index, row in enumerate(candidates):
        if len(records) >= TARGET:
            break
        try:
            image = make_preview(row["image_id"])
            # Exclude pathological files: our bootstrap must remain lightweight.
            if len(image) > 45_000:
                print(f"Skip oversized preview {row['id']}: {len(image)}B", flush=True)
                continue
            name = f"{row['id']}.webp"
            (THUMBS / name).write_bytes(image)
            row["bootstrap_asset"] = f"assets/gallery/thumbs/{name}"
            records.append(row)
            total += len(image)
            print(f"saved {len(records):02d}/{TARGET} #{row['id']} {len(image)}B", flush=True)
        except (URLError, HTTPError, TimeoutError, RuntimeError, OSError, UnidentifiedImageError, ValueError) as error:
            print(f"Skip {row['id']}: {type(error).__name__} {str(error)[:130]}", flush=True)
        time.sleep(1.05)
        if index >= 260 and len(records) < MINIMUM:
            break
    if len(records) < MINIMUM:
        raise SystemExit(f"Only {len(records)} independently verified preview images; need >= {MINIMUM}")
    # Source order is deterministic, and stays frozen after this one-time run.
    records.sort(key=lambda x: x["id"])
    manifest = DEST / "catalog.json"
    manifest.write_text(json.dumps(records, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"CATALOG_READY artworks={len(records)} images={total}B json={manifest.stat().st_size}B", flush=True)
    if total > 2_000_000:
        raise SystemExit(f"Compressed bootstrap exceeds 2MB: {total}")


if __name__ == "__main__":
    main()

# Bootstrap collection is version-pinned after the first successful run.
