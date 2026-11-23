#!/usr/bin/env python3
"""GLOBAL ARTDRIFT OPEN ACCESS: source-verified metadata-only second tier.

Import source records, never a scraping proxy. Keep 457 original offline WebPs;
remote tier stores a few MB of metadata only. Full/medium images are fetched
by Flutter only when visible. Idempotent, source-key unique, bounded by budget.
Never invent dates/artists or reuse a catalog's textual narrative descriptions.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlencode, urlparse, quote
from urllib.request import urlopen, Request
from import_museum_paintings import (
    ROOT, _json, _fetch, _url_ok, _int, _record, _value,
    _rijks_uri, _first_link, _edm_rights, _rijks_artist_and_date,
    _rijks_first_name, _csv_stream
)

OUT = ROOT / "assets" / "museums"
SOURCE = OUT / "catalog.json"
DEST = OUT / "catalog_global.json"
REPORT = OUT / "global_report.json"
MAX_RECORDS = int(os.environ.get("ARTDRIFT_GLOBAL_LIMIT", "5300"))
CAP = {"aic":700, "cleveland":950, "nga":750, "met":330,
       "rijks":240, "smithsonian_saam":350, "smithsonian_npg":350,
       "smithsonian_fsg":350, "smk":500, "walters":100, "mia":250}
# JSON must be source metadata, not a huge gallery preload.
MAX_CATALOG_BYTES = 7_500_000
HEADERS = {"User-Agent":"ArtDrift-OpenAccess-Catalog/1.0 research personal use",
           "Accept":"application/json,*/*"}
PREFIX = {"aic":0,"met":10_000_000,"cleveland":20_000_000,
          "rijks":3_000_000_000,"nga":4_000_000_000,
          "smithsonian":6_000_000_000,"smk":7_000_000_000,
          "mia":8_000_000_000,"walters":9_000_000_000}
HOSTS = {
    "aic":{"www.artic.edu"},"met":{"images.metmuseum.org"},
    "cleveland":{"openaccess-cdn.clevelandart.org"},
    "nga":{"api.nga.gov","media.nga.gov"},
    "rijks":{"iiif.micr.io"},
    "smithsonian":{"ids.si.edu"},
    "smk":{"iip.smk.dk","iip-thumb.smk.dk"},
    "mia":{"api.artsmia.org"},
    "walters":{"images.thewalters.org","art.thewalters.org","thewalters.org"},
}
MUSEUMS = {
    "aic":"Art Institute of Chicago","met":"The Metropolitan Museum of Art",
    "cleveland":"Cleveland Museum of Art","nga":"National Gallery of Art, Washington",
    "rijks":"Rijksmuseum","smithsonian":"Smithsonian American Art Museum",
    "smk":"SMK – National Gallery of Denmark","mia":"Minneapolis Institute of Art",
    "walters":"The Walters Art Museum",
}
SMITHSONIAN_UNITS = {
  "saam":"Smithsonian American Art Museum",
  "npg":"Smithsonian National Portrait Gallery",
  "fsg":"Smithsonian National Museum of Asian Art",
}

def safe(url,source):
    try:
        u=urlparse(url)
        return u.scheme=="https" and not u.username and not u.password and u.hostname in HOSTS.get(source,set()) and u.port in (None,443)
    except (TypeError,ValueError): return False

def val(x):
    return (x or "").strip() if isinstance(x,str) else ""

def stable_id(source, native):
    try:
        number=int(native)
        if number<1 or number>=950_000_000:raise ValueError()
    except (TypeError,ValueError):
        number=int(hashlib.sha256(str(native).encode("utf-8")).hexdigest()[:12],16)%850_000_000+1
    return PREFIX[source]+number

def make(source,native,title,image,*,artist="",date="",medium="",dimensions="",
         origin="",credit="",rights="",evidence="",detail="",full="",
         tags=(),museum="",license_field="",record_revision=""):
    if not val(title) or not safe(image,source) or not rights or not safe_evidence(evidence):
        return None
    uid=stable_id(source,native)
    if full and not safe(full,source):full=""
    return {
        "id":uid,"museum_native_id":str(native),
        "museum_source":source,"museum_name":museum or MUSEUMS[source],
        "title":val(title)[:230],"artist_title":val(artist)[:190],
        "date_display":val(date)[:80],
        "image_id":"",
        "is_public_domain":True,"rights_license":rights,
        "rights_evidence_url":evidence,
        "artwork_type_title":"Painting",
        "medium_display":val(medium)[:160],
        "dimensions_display":val(dimensions)[:125],
        "place_of_origin":val(origin)[:125],
        "credit_line":val(credit)[:180],
        "remote_preview_url":image,
        "remote_full_url":full,"remote_museum_url":detail,
        "subject_terms":list(dict.fromkeys(val(x)[:70] for x in tags if val(x)))[:12],
        "content_revision":record_revision or "2026-11-21",
    }

def safe_evidence(url):
    try:
        u=urlparse(url)
        return u.scheme=="https" and not u.username and not u.password and u.port in (None,443)
    except (TypeError,ValueError):return False

def accept(rows, source, limit):
    items={}
    for r in rows:
        if not r:continue
        if r["museum_source"]!=source or not safe(r.get("remote_preview_url",""),source):continue
        items.setdefault(r["id"],r)
        if len(items)>=limit:break
    return list(items.values())

def aic():
    print("AIC public-domain paintings",flush=True)
    topics=("landscape","flower","portrait","still life","sea",
        "impressionism","Japan","painting","monet","garden",
        "renaissance","river","french","chicago","american","religious")
    result={}
    fields="id,title,artist_title,date_display,image_id,is_public_domain,artwork_type_title,medium_display,place_of_origin,credit_line,thumbnail"
    for term in topics:
        if len(result)>=CAP["aic"]:break
        for page in (1,2):
            if len(result)>=CAP["aic"]:break
            try:
                d=_json("https://api.artic.edu/api/v1/artworks/search?"+
                  urlencode({"q":term,"query[term][is_public_domain]":"true",
                    "fields":fields,"limit":100,"page":page}),size=1_600_000)
                for x in d.get("data",[]):
                    if not isinstance(x,dict) or x.get("is_public_domain") is not True or x.get("artwork_type_title","").lower()!="painting":continue
                    iid=val(x.get("image_id",""))
                    if not re.fullmatch("[0-9a-fA-F-]{16,64}",iid):continue
                    native=x.get("id")
                    if not _int(native):continue
                    remote=f"https://www.artic.edu/iiif/2/{iid}/full/220,/0/default.jpg"
                    detail=f"https://www.artic.edu/artworks/{native}"
                    record=make("aic",native,x.get("title",""),remote,
                        artist=x.get("artist_title",""),date=x.get("date_display",""),
                        medium=x.get("medium_display",""),origin=x.get("place_of_origin",""),
                        credit=x.get("credit_line",""),rights="Public Domain",
                        evidence=detail,detail=detail,
                        full=f"https://www.artic.edu/iiif/2/{iid}/full/843,/0/default.jpg",
                        tags=[term])
                    if record:record["image_id"]=iid;result[record["id"]]=record
            except Exception as e:print("AIC_PAGE_HELD",term,page,str(e)[:85],flush=True)
            time.sleep(.15)
    return list(result.values())[:CAP["aic"]]

def cleveland():
    print("CMA CC0 painting API",flush=True)
    out={}
    # A few bounded independent paging windows.
    for skip in (0,300,600,900,1200):
        if len(out)>=CAP["cleveland"]:break
        try:
            d=_json("https://openaccess-api.clevelandart.org/api/artworks/?"+
                urlencode({"q":"painting","cc0":"1","has_image":"1",
                           "limit":300,"skip":skip}),size=9_000_000)
            for x in d.get("data",[]):
                if not isinstance(x,dict) or val(x.get("share_license_status")).upper()!="CC0" or "paint" not in val(x.get("type")).lower():continue
                img=(x.get("images") or {}).get("web") or {}
                url=val(img.get("url"))
                if not safe(url,"cleveland"):continue
                cr=x.get("creators") or []
                artist=next((val(z.get("description")) for z in cr if isinstance(z,dict) and val(z.get("description"))),"")
                terms=[z if isinstance(z,str) else val(z.get("name")) for z in x.get("keywords") or [] if isinstance(z,(dict,str))]
                rec=make("cleveland",x.get("id"),x.get("title"),url,
                    artist=artist,date=x.get("creation_date"),
                    medium=x.get("technique"),credit=x.get("creditline"),
                    dimensions=str(x.get("measurements") or "")[:120],
                    origin=x.get("culture"),rights="CC0",
                    evidence="https://www.clevelandart.org/open-access",
                    detail=x.get("url",""),tags=terms)
                if rec:out[rec["id"]]=rec
        except Exception as e:print("CMA_PAGE_HELD",skip,str(e)[:90],flush=True)
        time.sleep(.35)
    return list(out.values())[:CAP["cleveland"]]

def nga():
    print("NGA official public-domain two-CSV stream",flush=True)
    base="https://raw.githubusercontent.com/NationalGalleryOfArt/opendata/main/data/"
    imgs={}
    try:
        stream,rows=_csv_stream(base+"published_images.csv")
        try:
            for row in rows:
                if val(row.get("openaccess")).lower() not in ("1","true"):continue
                ident=_int(row.get("depictstmsobjectid"))
                if ident and ident not in imgs:
                    url=val(row.get("iiifurl")).removesuffix("/info.json").rstrip("/")
                    if safe(url,"nga"):imgs[ident]=url
        finally:stream.close()
    except Exception as e:
        print("NGA_IMAGES_FAILED",str(e)[:110],flush=True);return []
    out={}
    try:
        stream,rows=_csv_stream(base+"objects.csv")
        try:
            for row in rows:
                native=_int(row.get("objectid"))
                if not native or native not in imgs:continue
                typ=val(row.get("classification"))+" "+val(row.get("subclassification"))
                if "paint" not in typ.lower():continue
                baseurl=imgs[native]
                rec=make("nga",native,row.get("title"),
                    baseurl+"/full/220,/0/default.jpg",
                    artist=row.get("attribution"),date=row.get("displaydate"),
                    medium=row.get("medium"),dimensions=row.get("dimensions"),
                    credit=row.get("creditline"),rights="Public Domain",
                    evidence="https://www.nga.gov/artworks/free-images-and-open-access",
                    detail=f"https://www.nga.gov/artworks/{native}",
                    full=baseurl+"/full/1000,/0/default.jpg")
                if rec:
                    # Balance chronological coverage: first N centuries only is not global.
                    out[rec["id"]]=rec
        finally:stream.close()
    except Exception as e:print("NGA_OBJECTS_HELD",str(e)[:110],flush=True)
    # Stable deterministic spread across entire objects.csv rather than oldest only.
    return sorted(out.values(),key=lambda r:hashlib.sha256(str(r["id"]).encode()).hexdigest())[:CAP["nga"]]

def met():
    print("Met v1.1 search + per-record public-domain paint classification",flush=True)
    seen=set()
    queries=(
      ("painting",11),("landscape",11),("portrait",11),("impressionism",11),
      ("oil painting",1),("painting",1),("Japanese painting",6),
      ("Chinese painting",6),("Islamic painting",14),("painting",21),
      ("watercolor",11),("flowers",11),("Rembrandt",11),
    )
    for term,dept in queries:
        try:
            p={"q":term,"hasImages":"true","limit":1000,"offset":0,"departmentId":dept}
            d=_json("https://collectionapi.metmuseum.org/public/collection/v1.1/search?"+urlencode(p),size=700000)
            for id in d.get("objectIDs") or []:
                if isinstance(id,int):seen.add(id)
        except Exception as e:print("MET_SEARCH_HELD",term,str(e)[:90],flush=True)
        if len(seen)>1800:break
        time.sleep(.25)
    def work(id):
        try:
            row=_json(f"https://collectionapi.metmuseum.org/public/collection/v1/objects/{id}",size=200000)
            if row.get("isPublicDomain") is not True:return None
            kind=(val(row.get("classification"))+" "+val(row.get("objectName"))).lower()
            if "paint" not in kind and "oil on canvas" not in val(row.get("medium")).lower():return None
            url=val(row.get("primaryImageSmall"))
            if not safe(url,"met"):return None
            terms=[val(x.get("term")) for x in row.get("tags") or [] if isinstance(x,dict)]
            return make("met",id,row.get("title"),url,
                artist=row.get("artistDisplayName"),date=row.get("objectDate"),
                medium=row.get("medium"),dimensions=row.get("dimensions"),
                origin=row.get("culture"),credit=row.get("creditLine"),
                rights="CC0",evidence="https://www.metmuseum.org/hubs/open-access",
                detail=row.get("objectURL",""),tags=terms)
        except Exception:return None
    result={}
    ordered=sorted(seen,key=lambda v:hashlib.sha256(str(v).encode()).hexdigest())[:1400]
    # Bounded concurrency and finite per-provider API volume.
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures=[pool.submit(work,id) for id in ordered]
        for f in as_completed(futures):
            row=f.result()
            if row:result[row["id"]]=row
    return list(result.values())[:CAP["met"]]

def rijks():
    print("Rijks LinkedArt+RDF/EDM item-specific rights",flush=True)
    search="https://data.rijksmuseum.nl/search/collection?"+urlencode(
      {"type":"painting","imageAvailable":"true"})
    ids=[]
    visited=set()
    for page in range(19):
        if not search or search in visited:break
        visited.add(search)
        try:
            data=_json(search,size=240000)
            ids.extend(data.get("orderedItems") or [])
            nxt=data.get("next") or {}
            url=nxt.get("id") if isinstance(nxt,dict) else ""
            search=url if url.startswith("https://data.rijksmuseum.nl/search/collection?") else ""
        except Exception as e:
            print("RIJKS_PAGE_HELD",page,str(e)[:80],flush=True);break
        time.sleep(.2)
    def work(obj):
        try:
            url=_rijks_uri(obj.get("id")) if isinstance(obj,dict) else ""
            if not url:return None
            record=_json(url,size=1_000_000)
            rightsurl=url.replace("_profile=la-framed","_profile=edm")
            right=_edm_rights(rightsurl)
            if not right:return None
            vurl=_first_link(record,"shows")
            if not vurl:return None
            visual=_json(vurl,size=500000)
            durl=_first_link(visual,"digitally_shown_by")
            if not durl:return None
            image=_json(durl,size=500000)
            link=next((_value(x,"id") for x in image.get("access_point") or [] if isinstance(x,dict) and _value(x,"id").startswith("https://iiif.micr.io/")),"")
            mm=re.match(r"^https://iiif\.micr\.io/([A-Za-z0-9_-]+)/",link)
            if not mm:return None
            native=_int(urlparse(url).path.strip("/"))
            if not native:return None
            creator,date=_rijks_artist_and_date(record)
            ident=mm.group(1)
            return make("rijks",native,_rijks_first_name(record),
               f"https://iiif.micr.io/{ident}/full/220,/0/default.jpg",
               full=f"https://iiif.micr.io/{ident}/full/1000,/0/default.jpg",
               artist=creator,date=date,rights="Public Domain Mark"
                  if "mark" in right else "CC0",
               evidence=rightsurl,detail=f"https://data.rijksmuseum.nl/{native}")
        except Exception:return None
    result={}
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures=[pool.submit(work,unit) for unit in ids[:480]]
        for f in as_completed(futures):
            item=f.result()
            if item:result[item["id"]]=item
    return list(result.values())[:CAP["rijks"]]

def smk():
    print("SMK Copenhagen per-artwork public_domain and rights",flush=True)
    rows={}
    qs=("*","maleri","landskab","portræt","paintings","olie på lærred",
        "landscape","portrait","flowers","Hammershøi","Krøyer","Eckersberg")
    for q in qs:
        if len(rows)>=CAP["smk"]:break
        for offset in (0,100,200,300,400):
            try:
                uri="https://api.smk.dk/api/v1/art/search/?"+urlencode({
                  "keys":q,"filters":"[public_domain:true],[has_image:true]",
                  "offset":offset,"rows":100})
                data=_json(uri,size=3_000_000)
                for obj in data.get("items") or []:
                    if not isinstance(obj,dict) or obj.get("public_domain") is not True or not obj.get("has_image"):continue
                    typ=" ".join(val(it.get("name")) for it in obj.get("object_names") or [] if isinstance(it,dict)).lower()
                    dep=val(obj.get("responsible_department")).lower()
                    tech=" ".join(x for x in obj.get("techniques") or [] if isinstance(x,str)).lower()
                    if not any(a in typ for a in ("maleri","painting","oliemaleri")):
                        continue
                    rights=val(obj.get("rights"))
                    if not any(x in rights.lower() for x in ("creativecommons.org/publicdomain/mark/","creativecommons.org/publicdomain/zero/")):continue
                    img=val(obj.get("image_iiif_id"))
                    if not img.startswith("https://iip.smk.dk/iiif/"):continue
                    native=val(obj.get("object_number")) or obj.get("id")
                    if not native:continue
                    names=[val(x.get("title")) for x in obj.get("titles") or [] if isinstance(x,dict)]
                    title=next((x for x in names if x),"")
                    authors=obj.get("artist") or []
                    artist=authors[0] if authors and isinstance(authors[0],str) else ""
                    dates=obj.get("production_date") or []
                    date=val(dates[0].get("period")) if dates and isinstance(dates[0],dict) else ""
                    dimensions=[]
                    for it in obj.get("dimensions") or []:
                        if isinstance(it,dict) and it.get("value"):
                            dimensions.append(str(it["value"])+" "+val(it.get("unit")))
                    rec=make("smk",native,title,img+"/full/300,/0/default.jpg",
                        full=img+"/full/1000,/0/default.jpg",
                        artist=artist,date=date,medium=val((obj.get("techniques") or [""])[0]),
                        dimensions=" × ".join(dimensions[:2]),rights="Public Domain Mark",
                        evidence=rights,detail=obj.get("frontend_url",""),
                        tags=[q],museum=MUSEUMS["smk"])
                    if rec:rows[rec["id"]]=rec
            except Exception as e:
                print("SMK_PAGE_HELD",q,offset,str(e)[:90],flush=True)
            if len(rows)>=CAP["smk"]:break
            time.sleep(.1)
    return list(rows.values())[:CAP["smk"]]

def smithsonian_unit(unit,cap):
    print("Smithsonian S3 CC0 painting:",unit,flush=True)
    base=f"https://smithsonian-open-access.s3-us-west-2.amazonaws.com/metadata/edan/{unit}/"
    found={}
    def group(freetext,key):
        return [val(x.get("content")) for x in freetext.get(key) or [] if isinstance(x,dict)]
    # Staggered deterministic sharding rather than requiring complete 256 shards.
    shards=list(range(0,100))
    for i in shards:
        if len(found)>=cap:break
        try:
            block=_fetch(base+f"{i:02x}.txt",size=2_200_000)
            for line in block.splitlines():
                if not line.strip():continue
                try:row=json.loads(line)
                except Exception:continue
                content=row.get("content") or {}
                if not isinstance(content,dict):continue
                details=content.get("descriptiveNonRepeating") or {}
                textdata=content.get("freetext") or {}
                if not any("paint" in t.lower() for t in group(textdata,"objectType")):continue
                if (details.get("metadata_usage") or {}).get("access")!="CC0":continue
                imageurl=""
                for image in (details.get("online_media") or {}).get("media") or []:
                    if not isinstance(image,dict) or (image.get("usage") or {}).get("access")!="CC0":continue
                    url=val(image.get("thumbnail") or image.get("content"))
                    if safe(url,"smithsonian"):
                        # IDS max=320 limits bandwidth for infinite canvas.
                        from urllib.parse import parse_qsl,urlunparse
                        u=urlparse(url)
                        pairs=dict(parse_qsl(u.query));pairs["max"]="320"
                        imageurl=urlunparse((u.scheme,u.netloc,u.path,u.params,urlencode(pairs),u.fragment))
                        break
                if not imageurl:continue
                title=val((details.get("title") or {}).get("content")) or row.get("title")
                native=val(details.get("record_ID")) or row.get("id")
                rec=make("smithsonian",unit+":"+str(native),title,imageurl,
                    full=imageurl.replace("max=320","max=1000"),
                    artist=next(iter(group(textdata,"name")),""),
                    date=next(iter(group(textdata,"date")),""),
                    medium=next(iter(group(textdata,"physicalDescription")),""),
                    credit=next(iter(group(textdata,"creditLine")),""),
                    museum=SMITHSONIAN_UNITS[unit],rights="CC0",
                    evidence="https://www.si.edu/openaccess",
                    detail=details.get("record_link",""),
                    tags=group(textdata,"topic"))
                if rec:found[rec["id"]]=rec
        except Exception as e:
            if i<2:print("SMITHSONIAN_SHARD_HELD",unit,i,str(e)[:95],flush=True)
        if i%20==0:print("SI_STATUS",unit,i,len(found),flush=True)
    return list(found.values())[:cap]

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    prior=json.loads(SOURCE.read_text(encoding="utf-8"))
    pinned_keys={(v.get("museum_source","aic"),v.get("museum_native_id",str(v.get("id")))) for v in prior}
    # Built-in AIC is a separate catalog under assets/gallery, do not repeat.
    built=json.loads((ROOT/"assets/gallery/catalog.json").read_text(encoding="utf-8"))
    pinned_ids={("aic",str(v.get("id"))) for v in built}
    pinned_keys |= pinned_ids
    providers={
      "aic":aic,"cleveland":cleveland,"nga":nga,"met":met,
      "rijks":rijks,"smk":smk,
      "smithsonian_saam":lambda:smithsonian_unit("saam",CAP["smithsonian_saam"]),
      "smithsonian_npg":lambda:smithsonian_unit("npg",CAP["smithsonian_npg"]),
      "smithsonian_fsg":lambda:smithsonian_unit("fsg",CAP["smithsonian_fsg"]),
    }
    data={}
    def task(item):
        name,fn=item
        try:return name,fn()
        except Exception as e:
            print("PROVIDER_ERROR",name,type(e).__name__,str(e)[:170],flush=True)
            return name,[]
    # 3 independent bounded lanes. Each provider isolates timeouts/errors.
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures=[pool.submit(task,item) for item in providers.items()]
        for f in as_completed(futures):
            name,items=f.result()
            verified=0
            for item in items:
                if not item:continue
                key=(item["museum_source"],item["museum_native_id"])
                if key in pinned_keys or key in data:continue
                if not safe(item["remote_preview_url"],item["museum_source"]):continue
                if item["is_public_domain"] is not True:continue
                data[key]=item;verified+=1
            print("PROVIDER_READY",name,verified,flush=True)
    if DEST.exists():
        try:
            existing=json.loads(DEST.read_text(encoding="utf-8"))
            for row in existing:
                key=(row.get("museum_source"),row.get("museum_native_id"))
                if key not in pinned_keys and row.get("is_public_domain") is True and safe(row.get("remote_preview_url",""),row.get("museum_source","")):
                    data.setdefault(key,row)
        except Exception as e:print("PREVIOUS_GLOBAL_HELD",str(e)[:100],flush=True)
    # User-excluded metadata-only item (Smithsonian NPG.2007.11): do not reimport.
    data = {k: v for k, v in data.items() if not (
        v.get('museum_source') == 'smithsonian' and
        str(v.get('id')) == '6452594389')}
    # Entropy interleaving gives worldwide variety at first viewport.
    groups={}
    for r in data.values():
        groups.setdefault(r["museum_name"],[]).append(r)
    for group in groups.values():
        group.sort(key=lambda v:hashlib.sha256(str(v["id"]).encode()).hexdigest())
    names=sorted(groups)
    output=[]
    for i in range(max((len(v) for v in groups.values()),default=0)):
        for name in names:
            arr=groups[name]
            if i<len(arr):
                output.append(arr[i])
                if len(output)>=MAX_RECORDS:break
        if len(output)>=MAX_RECORDS:break
    # Fail on identity collisions, malformed output, unexpected catalog growth.
    keys=[(r["museum_source"],r["museum_native_id"]) for r in output]
    if len(set(keys))!=len(keys):raise SystemExit("Duplicate global identities")
    if len(output)<1200:
        raise SystemExit(f"FAIL CLOSED: only {len(output)} approved artworks from {len(groups)} institutions")
    encoded=json.dumps(output,ensure_ascii=False,separators=(",",":")).encode()
    if len(encoded)>MAX_CATALOG_BYTES:raise SystemExit("Global JSON asset exceeded 7.5MB")
    DEST.write_bytes(encoded+b"\n")
    counts={}
    for r in output:counts[r["museum_name"]]=counts.get(r["museum_name"],0)+1
    report={
      "schema_version":2,"records_global":len(output),
      "records_bundled_existing":len(prior)+len(built),
      "records_total":len(output)+len(prior)+len(built),
      "catalog_bytes":len(encoded)+1,
      "remote_images_only":len(output),
      "local_webp_bytes_added":0,
      "institutions":counts,
      "record_rights":"official item-specific CC0/PD flags only",
      "media_verification":"official image host + provider media rights; network delivery deferred to device",
      "store_rights_review_required":True,
    }
    REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("GLOBAL_MUSEUM_IMPORT_SUCCESS",json.dumps(report,ensure_ascii=False),flush=True)

if __name__=="__main__":main()

# Global catalog import run: 2026-11-21 / primary-source rights only.
