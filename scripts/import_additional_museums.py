#!/usr/bin/env python3
"""Add truly new museum institutions through official Smithsonian Open Access.

Datasets are per-owning-museum EDAN JSONL shards. Both metadata and the
individual *media item* must explicitly be CC0. Other than compact metadata,
nothing is downloaded, copied to the app, or sent to third-party servers.
The 1950+ period is prioritized but historic public-domain museum art can be
present in the museum section. An uncertain/undated work is never assigned a
fabricated year. This importer does not mutate the existing 4,499 + modern
Commons catalog, or user-owned data. 
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlparse, urlunparse, urlencode, parse_qsl
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets/museums"
DATA_FILE = OUT / "catalog_new_museums.json"
REPORT_FILE = OUT / "new_museums_report.json"
SOURCE_BASE = "https://smithsonian-open-access.s3-us-west-2.amazonaws.com/metadata/edan"
RIGHTS_URL = "https://www.si.edu/openaccess"
UNITS = {
    "chndm": "Cooper Hewitt, Smithsonian Design Museum",
    "hmsg": "Hirshhorn Museum and Sculpture Garden",
    "nmafa": "Smithsonian National Museum of African Art",
    "nmaahc": "Smithsonian National Museum of African American History and Culture",
}
# Small bounded shards, deterministic: full historical archive is much larger.
SHARDS = int(os.environ.get("ARTDRIFT_MUSEUM_SHARDS", "64"))
MAX_PER_MUSEUM = 250
MAX_RECORDS = MAX_PER_MUSEUM * len(UNITS)
MAX_DATA_BYTES = 1_750_000
YEAR = re.compile(r"(?<!\d)(?:1[0-9]{3}|20[0-9]{2})(?!\d)")
KINDS = (
    ("painting", ("painting","paintings","painted canvas","oil on canvas")),
    ("drawing", ("drawing","drawings","sketch")),
    ("print", ("print","prints","lithograph","etching","engraving","screenprint")),
    ("photograph", ("photograph","photography","photographic print")),
    ("sculpture", ("sculpture","sculptures","sculptural")),
    ("ceramic", ("ceramic","ceramics","pottery")),
    ("textile", ("textile","textiles","tapestry")),
    ("poster", ("poster","posters")),
    ("collage", ("collage",)),
    ("graphic design", ("graphic design","graphic arts")),
    ("design", ("design object","design work","industrial design")),
    ("mixed media", ("mixed media",)),
)
PROHIBITED = ("photocopy of", "reproduction", "replica", "postcard of")


def clean(value, cap=160):
    return value.strip()[:cap] if isinstance(value, str) else ""


def official_https(url, host):
    try:
        u = urlparse(url)
        return (u.scheme == "https" and u.hostname == host
                and not u.username and not u.password and u.port in (None,443))
    except (ValueError,TypeError):
        return False


def values(freetext, field):
    if not isinstance(freetext,dict):return []
    return [clean(row.get("content")) for row in (freetext.get(field) or [])
            if isinstance(row,dict) and clean(row.get("content"))]


def art_type(types):
    for raw in types:
        val=raw.lower()
        if any(w in val for w in PROHIBITED):
            continue
        for name, tokens in KINDS:
            if any(t in val for t in tokens):
                return name.title()
    return ""


def first_verified_year(date):
    matches=[int(v) for v in YEAR.findall(date)]
    if not matches or min(matches)<1000 or max(matches)>2026:
        return None
    return min(matches)


def stable_id(unit, native):
    # Match legacy importer stable_id("smithsonian",unit+":"+native):
    # legacy SHA256 first 12 hex digits % 850m + 1, source prefix 6e9.
    name=unit+":"+str(native)
    h=int(hashlib.sha256(name.encode("utf-8")).hexdigest()[:12],16)
    return 6_000_000_000 + h%850_000_000+1


def parse(unit, item):
    if unit not in UNITS or not isinstance(item,dict):return None
    content=item.get("content") or {}
    if not isinstance(content,dict):return None
    desc=content.get("descriptiveNonRepeating") or {}
    freetext=content.get("freetext") or {}
    if not isinstance(desc,dict) or not isinstance(freetext,dict):return None
    if (desc.get("metadata_usage") or {}).get("access") != "CC0":
        return None
    kind=art_type(values(freetext,"objectType"))
    if not kind:
        return None
    online=(desc.get("online_media") or {}).get("media") or []
    image_url=""
    for medium in online:
        if not isinstance(medium,dict) or (medium.get("usage") or {}).get("access")!="CC0":
            continue
        candidate=clean(medium.get("thumbnail") or medium.get("content"),1600)
        if not official_https(candidate,"ids.si.edu"):
            continue
        uri=urlparse(candidate)
        params=dict(parse_qsl(uri.query,keep_blank_values=True))
        params["max"]="320"
        image_url=urlunparse((uri.scheme,uri.netloc,uri.path,uri.params,
                             urlencode(params),uri.fragment))
        break
    if not image_url:
        return None
    title=clean((desc.get("title") or {}).get("content"),230)
    if not title:title=clean(item.get("title"),230)
    native=clean(desc.get("record_ID") or item.get("id"),230)
    if not title or not native:
        return None
    creator=next(iter(values(freetext,"name")),"")
    if not creator:
        creator=next(iter(values(freetext,"maker")),"")
    if not creator:
        creator=next(iter(values(freetext,"manufacturer")),"")
    date=next(iter(values(freetext,"date")),"")
    terms=values(freetext,"topic")
    detail=clean(desc.get("record_link"),750)
    if not official_https(detail,"www.si.edu"):
        detail=""
    record={
        "id":stable_id(unit,native),
        "museum_source":"smithsonian",
        "museum_native_id":unit+":"+native,
        "museum_name":UNITS[unit],
        "title":title,
        "artist_title":creator,
        "date_display":date,
        "image_id":"",
        "is_public_domain":True,
        "rights_license":"CC0",
        "rights_evidence_url":RIGHTS_URL,
        "artwork_type_title":kind,
        "medium_display":next(iter(values(freetext,"physicalDescription")),"")[:160],
        "credit_line":next(iter(values(freetext,"creditLine")),"")[:180],
        "remote_preview_url":image_url,
        "remote_museum_url":detail,
        "subject_terms":list(dict.fromkeys(terms))[:12],
        "source_unit_code":unit,
    }
    return record


def fetch_shard(unit,index):
    uri=f"{SOURCE_BASE}/{unit}/{index:02x}.txt"
    req=Request(uri,headers={"User-Agent":"ArtDrift-SourceOpenAccess/1.0",
                             "Accept":"text/plain"})
    with urlopen(req,timeout=20) as response:
        payload=response.read(2_750_001)
    if len(payload)>2_750_000:
        raise RuntimeError("Provider metadata shard exceeds bounded size")
    return payload


def load_existing(root=ROOT):
    identities=set()
    for file in (
        root/"assets/gallery/catalog.json",root/"assets/museums/catalog.json",
        root/"assets/museums/catalog_global.json",
        root/"assets/museums/catalog_modern_1950.json",
    ):
        if not file.is_file():continue
        for row in json.loads(file.read_text(encoding="utf-8")):
            if isinstance(row,dict) and isinstance(row.get("id"),int):
                identities.add((row.get("museum_source") or "aic",row["id"]))
    return identities


def import_all(fetch=fetch_shard, root=ROOT, shards=SHARDS):
    if not 1<=shards<=256:
        raise ValueError("Bad shard upper bound")
    existing=load_existing(root)
    per={}
    summary={}
    for unit in UNITS:
        records={}
        errors=0
        loaded=0
        inspected=0
        rights_held=0
        for shard in range(shards):
            try:
                payload=fetch(unit,shard)
                loaded+=1
            except Exception:
                errors+=1
                continue
            for line in payload.splitlines():
                if not line.strip():continue
                inspected+=1
                try: source=json.loads(line)
                except (ValueError,TypeError):continue
                rec=parse(unit,source)
                if rec is None:
                    rights_held+=1
                    continue
                k=("smithsonian",rec["id"])
                if k in existing:
                    continue
                records.setdefault(rec["id"],rec)
            # No silent selection by title/popularity. Deterministic metadata.
            if shard and shard%16==0:
                print("MUSEUM_SHARD_PROGRESS",unit,shard,len(records),flush=True)
        verified=list(records.values())
        verified.sort(key=lambda r: (
            0 if first_verified_year(r["date_display"]) and
                 first_verified_year(r["date_display"]) >= 1950 else 1,
            r["id"],
        ))
        per[unit]=verified[:MAX_PER_MUSEUM]
        summary[unit]={
            "name":UNITS[unit],"inspected_records":inspected,
            "shards_read":loaded,"shards_held":errors,
            "source_qualified":len(verified),
            "retained":len(per[unit]),
            "post_1950_retained":sum(
                first_verified_year(a["date_display"]) is not None and
                first_verified_year(a["date_display"])>=1950
                for a in per[unit]),
            "art_types":dict(sorted(Counter(x["artwork_type_title"]
                for x in per[unit]).items())),
        }
        print("MUSEUM_READY",unit,json.dumps(summary[unit]),flush=True)

    combined=[]
    for offset in range(max((len(v) for v in per.values()),default=0)):
        for unit in UNITS:
            if offset<len(per[unit]):
                combined.append(per[unit][offset])
    if not combined:
        raise RuntimeError("NO_NEW_INSTITUTION_SOURCE_RIGHTS: original catalog untouched")
    if len(set(x["id"] for x in combined))!=len(combined):
        raise RuntimeError("Museum catalog stable identity collision")
    encoded=(json.dumps(combined,ensure_ascii=False,separators=(",",":"))+"\n").encode()
    if len(encoded)>MAX_DATA_BYTES:
        raise RuntimeError("New museum metadata budget exceeded")

    report={
        "schema_version":1,
        "status":"SOURCE_VERIFIED_CANDIDATES_DELIVERY_AND_RIGHTS_REVIEW_PENDING",
        "source":"Smithsonian Open Access official EDAN dataset",
        "source_url":"https://www.si.edu/openaccess",
        "museums_added":sum(bool(x) for x in per.values()),
        "museum_institutions":{u:summary[u] for u in UNITS},
        "record_count":len(combined),
        "post_1950_records":sum(
            first_verified_year(r["date_display"]) is not None and
            first_verified_year(r["date_display"])>=1950
            for r in combined),
        "bytes":len(encoded),"images_packaged":0,
        "rights_rule":"EDAN descriptiveNonRepeating.metadata_usage AND per-media usage must both equal CC0",
        "source_url_host_allowlist":["ids.si.edu"],
        "original_records_modified":0,
        "device_image_delivery":"NOT_VERIFIED",
        "commercial_rights_review":"PENDING",
    }
    output=root/"assets/museums"
    output.mkdir(parents=True,exist_ok=True)
    (output/DATA_FILE.name).write_bytes(encoded)
    (output/REPORT_FILE.name).write_text(json.dumps(report,indent=2,
        ensure_ascii=False)+"\n",encoding="utf-8")
    return report


if __name__=="__main__":
    print("ARTDRIFT_NEW_MUSEUMS",json.dumps(import_all(),ensure_ascii=False))
