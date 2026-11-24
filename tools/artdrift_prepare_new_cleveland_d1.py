#!/usr/bin/env python3
"""Build 100 strictly NEW Cleveland METADATA_ONLY D1 HOLD stage records.

Requires successful live official-API discovery and prewrite D1 SELECT snapshot.
Generates SQL but never writes Cloudflare; remote write remains a separate gated action.
"""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from artdrift_new_cleveland_wave import discover
from artdrift_d1_reconcile import unwrap
from artdrift_museum_ingest import record,export

def prepare(items,remote_museum,remote_stage):
    if len(items)!=100:raise ValueError("Expected exactly 100 researched source IDs")
    if len(remote_museum)!=5085 or len(remote_stage)!=535:
        raise ValueError("Expected original D1 5085 museums + 535 stage rows")
    base={(r["museum_source"],r["museum_native_id"]) for r in remote_museum}
    staged={(r["provider"],r["native_id"]) for r in remote_stage}
    if len(base)!=5085 or len(staged)!=535:raise ValueError("Remote D1 duplicated identities")
    if any(r["publication_status"]!="HOLD" for r in remote_stage):
        raise ValueError("Cannot stage over remotely approved art")
    ids=set()
    output=[]
    for r in items:
        if r.get("provider")!="cleveland" or r.get("publication_status")!="HOLD" or r.get("rights_status")!="IMAGE_REVIEW" or r.get("source_share_license_status")!="CC0":
            raise ValueError("Source identity, review or CC0 metadata changed")
        native=r["native_id"]
        ident=("cleveland",native)
        if ident in ids or ident in base or ident in staged:
            raise ValueError("Duplicate Cleveland ID present in current D1 or batch")
        ids.add(ident)
        obj=record(provider="cleveland",native_id=native,
            museum=r["museum"],title=r["title"],artist=r["artist"],
            year=r["date"],medium=r["medium"],
            metadata_url=r["source_url"],
            rights_status="METADATA_ONLY")
        if obj["image_url"] or obj["full_image_url"] or obj["rights_evidence_url"] or obj["rights_license"]:
            raise ValueError("Unverified image or license accidentally entered stage")
        output.append(obj)
    if len(output)!=100:raise ValueError("Incomplete stage")
    return output

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--museum",type=Path,required=True)
    p.add_argument("--stage",type=Path,required=True)
    p.add_argument("--out",type=Path,default=Path("build/artdrift-d1-new-hold"))
    a=p.parse_args()
    summary,items=discover(ROOT,max_works=100)
    existing_museum=unwrap(a.museum)
    existing_stage=unwrap(a.stage)
    prepared=prepare(items,existing_museum,existing_stage)
    a.out.mkdir(parents=True,exist_ok=True)
    stats=export(prepared,a.out/"new-100.jsonl",a.out/"new-100-metadata-only.sql")
    assert stats["total"]==stats["metadata_only"]==100 and stats["published_by_import"]==0
    sql=(a.out/"new-100-metadata-only.sql").read_text(encoding="utf8")
    if sql.count("INSERT INTO artdrift_museum_ingest")!=100:raise ValueError("Unexpected SQL statement count")
    result={
        "record_count":100,
        "rights_status":"METADATA_ONLY",
        "publication_status":"HOLD",
        "source_status":summary["status"],
        "source_checked_utc":summary["checked_utc"],
        "source_url":summary["source"],
        "source_requests":summary["requests"],
        "prewrite_museum_rows":len(existing_museum),
        "prewrite_staged_rows":len(existing_stage),
        "new_ids_verified_not_overlapping":100,
        "images_downloaded":0,
        "image_urls_written":0,
        "automatic_approvals":0,
        "remote_writes_performed_by_this_script":0,
    }
    (a.out/"manifest.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print("ARTDRIFT_D1_NEW_100_HOLD_SOURCE_VALIDATION_PASS 5085 535 100_METADATA_ONLY")

if __name__=="__main__":main()
