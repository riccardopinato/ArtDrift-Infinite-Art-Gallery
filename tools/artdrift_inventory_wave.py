#!/usr/bin/env python3
"""Deterministic read-only museum inventory and 100-record review waves."""
import argparse
import json
import sys
from pathlib import Path
from collections import Counter

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"cloudflare/art-catalog/scripts"))
from make_museum_d1_import import SOURCES, normalize
CANDIDATES={"assets/museums/catalog_modern_1950.json","assets/museums/catalog_new_museums.json"}

def inspect(root,expected=5085):
    seen_keys=set()
    seen_native=set()
    by_file=Counter()
    by_provider=Counter()
    by_type=Counter()
    license_counts=Counter()
    packaged=0
    urls=0
    review=[]
    for source_file in SOURCES:
        data=json.loads((root/source_file).read_text(encoding="utf8"))
        if not isinstance(data,list):raise ValueError("Invalid catalog: "+source_file)
        by_file[source_file]=len(data)
        for item in data:
            row=normalize(item)
            if row is None:raise ValueError("Invalid rights/identity in "+source_file)
            key=(row["museum_source"],row["museum_native_id"])
            if row["source_key"] in seen_keys:raise ValueError("Duplicate internal ID "+row["source_key"])
            if key in seen_native:raise ValueError("Duplicate museum native ID "+str(key))
            seen_keys.add(row["source_key"])
            seen_native.add(key)
            by_provider[row["museum_source"]]+=1
            license_counts[row["rights_license"]]+=1
            kind=(item.get("artwork_type_title") or "UNKNOWN").strip() or "UNKNOWN"
            by_type[kind]+=1
            if row["image_url"]:urls+=1
            asset=item.get("bootstrap_asset")
            if isinstance(asset,str) and asset:
                if not (root/asset).is_file():raise ValueError("Missing bundled preview: "+asset)
                packaged+=1
            if source_file not in CANDIDATES:continue
            flags=["RIGHTS_OF_OBJECT_AND_MEDIA_NOT_REVIEWED","IMAGE_DELIVERY_NOT_VERIFIED"]
            if kind.lower()!="painting":flags.append("NOT_PAINTING")
            if not row["artist"]:flags.append("NO_ARTIST")
            if not row["source_url"]:flags.append("NO_OFFICIAL_DETAIL_URL")
            if not row["image_url"]:flags.append("NO_VALID_PREVIEW_URL")
            review.append({
                "source_key":row["source_key"],
                "museum_source":row["museum_source"],
                "museum_native_id":row["museum_native_id"],
                "museum":row["museum_name"],
                "title":row["title"],
                "artist":row["artist"],
                "year":row["date_display"],
                "type":kind,
                "license":row["rights_license"],
                "rights_evidence_url":row["rights_evidence_url"],
                "source_url":row["source_url"],
                "preview_url":row["image_url"],
                "publication_status":"HOLD",
                "flags":flags
            })
    if expected is not None and len(seen_keys)!=expected:
        raise ValueError("Catalog source count mismatch "+str(len(seen_keys)))
    review.sort(key=lambda r:r["source_key"])
    for i,r in enumerate(review):r["wave"]=i//100+1
    summary={
        "catalog_records":len(seen_keys),
        "native_identities":len(seen_native),
        "candidate_records":len(review),
        "candidate_waves":(len(review)+99)//100,
        "auto_approved":0,"canvas_enabled":0,
        "packaged_preview_files_verified":packaged,
        "image_urls_present_not_download_verified":urls,
        "per_file":dict(sorted(by_file.items())),
        "per_provider":dict(sorted(by_provider.items())),
        "per_type":dict(sorted(by_type.items())),
        "per_license":dict(sorted(license_counts.items())),
        "d1_live_checked":False,
        "rights_certified":False,
        "visual_review_completed":False,
        "stage_535":"SEPARATE_REMOTE_DATA_NOT_COUNTED_HERE"
    }
    return summary,review

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=ROOT)
    p.add_argument("--out",type=Path,default=Path("build/artdrift-inventory"))
    p.add_argument("--expected",type=int,default=5085)
    args=p.parse_args()
    summary,review=inspect(args.root,args.expected)
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/"summary.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    (args.out/"review.json").write_text(json.dumps(review,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    for i in range(0,len(review),100):
        (args.out/("wave-%02d.json"%(i//100+1))).write_text(json.dumps(review[i:i+100],indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    print("ARTDRIFT_INVENTORY_PASS",summary["catalog_records"],summary["candidate_records"],summary["candidate_waves"])

if __name__=="__main__":main()
