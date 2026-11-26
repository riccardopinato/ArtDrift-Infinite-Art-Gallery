#!/usr/bin/env python3
"""Second-pass evidence-only retry for 39 Commons 429s from Art Drift QA run 45905782588.

The first-pass 447 pixel successes are preserved. No new legal/publication
approvals, no app/runtime changes, no provider-bypass behavior.
"""
from __future__ import annotations

import argparse
import collections
import csv
import json
import time
from pathlib import Path
import artdrift_486_parallel_gate as gate

FIRST_RUN_ID = 45905782588
FIRST_PASS_COUNT = 486
FIRST_PASS_OK = 447
FIRST_PASS_429 = 39
WORKERS = 2


def read_initial(csv_path: Path, expected_count: int = FIRST_PASS_COUNT):
    with csv_path.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    identities = [x.get("source_identity") for x in rows]
    if len(rows) != expected_count or len(set(identities)) != expected_count or any(not x for x in identities):
        raise ValueError("Initial 486-image report is truncated or duplicated")
    for x in rows:
        if x["result"] not in ("PIXELS_OK_RIGHTS_AND_VISUAL_HOLD", "HOLD_TECHNICAL"):
            raise ValueError("Unrecognized first-pass status")
    return rows


def pending_ids(rows, expected_429: int = FIRST_PASS_429):
    pending = {x["source_identity"] for x in rows
               if x["result"] == "HOLD_TECHNICAL" and x["error"] == "HTTP_429"}
    any_hold = {x["source_identity"] for x in rows if x["result"] == "HOLD_TECHNICAL"}
    success = len(rows) - len(any_hold)
    if pending != any_hold or len(pending) != expected_429 or (
            len(rows) == FIRST_PASS_COUNT and success != FIRST_PASS_OK):
        raise ValueError("Unrecognized failed-image set; stop instead of rechecking approved pixels")
    return pending


def check_inventory(inventory, ids):
    source = {r["source_identity"]: r for r in inventory}
    if not ids.issubset(source) or len(source) != len(inventory):
        raise ValueError("First-pass records not reconciled against source pin")
    return source


def run_worker(queue, first_pass, worker, out: Path, *,
               workers: int = WORKERS, do_download: bool = True):
    ids = pending_ids(first_pass)
    source = check_inventory(queue, ids)
    subset = [source[k] for k in sorted(ids) if gate.shard_of(k, workers) == worker]
    rows = []
    out.mkdir(parents=True, exist_ok=True)
    for i, record in enumerate(subset):
        if do_download:
            # Sequential per worker, pace requests even when Commons is healthy.
            if i:
                time.sleep(2.5)
            check, _ = gate.assess(record)
        else:
            check, _ = gate.assess(record, download=lambda url: (_ for _ in ()).throw(RuntimeError("OFFLINE_TEST")))
        check["first_pass_status"] = "HOLD_TECHNICAL"
        check["first_pass_error"] = "HTTP_429"
        check["retry_run_source"] = FIRST_RUN_ID
        check["commercially_approved"] = False
        check["runtime_visible"] = False
        rows.append(check)
        print(json.dumps({"identity": check["source_identity"],
                          "result": check["result"], "error": check.get("technical_error")},
                         ensure_ascii=False), flush=True)
    report = {
        "worker": worker, "workers": workers,
        "first_pass_count": FIRST_PASS_COUNT,
        "first_pass_pixel_successes_untouched": FIRST_PASS_OK,
        "first_pass_http429_count": FIRST_PASS_429,
        "processed": len(rows),
        "rows": rows,
        "commercially_approved": 0, "runtime_imported": 0
    }
    (out / ("retry_%02d.json" % worker)).write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    return report


def merge(first_pass, queue, directory: Path, out: Path, workers: int = WORKERS):
    failed = pending_ids(first_pass)
    check_inventory(queue, failed)
    recovered = {}
    seen = set()
    for worker in range(workers):
        obj = json.loads((directory / ("retry_%02d.json" % worker)).read_text(encoding="utf-8"))
        if obj["worker"] != worker or obj["workers"] != workers or obj["commercially_approved"] != 0:
            raise ValueError("Invalid worker report or unsafe approval")
        if obj["processed"] != len(obj["rows"]):
            raise ValueError("Truncated retry report")
        for r in obj["rows"]:
            key = r["source_identity"]
            if key in seen or key not in failed or gate.shard_of(key, workers) != worker:
                raise ValueError("Duplicate or unexpected record in retry")
            if r.get("commercially_approved") is not False or r.get("runtime_visible") is not False:
                raise ValueError("Unapproved image has been promoted")
            seen.add(key)
            recovered[key] = r
    if seen != failed:
        raise ValueError("Second pass did not cover all 39 failed identities")
    recovered_ok = sum(r["result"] == "PIXELS_OK_RIGHTS_AND_VISUAL_HOLD" for r in recovered.values())
    unverified = sorted(x for x,r in recovered.items() if r["result"] != "PIXELS_OK_RIGHTS_AND_VISUAL_HOLD")
    summary = {
        "schema_version": 1, "first_pass_run_id": FIRST_RUN_ID,
        "original_total": FIRST_PASS_COUNT,
        "first_pass_technical_ok": FIRST_PASS_OK,
        "rate_limited_to_retry": FIRST_PASS_429,
        "retry_evidence_rows": len(recovered),
        "newly_recovered_technical_ok": recovered_ok,
        "combined_technical_ok": FIRST_PASS_OK + recovered_ok,
        "combined_technical_hold": len(unverified),
        "remaining_unresolved_identities": unverified,
        "commercially_approved": 0,
        "runtime_imported": 0,
        "legal_rights_review": "HOLD_PER_ITEM_TERRITORY",
        "human_visual_review": "HOLD",
    }
    if summary["combined_technical_ok"] + summary["combined_technical_hold"] != FIRST_PASS_COUNT:
        raise ValueError("Total image count changed unexpectedly")
    out.mkdir(parents=True, exist_ok=True)
    (out / "retry_summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (out / "retry_per_item.json").write_text(json.dumps([recovered[k] for k in sorted(recovered)],ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False), flush=True)
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--initial-csv", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--worker", type=int)
    parser.add_argument("--workers", type=int, default=WORKERS)
    parser.add_argument("--merge-from", type=Path)
    args = parser.parse_args()
    inventory = gate.read_queue(args.inventory)
    initial = read_initial(args.initial_csv)
    if args.merge_from is not None:
        merge(initial, inventory, args.merge_from, args.out, args.workers)
    else:
        if args.worker is None or not 0 <= args.worker < args.workers:
            parser.error("--worker must be within --workers")
        run_worker(inventory, initial, args.worker, args.out, workers=args.workers)


if __name__ == "__main__":
    main()
