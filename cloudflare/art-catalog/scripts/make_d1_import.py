#!/usr/bin/env python3
"""Convert pinned official MoMA CSV to ordered D1 shards, metadata only."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

SHA256="73056fe35477608d169b2dcc6ecfde617c5652fa8f61967e819610985423b1dd"
SIZE=73480509
SOURCE="6ca06d4cc92dd39b57cec63278a63059cfa6c1a6"

def sql_quote(x):
    return "'"+str(x or "").replace("\x00","").replace("'","''")+"'"

def convert(source,out,chunk=2500,verify=True):
    if verify:
        digest=hashlib.sha256()
        count_bytes=0
        with source.open("rb") as data:
            for block in iter(lambda:data.read(1024*1024),b""):
                digest.update(block)
                count_bytes+=len(block)
        if digest.hexdigest()!=SHA256 or count_bytes!=SIZE:
            raise ValueError("Official source checksum or byte count mismatch")
    out.mkdir(parents=True,exist_ok=True)
    seen=set()
    batch=[]
    files=[]
    total=0
    def save():
        if not batch:return
        name="import-%04d.sql"%(len(files)+1)
        (out/name).write_text("BEGIN TRANSACTION;\n"+"\n".join(batch)+
            "\nCOMMIT;\n",encoding="utf-8")
        files.append({"file":name,"works":len(batch)//2})
        batch.clear()
    with source.open(encoding="utf-8-sig",newline="") as stream:
        csv.field_size_limit(8000000)
        reader=csv.DictReader(stream)
        if not {"ObjectID","Title","Artist","Date","Medium"}.issubset(reader.fieldnames or []):
            raise ValueError("MoMA CSV schema mismatch")
        for row in reader:
            art_id=(row.get("ObjectID") or "").strip()
            if not art_id.isdecimal() or int(art_id)<=0 or art_id in seen:
                raise ValueError("Invalid or duplicate ObjectID")
            seen.add(art_id)
            official="https://www.moma.org/collection/works/"+art_id
            vals=[art_id,row.get("Title"),row.get("Artist"),row.get("Date"),
                row.get("Medium"),row.get("Dimensions"),
                row.get("Classification"),row.get("Department"),official]
            sql_vals=",".join(vals[0:1]+[sql_quote(x) for x in vals[1:]])
            batch.append("INSERT INTO works (id,title,artist,date_display,medium,dimensions,classification,department,work_url) VALUES ("+sql_vals+");")
            fts=[sql_quote(x) for x in (vals[1],vals[2],vals[4],vals[6])]
            batch.append("INSERT INTO works_fts (rowid,title,artist,medium,classification) VALUES ("+
                art_id+","+",".join(fts)+");")
            total+=1
            if len(batch)>=2*chunk:save()
        save()
    manifest={"source_commit":SOURCE,"source_sha256":SHA256 if verify else "fixture",
        "artworks":total,"shards":files,"sql_inserts_per_artwork":2,
        "images_included":False,"image_license":"NOT_INCLUDED_NOT_LICENSED"}
    (out/"manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    return manifest

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--input",type=Path,required=True)
    p.add_argument("--out",type=Path,default=Path("dist/moma-d1"))
    p.add_argument("--chunk",type=int,default=2500)
    args=p.parse_args()
    if not 100<=args.chunk<=5000:raise ValueError("Chunk outside permitted range")
    result=convert(args.input,args.out,args.chunk)
    print("MOMA_D1_EXPORT works=%d shards=%d"%(result["artworks"],len(result["shards"])))
