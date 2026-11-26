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


def is_scenic(title: str) -> bool:
    norm = re.sub(r"[^a-z0-9 ]+", " ", title.lower())
    if any(re.search(r"\b" + re.escape(w) + r"\b", norm) for w in EXCLUDE):
        return False
    return any(s in norm for s in SCENES)


def get_image_pages(q: dict, max_pages: int) -> tuple[list[dict], int, list[str]]:
    """Only Commons public MediaWiki API; follow its continuation as provided."""
    q = {"action": "query", "format": "json", "formatversion": 2,
         "prop": "imageinfo", "iiprop": "url|mime|extmetadata|sha1",
         "iiurlwidth": 320, "iilimit": 1, **q}
    results = {}
    errors = []
    pages = 0
    visited = set()
    for _ in range(max_pages):
        url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(q)
        try:
            response = jget(url)
        except Exception as e:
            errors.append(str(e)[:190])
            break
        if response.get("error"):
            errors.append(str(response["error"])[:190])
            break
        pages += 1
        for item in (response.get("query") or {}).get("pages") or []:
            pid = item.get("pageid")
            if isinstance(pid, int) and item.get("title", "").startswith("File:"):
                results[pid] = item
        continuation = response.get("continue") or {}
        if not continuation:
            break
        stamp = json.dumps(continuation, sort_keys=True)
        if stamp in visited:
            errors.append("REPEATED_COMMONS_CONTINUATION")
            break
        visited.add(stamp)
        q.update(continuation)
        time.sleep(0.18)
    return list(results.values()), pages, errors


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
    subject = is_scenic(title)
    provenance = "INSTITUTIONAL_CATEGORY" if exact_category else "SEARCH_RESULT_REVIEW"
    return {
        "source": museum, "museum_native_id": str(p["pageid"]),
        "title": title[:240], "artist": artist, "creation_date_raw": date,
        "museum_url": "https://commons.wikimedia.org/w/index.php?curid=" + str(p["pageid"]),
        "remote_preview_url": url if safe_media else None,
        "original_media_url": str(info.get("url") or "")[:500],
        "image_license_per_item": rights if license_ok else "UNVERIFIED_OR_RESTRICTED",
        "image_license_checked": bool(license_ok),
        "institutional_provenance": provenance,
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
    for category in cfg.get("categories", []):
        q = {"generator": "categorymembers", "gcmtitle": category,
             "gcmtype": "file", "gcmlimit": 50}
        rows, pages, errs = get_image_pages(q, CATEGORY_BOUND)
        stats["category_pages"] += pages
        stats["category_file_hits"] += len(rows)
        errors.extend({"source": category, "error": e} for e in errs)
        for row in rows:
            candidates[row["pageid"]] = from_commons(row, museum, category, True)
        time.sleep(0.2)
    for search in cfg["terms"]:
        q = {"generator": "search", "gsrnamespace": 6,
             "gsrsearch": search, "gsrlimit": 50}
        rows, pages, errs = get_image_pages(q, 3)
        stats["search_pages"] += pages
        stats["search_file_hits"] += len(rows)
        errors.extend({"source": search, "error": e} for e in errs)
        for row in rows:
            if row["pageid"] not in candidates:
                candidates[row["pageid"]] = from_commons(row, museum, search, False)
        time.sleep(0.18)
    all_rows = list(candidates.values())
    stats["unique_files_discovered"] = len(all_rows)
    stats["file_open_rights"] = sum(x["image_license_checked"] for x in all_rows)
    stats["scenic_title_matches"] = sum(x["scenic_title_indicator"] for x in all_rows)
    all_rows.sort(key=lambda x: (
        not x["scenic_title_indicator"],
        not x["image_license_checked"],
        x["institutional_provenance"] != "INSTITUTIONAL_CATEGORY",
        x["museum_native_id"]))
    return all_rows[:bound], stats, errors


def discover_rijks(bound: int):
    """Metadata-first discovery: thematic search PLUS broad decade inventories.

    Any filter on title alone silently loses landscapes titled by local place,
    artist or historical numbering. Search dates without title terms and retain
    not-yet-inspected IDs; inspect a balanced sample only after discovery.
    """
    terms=LANES["rijks"]["terms"]
    decades=("185?","186?","187?","188?","189?","190?",
             "191?","192?","193?","194?","195?")
    discovered={};counts=Counter();errors=[];buckets=[]
    def record(ident,kind):
        if not re.fullmatch(r"https://id\.rijksmuseum\.nl/\d+",str(ident)):
            return
        if ident not in discovered:
            discovered[ident]={"id":ident,"search_terms":[]}
        if kind not in discovered[ident]["search_terms"]:
            discovered[ident]["search_terms"].append(kind)

    for term in terms:
        try:
            ids,total=search_rijks(term,max_pages=5)
            counts["sum_query_matches_nonunique"]+=total
            counts["id_links_returned_nonunique"]+=len(ids)
            buckets.append((term,ids))
            for ident in ids:record(ident,term)
        except Exception as e:
            errors.append({"query":term,"error":str(e)[:190]})
        time.sleep(0.10)

    def period_scan(period,limit=6):
        q={"type":"painting","imageAvailable":"true","creationDate":period}
        uri="https://data.rijksmuseum.nl/search/collection?"+urllib.parse.urlencode(q)
        seen_tokens=set();ids=[];first_total=0
        for page in range(limit):
            if uri in seen_tokens:
                raise ValueError("REPEATED_RIJKS_NEXT_LINK")
            seen_tokens.add(uri)
            response=jget(uri)
            if page==0:
                first_total=int((response.get("partOf") or {}).get("totalItems") or 0)
            for x in response.get("orderedItems") or []:
                if isinstance(x,dict) and x.get("id"):
                    ids.append(x["id"])
            nxt=response.get("next")
            uri=nxt.get("id") if isinstance(nxt,dict) else None
            if not uri or not uri.startswith("https://data.rijksmuseum.nl/"):
                break
            time.sleep(.10)
        return ids,first_total

    decade_success=0
    for era in decades:
        try:
            ids,total=period_scan(era)
            decade_success+=1
            buckets.append((era,ids))
            counts["era_search_matches_nonunique"]+=total
            counts["era_identifier_links_returned"]+=len(ids)
            for ident in ids:record(ident,era)
        except Exception as e:
            errors.append({"period":era,"error":str(e)[:190]})
        time.sleep(.12)

    # If an upstream API stops accepting 3-digit decade wildcards, still
    # discover by the officially documented 18?? / 19?? century format.
    if not decade_success or counts["era_identifier_links_returned"]==0:
        for era in ("18??","19??"):
            try:
                ids,total=period_scan(era,limit=7)
                buckets.append((era,ids))
                counts["era_search_matches_nonunique"]+=total
                counts["era_identifier_links_returned"]+=len(ids)
                for ident in ids:record(ident,era)
            except Exception as e:
                errors.append({"period":era,"error":str(e)[:190]})

    balanced=[];seen=set()
    # Diverse thematic/chronological buckets prevent older masters from
    # monopolizing the bound and avoid random sampling before qualification.
    max_len=max((len(ids) for _,ids in buckets),default=0)
    for i in range(max_len):
        for _,ids in buckets:
            if i<len(ids) and ids[i] not in seen:
                seen.add(ids[i]);balanced.append(ids[i])
    counts["unique_search_ids"]=len(discovered)
    counts["uninspected_metadata_count"]=max(0,len(balanced)-bound)
    candidates=[]
    for ident in balanced[:bound]:
        try:
            work=rijks_object(ident)
            if work is not None:
                work["source_queries"]=discovered[ident]["search_terms"]
                work["runtime_visible"]=False
                work["commercially_approved"]=False
                work["review_status"]="HOLD_VISUAL_AND_PER_IMAGE_RIGHTS"
                candidates.append(work)
                counts["full_records_scenic_with_media"]+=1
            else:
                counts["full_records_filtered_or_without_iiif"]+=1
        except Exception as e:
            counts["object_errors"]+=1
            if len(errors)<30:
                errors.append({"id":ident,"error":str(e)[:190]})
    counts["full_records_attempted"]=min(len(balanced),bound)
    return candidates,counts,errors,balanced[:500]


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
                 not c.get("image_license_checked", False))):
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
        candidates, stats, errs = discover_commons(provider, max_records)
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
