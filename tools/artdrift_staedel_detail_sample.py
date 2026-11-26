#!/usr/bin/env python3
"""Second-stage Städel study: stratified official LIDO GetRecord requests.

Input: verified active OAI identifiers. Output: metadata/image research HOLD.
No gallery assets or commercial release. One request lane, no concurrency.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.parse
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from artdrift_eu_new_museums_batch import fetch, staedel_parse, image_raster, color_tier

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"research/museums/20261126/lanes"
IDENTS=OUT/"staedel_identifier_inventory.json"
REPORT=OUT/"staedel_lido_detail_sample.json"
OLD=OUT/"results/staedel.json"
NS={"oai":"http://www.openarchives.org/OAI/2.0/"}
HOST="https://sammlung.staedelmuseum.de/api/oai?"


def select_ids(all_ids, excluded, count):
    """Deterministic spread across ALL source IDs; never first-100 bias."""
    usable=[x for x in set(all_ids) if x not in set(excluded) and
            x.startswith("oai:DE-MUS-048017:")]
    usable.sort(key=lambda x: hashlib.sha256(x.encode("utf-8")).hexdigest())
    return usable[:count]


def fetch_record(identifier, read=fetch):
    url=HOST+urllib.parse.urlencode({
        "verb":"GetRecord","metadataPrefix":"lido","identifier":identifier})
    root=ET.fromstring(read(url,limit=1_700_000,timeout=25))
    errors=root.findall(".//oai:error",NS)
    if errors:
        raise ValueError("OAI_SOURCE_ERROR_"+str([(x.attrib.get("code"),x.text)
                         for x in errors])[:150])
    record=root.find(".//oai:GetRecord/oai:record",NS)
    if record is None:
        raise ValueError("OAI_GETRECORD_LIDO_MISSING")
    return record


def run(max_records, max_images):
    ids=json.loads(IDENTS.read_text(encoding="utf-8"))
    if ids.get("provider")!="staedel":
        raise ValueError("Incorrect source identifier provider")
    previous=json.loads(REPORT.read_text(encoding="utf-8")) if REPORT.is_file() else {}
    first=json.loads(OLD.read_text(encoding="utf-8")) if OLD.is_file() else {}
    finished=set(previous.get("processed_oai_identifiers") or [])
    first_ids=set(first.get("source_identifier_sample") or [])
    selection=select_ids(ids.get("active_identifiers") or [],
                         finished|first_ids,max_records)
    stats=Counter()
    errors=[]
    sample={str(x.get("museum_native_id")):x
            for x in previous.get("review_candidates") or []}
    pixels=0
    stopped=False
    for oid in selection:
        try:
            r=fetch_record(oid)
        except Exception as e:
            errors.append({"oai_id":oid,"reason":str(e)[:190]})
            if "429" in str(e) or "503" in str(e):
                stopped=True
                break
            continue
        finished.add(oid)
        stats["new_records_read"]+=1
        rec=staedel_parse(r)
        if rec is None:
            stats["not_scenic_or_no_image_or_creation_date"]+=1
            time.sleep(.15)
            continue
        rec["original_oai_identifier"]=oid
        rec["runtime_visible"]=False
        rec["commercially_approved"]=False
        rec["curatorial_status"]="HOLD_SUBJECT_COLOR_LICENSE_AND_CREDIT"
        if pixels<max_images:
            pixels+=1
            try:
                measures,sha,img=image_raster(rec["remote_preview_url"])
                rec["color_metrics"]=measures
                rec["image_sha256"]=sha
                rec["color_tier"]=color_tier(measures)
                stats["new_images_checked"]+=1
                if not str(rec["color_tier"]).startswith("HOLD"):
                    stats["new_color_pass"]+=1
            except Exception as e:
                rec["image_error"]=str(e)[:160]
                stats["new_image_errors"]+=1
        sample[str(rec["museum_native_id"])]=rec
        stats["new_scenic_image_records"]+=1
        time.sleep(.15)
    result={
        "schema_version":1,
        "as_of_utc":datetime.now(timezone.utc).isoformat(),
        "provider":"staedel",
        "source_identifiers_count":len(ids.get("active_identifiers") or []),
        "previous_oai_ids_skipped":len(first_ids),
        "new_selected_oai_ids_count":len(selection),
        "processed_oai_identifiers":sorted(finished),
        "total_new_metadata_processed":len(finished),
        "review_candidates":sorted(sample.values(),
            key=lambda r: str(r.get("museum_native_id"))),
        "candidates_in_report":len(sample),
        "stats":dict(stats),
        "errors":errors[:50],
        "source_429_stopped":stopped,
        "catalog_exhaustively_searched":False,
        "source_zero_artworks_proven":False,
        "rights_status":"HOLD_CC_BY_SA_OFFICIAL_IMAGE_AND_PER_OBJECT",
        "visual_status":"HOLD",
        "runtime_imported":0,
        "commercially_approved":0,
    }
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    REPORT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",
                      encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k not in
                     ("processed_oai_identifiers","review_candidates")},
                    ensure_ascii=False),flush=True)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--max-records",type=int,default=90)
    parser.add_argument("--max-images",type=int,default=25)
    a=parser.parse_args()
    if not 1<=a.max_records<=140 or not 0<=a.max_images<=60:
        parser.error("bounded source and image sampling limits exceeded")
    run(a.max_records,a.max_images)


if __name__=="__main__":
    main()
