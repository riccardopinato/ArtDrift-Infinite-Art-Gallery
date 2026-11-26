#!/usr/bin/env python3
"""Independent, metadata-first museum discovery lanes for Art Drift.

No gallery/runtime changes. Never interpret a small sample as museum absence.
Copyright, visual selection and commercial deployment are different gates.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
import urllib.parse
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw

from artdrift_eu_new_museums_batch import (
    ART_URL_LICENSE, AVOID_RE, ROOT, color_tier, common_license,
    image_raster, jget, rijks_object, scene_title, search_rijks,
    staedel_parse, staedel_records, visual_review_exception,
)
from artdrift_commons_pd_bright import safe_thumb, strip_html

LANES = {
    "rijks": {
        "museum": "Rijksmuseum", "country": "Netherlands",
        "terms": ["landschap", "tuin", "bloemen", "boom", "bomen", "veld",
                  "rivieroever", "rivier", "strand", "kust", "zee",
                  "duinen", "zomer", "park", "lente", "natuur",
                  "Jongkind", "Toorop", "Monet", "Gestel", "Sluijters"],
    },
    "nationalmuseum_se": {
        "museum": "Nationalmuseum Stockholm", "country": "Sweden",
        "categories": ["Category:Paintings in the Nationalmuseum Stockholm",
                       "Category:Images from the Nationalmuseum Stockholm"],
        "terms": ["Nationalmuseum Stockholm landscape",
                  "Nationalmuseum Stockholm flowers",
                  "Nationalmuseum Stockholm garden",
                  "Nationalmuseum Stockholm landscape sea",
                  "Nationalmuseum Stockholm meadow",
                  "Nationalmuseum Stockholm spring"],
    },
    "staedel": {
        "museum": "Städel Museum", "country": "Germany",
        "terms": ["scope:major LIDO"],
    },
    "finnish_national_gallery": {
        "museum": "Finnish National Gallery / Ateneum", "country": "Finland",
        "categories": ["Category:Paintings in the Ateneum",
                       "Category:Paintings in the Finnish National Gallery"],
        "terms": ["Ateneum landscape", "Ateneum flowers",
                  "Finnish National Gallery painting landscape",
                  "Sinebrychoff landscape", "Ateneum lake"],
    },
    "birmingham": {
        "museum": "Birmingham Museums Trust", "country": "United Kingdom",
        "categories": ["Category:Paintings in the Birmingham Museum and Art Gallery",
                       "Category:Art in Birmingham Museum and Art Gallery"],
        "terms": ["Birmingham Museum and Art Gallery landscape",
                  "Birmingham Museum and Art Gallery flowers",
                  "Birmingham Museums Trust painting landscape",
                  "Birmingham Museum and Art Gallery sea"],
    },
    "belvedere": {
        "museum": "Belvedere Vienna", "country": "Austria",
        "categories": ["Category:Paintings in the Belvedere (Vienna)",
                       "Category:Paintings in the Österreichische Galerie Belvedere"],
        "terms": ["Belvedere Vienna landscape painting",
                  "Belvedere Vienna flowers", "Österreichische Galerie Belvedere garden",
                  "Belvedere Vienna landscape"],
    },
    "paris_musees": {
        "museum": "Paris Musées", "country": "France",
        "categories": ["Category:Paintings in the Petit Palais",
                       "Category:Paintings in the Musée Carnavalet"],
        "terms": ["Petit Palais Paris landscape painting",
                  "Musée Carnavalet landscape painting",
                  "Paris Musées painting flowers",
                  "Musée d'Art Moderne de Paris landscape"],
    },
    "te_papa": {
        "museum": "Museum of New Zealand Te Papa Tongarewa",
        "country": "New Zealand",
        "categories": ["Category:Paintings in the Museum of New Zealand Te Papa Tongarewa"],
        "terms": ["Te Papa museum landscape painting",
                  "Museum of New Zealand Te Papa painting",
                  "Te Papa floral painting", "Te Papa seaside painting"],
    },
    "nasjonalmuseet": {
        "museum": "Nasjonalmuseet Oslo", "country": "Norway",
        "categories": ["Category:Paintings in the National Gallery of Norway",
                       "Category:Paintings in the Nasjonalmuseet"],
        "terms": ["Nasjonalmuseet landscape painting",
                  "National Gallery of Norway landscape",
                  "Nasjonalmuseet summer sea painting",
                  "Nasjonalmuseet garden painting"],
    },
}
CATEGORY_BOUND = 12
SCENES = ("landscape", "landskap", "landschap", "landskab", "garden",
          "flowers", "blom", "sea", "coast", "tree", "wood", "river",
          "summer", "spring", "meadow", "mountain", "village",
          "lake", "forest", "shore", "beach", "fjord", "water",
          "field", "park", "pastoral", "garden", "nature", "somm",
          "kust", "bergen", "baum", "himmel", "sol", "lumiere", "paysage")
EXCLUDE = ("portrait", "self portrait", "self-portrait", "dolls",
           "puppen", "toys", "nude", "night", "nocturne", "war",
           "battle", "black")
OUT = ROOT / "research/museums/20261126/lanes/results"

# Distinguish files merely returned by a full-text query from works whose
# institutional origin can be grounded in a museum category or file record.
PROVENANCE_NAMES = {
    "nationalmuseum_se": ("nationalmuseum", "national museum stockholm"),
    "finnish_national_gallery": ("ateneum", "finnish national gallery", "sinebrychoff",
                                  "kansallisgalleria"),
    "birmingham": ("birmingham museum and art gallery", "birmingham museums trust",
                   "birmingham museums"),
    "belvedere": ("österreichische galerie belvedere", "osterreichische galerie belvedere",
                  "belvedere vienna", "belvedere wien"),
    "paris_musees": ("petit palais", "musee carnavalet", "musée carnavalet",
                    "paris musées", "paris musees"),
    "te_papa": ("te papa", "museum of new zealand"),
    "nasjonalmuseet": ("nasjonalmuseet", "nasjonalgalleriet",
                       "national gallery of norway",
                       "national museum of art architecture and design",
                       "national museum of art, architecture and design"),
}
SUPPORTED_FILE_MIME = ("image/jpeg", "image/png", "image/webp", "image/tiff")


def institutional_mention(provider: str, title: str, ext: dict) -> bool:
    fields = [title]
    for key in ("Credit", "Source", "Institution", "ObjectName", "ImageDescription"):
        value = (ext.get(key) or {}).get("value", "") if isinstance(ext.get(key),dict) else ""
        if value:
            fields.append(strip_html(value))
    text = " ".join(fields).casefold()
    return any(s.casefold() in text for s in PROVENANCE_NAMES.get(provider, ()))



def is_scenic(title: str) -> bool:
    norm = re.sub(r"[^a-z0-9 ]+", " ", title.lower())
    if any(re.search(r"\b" + re.escape(w) + r"\b", norm) for w in EXCLUDE):
        return False
    return any(s in norm for s in SCENES)


COMMONS_THROTTLED = False


def get_image_pages(q: dict, max_pages: int, resume: dict | None = None):
    """Bounded MediaWiki continuation, preserving cursor on API 429.

    Return (files, pages_fetched, errors, next_cursor, exhausted).
    An exhausted query is not proof that the museum catalog is exhaustive.
    """
    global COMMONS_THROTTLED
    if COMMONS_THROTTLED:
        return [], 0, ["COMMONS_API_THROTTLED_NO_FURTHER_REQUESTS"], resume, False
    q = {"action": "query", "format": "json", "formatversion": 2,
         "prop": "imageinfo", "iiprop": "url|mime|extmetadata|sha1",
         "iiurlwidth": 320, "iilimit": 1, **q}
    if resume:
        q.update(resume)
    results = {}
    errors = []
    pages = 0
    visited = set()
    request_cursor = dict(resume) if resume else None
    for _ in range(max_pages):
        url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(q)
        try:
            response = jget(url)
        except Exception as e:
            msg = str(e)
            if (getattr(e, "code", None) in (429, 503) or
                    "HTTP Error 429" in msg or "HTTP Error 503" in msg):
                COMMONS_THROTTLED = True
                errors.append("COMMONS_HOST_THROTTLED_STOP__"+msg[:130])
            else:
                errors.append(msg[:190])
            break
        if response.get("error"):
            err = response["error"]
            code = str(err.get("code", "")).lower() if isinstance(err, dict) else ""
            if code in ("ratelimited", "maxlag"):
                COMMONS_THROTTLED = True
            errors.append(str(err)[:190])
            break
        pages += 1
        for item in (response.get("query") or {}).get("pages") or []:
            pid = item.get("pageid")
            if isinstance(pid, int) and item.get("title", "").startswith("File:"):
                results[pid] = item
        continuation = response.get("continue") or {}
        if not continuation:
            return list(results.values()), pages, errors, None, True
        stamp = json.dumps(continuation, sort_keys=True)
        if stamp in visited:
            errors.append("REPEATED_COMMONS_CONTINUATION")
            break
        visited.add(stamp)
        request_cursor = dict(continuation)
        q.update(continuation)
        time.sleep(0.35)
    return list(results.values()), pages, errors, request_cursor, False



def from_commons(p: dict, museum: str, origin: str, exact_category: bool) -> dict:
    info = ((p.get("imageinfo") or [{}])[0])
    ext = info.get("extmetadata") or {}
    title = str(p.get("title") or "").removeprefix("File:")
    license_ok, lic = common_license(ext)
    artist = re.sub(r"\s+", " ", strip_html((ext.get("Artist") or {}).get("value", "")))[:150]
    date = strip_html((ext.get("DateTimeOriginal") or {}).get("value", ""))[:100]
    url = str(info.get("thumburl") or "")
    rights = str(lic.get("license_name") or "") if lic else ""
    safe_media = bool(safe_thumb(url))
    mime_supported = str(info.get("mime") or "") in SUPPORTED_FILE_MIME
    subject = is_scenic(title)
    trustworthy = exact_category or institutional_mention(museum, title, ext)
    provenance = ("INSTITUTIONAL_CATEGORY" if exact_category else
                  "SEARCH_RECORD_MUSEUM_MATCH" if trustworthy else
                  "SEARCH_RESULT_INSTITUTION_UNCONFIRMED")
    return {
        "source": museum, "museum_native_id": str(p["pageid"]),
        "title": title[:240], "artist": artist, "creation_date_raw": date,
        "museum_url": "https://commons.wikimedia.org/w/index.php?curid=" + str(p["pageid"]),
        "remote_preview_url": url if safe_media else None,
        "original_media_url": str(info.get("url") or "")[:500],
        "image_license_per_item": rights if license_ok else "UNVERIFIED_OR_RESTRICTED",
        "image_license_checked": bool(license_ok),
        "institutional_provenance": provenance,
        "institutional_origin_confirmed": trustworthy,
        "image_mime": str(info.get("mime") or ""),
        "supported_image_format": mime_supported,
        "origin_query": origin, "file_sha1": str(info.get("sha1") or ""),
        "scenic_title_indicator": subject,
        "date_needs_verification": True,
        "commercially_approved": False, "runtime_visible": False,
        "review_status": "HOLD_VISUAL_SOURCE_RIGHTS_TERRITORY",
    }


def discover_commons(museum: str, bound: int):
    cfg = LANES[museum]
    candidates = {}
    stats = Counter()
    errors = []
    old_report_path = OUT / (museum + ".json")
    if old_report_path.is_file():
        saved_report = json.loads(old_report_path.read_text(encoding="utf-8"))
        if saved_report.get("provider") != museum:
            raise ValueError("Prior source report provider mismatch")
        saved_progress = saved_report.get("query_progress") or {}
    else:
        saved_progress = {}
    progress = {}
    for category in cfg.get("categories", []):
        q = {"generator": "categorymembers", "gcmtitle": category,
             "gcmtype": "file", "gcmlimit": 50}
        old = saved_progress.get(category) or {}
        if old.get("status") == "exhausted":
            progress[category] = old
            stats["queries_previously_exhausted"] += 1
            continue
        rows, pages, errs, cursor, exhausted = get_image_pages(
            q, CATEGORY_BOUND, resume=old.get("cursor"))
        stats["category_pages"] += pages
        stats["category_file_hits"] += len(rows)
        errors.extend({"source": category, "error": e} for e in errs)
        progress[category] = {"status": "exhausted" if exhausted else "partial",
                              "cursor": cursor, "pages_in_this_run": pages}
        for row in rows:
            candidates[row["pageid"]] = from_commons(row, museum, category, True)
        time.sleep(0.30)
    for search in cfg["terms"]:
        q = {"generator": "search", "gsrnamespace": 6,
             "gsrsearch": search, "gsrlimit": 50}
        old = saved_progress.get(search) or {}
        if old.get("status") == "exhausted":
            progress[search] = old
            stats["queries_previously_exhausted"] += 1
            continue
        rows, pages, errs, cursor, exhausted = get_image_pages(
            q, 3, resume=old.get("cursor"))
        stats["search_pages"] += pages
        stats["search_file_hits"] += len(rows)
        errors.extend({"source": search, "error": e} for e in errs)
        progress[search] = {"status": "exhausted" if exhausted else "partial",
                            "cursor": cursor, "pages_in_this_run": pages}
        for row in rows:
            if row["pageid"] not in candidates:
                candidates[row["pageid"]] = from_commons(row, museum, search, False)
        time.sleep(0.30)
    all_rows = list(candidates.values())
    stats["unique_files_discovered"] = len(all_rows)
    stats["file_open_rights"] = sum(x["image_license_checked"] for x in all_rows)
    stats["scenic_title_matches"] = sum(x["scenic_title_indicator"] for x in all_rows)
    stats["institutional_origin_confirmed"] = sum(
        x["institutional_origin_confirmed"] for x in all_rows)
    stats["supported_image_file_count"] = sum(
        x["supported_image_format"] for x in all_rows)
    stats["rejected_nonimage_or_pdf_hits"] = sum(
        not x["supported_image_format"] for x in all_rows)
    all_rows.sort(key=lambda x: (
        not x["institutional_origin_confirmed"],
        not x["supported_image_format"],
        not x["scenic_title_indicator"],
        not x["image_license_checked"],
        x["institutional_provenance"] != "INSTITUTIONAL_CATEGORY",
        x["museum_native_id"]))
    stats["source_host_throttled"] = int(COMMONS_THROTTLED)
    return all_rows[:bound], stats, errors, progress


def discover_rijks(bound: int):
    """Broad query inventory before inspecting full records or pixels."""
    terms = LANES["rijks"]["terms"]
    discovered = {}
    counts = Counter()
    errors = []
    for term in terms:
        try:
            ids, total = search_rijks(term, max_pages=5)
            counts["sum_query_matches_nonunique"] += total
            counts["id_links_returned_nonunique"] += len(ids)
            for ident in ids:
                discovered.setdefault(ident, {"id": ident, "search_terms": []})
                discovered[ident]["search_terms"].append(term)
        except Exception as e:
            errors.append({"query": term, "error": str(e)[:190]})
        time.sleep(0.12)
    ids = list(discovered)
    # Interleave query buckets rather than giving the entire budget to term 1.
    buckets = [[ident for ident, v in discovered.items() if term in v["search_terms"]]
               for term in terms]
    balanced = []
    seen = set()
    for index in range(max((len(b) for b in buckets), default=0)):
        for b in buckets:
            if index < len(b) and b[index] not in seen:
                seen.add(b[index])
                balanced.append(b[index])
    counts["unique_search_ids"] = len(ids)
    counts["uninspected_metadata_count"] = max(0, len(ids)-bound)
    candidates = []
    for ident in balanced[:bound]:
        try:
            work = rijks_object(ident)
            if work is not None:
                work["source_queries"] = discovered[ident]["search_terms"]
                work["runtime_visible"] = False
                work["commercially_approved"] = False
                work["review_status"] = "HOLD_VISUAL_AND_PER_IMAGE_RIGHTS"
                candidates.append(work)
                counts["full_records_scenic_with_media"] += 1
            else:
                counts["full_records_filtered_or_without_iiif"] += 1
        except Exception as e:
            counts["object_errors"] += 1
            if len(errors) < 20:
                errors.append({"id": ident, "error": str(e)[:190]})
    counts["full_records_attempted"] = min(len(ids), bound)
    # Retain ALL candidate identifiers even when metadata selection fails,
    # so uninspected URLs are never confused with rejected artwork.
    return candidates, counts, errors, balanced[:500]


def discover_staedel(bound: int):
    stats = Counter()
    errors = []
    try:
        records = staedel_records()
    except Exception as e:
        return [], stats, [{"source": "official_oai", "error": str(e)[:240]}], []
    stats["active_lido_records"] = len(records)
    candidates = []
    raw_ids = []
    for record in records:
        header = record.find(".//{http://www.openarchives.org/OAI/2.0/}identifier")
        if header is not None and header.text:
            raw_ids.append(header.text)
        item = staedel_parse(record)
        if item:
            item["review_status"] = "HOLD_VISUAL_AND_BY_SA_CREDIT"
            candidates.append(item)
    stats["scenic_media_records"] = len(candidates)
    return candidates[:bound], stats, errors, raw_ids[:500]


def image_review(candidates: list[dict], checks: int, stats: Counter):
    checked = 0
    images = []
    for c in candidates:
        url = c.get("remote_preview_url")
        if not url or checked >= checks or (
                c["source"] not in ("rijks", "staedel") and
                (not c.get("scenic_title_indicator", True) or
                 not c.get("image_license_checked", False) or
                 not c.get("institutional_origin_confirmed", False) or
                 not c.get("supported_image_format", False))):
            continue
        checked += 1
        try:
            metrics, sha, thumb = image_raster(url)
            c["color_metrics"] = metrics
            c["image_sha256"] = sha
            tier = color_tier(metrics)
            c["color_tier"] = tier
            if tier.startswith("HOLD"):
                c["review_status"] = ("HOLD_HIGH_CHROMA_VISUAL" if
                    visual_review_exception(metrics) else "HOLD_MUTED_OR_DARK")
            else:
                c["review_status"] = "HOLD_VISUAL_AND_COMMERCIAL_RIGHTS"
                stats["technical_color_pass"] += 1
            if len(images) < 50:
                images.append((c["title"][:27], thumb))
            stats["pixel_checked"] += 1
        except Exception as e:
            c["image_error"] = str(e)[:160]
            stats["image_errors"] += 1
    stats["image_requests_attempted"] = checked
    return images


def mosaic(images, museum):
    if not images:
        return
    cols = 5
    width, height = 190, 185
    canvas = Image.new("RGB", (cols*width, ((len(images)+cols-1)//cols)*height),
                       "white")
    painter = ImageDraw.Draw(canvas)
    for i, (name, thumb) in enumerate(images):
        x, y = (i % cols)*width, (i // cols)*height
        canvas.paste(thumb, (x+(width-thumb.width)//2, y))
        painter.text((x+4, y+141), name, fill="black")
    OUT.mkdir(parents=True, exist_ok=True)
    canvas.save(OUT/(museum+"_contact_sheet.jpg"), quality=82, optimize=True)


def run(provider: str, max_records: int, max_images: int):
    cfg = LANES[provider]
    if provider == "rijks":
        candidates, stats, errs, raw_ids = discover_rijks(max_records)
    elif provider == "staedel":
        candidates, stats, errs, raw_ids = discover_staedel(max_records)
    else:
        candidates, stats, errs, query_progress = discover_commons(provider, max_records)
        raw_ids = [x["museum_native_id"] for x in candidates]
    stats = Counter(stats)
    previews = image_review(candidates, max_images, stats)
    mosaic(previews, provider)
    report = {
        "schema_version": 1,
        "date_utc": datetime.now(timezone.utc).isoformat(),
        "provider": provider,
        "museum": cfg["museum"],
        "source_approach": ("OFFICIAL_LINKED_ART" if provider == "rijks"
                            else "OFFICIAL_OAI_LIDO" if provider == "staedel"
                            else "WIKIMEDIA_COMMONS_INSTITUTIONAL_CATEGORIES_AND_SEARCH"),
        "catalog_exhaustively_searched": False,
        "source_zero_artworks_proven": False,
        "metadata_identifiers_discovered_or_scanned": stats.get(
            "unique_search_ids", stats.get("unique_files_discovered",
            stats.get("active_lido_records", 0))),
        "candidates_in_report": len(candidates),
        "stats": dict(stats),
        "errors": errs[:30],
        "source_identifier_sample": raw_ids[:500],
        "review_candidates": candidates,
        "cross_museum_dedupe": "PENDING_GLOBAL_ARTWORK_AND_FILE_HASH",
        "per_image_commercial_rights": "HOLD",
        "runtime_imported": 0,
        "commercially_approved": 0,
    }
    if provider not in ("rijks", "staedel"):
        report["query_progress"] = query_progress
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT/(provider+".json")
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n",
                    encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items()
        if k not in ("source_identifier_sample", "review_candidates")},
        ensure_ascii=False), flush=True)
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", required=True, choices=sorted(LANES))
    parser.add_argument("--max-records", type=int, default=180)
    parser.add_argument("--max-image-checks", type=int, default=70)
    args = parser.parse_args()
    if not 30 <= args.max_records <= 1000:
        parser.error("max-records must be between 30 and 1000")
    if not 0 <= args.max_image_checks <= 200:
        parser.error("max-image-checks must be between 0 and 200")
    run(args.provider, args.max_records, args.max_image_checks)


if __name__ == "__main__":
    main()
