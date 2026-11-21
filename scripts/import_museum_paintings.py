#!/usr/bin/env python3
"""Build a *small* rights-filtered snapshot of real paintings for ArtDrift.

Museum connectors deliberately work with source-controlled public data.
Images are downloaded ONLY at ~200px and re-encoded as tiny WebP; hi-res art
is NEVER bundled in the APK. No API keys, scraping or model/cloud costs.
This script runs only as a one-time explicit GitHub Actions import job.
"""
from __future__ import annotations

import csv
import hashlib
import xml.etree.ElementTree as ET
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
LIMIT = int(os.environ.get("ARTDRIFT_MUSEUM_LIMIT", "450"))
MAX_BYTES = 2_500_000  # a remotely fetched small JPEG must not be multi-MB
MAX_SUM = 2_600_000  # total WebP snapshot is deliberately tiny
HEADERS = {"User-Agent": "ArtDrift-Museum-OpenAccess/0.1 (community gallery; low-rate)", "Accept": "*/*"}
CAPS = {"met": 160, "cleveland": 150, "rijks": 80, "nga": 60, "getty": 3, "smithsonian": 60}
SOURCE_LABELS = {
    "met": "The Metropolitan Museum of Art",
    "cleveland": "Cleveland Museum of Art",
    "rijks": "Rijksmuseum",
    "nga": "National Gallery of Art, Washington",
    "getty": "J. Paul Getty Museum",
    "smithsonian": "Smithsonian American Art Museum",
}
ALLOWED_HOSTS = {
    "met": {"images.metmuseum.org"},
    "cleveland": {"openaccess-cdn.clevelandart.org", "clevelandart.org", "www.clevelandart.org"},
    "rijks": {"iiif.micr.io"},
    "nga": {"api.nga.gov", "media.nga.gov"},
    "getty": {"media.getty.edu"},
    "smithsonian": {"ids.si.edu", "www.si.edu", "si.edu"},
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
                "getty": 5_000_000_000, "smithsonian": 6_000_000_000}
    unique_id = native_id + prefixes[source]
    if source in ("rijks", "nga", "getty", "smithsonian") and native_id >= 990_000_000:
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
    if not isinstance(value, dict): return ""
    for key in ("_label", "content"):
        if isinstance(value.get(key), str) and value[key].strip():
            return value[key].strip()
    for entry in value.get("notation") or []:
        if isinstance(entry, dict) and isinstance(entry.get("@value"), str):
            return entry["@value"]
    for key in ("identified_by", "referred_to_by"):
        for item in value.get(key) or []:
            found=_rijks_label(item)
            if found: return found
    return ""

def _rijks_first_name(record):
    labels=[]
    for item in record.get("identified_by") or []:
        if not isinstance(item,dict):continue
        if item.get("type")=="Name":
            txt=_rijks_label(item)
            if txt:labels.append(txt)
    return labels[0] if labels else _rijks_label(record)

def _edm_rights(url):
    """The official EDM representation is RDF/XML, not JSON-LD.
    Parse only <edm:rights rdf:resource="...">, no guess from website.
    """
    data=_fetch(url,size=500000)
    doc=ET.fromstring(data)
    for elt in doc.iter():
        if not (elt.tag.endswith("}rights") or elt.tag=="rights"):continue
        allvalues=[elt.text or ""]+list(elt.attrib.values())
        for value in allvalues:
            if _valid_right(value): return value
    return ""

def _rijks_artist_and_date(record):
    produced=record.get("produced_by") or {}
    artist=""
    date=""
    parts=[produced]+[p for p in produced.get("part") or [] if isinstance(p,dict)]
    for part in parts:
        if not artist:
            for person in part.get("carried_out_by") or []:
                artist=_rijks_label(person)
                if artist:break
        if not date:
            timespan=part.get("timespan") or part.get("time_span") or {}
            date=_rijks_label(timespan)
            if not date:
                start=_value(timespan,"begin_of_the_begin")
                date=start[:4] if start else ""
    return artist,date

def rijks_candidates():
    print("SOURCE rijks: JSON-LD + official EDM RDF/XML rights",flush=True)
    try:
        pages=_json("https://data.rijksmuseum.nl/search/collection?"+
             urlencode({"type":"painting","imageAvailable":"true"}))
    except Exception as e:
        print("RIJKS_SEARCH_HELD",type(e).__name__,str(e)[:110],flush=True)
        return []
    records=[]
    items=pages.get("orderedItems") or []
    def resolve(item):
        uri=_rijks_uri(item.get("id")) if isinstance(item,dict) else ""
        if not uri:return None
        obj=_json(uri,size=1000000)
        rightsurl=uri.replace("_profile=la-framed","_profile=edm")
        rights=_edm_rights(rightsurl)
        if not rights:return None
        vurl=_first_link(obj,"shows")
        if not vurl:return None
        visual=_json(vurl,size=500000)
        durl=_first_link(visual,"digitally_shown_by")
        if not durl:return None
        digital=_json(durl,size=500000)
        pointer=next((_value(x,"id") for x in digital.get("access_point") or []
                      if isinstance(x,dict) and _value(x,"id").startswith("https://iiif.micr.io/")),"")
        match=re.fullmatch(r"https://iiif\.micr\.io/([A-Za-z0-9_-]+)/.*",pointer)
        if not match:return None
        native=_int(urlparse(uri).path.strip("/"))
        if not native:return None
        title=_rijks_first_name(obj)
        if not title:return None
        author,date=_rijks_artist_and_date(obj)
        imageid=match.group(1)
        licence="CC0" if "zero" in rights.lower() else "Public Domain Mark"
        return _record("rijks",native,title,author,date,"",
             f"https://iiif.micr.io/{imageid}/full/220,/0/default.jpg",
             full=f"https://iiif.micr.io/{imageid}/full/1000,/0/default.jpg",
             detail=f"https://data.rijksmuseum.nl/{native}",
             rights=licence,evidence=rightsurl)
    with ThreadPoolExecutor(max_workers=3) as pool:
        tasks=[pool.submit(resolve,v) for v in items[:105]]
        for f in as_completed(tasks):
            try:
                row=f.result()
                if row:records.append(row)
            except Exception as e:
                if len(records)<3:print("RIJKS_HELD",type(e).__name__,str(e)[:80],flush=True)
    print(f"SOURCE rijks: rights-approved={len(records)}",flush=True)
    return sorted(records,key=lambda x:x["id"])[:CAPS["rijks"]]

def _csv_stream(url):
    request=Request(url,headers=HEADERS)
    response=urlopen(request,timeout=50)
    # Streaming permits 80-100 MB official NGA CSV data without bundling it
    # or allocating a giant 100 MB byte string.
    return response, csv.DictReader(io.TextIOWrapper(response,encoding="utf-8-sig",newline=""))

def nga_candidates():
    print("SOURCE nga: streaming official openaccess-only published images",flush=True)
    base="https://raw.githubusercontent.com/NationalGalleryOfArt/opendata/main/data/"
    image_map={}
    try:
        response,rows=_csv_stream(base+"published_images.csv")
        try:
            for i,row in enumerate(rows):
                if i>=32000:break
                if (row.get("openaccess") or "").strip().lower() not in ("1","true"):continue
                ident=_int(row.get("depictstmsobjectid"))
                if not ident or ident in image_map:continue
                baseurl=(row.get("iiifurl") or "").strip().removesuffix("/info.json").rstrip("/")
                if not _url_ok(baseurl,"nga"):continue
                image_map[ident]=baseurl
        finally:
            response.close()
    except Exception as e:
        print("NGA_IMAGES_HELD",type(e).__name__,str(e)[:90],flush=True)
        return []
    print(f"NGA_IMAGE_CANDIDATES={len(image_map)}",flush=True)
    if not image_map:return []
    found=[]
    try:
        response,rows=_csv_stream(base+"objects.csv")
        try:
            for row in rows:
                native=_int(row.get("objectid"))
                if not native or native not in image_map:continue
                kind=(row.get("classification") or "")+" "+(row.get("subclassification") or "")
                if "paint" not in kind.lower():continue
                imagebase=image_map[native]
                image=imagebase+"/full/220,/0/default.jpg"
                record=_record("nga",native,row.get("title",""),
                     row.get("attribution",""),row.get("displaydate",""),
                     row.get("medium",""),image,
                     full=imagebase+"/full/1000,/0/default.jpg",
                     detail=f"https://www.nga.gov/artworks/{native}",
                     rights="Public Domain / NGA Open Access",
                     evidence="https://www.nga.gov/artworks/free-images-and-open-access",
                     credit=row.get("creditline",""),dimensions=row.get("dimensions",""))
                if record:found.append(record)
                if len(found)>=CAPS["nga"]:break
        finally:
            response.close()
    except Exception as e:
        print("NGA_OBJECTS_HELD",type(e).__name__,str(e)[:90],flush=True)
    print(f"SOURCE nga: eligible={len(found)}",flush=True)
    return found

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

def smithsonian_candidates():
    """Keyless Smithsonian Open Access official public S3 EDAN metadata.
    Only SAAM paintings, each media item independently marked CC0.
    """
    print("SOURCE smithsonian: public SAAM NDJSON no API key",flush=True)
    results={}
    base="https://smithsonian-open-access.s3-us-west-2.amazonaws.com/metadata/edan/saam/"
    def textitems(section,key):
        values=section.get(key) or []
        return [v.get("content","").strip() for v in values
                if isinstance(v,dict) and isinstance(v.get("content"),str)]
    for number in range(70):
        if len(results)>=CAPS["smithsonian"]:break
        shard=f"{number:02x}"
        try:
            raw=_fetch(base+shard+".txt",size=1700000)
            for line in raw.splitlines():
                if not line.strip():continue
                row=json.loads(line)
                payload=row.get("content") or {}
                info=payload.get("descriptiveNonRepeating") or {}
                ft=payload.get("freetext") or {}
                if not any("paint" in term.lower() for term in textitems(ft,"objectType")):
                    continue
                if (info.get("metadata_usage") or {}).get("access")!="CC0":continue
                media=(info.get("online_media") or {}).get("media") or []
                matched=[]
                for item in media:
                    if not isinstance(item,dict):continue
                    rights=(item.get("usage") or {}).get("access")
                    if rights!="CC0":continue
                    url=item.get("thumbnail") or item.get("content") or ""
                    if _url_ok(url,"smithsonian"):matched.append(url)
                if not matched:continue
                recordid=info.get("record_ID") or row.get("id") or ""
                if not recordid:continue
                native=(int(hashlib.sha256(recordid.encode()).hexdigest()[:8],16)
                        %800000000)+1
                nameinfo=info.get("title") or {}
                title=nameinfo.get("content") if isinstance(nameinfo,dict) else ""
                title=title or row.get("title") or ""
                link=info.get("record_link") or ""
                date=next(iter(textitems(ft,"date")),"")
                artist=next(iter(textitems(ft,"name")),"")
                medium=next(iter(textitems(ft,"physicalDescription")),"")
                descriptions=textitems(ft,"physicalDescription")
                scale=next((v for v in descriptions if any(c in v.lower() for c in
                         ("cm","inch","in.","×"," x "))),"")
                record=_record("smithsonian",native,title,artist,date,medium,
                        matched[0],detail=link,rights="CC0",
                        evidence="https://www.si.edu/openaccess",
                        credit=next(iter(textitems(ft,"creditLine")),""),
                        dimensions=scale,tags=textitems(ft,"topic"))
                if record:results[record["id"]]=record
        except Exception as e:
            if number<2:print("SI_SHARD_HELD",shard,type(e).__name__,str(e)[:80],flush=True)
        if number%16==0:print(f"SI_SHARDS={number+1} accepted={len(results)}",flush=True)
    print(f"SOURCE smithsonian: eligible={len(results)}",flush=True)
    return sorted(results.values(),key=lambda x:x["id"])[:CAPS["smithsonian"]]

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
    catalog=OUT/"catalog.json"
    entries=[]
    if catalog.exists():
        try:
            prior=json.loads(catalog.read_text(encoding="utf-8"))
            for row in prior:
                expected=f'{row["museum_source"]}_{row["id"]}.webp'
                asset=THUMBS/expected
                if (asset.exists() and asset.stat().st_size<=22000
                    and row.get("bootstrap_asset")=="assets/museums/thumbs/"+expected):
                    entries.append(row)
        except Exception as e:
            print("EXISTING_CATALOG_INVALID",type(e).__name__,str(e)[:120],flush=True)
            entries=[]
    saved={row["id"] for row in entries}
    total=sum((THUMBS/f'{row["museum_source"]}_{row["id"]}.webp').stat().st_size for row in entries)
    sourcecounts={}
    for row in entries:
        sourcecounts[row["museum_source"]]=sourcecounts.get(row["museum_source"],0)+1
    print("EXISTING",len(entries),sourcecounts,total,flush=True)
    # Preserve previously generated records/bytes. Second pass only for missing
    # museum connectors, making the catalog revision incremental and idempotent.
    functions={
        "met":met_candidates,
        "cleveland":cleveland_candidates,
        "rijks":rijks_candidates,
        "nga":nga_candidates,
        "getty":getty_candidates,
        "smithsonian":smithsonian_candidates,
    }
    candidates=[]
    for source in ("rijks","nga","smithsonian","getty","met","cleveland"):
        if sourcecounts.get(source,0)>0:continue
        try:
            candidates+=functions[source]()
        except Exception as e:
            print("PROVIDER_HELD",source,type(e).__name__,str(e)[:110],flush=True)
    bysource={}
    for row in candidates:
        if row["id"] in saved:continue
        bysource.setdefault(row["museum_source"],[]).append(row)
    for value in bysource.values():value.sort(key=lambda row:row["id"])
    # Source round-robin prevents large providers from starving Rijks/Smithsonian.
    order=("rijks","nga","smithsonian","getty","met","cleveland")
    ordered=[]
    maxitems=max((len(v) for v in bysource.values()),default=0)
    for i in range(maxitems):
        for source in order:
            group=bysource.get(source,[])
            if i<len(group):ordered.append(group[i])
    for row in ordered:
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
            if sourcecounts.get(row["museum_source"],0)<3:
                print("IMAGE_HELD",row["museum_source"],type(e).__name__,str(e)[:95],flush=True)
        time.sleep(.08)
    if len(entries)<48 or len(sourcecounts)<2:
        raise SystemExit(f"FAIL CLOSED insufficient rights-approved images: {len(entries)} {sourcecounts}")
    entries.sort(key=lambda row:(row["museum_source"],row["id"]))
    catalog.write_text(json.dumps(entries,ensure_ascii=False,separators=(",",":"))+"\n",encoding="utf-8")
    report={
      "schema":1,"image_count":len(entries),"preview_bytes":total,
      "sources":sourcecounts,"rights_gate":"individual source rights, official image host and WebP decode",
      "image_max_bytes":22000,"catalog_path":"assets/museums/catalog.json",
      "license_reviews_required_before_store":True,
    }
    (OUT/"import_report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("MUSEUM_IMPORT_SUCCESS",json.dumps(report,sort_keys=True),flush=True)

if __name__ == "__main__":
    main()
