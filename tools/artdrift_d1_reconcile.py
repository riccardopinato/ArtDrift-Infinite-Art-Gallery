#!/usr/bin/env python3
"""Prove exact local-vs-existing-D1 identity and prepare at most one safe SQL delta.
The generated SQL is NEVER run by this script or its workflow.
"""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"cloudflare/art-catalog/scripts"))
from make_museum_d1_import import SOURCES,normalize,COLUMNS,quote

def unwrap(path):
    payload=json.loads(Path(path).read_text(encoding="utf8"))
    if isinstance(payload,dict):payload=payload.get("result",payload)
    if isinstance(payload,list):
        if len(payload)!=1 or not isinstance(payload[0],dict) or "results" not in payload[0]:
            raise ValueError("Unexpected Wrangler JSON result")
        rows=payload[0]["results"]
    elif isinstance(payload,dict) and "results" in payload:rows=payload["results"]
    else:raise ValueError("Unexpected Wrangler response")
    if not isinstance(rows,list):raise ValueError("Malformed D1 rows")
    return rows

def reconcile(local,remote,staging):
    a={(r["museum_source"],r["museum_native_id"]):r for r in local}
    if len(a)!=len(local):raise ValueError("Local duplicate native identity")
    b={(r["museum_source"],r["museum_native_id"]):r for r in remote}
    if len(b)!=len(remote):raise ValueError("Remote duplicate native identity")
    if len({r["source_key"] for r in remote})!=len(remote):raise ValueError("Remote duplicate key")
    if len(remote) not in (5084,5085):raise ValueError("Unexpected D1 museum count")
    extra=set(b)-set(a)
    if extra:raise ValueError("Unexpected remote IDs "+str(sorted(extra)[:4]))
    missing=set(a)-set(b)
    if len(missing)>1:raise ValueError("More than one missing remote museum ID")
    for key in set(a)&set(b):
        if a[key]["source_key"]!=b[key]["source_key"]:
            raise ValueError("Remote internal identity collision "+str(key))
    if len(staging) not in (535,635):raise ValueError("Unexpected D1 stage count")
    stage_ids=set()
    for row in staging:
        identity=(row["provider"],row["native_id"])
        if identity in stage_ids:raise ValueError("Duplicate staged native identity")
        stage_ids.add(identity)
        if row["publication_status"]!="HOLD":raise ValueError("Unexpected published stage record")
    overlap=len(stage_ids & set(a))
    if len(staging)==635:
        new=[r for r in staging if r['provider']=='cleveland' and (r['provider'],r['native_id']) not in a]
        if len(new)!=100 or any(r.get('rights_status')!='METADATA_ONLY' for r in new):
            raise ValueError('Expected exactly 100 new Cleveland metadata-only HOLD rows')
    if overlap!=49:raise ValueError("Expected 49 Cleveland native overlaps, got "+str(overlap))
    if sum((r["provider"]=="cleveland") for r in staging)!=(49+(len(staging)-535)):raise ValueError("Cleveland count mismatch")
    return {
        "local_catalog":len(local),
        "remote_museum_rows_before":len(remote),
        "missing_remote_native_ids":len(missing),
        "missing":sorted(list(missing)),
        "staged_rows":len(staging),
        "staged_hold":sum(r["publication_status"]=="HOLD" for r in staging),
        "staged_already_in_museum_catalog":overlap,
        "distinct_native_identities":len(a)+len(stage_ids-set(a)),
        "approved_staged_rows":0,
        "remote_writes_executed":0,
    }

def source_rows(root):
    records=[]
    for name in SOURCES:
        raw=json.loads((root/name).read_text(encoding="utf8"))
        if not isinstance(raw,list):raise ValueError("Invalid catalog")
        for item in raw:
            row=normalize(item)
            if row is None:raise ValueError("Source did not pass rights metadata filter")
            records.append(row)
    if len(records)!=5085:raise ValueError("Unexpected source total")
    return records

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--museum-json",required=True,type=Path)
    p.add_argument("--stage-json",required=True,type=Path)
    p.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1])
    p.add_argument("--out",type=Path,default=Path("build/d1-reconciliation"))
    a=p.parse_args()
    local=source_rows(a.root)
    remote=unwrap(a.museum_json)
    stage=unwrap(a.stage_json)
    report=reconcile(local,remote,stage)
    by_identity={(r["museum_source"],r["museum_native_id"]):r for r in local}
    missing=[by_identity[k] for k in report["missing"]]
    sql=["-- HOLD-neutral museum metadata delta: generated but NEVER automatically executed."]
    for row in missing:
        sql.append("INSERT OR IGNORE INTO museum_works ("+",".join(COLUMNS)+") VALUES ("+
                   ",".join(quote(row[field]) for field in COLUMNS)+");")
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"report.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    (a.out/"museum_delta_NOT_APPLIED.sql").write_text("\n".join(sql)+"\n",encoding="utf8")
    print("D1_EXACT_IDENTITY_RECONCILE_PASS",report["local_catalog"],
          report["remote_museum_rows_before"],report["staged_rows"],
          report["distinct_native_identities"],"MISSING",len(missing))

if __name__=="__main__":main()
