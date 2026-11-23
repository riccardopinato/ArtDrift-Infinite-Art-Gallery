#!/usr/bin/env python3
"""Wikimedia Commons 1950+ self-licensed paintings. Candidate rights review only.

Never confuse Creative Commons image metadata with public-domain artwork.
Admit only explicit commercial CC terms, original own-work declaration, and
matching creator/uploader. All records keep source/author/license proof.
"""
from __future__ import annotations

import html
import json
import re
import time
import unicodedata
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets/museums"
API = "https://commons.wikimedia.org/w/api.php"
LICENSES = {
    "CC0": "https://creativecommons.org/publicdomain/zero/1.0/",
    "CC BY 3.0": "https://creativecommons.org/licenses/by/3.0/",
    "CC BY 4.0": "https://creativecommons.org/licenses/by/4.0/",
    "CC BY-SA 3.0": "https://creativecommons.org/licenses/by-sa/3.0/",
    "CC BY-SA 4.0": "https://creativecommons.org/licenses/by-sa/4.0/",
}
OWN = ("own work", "own artwork", "my work", "self-made", "eigenes werk",
       "eigene arbeit", "obra propia", "travail personnel", "trabalho próprio")
MAX_RECORDS = 320
YEARS = (1950, 1960, 1970, 1980, 1990, 2000, 2010, 2020, 2023, 2024, 2025, 2026)


def clean(x):
    return " ".join(re.sub(r"<[^>]*>", " ", html.unescape(str(x))).split())


def norm(x):
    s = unicodedata.normalize("NFKD", x).encode("ascii", "ignore").decode().lower()
    return re.sub("[^a-z0-9]+", "", s)


def official(url, hosts):
    try:
        u=urlparse(url)
        return u.scheme=="https" and u.hostname in hosts and not u.username \
            and not u.password and u.port in (None, 443)
    except (ValueError, TypeError):
        return False


def parse(page, year):
    if not isinstance(page, dict) or not 1950<=year<=2026:
        return None
    pid=page.get("pageid")
    if type(pid) is not int or pid<1 or not str(page.get("title","")).startswith("File:"):
        return None
    images=page.get("imageinfo") or []
    if not images or not isinstance(images[0], dict):
        return None
    img=images[0]
    if img.get("mime") not in ("image/jpeg","image/png","image/webp"):
        return None
    thumb=img.get("thumburl","")
    details=img.get("descriptionurl","")
    if not official(thumb, {"upload.wikimedia.org"}) or \
       not official(details, {"commons.wikimedia.org"}):
        return None
    meta=img.get("extmetadata") or {}
    def field(key):
        item=meta.get(key) or {}
        return clean(item.get("value") or "") if isinstance(item,dict) else ""
    license_name=field("LicenseShortName")
    canonical=LICENSES.get(license_name)
    given=field("LicenseUrl").replace("http://creativecommons.org/",
        "https://creativecommons.org/").rstrip("/")
    if canonical is None or not official(given, {"creativecommons.org"}) or \
       not given.startswith(canonical.rstrip("/")):
        return None
    creator=field("Artist")[:190]
    uploader=str(img.get("user") or "")[:190]
    credit=field("Credit")
    if len(norm(uploader))<4 or norm(uploader) not in norm(creator) or \
       not any(word in credit.lower() for word in OWN):
        return None
    title=field("ObjectName") or str(page["title"])[5:]
    title=re.sub(r"\.(?:jpe?g|png|webp)$","",title,flags=re.IGNORECASE)[:230].strip()
    if len(title)<3:
        return None
    return {
        "id": 10_000_000_000 + pid,
        "museum_source":"commons", "museum_native_id":str(pid),
        "museum_name":"Wikimedia Commons · Artist uploads",
        "title":title, "artist_title":creator,
        "date_display":str(year), "creation_year_verified":year,
        "artwork_type_title":"Painting", "image_id":"",
        "is_public_domain":license_name=="CC0",
        "rights_license":license_name,
        "rights_license_url":canonical,
        "rights_evidence_url":details,
        "remote_preview_url":thumb, "remote_museum_url":details,
        "credit_line":(creator+" · "+license_name)[:180],
        "medium_display":"Painting",
        "subject_terms":["modern painting","contemporary art",str(year)],
        "provenance":"Commons year category, self-owned original, matching uploader",
    }


def fetch_year(year):
    continuation=None
    accepted=[]
    inspected=0
    for page in range(1):
        params={"action":"query","format":"json","formatversion":"2",
            "generator":"categorymembers","gcmtitle":f"Category:{year} paintings",
            "gcmtype":"file","gcmlimit":"80","prop":"imageinfo",
            "iiprop":"url|extmetadata|mime|size|user",
            "iiurlwidth":"700"}
        if continuation:
            params["gcmcontinue"]=continuation
        request=Request(API+"?"+urlencode(params),headers={
            "Accept":"application/json",
            "User-Agent":"ArtDrift-OpenArt/0.3 (CC0/CC BY terms and credits)"})
        response=None
        for attempt in range(3):
            try:
                with urlopen(request, timeout=30) as r:
                    payload=r.read(2_800_001)
                if len(payload)>2_800_000:
                    raise ValueError("Commons API payload too large")
                response=json.loads(payload)
                break
            except (URLError, HTTPError, TimeoutError):
                if attempt==2: raise
                time.sleep(1.5*(attempt+1))
        if not isinstance(response,dict) or "error" in response:
            raise RuntimeError(f"Commons query error for {year}")
        pages=(response.get("query") or {}).get("pages") or []
        inspected+=len(pages)
        for item in pages:
            value=parse(item,year)
            if value: accepted.append(value)
        continuation=(response.get("continue") or {}).get("gcmcontinue")
        if not continuation: break
        time.sleep(.2)
    return year,accepted,inspected


def generate(fetch=fetch_year, output=OUT):
    rows={}
    inspected=0
    years_completed=0
    failures=[]
    with ThreadPoolExecutor(max_workers=1) as pool:
        pending={pool.submit(fetch,year):year for year in YEARS}
        for future in as_completed(pending):
            try:
                year,found,count=future.result()
                years_completed+=1
                inspected+=count
                for item in found:
                    rows.setdefault(item["id"], item)
            except Exception as e:
                failures.append(str(pending[future])+":"+type(e).__name__)
    if failures:
        raise RuntimeError("COMMONS_YEAR_COVERAGE_PARTIAL "+",".join(failures[:12]))
    decades=defaultdict(list)
    for item in rows.values():
        decades[(item["creation_year_verified"]//10)*10].append(item)
    for values in decades.values():
        values.sort(key=lambda r:(r["creation_year_verified"],r["id"]))
    result=[]
    for i in range(max((len(x) for x in decades.values()),default=0)):
        for decade in sorted(decades):
            if i<len(decades[decade]):
                result.append(decades[decade][i])
                if len(result)>=MAX_RECORDS:break
        if len(result)>=MAX_RECORDS:break
    if not result:
        raise RuntimeError("NO_SELF_LICENSED_MODERN_PAINTINGS: no catalog replacement")
    payload=(json.dumps(result,ensure_ascii=False,separators=(",",":"))+"\n").encode()
    if len(payload)>1_250_000:
        raise RuntimeError("Modern Commons asset exceeds 1.25 MB")
    assert len(set(r["id"] for r in result))==len(result)
    output.mkdir(parents=True,exist_ok=True)
    (output/"catalog_modern_1950.json").write_bytes(payload)
    report={
        "schema_version":1,
        "status":"RIGHTS_AND_IMAGE_DELIVERY_REVIEW_PENDING",
        "provider":"Wikimedia Commons MediaWiki API",
        "years":years_completed,"years_sampled":list(YEARS),"files_inspected":inspected,
        "admitted_records":len(result),
        "license_distribution":dict(sorted(Counter(r["rights_license"]
          for r in result).items())),
        "by_decade":dict(sorted((str(k),len(v)) for k,v in decades.items())),
        "data_bytes":len(payload),"images_bundled":0,
        "rights_basis":"own-work and artist/uploader match + explicit CC license",
        "underlying_rights_review":"PENDING",
        "image_delivery_review":"PENDING",
        "production_release":"NOT_AUTHORIZED"
    }
    (output/"modern_1950_report.json").write_text(json.dumps(
        report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return report


if __name__=="__main__":
    print("COMMONS_MODERN_CATALOG",json.dumps(generate(),ensure_ascii=False))
