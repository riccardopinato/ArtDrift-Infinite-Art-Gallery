#!/usr/bin/env python3
"""Read nine independent museum inventories and flag duplicate/attribution risk.

No network calls, no image publishing, no automatic rights approvals.
Treat an identical Commons file as one *file*, not proof of museum ownership.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

PROVIDERS = ("rijks","nationalmuseum_se","staedel",
             "finnish_national_gallery","birmingham","belvedere",
             "paris_musees","te_papa","nasjonalmuseet")
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research/museums/20261126/lanes"
COMMONS_RE = re.compile(r"(?:\?|&)curid=(\d+)(?:&|$)")


def normalize(s):
    s = str(s or "").casefold()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def validate_inventory(obj, expected):
    if obj.get("provider") != expected:
        raise ValueError(f"Wrong provider on branch {expected}")
    if obj.get("runtime_imported", 0) != 0 or obj.get("commercially_approved",0) != 0:
        raise ValueError(f"Unverified release in {expected}")
    for r in obj.get("review_candidates") or []:
        if r.get("source") != expected or r.get("commercially_approved") is not False or r.get("runtime_visible") is not False:
            raise ValueError(f"Unverified work evidence on {expected}")


def build(reports: dict[str, dict]):
    if set(reports) != set(PROVIDERS):
        raise ValueError("Require all nine providers; never silently undercount")
    indexed = {}
    per_museum = []
    for p in PROVIDERS:
        report = reports[p]
        validate_inventory(report, p)
        rows = report.get("review_candidates") or []
        per_museum.append({
            "source": p,
            "records_retained": len(rows),
            "latest_run_records": report.get("latest_run_candidates_in_report",len(rows)),
            "source_identifiers_tracked": report.get("cumulative_retained_source_identifiers"),
            "technical_color_pass": sum(1 for r in rows if r.get("color_tier") and not str(r.get("color_tier")).startswith("HOLD")),
            "catalog_exhaustively_searched": False,
            "commercially_approved": 0,
        })
        for row in rows:
            native = str(row.get("museum_native_id") or "")
            if not native:
                raise ValueError(f"Missing native ID: {p}")
            key = p+":"+native
            if key in indexed:
                raise ValueError(f"Duplicate primary key within {p}")
            indexed[key] = row

    parent = {key:key for key in indexed}
    def find(k):
        while parent[k] != k:
            parent[k] = parent[parent[k]]
            k = parent[k]
        return k
    def union(a,b):
        ra,rb = find(a),find(b)
        if ra != rb:
            parent[max(ra,rb)] = min(ra,rb)
    signals = {
        "commons_file": defaultdict(list),
        "file_sha1": defaultdict(list),
        "raster_sha256": defaultdict(list),
        "semantic": defaultdict(list),
    }
    for key,row in indexed.items():
        p=key.split(":",1)[0]
        if p not in ("rijks","staedel"):
            link=str(row.get("museum_url") or "")
            hit=COMMONS_RE.search(link)
            if hit:
                signals["commons_file"][hit.group(1)].append(key)
            sha=str(row.get("file_sha1") or row.get("source_file_sha1") or "")
            if re.fullmatch(r"[a-fA-F0-9]{40}",sha):
                signals["file_sha1"][sha.lower()].append(key)
        pix=str(row.get("image_sha256") or "")
        if re.fullmatch(r"[a-fA-F0-9]{64}",pix):
            signals["raster_sha256"][pix.lower()].append(key)
        artist,title=normalize(row.get("artist")),normalize(row.get("title"))
        year=row.get("year")
        if artist and title and isinstance(year,int) and year>=1:
            signals["semantic"][(artist,title,year)].append(key)
    duplicate_evidence=[]
    semantic_evidence=[]
    for kind,values in signals.items():
        for ident,keys in values.items():
            keys=sorted(set(keys))
            if len(keys)<2 or len({k.split(":",1)[0] for k in keys})<2:
                continue
            desc={
                "match_type":kind,
                "fingerprint":str(ident)[:160],
                "record_keys":keys[:15],
                "museum_sources":sorted({k.split(":",1)[0] for k in keys}),
                "review_status":"HOLD_CROSS_SOURCE_DUPLICATE_OR_PROVENANCE",
            }
            if kind=="semantic":
                semantic_evidence.append(desc)
            else:
                duplicate_evidence.append(desc)
                for other in keys[1:]:
                    union(keys[0],other)
    clusters=defaultdict(list)
    for k in indexed:
        clusters[find(k)].append(k)
    multi=[sorted(v) for v in clusters.values()
           if len({k.split(":",1)[0] for k in v})>1]
    result={
        "schema_version":1,
        "purpose":"RESEARCH_ONLY__CROSS_SOURCE_FILE_DUPLICATES_AND_PROVENANCE",
        "source_count":len(PROVIDERS),
        "per_museum":per_museum,
        "records_retained_across_museums":len(indexed),
        "exact_file_cluster_count":len(clusters),
        "cross_museum_exact_file_clusters":len(multi),
        "cross_museum_exact_file_cluster_examples":sorted(multi)[:120],
        "exact_match_evidence_count":len(duplicate_evidence),
        "exact_match_evidence":sorted(duplicate_evidence,key=lambda x:(x["match_type"],x["fingerprint"]))[:150],
        "semantic_match_evidence_count":len(semantic_evidence),
        "semantic_match_evidence":sorted(semantic_evidence,key=lambda x:x["fingerprint"])[:150],
        "unique_paintings_proven":False,
        "museum_custody_confirmed":False,
        "catalog_exhaustively_searched":False,
        "commercially_approved":0,
        "runtime_imported":0,
        "license_per_object_review":"REQUIRED",
        "next_step":"Human visual audit and institutional source/licensing verification of shortlisted candidates",
    }
    return result


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--input-dir",type=Path,default=OUT/"imports")
    parser.add_argument("--output",type=Path,default=OUT/"global_cross_museum_dedupe.json")
    args=parser.parse_args()
    reports={}
    report_hashes={}
    for p in PROVIDERS:
        path=args.input_dir/f"{p}.json"
        data=path.read_bytes()
        reports[p]=json.loads(data)
        report_hashes[p]=hashlib.sha256(data).hexdigest()
    result=build(reports)
    result["source_report_sha256"]=report_hashes
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k not in (
        "exact_match_evidence","semantic_match_evidence",
        "cross_museum_exact_file_cluster_examples","per_museum",
        "source_report_sha256")},sort_keys=True,ensure_ascii=False),flush=True)


if __name__=="__main__":
    main()
