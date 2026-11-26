#!/usr/bin/env python3
"""Independent per-image technical/curatorial evidence for the 486 artist leads.

No source or remote metadata is converted into a commercial rights approval.
No production/catalogue/Cloudflare write is performed.
"""
from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import io
import json
import math
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps, UnidentifiedImageError

Image.MAX_IMAGE_PIXELS = 25_000_000
IMAGE_MAX_BYTES = 8 * 1024 * 1024
HOSTS = {"upload.wikimedia.org", "thumb.wikimedia.org"}
EXPECTED = 486
SHARDS = 18


def read_queue(path: Path):
    doc = json.loads(path.read_text(encoding="utf-8"))
    rows = doc.get("complete_queue")
    if doc.get("all_candidate_records_retained") != EXPECTED or not isinstance(rows, list) or len(rows) != EXPECTED:
        raise ValueError("Pinned 486-candidate inventory is missing or incomplete")
    identities = [x.get("source_identity") for x in rows]
    if len(set(identities)) != EXPECTED or any(not isinstance(x, str) or not x.startswith("commons:") for x in identities):
        raise ValueError("Missing or repeated canonical Commons identities")
    if any(x.get("commercially_approved") is not False or x.get("runtime_visible") is not False for x in rows):
        raise ValueError("Research-only rights and runtime invariants were changed")
    return rows


def shard_of(identity: str, total: int = SHARDS) -> int:
    if total < 1:
        raise ValueError("Invalid shard count")
    return int(hashlib.sha256(identity.encode("utf-8")).hexdigest()[:12], 16) % total


def url_safe(url: str) -> bool:
    try:
        p = urllib.parse.urlsplit(url)
        return p.scheme == "https" and p.hostname in HOSTS and p.port is None and not p.username and not p.password
    except (ValueError, TypeError):
        return False


def fetch_preview(url: str, *, attempts: int = 3):
    if not url_safe(url):
        raise ValueError("PREVIEW_URL_NOT_ALLOWED")
    last = None
    for attempt in range(attempts):
        req = urllib.request.Request(url, headers={
            "User-Agent": "ArtDriftResearchQA/1.0 (noncommercial thumbnail evidence; contact GitHub riccardopinato)",
            "Accept": "image/webp,image/jpeg,image/png,*/*;q=0.1",
        })
        try:
            with urllib.request.urlopen(req, timeout=16) as resp:
                final = resp.geturl()
                if not url_safe(final):
                    raise ValueError("UNEXPECTED_REDIRECT_HOST")
                mimetype = resp.headers.get("Content-Type", "").split(";")[0].strip().lower()
                if mimetype not in ("image/jpeg", "image/png", "image/webp"):
                    raise ValueError("UNEXPECTED_CONTENT_TYPE:" + mimetype[:40])
                content = resp.read(IMAGE_MAX_BYTES + 1)
                if len(content) > IMAGE_MAX_BYTES:
                    raise ValueError("IMAGE_TOO_LARGE")
                if not content:
                    raise ValueError("EMPTY_IMAGE")
                return content
        except urllib.error.HTTPError as ex:
            last = "HTTP_" + str(ex.code)
            if ex.code not in (429, 500, 502, 503, 504) or attempt == attempts - 1:
                break
            try:
                delay = min(25.0, max(3.0, float(ex.headers.get("Retry-After", "0"))))
            except (TypeError, ValueError):
                delay = 3.0 + attempt * 5.0
            time.sleep(delay + attempt * 3)
        except (urllib.error.URLError, TimeoutError, OSError) as ex:
            last = type(ex).__name__
            if attempt < attempts - 1:
                time.sleep(2 + attempt * 4)
    raise RuntimeError(last or "FETCH_FAILED")


def pixel_metrics(blob: bytes):
    with Image.open(io.BytesIO(blob)) as source:
        source.load()
        width, height = source.size
        if width < 40 or height < 40 or width * height > 25_000_000:
            raise ValueError("INVALID_PIXEL_DIMENSIONS")
        im = ImageOps.exif_transpose(source).convert("RGB")
    reduced = im.copy()
    reduced.thumbnail((128, 128))
    pixels = list(reduced.getdata())
    n = len(pixels)
    lum = [(.2126*r + .7152*g + .0722*b)/255.0 for r, g, b in pixels]
    dark = sum(v < .20 for v in lum) / n
    saturated = sum((max(p)-min(p)) / 255.0 > .32 for p in pixels) / n
    return {
        "width": width, "height": height,
        "mean_luminance": round(sum(lum)/n, 4),
        "dark_fraction": round(dark, 4),
        "saturated_fraction": round(saturated, 4),
        "decoded_rgb_sha256": hashlib.sha256(im.tobytes()).hexdigest(),
    }, im


def assess(row, *, download=fetch_preview):
    identity = row["source_identity"]
    result = {
        "source_identity": identity, "artist_id": row.get("artist_id"),
        "title": row.get("title"), "record_url": row.get("record_url"),
        "preview_url": row.get("preview_url"),
        "source_license_claim": row.get("image_license_claim"),
        "artist_attribution": row.get("artist_attribution"),
        "origin_confirmed": row.get("origin_confirmed"),
        "initial_lane": row.get("review_lane"),
        "risk_codes": row.get("risk_codes", []),
        "possible_existing_runtime_matches": row.get("possible_existing_runtime_matches", []),
        "commercially_approved": False,
        "runtime_visible": False,
        "image_rights_gate": "HOLD_PER_ITEM_TERRITORY",
        "identity_gate": "HOLD_AUTHOR_AND_WORK_ORIGIN",
        "visual_gate": "HOLD_HUMAN_REVIEW",
        "result": "HOLD_TECHNICAL",
    }
    preview = row.get("preview_url")
    if not url_safe(preview):
        result["technical_error"] = "UNSAFE_OR_MISSING_URL"
        return result, None
    try:
        blob = download(preview)
        pix, image = pixel_metrics(blob)
        result["pixel"] = pix
        result["thumbnail_sha256"] = hashlib.sha256(blob).hexdigest()
        result["thumbnail_size_bytes"] = len(blob)
        if pix["dark_fraction"] <= .15 and pix["mean_luminance"] >= .38:
            result["technical_color_class"] = "LUMINOUS_VISUAL_REVIEW"
        elif pix["saturated_fraction"] >= .25:
            result["technical_color_class"] = "COLORFUL_VISUAL_REVIEW"
        else:
            result["technical_color_class"] = "OTHER_VISUAL_REVIEW"
        result["result"] = "PIXELS_OK_RIGHTS_AND_VISUAL_HOLD"
        return result, image
    except (ValueError, RuntimeError, OSError, UnidentifiedImageError, Image.DecompressionBombError) as ex:
        result["technical_error"] = str(ex)[:180]
        return result, None


def make_contact_sheet(entries, path):
    columns = 4
    cell_w, cell_h = 260, 242
    rows = max(1, math.ceil(len(entries) / columns))
    sheet = Image.new("RGB", (columns * cell_w, rows * cell_h + 34), "#eeeae0")
    draw = ImageDraw.Draw(sheet)
    draw.text((10, 10), "ARTDRIFT RESEARCH ONLY — NOT PUBLICATION APPROVAL", fill="black")
    for idx, (record, im) in enumerate(entries):
        x, y = (idx % columns)*cell_w, 34+(idx // columns)*cell_h
        draw.rectangle((x+1, y+1, x+cell_w-2, y+cell_h-2), outline="#aaa59c", width=1)
        if im is not None:
            im = im.copy()
            im.thumbnail((cell_w-12, 193))
            sheet.paste(im, (x+(cell_w-im.width)//2, y+4+(193-im.height)//2))
        else:
            draw.text((x+7, y+80), "IMAGE UNAVAILABLE", fill="black")
        draw.text((x+6, y+200), str(record["source_identity"])[:35], fill="black")
        draw.text((x+6, y+218), str(record.get("title") or "")[:37], fill="black")
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(path, quality=80)


def run_shard(queue, shard, total, out: Path, offline=False):
    selected = [r for r in queue if shard_of(r["source_identity"], total) == shard]
    out.mkdir(parents=True, exist_ok=True)
    entries = []
    statuses = collections.Counter()
    records = []
    for row in selected:
        if offline:
            record, im = assess(row, download=lambda url: (_ for _ in ()).throw(RuntimeError("OFFLINE_SMOKE_ONLY")))
        else:
            record, im = assess(row)
        records.append(record)
        entries.append((record, im))
        statuses[record["result"]] += 1
        print(json.dumps({"identity": record["source_identity"], "status": record["result"],
                          "error": record.get("technical_error")}, ensure_ascii=False), flush=True)
    output = {"schema_version": 1, "shard": shard, "shards": total,
              "pinned_inventory_count": len(queue), "processed": len(records),
              "status_counts": dict(statuses), "rows": records,
              "commercially_approved": 0, "runtime_imported": 0}
    (out / ("shard_%02d.json" % shard)).write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if not offline:
        make_contact_sheet(entries, out / ("contact_%02d.jpg" % shard))
    return output


def aggregate(queue, directory: Path, out: Path, total=SHARDS):
    records, seen = [], set()
    for shard in range(total):
        p = directory / ("shard_%02d.json" % shard)
        obj = json.loads(p.read_text(encoding="utf-8"))
        if obj["shard"] != shard or obj["shards"] != total or obj["commercially_approved"] != 0:
            raise ValueError("Invalid shard gate or unexpected commercial approval")
        if obj["processed"] != len(obj["rows"]):
            raise ValueError("Truncated shard")
        for r in obj["rows"]:
            identity = r["source_identity"]
            if identity in seen or shard_of(identity, total) != shard or r.get("commercially_approved") is not False or r.get("runtime_visible") is not False:
                raise ValueError("Identity collision, partition mismatch, or unsafe approval")
            seen.add(identity)
            records.append(r)
    original = {x["source_identity"] for x in queue}
    if seen != original or len(records) != EXPECTED:
        raise ValueError("Missing, additional, or repeated image candidates")
    duplicate = collections.defaultdict(list)
    for r in records:
        if r.get("pixel"):
            duplicate[r["pixel"]["decoded_rgb_sha256"]].append(r["source_identity"])
    statuses = collections.Counter(r["result"] for r in records)
    color = collections.Counter(r.get("technical_color_class", "NOT_DECODED") for r in records)
    artist = collections.Counter(r.get("artist_id") for r in records)
    summary = {
        "source_candidates": EXPECTED,
        "independent_evidence_rows": len(records),
        "statuses": dict(statuses),
        "color_classes": dict(color),
        "by_artist": dict(artist),
        "pixel_duplicate_groups": [v for v in duplicate.values() if len(v) > 1],
        "commercially_approved": 0, "runtime_imported": 0,
        "rights_and_territory_review": "OPEN",
        "manual_curatorial_review": "OPEN",
        "candidate_release": "BLOCKED",
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (out / "review_queue.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(("source_identity", "artist", "title", "result", "technical_color_class",
                         "license_claim", "identity_gate", "image_rights_gate", "visual_gate", "record_url", "error"))
        for r in sorted(records, key=lambda x: (x.get("artist_id") or "", x["source_identity"])):
            writer.writerow((r["source_identity"], r.get("artist_id"), r.get("title"), r["result"],
                             r.get("technical_color_class"), r.get("source_license_claim"),
                             r["identity_gate"], r["image_rights_gate"], r["visual_gate"],
                             r.get("record_url"), r.get("technical_error")))
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--shard", type=int)
    parser.add_argument("--shards", type=int, default=SHARDS)
    parser.add_argument("--aggregate-from", type=Path)
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    queue = read_queue(args.inventory)
    if args.aggregate_from is not None:
        aggregate(queue, args.aggregate_from, args.out, args.shards)
    else:
        if args.shard is None or not 0 <= args.shard < args.shards:
            parser.error("--shard must be within [0, --shards)")
        run_shard(queue, args.shard, args.shards, args.out, args.offline)


if __name__ == "__main__":
    main()
