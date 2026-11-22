#!/usr/bin/env python3
"""Export all MoMA CC0 metadata at a pinned official dataset SHA. No images."""
import argparse
import collections
import csv
import datetime as dt
import hashlib
import json
import re
import sqlite3
import urllib.request
from pathlib import Path

REPO = "MuseumofModernArt/collection"
SOURCE_SHA = "6ca06d4cc92dd39b57cec63278a63059cfa6c1a6"
USER_AGENT = "ArtDrift-MoMA-metadata-exporter/1.0"
LIMIT = {"Artworks.csv": 200000000, "Artists.csv": 10000000}

def retrieve_verified(name, output):
    pointer_url = f"https://raw.githubusercontent.com/{REPO}/{SOURCE_SHA}/{name}"
    req = urllib.request.Request(pointer_url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=80) as stream:
        pointer = stream.read(1500).decode("utf-8-sig")
    expected_hash = re.search(r"^oid sha256:([0-9a-f]{64})$", pointer, re.M)
    expected_size = re.search(r"^size (\d+)$", pointer, re.M)
    if not pointer.startswith("version https://git-lfs.github.com/spec/v1") or not expected_hash or not expected_size:
        raise RuntimeError("Missing official immutable LFS pointer: "+name)
    digest = expected_hash.group(1)
    length = int(expected_size.group(1))
    if not (100 < length <= LIMIT[name]):
        raise ValueError("Unsafe LFS size "+str(length))
    data_url = f"https://media.githubusercontent.com/media/{REPO}/{SOURCE_SHA}/{name}"
    req = urllib.request.Request(data_url, headers={"User-Agent": USER_AGENT})
    temp = output/(name+".partial")
    actual = hashlib.sha256()
    total = 0
    try:
        with urllib.request.urlopen(req,timeout=180) as input_stream, temp.open("wb") as target:
            while True:
                block = input_stream.read(1024*1024)
                if not block:
                    break
                total += len(block)
                if total > LIMIT[name]:
                    raise ValueError("Oversized official dataset")
                actual.update(block)
                target.write(block)
        if total != length or actual.hexdigest() != digest:
            raise ValueError(f"{name}: LFS checksum/size mismatch actual {total}/{actual.hexdigest()}")
        temp.replace(output/name)
    finally:
        temp.unlink(missing_ok=True)
    print(f"MOMA_LFS_OK {name} bytes={total} sha256={digest}",flush=True)
    return {"file":name,"sha256":digest,"bytes":total,"pointer":pointer_url,"download":data_url}

def artist_ids(value):
    return list(dict.fromkeys(str(int(x)) for x in re.findall(r"\d+",value or "")))

def csv_rows(path):
    csv.field_size_limit(20*1024*1024)
    stream=path.open("r",encoding="utf-8-sig",newline="")
    return stream,csv.DictReader(stream)

def run(destination):
    destination.mkdir(parents=True,exist_ok=True)
    source={x:retrieve_verified(x,destination) for x in ("Artists.csv","Artworks.csv")}
    af,rd=csv_rows(destination/"Artists.csv")
    artists={}
    try:
        for row in rd:
            aid=(row.get("ConstituentID") or "").strip()
            if not aid:continue
            if aid in artists:raise ValueError("Repeated artist id "+aid)
            artists[aid]=row
    finally:af.close()

    dbpath=destination/"MoMA_full_metadata.sqlite"
    dbpath.unlink(missing_ok=True)
    db=sqlite3.connect(dbpath)
    db.executescript("""
      CREATE TABLE artworks(
        object_id INTEGER PRIMARY KEY,title TEXT,artist TEXT,date TEXT,
        medium TEXT,dimensions TEXT,classification TEXT,department TEXT,
        date_acquired TEXT,credit_line TEXT,source_url TEXT,
        thumbnail_url_unlicensed TEXT,cataloged TEXT,raw_json TEXT NOT NULL);
      CREATE TABLE artists(
        constituent_id INTEGER PRIMARY KEY,name TEXT,artist_bio TEXT,
        nationality TEXT,gender TEXT,born TEXT,died TEXT,
        wikidata_qid TEXT,getty_ulan TEXT);
      CREATE TABLE artwork_artists(
        object_id INTEGER NOT NULL,constituent_id INTEGER NOT NULL,
        PRIMARY KEY(object_id,constituent_id));
      CREATE INDEX idx_artworks_artist ON artworks(artist);
      CREATE INDEX idx_artwork_artists_artist ON artwork_artists(constituent_id);
      CREATE INDEX idx_artworks_department ON artworks(department);
    """)
    with db:
        db.executemany("INSERT INTO artists VALUES (?,?,?,?,?,?,?,?,?)",(
            (int(aid),row.get("DisplayName"),row.get("ArtistBio"),row.get("Nationality"),
             row.get("Gender"),row.get("BeginDate"),row.get("EndDate"),
             row.get("Wiki QID"),row.get("ULAN"))
            for aid,row in artists.items()
        ))
    af,works=csv_rows(destination/"Artworks.csv")
    ids_seen=set()
    counts=collections.Counter()
    missing=collections.Counter()
    kinds=collections.Counter()
    without_id=0
    rows=0
    relationships=0
    urls=0
    thumb_urls=0
    work_batch=[]
    relation_batch=[]
    with af, (destination/"MoMA_ArtDrift_metadata_only.jsonl").open("w",encoding="utf-8") as jsonl, (
        destination/"MoMA_artwork_artist_links.csv").open("w",encoding="utf-8-sig",newline=""
    ) as linkf, (destination/"MoMA_ArtDrift_metadata_only.csv").open(
        "w",encoding="utf-8-sig",newline=""
    ) as exportf:
        links=csv.writer(linkf)
        links.writerow(["ObjectID","ConstituentID","ArtistName"])
        export_fields=["ObjectID","Title","Artist","Date","Medium",
           "Dimensions","Classification","Department","DateAcquired",
           "CreditLine","ConstituentID","URL","source","image_license_status"]
        writer=csv.DictWriter(exportf,fieldnames=export_fields,extrasaction="ignore")
        writer.writeheader()
        fields=works.fieldnames or []
        if "ObjectID" not in fields or "ConstituentID" not in fields:
            raise ValueError("Official artwork schema invalid: "+str(fields))
        for row in works:
            oid=(row.get("ObjectID") or "").strip()
            if not oid.isdecimal():raise ValueError("Invalid ObjectID "+repr(oid))
            ident=int(oid)
            if ident in ids_seen:raise ValueError("Repeated ObjectID "+oid)
            ids_seen.add(ident)
            aid_list=artist_ids(row.get("ConstituentID"))
            if not aid_list:without_id+=1
            for aid in aid_list:
                a=artists.get(aid)
                links.writerow([oid,aid,a.get("DisplayName","") if a else ""])
                relation_batch.append((ident,int(aid)))
                relationships+=1
                if a:counts[aid]+=1
                else:missing[aid]+=1
            source_url=(row.get("URL") or "").strip()
            thumb=(row.get("ThumbnailURL") or "").strip()
            if source_url.startswith("https://www.moma.org/collection/works/"):urls+=1
            if thumb:thumb_urls+=1
            kinds[row.get("Classification","")]+=1
            normalized={k:(v if v is not None else "") for k,v in row.items() if k}
            derived={**normalized,"source":"MoMA metadata CC0",
              "source_commit":SOURCE_SHA,
              "artist_constituent_ids":aid_list,
              "image_license_status":"NOT_INCLUDED_NOT_LICENSED"}
            jsonl.write(json.dumps(derived,ensure_ascii=False,separators=(",",":"))+"\n")
            writer.writerow({**row,"source":"MoMA metadata CC0",
                "image_license_status":"NOT_INCLUDED_NOT_LICENSED"})
            work_batch.append((ident,row.get("Title"),row.get("Artist"),
              row.get("Date"),row.get("Medium"),row.get("Dimensions"),
              row.get("Classification"),row.get("Department"),
              row.get("DateAcquired"),row.get("CreditLine"),
              source_url,thumb,row.get("Cataloged"),
              json.dumps(normalized,ensure_ascii=False,separators=(",",":"))))
            rows+=1
            if len(work_batch)>=1000:
                with db:
                    db.executemany("INSERT INTO artworks VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",work_batch)
                    db.executemany("INSERT INTO artwork_artists VALUES (?,?)",relation_batch)
                work_batch.clear()
                relation_batch.clear()
        with db:
            db.executemany("INSERT INTO artworks VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",work_batch)
            db.executemany("INSERT INTO artwork_artists VALUES (?,?)",relation_batch)
    with (destination/"MoMA_artists_with_counts.csv").open("w",encoding="utf-8-sig",newline="") as index:
        headers=["ConstituentID","DisplayName","ArtistBio","Nationality","Gender",
            "BeginDate","EndDate","Wiki QID","ULAN","artworks_count"]
        writer=csv.DictWriter(index,fieldnames=headers,extrasaction="ignore")
        writer.writeheader()
        for aid,artist in artists.items():
            writer.writerow({**artist,"artworks_count":counts[aid]})
    sql=[
        db.execute("SELECT COUNT(*) FROM artworks").fetchone()[0],
        db.execute("SELECT COUNT(*) FROM artists").fetchone()[0],
        db.execute("SELECT COUNT(*) FROM artwork_artists").fetchone()[0],
    ]
    if sql != [rows,len(artists),relationships]:
        raise AssertionError("SQLite row mismatch "+str(sql))
    if db.execute("PRAGMA integrity_check").fetchone()[0]!="ok":
        raise AssertionError("SQLite integrity_check failed")
    db.close()
    manifest={
       "timestamp_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
       "source_repository":f"https://github.com/{REPO}",
       "source_commit":SOURCE_SHA,"files_verified_by_sha256":source,
       "license_metadata":"CC0 1.0","images_included":False,
       "images_licensed_by_export":False,
       "artworks":rows,"artists":len(artists),"artwork_artist_links":relationships,
       "artworks_without_constituent_ids":without_id,
       "links_to_artist_ids_missing_from_artist_table":dict(missing),
       "artworks_with_source_url":urls,
       "artworks_with_unlicensed_thumbnail_url_reference":thumb_urls,
       "classification_counts":dict(kinds),"original_artwork_fields":fields,
       "database_integrity_check":"ok",
       "warning":"Only works in pinned official MoMA metadata snapshot. The website and museum holdings can differ; some records have incomplete unapproved metadata. Never treat thumbnail URLs as licensed images."
    }
    (destination/"MoMA_export_manifest.json").write_text(
        json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
    (destination/"LEGGIMI.txt").write_text(
        "Esportazione integrale dei metadati ufficiali MoMA (NON delle immagini)\n"
        f"Source SHA: {SOURCE_SHA}\nMetadati CC0; immagini NON incluse né licenziate.\n"
        "Non equivale alle opere totali fisicamente possedute o a tutte le pagine online.\n"
        "Alcuni record non sono completi o approvati dai curatori.\n\n"
        "Artworks.csv e Artists.csv: copie originali ufficiali.\n"
        "MoMA_artwork_artist_links.csv: collegamenti opera-autore.\n"
        "MoMA_artists_with_counts.csv: artisti e loro opere nel dataset.\n"
        "MoMA_ArtDrift_metadata_only.csv: estratto per revisione/importazione.\n"
        "MoMA_ArtDrift_metadata_only.jsonl: record con tutti i campi e provenienza.\n"
        "MoMA_full_metadata.sqlite: database locale (opere, autori, relazioni).\n"
        "MoMA_export_manifest.json: verifiche conteggi, hash e schema.\n",
        encoding="utf-8")
    print(f"MOMA_EXPORT_OK works={rows} artists={len(artists)} links={relationships} sqlite=ok",flush=True)
    return manifest

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--out",default="dist/moma",type=Path)
    args=p.parse_args()
    run(args.out)
