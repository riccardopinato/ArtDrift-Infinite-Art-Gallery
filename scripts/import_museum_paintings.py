#!/usr/bin/env python3
"""Build a *small* rights-filtered snapshot of real paintings for ArtDrift.

Museum connectors deliberately work with source-controlled public data.
Images are downloaded ONLY at ~200px and re-encoded as tiny WebP; hi-res art
is NEVER bundled in the APK. No API keys, scraping or model/cloud costs.
This script runs only as a one-time explicit GitHub Actions import job.
"""
from __future__ import annotations

import csv
import io
import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import quote, urlencode, urlparse
from urllib.request import Request, urlopen

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "museums"
THUMBS = OUT / "thumbs"
LIMIT = int(os.environ.get("ARTDRIFT_MUSEUM_LIMIT", "350"))
MAX_BYTES = 2_500_000  # a remotely fetched small JPEG must not be multi-MB
MAX_SUM = 2_600_000  # total WebP snapshot is deliberately tiny
HEADERS = {"User-Agent": "ArtDrift-Museum-OpenAccess/0.1 (community gallery; low-rate)", "Accept": "*/*"}
CAPS = {"met": 160, "cleveland": 150, "rijks": 80, "nga": 60, "getty": 3}
SOURCE_LABELS = {
    "met": "The Metropolitan Museum of Art",
    "cleveland": "Cleveland Museum of Art",
    "rijks": "Rijksmuseum",
    "nga": "National Gallery of Art, Washington",
    "getty": "J. Paul Getty Museum",
}
ALLOWED_HOSTS = {
    "met": {"images.metmuseum.org"},
    "cleveland": {"openaccess-cdn.clevelandart.org", "clevelandart.org", "www.clevelandart.org"},
    "rijks": {"iiif.micr.io"},
    "nga": {"api.nga.gov", "media.nga.gov"},
    "getty": {"media.getty.edu"},
}
RIGHTS = ("creativecommons.org/publicdomain/zero/1.0", "creativecommons.org/publicdomain/mark/1.0")

def _url_ok(url, source):
    try:
        u = urlparse(url)
        return u.scheme == "https" and not u.username and not u.password and u.port in (None, 443) and u.hostname in ALLOWED_HOSTS[source]
    except Exception:
        return False

def _fetch(url, size=MAX_BYTES, attempts=2):
    for try_index in range(attempts):
        try:
            req = Request(url, headers=HEADERS)
            with urlopen(req, timeout=22) as response:
                if response.status != 200:
                    raise RuntimeError(f"status={response.status}")
                body = response.read(size + 1)
                if not body or len(body) > size:
                    raise ValueError(f"empty / >{size}B response")
                return body
        except Exception as e:
            if try_index + 1 >= attempts:
                raise
            time.sleep(1.3 + try_index * 1.2)
    raise RuntimeError("unreachable")

def _json(url, size=5_000_000):
    return json.loads(_fetch(url, size))

def _value(d, key):
    x = d.get(key) if isinstance(d, dict) else None
    return x.strip() if isinstance(x, str) else ""

def _int(v):
    try: return int(v)
    except (TypeError, ValueError): return None

def _valid_right(v):
    if not isinstance(v, str): return False
    return any(token in v.lower() for token in RIGHTS)

def _marked_public(obj):
    """Require a rights/license *key*, never find CC0 somewhere in narrative prose."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            if any(x in key.lower() for x in ("rights", "license", "copyright")):
                if _valid_right(value): return True
                if isinstance(value, dict) and any(_valid_right(q) for q in value.values()): return True
                if isinstance(value, list) and any(_valid_right(q) for q in value): return True
            if isinstance(value, (list, dict)) and _marked_public(value):
                return True
    if isinstance(obj, list):
        return any(_marked_public(v) for v in obj)
    return False

def _record(source, native_id, title, artist, date, medium, image, *,
            detail="", rights="", evidence="", origin="", credit="",
            full="", tags=None, dimensions="", technique=""):
    native_id = _int(native_id)
    if not native_id or native_id < 1 or not _url_ok(image, source):
        return None
    title = (title or "").strip()
    if not title: return None
    # Existing Met/Cleveland IDs stay compatible with the already-live search.
    prefixes = {"met": 10_000_000, "cleveland": 20_000_000,
                "rijks": 3_000_000_000, "nga": 4_000_000_000,
                "getty": 5_000_000_000}
    unique_id = native_id + prefixes[source]
    if source in ("rijks", "nga", "getty") and native_id >= 990_000_000:
        return None
    if full and not _url_ok(full, source): full = ""
    return {
        "id": unique_id,
        "museum_native_id": str(native_id),
        "museum_source": source, "museum_name": SOURCE_LABELS[source],
        "title": title[:250], "artist_title": (artist or "").strip()[:250],
        "date_display": (date or "").strip()[:130],
        "image_id": "", "is_public_domain": True,
        "rights_license": rights or "Public Domain / CC0",
        "rights_evidence_url": evidence,
        "artwork_type_title": "Painting",
        "medium_display": (medium or "").strip()[:230],
        "dimensions_display": (dimensions or "").strip()[:180],
        "technique_display": (technique or "").strip()[:150],
        "place_of_origin": (origin or "").strip()[:150],
        "credit_line": (credit or "").strip()[:230],
        "remote_preview_url": image, "remote_full_url": full,
        "remote_museum_url": detail,
        "subject_terms": [x[:75] for x in (tags or []) if isinstance(x, str) and x.strip()][:20],
    }

def met_candidates():
    print("SOURCE met: acquiring object IDs", flush=True)
    candidates = []
    subjects = ("Monet", "Renoir", "landscape", "flowers", "portrait", "Vermeer", "painting")
    ids = set()
    for q in subjects:
        try:
            data = _json("https://collectionapi.metmuseum.org/public/collection/v1.1/search?" +
                         urlencode({"q": q, "hasImages": "true", "limit": "80", "offset": "0"}))
            for ident in data.get("objectIDs", []):
                if isinstance(ident, int) and ident > 0: ids.add(ident)
        except Exception as e:
            print(f"met search {q}: {type(e).__name__}: {str(e)[:80]}", flush=True)
        if len(ids) > 450: break
        time.sleep(.4)
    ids = sorted(ids)[:500]
    # One small metadata call per ID. Bounded concurrency prevents provider overload.
    def get_one(ident):
        data = _json(f"https://collectionapi.metmuseum.org/public/collection/v1/objects/{ident}", size=120000)
        if data.get("isPublicDomain") is not True: return None
        kind = (_value(data, "classification") + " " + _value(data, "objectName")).lower()
        if "paint" not in kind and "oil on" not in _value(data, "medium").lower(): return None
        image = _value(data, "primaryImageSmall")
        tags = [v.get("term", "") for v in data.get("tags") or [] if isinstance(v, dict)]
        return _record("met", ident, _value(data, "title"), _value(data, "artistDisplayName"),
                       _value(data, "objectDate"), _value(data, "medium"), image,
                       full=_value(data, "primaryImage"), detail=_value(data, "objectURL"),
                       origin=_value(data, "culture"), credit=_value(data, "creditLine"),
                       dimensions=_value(data, "dimensions"), tags=tags,
                       rights="CC0", evidence="https://www.metmuseum.org/hubs/open-access")
    with ThreadPoolExecutor(max_workers=3) as pool:
        tasks = [pool.submit(get_one, ident) for ident in ids]
        for future in as_completed(tasks):
            try:
                record = future.result()
                if record: candidates.append(record)
            except Exception: pass
    print(f"SOURCE met: eligible={len(candidates)}", flush=True)
    return sorted(candidates, key=lambda row: row["id"])[:CAPS["met"]]

def cleveland_candidates():
    print("SOURCE cleveland: acquiring CC0 objects", flush=True)
    items = {}
    for q in ("landscape", "portrait", "painting", "flowers", "Monet", "Rembrandt", "garden"):
        try:
            url = "https://openaccess-api.clevelandart.org/api/artworks/?" + urlencode({
                "q": q, "cc0": "1", "has_image": "1", "limit": "100", "skip": "0",
            })
            data = _json(url)
            for row in data.get("data", []):
                if not isinstance(row, dict): continue
                if _value(row, "share_license_status").upper() != "CC0": continue
                if "paint" not in _value(row, "type").lower(): continue
                image = ((row.get("images") or {}).get("web") or {}).get("url")
                if not _url_ok(image, "cleveland"): continue
                creators = row.get("creators") or []
                artist = next((_value(c, "description") for c in creators if isinstance(c, dict)
                               and _value(c, "description")), "")
                tags = [x if isinstance(x, str) else _value(x, "name") for x in row.get("keywords") or []]
                record = _record(
                    "cleveland", row.get("id"), _value(row, "title"), artist,
                    _value(row, "creation_date"), _value(row, "technique"), image,
                    full=((row.get("images") or {}).get("print") or {}).get("url", ""),
                    detail=_value(row, "url"), rights="CC0",
                    evidence="https://www.clevelandart.org/open-access",
                    credit=_value(row, "creditline"), origin=_value(row, "culture"),
                    dimensions=_value(row, "measurements"), tags=tags)
                if record: items[record["id"]] = record
        except Exception as e:
            print(f"cleveland {q}: {type(e).__name__}: {str(e)[:85]}", flush=True)
        if len(items) >= CAPS["cleveland"] * 2: break
        time.sleep(.5)
    print(f"SOURCE cleveland: eligible={len(items)}", flush=True)
    return sorted(items.values(), key=lambda x: x["id"])[:CAPS["cleveland"]]

def _rijks_uri(url):
    if not isinstance(url, str): return ""
    m = re.fullmatch(r"https://(?:id|data)\.rijksmuseum\.nl/(\d+)", url)
    return f"https://data.rijksmuseum.nl/{m.group(1)}?_profile=la-framed" if m else ""

def _first_link(record, key):
    if not isinstance(record, dict): return ""
    for entry in record.get(key) or []:
        if isinstance(entry, dict) and _rijks_uri(entry.get("id")):
            return _rijks_uri(entry["id"])
    return ""

def _rijks_label(value):
    if isinstance(value, dict):
        if isinstance(value.get("_label"), str): return value["_label"]
        for k in ("identified_by", "referred_to_by"):
            seq = value.get(k) or []
            for item in seq:
                if isinstance(item, dict) and isinstance(item.get("content"), str):
                    return item["content"]
    return ""

def _rijks_first_name(record):
    labels = []
    for info in record.get("identified_by") or []:
        if isinstance(info, dict) and info.get("type") == "Name":
            txt = _rijks_label(info)
            if txt: labels.append(txt)
    return labels[0] if labels else _rijks_label(record)

def rijks_candidates():
    print("SOURCE rijks: resolving Linked Art -> IIIF with per-item license", flush=True)
    records = []
    try:
        search = _json("https://data.rijksmuseum.nl/search/collection?" +
                       urlencode({"type":"painting", "imageAvailable":"true"}))
    except Exception as e:
        print(f"SOURCE rijks search unavailable {type(e).__name__}: {e}", flush=True)
        return []
    items = search.get("orderedItems") or []
    def work(item):
        uri = _rijks_uri(item.get("id")) if isinstance(item, dict) else ""
        if not uri: return None
        obj = _json(uri, size=1000000)
        # The EDM representation provides machine-readable rights metadata.
        edm = _json(uri.replace("_profile=la-framed", "_profile=edm"), size=1000000)
        if not _marked_public(edm):
            return None
        vurl = _first_link(obj, "shows")
        if not vurl: return None
        visual = _json(vurl, size=500000)
        durl = _first_link(visual, "digitally_shown_by")
        if not durl: return None
        digital = _json(durl, size=500000)
        pointer = next((_value(x, "id") for x in digital.get("access_point") or []
                        if isinstance(x, dict) and
                        _value(x, "id").startswith("https://iiif.micr.io/")), "")
        found = re.fullmatch(r"https://iiif\.micr\.io/([A-Za-z0-9_-]+)/.*", pointer)
        if not found: return None
        image_id = found.group(1)
        native = _int(urlparse(uri).path.strip("/"))
        title = _rijks_first_name(obj)
        if not native or not title: return None
        produced = obj.get("produced_by") or {}
        artist = ""
        for part in produced.get("carried_out_by") or []:
            artist = _rijks_label(part)
            if artist: break
        period = produced.get("timespan") or produced.get("time_span") or {}
        date = _rijks_label(period)
        if not date: date = _value(period, "begin_of_the_begin")[:4]
        return _record("rijks", native, title, artist, date, "",
                       f"https://iiif.micr.io/{image_id}/full/220,/0/default.jpg",
                       full=f"https://iiif.micr.io/{image_id}/full/1000,/0/default.jpg",
                       detail=f"https://www.rijksmuseum.nl/en/collection/{native}",
                       rights="Public Domain / CC0", evidence=urlparse(uri)._replace(query="_profile=edm").geturl())
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = [pool.submit(work, item) for item in items[:140]]
        for f in as_completed(futures):
            try:
                v=f.result()
                if v: records.append(v)
            except Exception as e:
                if len(records)<2: print(f"rijks item held: {type(e).__name__}: {str(e)[:70]}", flush=True)
    print(f"SOURCE rijks: rights-approved={len(records)}", flush=True)
    return sorted(records, key=lambda x:x["id"])[:CAPS["rijks"]]

def nga_candidates():
    """NGA source CSV explicitly distinguishes openaccess=1 imagery from metadata."""
    print("SOURCE nga: checking CC0 CSV + openaccess image flag", flush=True)
    # The dataset is large; hard cap each GET and skip on changed provider schema.
    base="https://raw.githubusercontent.com/NationalGalleryOfArt/opendata/main/data/"
    try:
        art_bytes=_fetch(base+"objects.csv",size=42000000)
        images_bytes=_fetch(base+"published_images.csv",size=30000000)
    except Exception as e:
        print(f"SOURCE nga not loaded (CSV): {type(e).__name__}: {str(e)[:90]}", flush=True)
        return []
    data={}
    for row in csv.DictReader(io.StringIO(art_bytes.decode("utf-8-sig"))):
        ident=_int(row.get("objectid"))
        if not ident: continue
        typefield=(row.get("classification") or row.get("subclassification") or "").lower()
        if "paint" not in typefield: continue
        data[ident]=row
    results=[]
    for row in csv.DictReader(io.StringIO(images_bytes.decode("utf-8-sig"))):
        if (row.get("openaccess") or "").strip() not in ("1","true","True"): continue
        ident=_int(row.get("depictstmsobjectid") or row.get("associatedtmsobjectid"))
        if not ident or ident not in data: continue
        src=data[ident]
        url=(row.get("iiifurl") or "").strip().rstrip("/")
        if not _url_ok(url, "nga"): continue
        image=url+"/full/220,/0/default.jpg"
        record=_record("nga",ident,(src.get("title") or ""), "",
                      (src.get("displaydate") or ""), (src.get("medium") or ""),
                      image,full=url+"/full/1000,/0/default.jpg",
                      detail=f"https://www.nga.gov/artworks/{ident}",
                      rights="Public Domain / NGA Open Access",
                      evidence="https://www.nga.gov/artworks/free-images-and-open-access",
                      credit=src.get("creditline",""),dimensions=src.get("dimensions",""))
        if record: results.append(record)
        if len(results)>=CAPS["nga"]: break
    print(f"SOURCE nga: eligible={len(results)}", flush=True)
    return results

def getty_candidates():
    """Getty Linked Art: no general enumerate API. Probe one documented item
    and only use image if its explicit subject_to classification is CC0.
    """
    print("SOURCE getty: official documented CC0 item probe", flush=True)
    # Full dataset harvesting is not possible through the Getty REST enumeration API.
    obj_id="c88b3df0-de91-4f5b-a9ef-7b2b9a6d8abb"  # Irises (official API docs)
    url=f"https://data.getty.edu/museum/collection/object/{obj_id}"
    try:
        obj=_json(url,size=1500000)
    except Exception as e:
        print(f"SOURCE getty unavailable: {type(e).__name__} {str(e)[:80]}", flush=True)
        return []
    title=_rijks_first_name(obj) or "Irises"
    visual=obj.get("shows") or []
    out=[]
    for show in visual:
        # Do not reuse ambiguous images or unlicensed narrative descriptions.
        if not isinstance(show, dict):continue
        if not _marked_public(show): continue
        image = ""
        for objpart in show.get("digitally_shown_by") or []:
            if isinstance(objpart,dict) and "media.getty.edu" in str(objpart):
                image=_value(objpart,"id")
        if not _url_ok(image,"getty"): continue
        native=int.from_bytes(obj_id.encode()[:5],"little")%800000000
        record=_record("getty",native,title,"Vincent van Gogh","1889",
                       "Oil on canvas",image,
                       detail="https://www.getty.edu/art/collection/",
                       rights="CC0",evidence=url)
        if record: out.append(record)
    print(f"SOURCE getty: eligible={len(out)}", flush=True)
    return out[:CAPS["getty"]]

def _encode_preview(url,source):
    if not _url_ok(url,source): raise ValueError("invalid image provenance")
    data=_fetch(url)
    with Image.open(io.BytesIO(data)) as raw:
        original=ImageOps.exif_transpose(raw)
        if original.width<40 or original.height<40:raise ValueError("image too small")
        iw,ih=original.width,original.height
        img=original.convert("RGB")
        img.thumbnail((220,260),Image.Resampling.LANCZOS)
        out=io.BytesIO()
        img.save(out,"WEBP",quality=60,method=6)
        blob=out.getvalue()
        if len(blob)<250 or len(blob)>22000:
            raise ValueError("WebP budget fail")
        return blob,iw,ih

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    THUMBS.mkdir(parents=True,exist_ok=True)
    collected=[]
    connectors=(met_candidates,cleveland_candidates,rijks_candidates,nga_candidates,getty_candidates)
    for connector in connectors:
        try:
            entries=connector()
            collected.extend(entries)
        except Exception as e:
            print(f"Source {connector.__name__} failed: {type(e).__name__} {str(e)[:110]}",flush=True)
    canonical={r["id"]:r for r in collected if r}
    print("CANDIDATES", len(canonical), flush=True)
    entries=[]
    total=0
    sourcecounts={}
    for row in sorted(canonical.values(), key=lambda r:(r["museum_source"],r["id"])):
        if len(entries)>=LIMIT:break
        try:
            blob,iw,ih=_encode_preview(row["remote_preview_url"],row["museum_source"])
            if total+len(blob)>MAX_SUM:break
            name=f'{row["museum_source"]}_{row["id"]}.webp'
            (THUMBS/name).write_bytes(blob)
            row["bootstrap_asset"]="assets/museums/thumbs/"+name
            row["thumbnail"]={"width":iw,"height":ih}
            entries.append(row)
            total+=len(blob)
            sourcecounts[row["museum_source"]]=sourcecounts.get(row["museum_source"],0)+1
            if len(entries)%25==0:
                print(f"ASSET {len(entries)} images={total}B by={sourcecounts}",flush=True)
        except Exception as e:
            if len(entries)<12:
                print(f"image held {row['museum_source']}:{row['id']} {type(e).__name__}: {str(e)[:90]}",flush=True)
        time.sleep(.1)
    if len(entries)<48 or len(sourcecounts)<2:
        raise SystemExit(f"FAIL CLOSED insufficient rights-approved images: {len(entries)} from {sourcecounts}")
    entries.sort(key=lambda row:(row["museum_source"],row["id"]))
    (OUT/"catalog.json").write_text(json.dumps(entries,ensure_ascii=False,separators=(",",":"))+"\n",encoding="utf-8")
    report={
      "schema":1,"image_count":len(entries),"preview_bytes":total,
      "sources":sourcecounts,"rights_gate":"explicit source record rights + host allowlist + independently decoded tiny WebP",
      "image_max_bytes":22000,"catalog_path":"assets/museums/catalog.json",
      "license_reviews_required_before_store":True,
    }
    (OUT/"import_report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("MUSEUM_IMPORT_SUCCESS",json.dumps(report,sort_keys=True),flush=True)

if __name__ == "__main__":
    main()
