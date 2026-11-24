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

def convert(source,out,chunk=2500,verify=True,allowlist=None,expected_count=None):
    # Deliberate fail-closed gate: the old 161,038-row SQL export must NEVER
    # be generated for D1 unless a reviewed P1 ID allowlist is provided.
    if not allowlist or not isinstance(allowlist,set):
        raise ValueError("APPROVED_P1_ALLOWLIST_REQUIRED; no bulk import allowed")
    if not all(isinstance(item,str) and item.isdecimal() and int(item)>0
               for item in allowlist):
        raise ValueError("Invalid P1 allowlist identity")
    if expected_count is not None and len(allowlist)!=expected_count:
        raise ValueError("Approved P1 count mismatch")
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
        (out/name).write_text("\n".join(batch)+"\n",encoding="utf-8")
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
            if art_id not in allowlist:
                continue
            if verify and (row.get("Cataloged") or "").strip().upper()!="Y":
                raise ValueError("Selected P1 item is not cataloged")
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
    if total!=len(allowlist):
        for existing in out.glob("import-*.sql"):
            existing.unlink()
        raise ValueError("P1 allowlist contains missing/unverified source IDs")
    manifest={"source_commit":SOURCE,"source_sha256":SHA256 if verify else "fixture",
        "artworks":total,"shards":files,"sql_inserts_per_artwork":2,
        "images_included":False,"image_license":"NOT_INCLUDED_NOT_LICENSED",
        "selection_scope":"APPROVED_P1_ONLY", "allowlist_count":len(allowlist)}
    (out/"manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    return manifest

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--input",type=Path,required=True)
    p.add_argument("--out",type=Path,default=Path("dist/moma-d1"))
    p.add_argument("--chunk",type=int,default=2500)
    p.add_argument("--allowlist",type=Path,required=True,
        help="Reviewed JSON array of exactly the accepted MoMA ObjectID values")
    p.add_argument("--approved-count",type=int,default=15294)
    args=p.parse_args()
    if not 100<=args.chunk<=5000:raise ValueError("Chunk outside permitted range")
    raw=json.loads(args.allowlist.read_text(encoding="utf-8"))
    if not isinstance(raw,list):
        raise ValueError("Approved P1 allowlist must be a JSON array")
    selected=set(str(x) for x in raw if type(x) is int or
                 (isinstance(x,str) and x.isdecimal()))
    if len(selected)!=len(raw):
        raise ValueError("Duplicate/invalid P1 ObjectID")
    result=convert(args.input,args.out,args.chunk,allowlist=selected,
                   expected_count=args.approved_count)
    print("MOMA_D1_EXPORT works=%d shards=%d"%(result["artworks"],len(result["shards"])))
