#!/usr/bin/env python3
"""Prepare an additive, metadata-only D1 mirror of Art Drift's approved catalog.

This is a LOCAL SQL EXPORT, NOT a Cloudflare deployment. No network requests,
image downloads, Supabase credentials or write access to Cloudflare.
The current app continues using its bundled, offline-first catalog.
"""
from __future__ import annotations
import argparse
import json
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parents[3]
SOURCES=(
    "assets/gallery/catalog.json",
    "assets/museums/catalog.json",
    "assets/museums/catalog_global.json",
    "assets/museums/catalog_modern_1950.json",
    "assets/museums/catalog_new_museums.json",
)
LICENSES={"CC0","Public Domain","CC BY 3.0","CC BY 4.0",
          "CC BY-SA 3.0","CC BY-SA 4.0"}
PREVIEW_HOSTS={
    "aic":{"www.artic.edu"},"met":{"images.metmuseum.org"},
    "cleveland":{"openaccess-cdn.clevelandart.org","clevelandart.org","www.clevelandart.org"},
    "rijks":{"iiif.micr.io"},"nga":{"api.nga.gov","media.nga.gov"},
    "getty":{"media.getty.edu"},"smithsonian":{"ids.si.edu","www.si.edu","si.edu"},
    "smk":{"iip.smk.dk","iip-thumb.smk.dk"},"mia":{"api.artsmia.org"},
    "walters":{"images.thewalters.org","art.thewalters.org"},
    "commons":{"upload.wikimedia.org"},
}
DETAIL_HOSTS={
    "aic":{"www.artic.edu"},
    "met":{"metmuseum.org","www.metmuseum.org"},
    "cleveland":{"clevelandart.org","www.clevelandart.org"},
    "rijks":{"www.rijksmuseum.nl","rijksmuseum.nl","data.rijksmuseum.nl"},
    "nga":{"www.nga.gov","nga.gov"},
    "getty":{"getty.edu","www.getty.edu","data.getty.edu"},
    "smithsonian":{"www.si.edu","si.edu","americanart.si.edu","npg.si.edu","asia.si.edu"},
    "smk":{"open.smk.dk","www.smk.dk","www.open.smk.dk"},
    "mia":{"collections.artsmia.org"},
    "walters":{"www.thewalters.org","art.thewalters.org"},
    "commons":{"commons.wikimedia.org"},
}


def official(value,hosts):
    if not isinstance(value,str) or not value:return False
    try:
        u=urlparse(value)
        return u.scheme=="https" and u.hostname in hosts and not u.username \
            and not u.password and u.port in (None,443)
    except (ValueError,TypeError):
        return False


def quote(value):
    return "'"+str(value or "").replace("\x00","").replace("'","''")+"'"

def field(item,key,maximum=300):
    v=item.get(key)
    return v.strip()[:maximum] if isinstance(v,str) else ""

def normalize(item):
    if not isinstance(item,dict):return None
    art_id=item.get("id")
    if type(art_id) is not int or art_id<1:return None
    source=field(item,"museum_source",32) or "aic"
    if source not in PREVIEW_HOSTS:return None
    license=field(item,"rights_license",40) or ("Public Domain" if source=="aic" else "")
    if license not in LICENSES:return None
    is_pd=item.get("is_public_domain") is True
    if source=="commons":
        if is_pd!=(license=="CC0"):return None
        if not field(item,"artist_title",220) or not field(item,"credit_line",250):return None
        if not official(field(item,"rights_evidence_url",900),{"commons.wikimedia.org"}):return None
        if not official(field(item,"rights_license_url",500),{"creativecommons.org"}):return None
    elif not is_pd or license not in ("CC0","Public Domain"):
        return None
    title=field(item,"title",230)
    if not title:return None
    native=field(item,"museum_native_id",230) or str(art_id)
    museum=field(item,"museum_name",210)
    if not museum:
        if source=="aic":museum="Art Institute of Chicago"
        else:return None
    image=field(item,"remote_preview_url",1300)
    if image and not official(image,PREVIEW_HOSTS[source]):image=""
    page=field(item,"remote_museum_url",900)
    if not official(page,DETAIL_HOSTS[source]):page=""
    if source=="aic":
        page="https://www.artic.edu/artworks/"+str(art_id)
    evidence=field(item,"rights_evidence_url",900)
    if source=="aic" and not evidence:
        evidence="https://www.artic.edu/open-access/open-access-images"
    if not official(evidence,{"commons.wikimedia.org","www.si.edu","si.edu",
        "www.clevelandart.org","clevelandart.org","www.metmuseum.org",
        "www.nga.gov","www.artic.edu","www.getty.edu",
        "www.rijksmuseum.nl","www.smk.dk","open.smk.dk",
        "collections.artsmia.org","www.thewalters.org",
        "art.thewalters.org"}):return None
    return {
        "source_key":source+":"+str(art_id),
        "museum_source":source,
        "museum_native_id":native,
        "museum_name":museum,
        "title":title,
        "artist":field(item,"artist_title",220) or field(item,"artist_display",220),
        "date_display":field(item,"date_display",100),
        "medium":field(item,"artwork_type_title",120) or field(item,"medium_display",140),
        "source_url":page,
        "image_url":image,
        "rights_license":license,
        "rights_evidence_url":evidence,
        "credit_line":field(item,"credit_line",250),
    }


COLUMNS=("source_key","museum_source","museum_native_id","museum_name",
    "title","artist","date_display","medium","source_url","image_url",
    "rights_license","rights_evidence_url","credit_line")


def export(root=ROOT,out=None,expected=5084,chunk=200):
    if not 25<=chunk<=500:raise ValueError("Unsafe D1 shard size")
    if out is None:out=root/"build/d1-museums"
    out=Path(out)
    values=[]
    rejected=[]
    seen=set()
    for path in SOURCES:
        data=json.loads((root/path).read_text(encoding="utf-8"))
        if not isinstance(data,list):raise ValueError("Invalid catalog "+path)
        for entry in data:
            row=normalize(entry)
            if row is None:
                rejected.append((path,entry.get("id") if isinstance(entry,dict) else None))
                continue
            if row["source_key"] in seen:
                raise ValueError("Duplicate identity "+row["source_key"])
            seen.add(row["source_key"])
            values.append(row)
    if rejected:
        raise ValueError("Rights/identity rejection; fail closed: "+repr(rejected[:5]))
    if expected is not None and len(values)!=expected:
        raise ValueError("Museum catalog count mismatch "+str(len(values))+" != "+str(expected))
    if len(values)>20000:raise ValueError("Unexpected museum catalog expansion")
    out.mkdir(parents=True,exist_ok=True)
    for old in out.glob("museum-*.sql"):old.unlink()
    files=[]
    total_bytes=0
    for start in range(0,len(values),chunk):
        batch=values[start:start+chunk]
        lines=["-- Art Drift museum metadata; no image bytes; source item rights checked.",
               "BEGIN TRANSACTION;"]
        for record in batch:
            args=",".join(quote(record[k]) for k in COLUMNS)
            lines.append("INSERT OR IGNORE INTO museum_works ("+
                         ",".join(COLUMNS)+") VALUES ("+args+");")
        lines.append("COMMIT;")
        name=f"museum-{len(files)+1:04d}.sql"
        data=("\n".join(lines)+"\n").encode("utf-8")
        total_bytes+=len(data)
        (out/name).write_bytes(data)
        files.append({"filename":name,"records":len(batch),"bytes":len(data)})
    if total_bytes>15_000_000:raise ValueError("D1 source size exceeds 15MB")
    report={
        "version":1,"status":"PREPARED_ONLY_DO_NOT_DEPLOY_AUTOMATICALLY",
        "records":len(values),"unique_sources":len({r["museum_source"] for r in values}),
        "museums":dict(sorted(Counter(r["museum_name"] for r in values).items())),
        "license_count":dict(sorted(Counter(r["rights_license"] for r in values).items())),
        "shards":files,"sql_bytes":total_bytes,
        "images_bundled":0,"personal_data":False,
        "source_files":list(SOURCES),"schema":"museum_schema.sql",
        "d1_remote_import":"REQUIRES_EXPLICIT_APPROVAL",
        "app_canvas_source":"UNCHANGED_LOCAL",
    }
    (out/"manifest.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",
                                      encoding="utf-8")
    return report


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=ROOT)
    p.add_argument("--out",type=Path,default=ROOT/"build/d1-museums")
    p.add_argument("--expected",type=int,default=5084)
    p.add_argument("--chunk",type=int,default=200)
    args=p.parse_args()
    result=export(args.root,args.out,args.expected,args.chunk)
    print("D1_MUSEUM_SQL_QA",json.dumps({
       "records":result["records"],"shards":len(result["shards"]),
       "status":result["status"]}))
