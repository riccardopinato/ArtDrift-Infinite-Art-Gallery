#!/usr/bin/env python3
"""Targeted public-museum research. NEVER publishes works to runtime automatically."""
import argparse
import hashlib
import json
import re
import unicodedata
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

ROOT=Path(__file__).resolve().parents[1]
WORKS=ROOT/"research/modern_masters_53_20261125.json"
ARTISTS=ROOT/"research/modern_artists_109_20261125.json"
BASE="https://api.smk.dk/api/v1/art/"
SEARCH=BASE+"search/"
HOSTS={"api.smk.dk"}
IMG_HOSTS={"iip.smk.dk","iip-thumb.smk.dk"}
FREE=("creativecommons.org/publicdomain/mark/","creativecommons.org/publicdomain/zero/")
BLOCKED={"LICENZA_RICHIESTA__NON_USARE","NO_IMAGE__NON_IMPORTARE"}

def norm(x):
    return re.sub(r"[^a-z0-9]+"," ",unicodedata.normalize("NFKD",str(x))
                  .encode("ascii","ignore").decode().lower()).strip()

def safe(url,hosts):
    if not isinstance(url,str):return False
    try:
        u=urlsplit(url)
        return (u.scheme=="https" and u.hostname in hosts and not u.username
                and not u.password and u.port in (None,443))
    except ValueError:return False

def get_json(url):
    if not safe(url,HOSTS):raise ValueError("API_HOST")
    request=Request(url,headers={"Accept":"application/json","User-Agent":"ArtDrift-Research/1.0"})
    with urlopen(request,timeout=20) as response:
        if not safe(response.url,HOSTS):raise ValueError("API_REDIRECT")
        content=response.read(2_000_001)
    if len(content)>2_000_000:raise ValueError("OVERSIZED_JSON")
    data=json.loads(content)
    if not isinstance(data,dict):raise ValueError("MALFORMED_JSON")
    return data

def get_image_sha(url):
    if not safe(url,IMG_HOSTS):raise ValueError("IMAGE_HOST")
    with urlopen(Request(url,headers={"Accept":"image/jpeg,image/png,image/webp",
                      "User-Agent":"ArtDrift-Research/1.0"}),timeout=18) as response:
        if not safe(response.url,IMG_HOSTS):raise ValueError("IMAGE_REDIRECT")
        if not response.headers.get("Content-Type","").startswith("image/"):
            raise ValueError("INVALID_IMAGE_MIME")
        body=response.read(3_000_001)
    if not 500<=len(body)<=3_000_000:raise ValueError("INVALID_IMAGE_LENGTH")
    if not (body.startswith(b"\xff\xd8\xff") or body.startswith(b"\x89PNG") or
            (body[:4]==b"RIFF" and body[8:12]==b"WEBP")):
        raise ValueError("INVALID_IMAGE_SIGNATURE")
    return hashlib.sha256(body).hexdigest()

def rows(data):
    for name in ("items","data","results"):
        value=data.get(name)
        if isinstance(value,list):return [v for v in value if isinstance(v,dict)]
        if isinstance(value,dict):return [value]
    return [data] if "object_number" in data else []

def inventory():
    works=json.loads(WORKS.read_text(encoding="utf-8"))["works"]
    rights=Counter(w["rights_inventory_status"] for w in works)
    expected={"MUSEO_DICHIARA_FREE_TO_USE__PRE_IMPORT":32,
              "SCHEDA_INDIVIDUATA__LICENZA_IMMAGINE_DA_VERIFICARE":16,
              "NO_IMAGE__NON_IMPORTARE":1,"LICENZA_RICHIESTA__NON_USARE":4}
    if len(works)!=53 or set(w["research_id"] for w in works)!=set(range(53)) or dict(rights)!=expected:
        raise ValueError("SOURCE_INVENTORY_DRIFT")
    return works

def existing_ids():
    result=set()
    for name in ("assets/gallery/catalog.json","assets/museums/catalog.json",
                 "assets/museums/catalog_global.json"):
        path=ROOT/name
        if not path.is_file():continue
        for row in json.loads(path.read_text(encoding="utf-8")):
            native=row.get("museum_native_id") or row.get("id")
            if native:result.add((row.get("museum_source","aic"),str(native).casefold()))
    return result

def validate_smk(item,expected,image_probe=get_image_sha):
    native=expected["native_id"]
    if str(item.get("object_number","")).casefold()!=native.casefold():
        raise ValueError("NATIVE_ID_MISMATCH")
    if item.get("public_domain") is not True or not item.get("has_image"):
        raise ValueError("UNDERLYING_PUBLIC_DOMAIN_UNPROVEN")
    rights=item.get("rights") or ""
    if not isinstance(rights,str) or not any(v in rights.lower() for v in FREE):
        raise ValueError("IMAGE_RIGHTS_UNPROVEN")
    objects=" ".join(str(x.get("name","")) for x in item.get("object_names") or []
                     if isinstance(x,dict)).lower()
    kind="Painting" if "painting" in objects or "maleri" in objects else (
        "Collage" if "collage" in objects else "Other")
    if kind=="Other":raise ValueError("ARTWORK_KIND_UNSUPPORTED")
    authors=item.get("artist") or []
    artist=authors[0] if authors and isinstance(authors[0],str) else ""
    surname=norm(expected["artist"]).split()[-1]
    if surname not in norm(artist):raise ValueError("ARTIST_MISMATCH")
    iiif=str(item.get("image_iiif_id") or "").rstrip("/")
    if not safe(iiif,{"iip.smk.dk"}):raise ValueError("NOT_OFFICIAL_IIIF")
    preview=iiif+"/full/300,/0/default.jpg"
    checksum=image_probe(preview)
    titles=[v.get("title") for v in item.get("titles") or []
            if isinstance(v,dict) and isinstance(v.get("title"),str)]
    ident=int(hashlib.sha256(native.encode()).hexdigest()[:12],16)%850_000_000+1
    return {"research_id":expected["research_id"],"museum_source":"smk",
            "museum_native_id":native,"id":7_000_000_000+ident,
            "artist_title":artist,"title":next((t.strip() for t in titles if t.strip()),expected["title"]),
            "artwork_type_title":kind,"rights_evidence_url":rights,
            "remote_museum_url":"https://open.smk.dk/en/artwork/image/"+native,
            "remote_preview_url":preview,"remote_full_url":iiif+"/full/1000,/0/default.jpg",
            "image_sha256":checksum,"image_bytes_verified":True,
            "worldwide_commercial_clearance":False,
            "publication_status":"HOLD_TERRITORY_AND_CURATORIAL","runtime_visible":False}

def lookup_smk(record):
    native=record["native_id"]
    try:
        candidates=rows(get_json(BASE+"?"+urlencode({"object_number":native})))
    except (OSError,ValueError,TimeoutError):
        candidates=[]
    candidates=[v for v in candidates if str(v.get("object_number","")).casefold()==native.casefold()]
    if not candidates:
        args=urlencode({"keys":native,"filters":"[public_domain:true],[has_image:true]","rows":50})
        candidates=[v for v in rows(get_json(SEARCH+"?"+args))
                    if str(v.get("object_number","")).casefold()==native.casefold()]
    if not candidates:raise ValueError("EXACT_ITEM_NOT_FOUND")
    return validate_smk(candidates[0],record)

def target(max_records,workers):
    works=[w for w in inventory() if w["source"]=="smk" and
           w["rights_inventory_status"] not in BLOCKED and
           w["native_id"] not in ("UNVERIFIED","NON_VERIFIED")]
    known=existing_ids()
    accepted=[];holds=[]
    def one(w):
        try:return w,lookup_smk(w),None
        except Exception as ex:return w,None,str(ex)[:180]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for future in as_completed([pool.submit(one,w) for w in works[:max_records]]):
            w,ok,error=future.result()
            if error:holds.append({"research_id":w["research_id"],"native_id":w["native_id"],"reason":error})
            else:
                ok["already_in_main_catalog"]=("smk",ok["museum_native_id"].casefold()) in known
                accepted.append(ok)
    accepted.sort(key=lambda w:w["research_id"])
    holds.sort(key=lambda w:w["research_id"])
    return {"mode":"target","reviewed":len(accepted)+len(holds),
            "media_verified":len(accepted),
            "already_in_main_catalog":sum(x["already_in_main_catalog"] for x in accepted),
            "blocked_or_no_image_in_inventory":5,
            "approved_for_worldwide":0,"integrated_into_runtime":0,
            "media_review_records":accepted,"holds":holds}

def discover(max_artists,max_records,workers):
    artists=json.loads(ARTISTS.read_text(encoding="utf-8"))["artists"]
    artists=[a for a in artists if a["eu_status"]=="PRESUMIBILMENTE_PD"
             and a["color_priority"]=="ALTA"][:max_artists]
    seen=existing_ids()|{("smk",w["native_id"].casefold())
                          for w in inventory() if w["source"]=="smk"}
    found={};errors=[]
    def one(artist):
        url=SEARCH+"?"+urlencode({"keys":artist["artist"],
               "filters":"[public_domain:true],[has_image:true]","rows":100})
        try:return artist,rows(get_json(url)),None
        except Exception as ex:return artist,[],str(ex)[:180]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for future in as_completed([pool.submit(one,a) for a in artists]):
            a,data,error=future.result()
            if error:
                errors.append({"artist":a["artist"],"reason":error})
                continue
            surname=norm(a["artist"]).split()[-1]
            for obj in data:
                native=str(obj.get("object_number") or "")
                key=("smk",native.casefold())
                if not native or key in seen or key in found:continue
                author=obj.get("artist") or []
                author=author[0] if author and isinstance(author[0],str) else ""
                names=" ".join(str(x.get("name","")) for x in obj.get("object_names") or []
                               if isinstance(x,dict)).lower()
                rights=str(obj.get("rights") or "").lower()
                image=str(obj.get("image_iiif_id") or "").rstrip("/")
                if not (surname in norm(author) and obj.get("public_domain") is True and
                        obj.get("has_image") and any(x in names for x in ("painting","maleri")) and
                        any(x in rights for x in FREE) and safe(image,{"iip.smk.dk"})):
                    continue
                found[key]={"museum_source":"smk","museum_native_id":native,
                            "artist":author,"source_url":"https://open.smk.dk/en/artwork/image/"+native,
                            "rights_evidence_url":obj.get("rights"),
                            "remote_preview_url":image+"/full/300,/0/default.jpg",
                            "publication_status":"HOLD_MEDIA_AND_TERRITORY",
                            "runtime_visible":False}
    results=[found[k] for k in sorted(found)][:max_records]
    return {"mode":"discover","artist_queries":len(artists),
            "new_candidate_ids":len(results),"approved_for_worldwide":0,
            "integrated_into_runtime":0,"query_errors":sorted(errors,key=lambda x:x["artist"]),
            "candidates":results}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--mode",choices=("inventory","target","discover"),default="inventory")
    p.add_argument("--max-records",type=int,default=48)
    p.add_argument("--max-artists",type=int,default=30)
    p.add_argument("--workers",type=int,default=3)
    p.add_argument("--output-dir",type=Path,default=ROOT/".artdrift_research/modern_masters")
    a=p.parse_args()
    if not 1<=a.max_records<=100 or not 1<=a.max_artists<=109 or not 1<=a.workers<=4:
        p.error("unsafe limits")
    if a.mode=="inventory":
        result={"mode":"inventory","total":len(inventory()),
                "rights":dict(sorted(Counter(x["rights_inventory_status"] for x in inventory()).items())),
                "integrated_into_runtime":0}
    elif a.mode=="target":result=target(a.max_records,a.workers)
    else:result=discover(a.max_artists,a.max_records,a.workers)
    a.output_dir.mkdir(parents=True,exist_ok=True)
    (a.output_dir/(a.mode+"_report.json")).write_text(
        json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items()
                      if k not in ("media_review_records","holds","candidates","query_errors")},
                     ensure_ascii=False,sort_keys=True))

if __name__=="__main__":main()
