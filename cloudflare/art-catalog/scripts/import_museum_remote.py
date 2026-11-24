#!/usr/bin/env python3
"""Art Drift: verify (default) or import 5,084 museum metadata rows into D1.

Usage from the repo root after Wrangler's browser authentication:
  python cloudflare/art-catalog/scripts/import_museum_remote.py
  python cloudflare/art-catalog/scripts/import_museum_remote.py --apply \
      --confirm-id 4e7cb3bf-bf3c-480d-9789-93072e70274c

NEVER obtains secrets from ChatGPT or commits them. Cloudflare writes are
possible only with --apply + the exact full D1 UUID. No MoMA/R2 activity.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

WORKER = Path(__file__).resolve().parents[1]
ROOT = WORKER.parents[1]
DATABASE_ID = "4e7cb3bf-bf3c-480d-9789-93072e70274c"
DATABASE_NAME = "artdrift-moma-cc0"
EXPECTED = 5084
SHARDS = 26


def json_result(raw: str):
    # Wrangler's --json mode should emit JSON alone. Fail closed otherwise.
    try:
        return json.loads(raw.strip())
    except (ValueError, TypeError) as exc:
        raise RuntimeError("Wrangler JSON response was not parseable; no import performed") from exc


def find_rows(obj):
    """Extract D1 row objects, supporting Wrangler's list/result wrappers."""
    if isinstance(obj, list):
        for part in obj:
            yield from find_rows(part)
    elif isinstance(obj, dict):
        if isinstance(obj.get("results"), list):
            for row in obj["results"]:
                if isinstance(row, dict):
                    yield row
        elif "result" in obj:
            yield from find_rows(obj["result"])


def safe_count(raw: str, expected_field: str) -> int:
    data = json_result(raw)
    matches = [r[expected_field] for r in find_rows(data) if expected_field in r]
    if len(matches) != 1 or type(matches[0]) is not int or matches[0] < 0:
        raise RuntimeError(f"Unexpected D1 count response for {expected_field}")
    return matches[0]


def check_config():
    config = json.loads((WORKER / "wrangler.jsonc").read_text("utf-8"))
    databases = config.get("d1_databases") or []
    matches = [x for x in databases if x.get("binding") == "CATALOG_DB"]
    if len(matches) != 1 or matches[0].get("database_id") != DATABASE_ID \
            or matches[0].get("database_name") != DATABASE_NAME:
        raise RuntimeError("Wrangler D1 binding/ID mismatch; no import")
    return True


def wrangler(*args, as_json=False):
    cli = shutil.which("npx")
    if not cli:
        raise RuntimeError("Node.js/npm/npx required. No remote changes made")
    command = [cli, "--no-install", "wrangler", *args]
    if as_json:
        command.append("--json")
    result = subprocess.run(command, cwd=WORKER, capture_output=True,
                            text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        # Never reveal command output that could contain provider credentials.
        raise RuntimeError("Wrangler command failed; status="
                           + str(result.returncode) + ", action=" + args[0])
    return result.stdout


def cloud_inventory():
    raw = json_result(wrangler("d1", "list", as_json=True))
    dbs = raw if isinstance(raw, list) else raw.get("result", [])
    if not isinstance(dbs, list):
        raise RuntimeError("Unexpected D1 inventory shape")
    matching = [x for x in dbs if isinstance(x, dict) and
                (x.get("uuid") or x.get("id")) == DATABASE_ID]
    if len(matching) != 1 or matching[0].get("name") != DATABASE_NAME:
        raise RuntimeError("Target Cloudflare account/database name mismatch")
    return True


def remote_count(table: str) -> int:
    if table not in ("museum_works", "museum_works_fts", "works", "works_fts"):
        raise ValueError("Unexpected table")
    sql = f"SELECT COUNT(*) AS n FROM {table};"
    return safe_count(
        wrangler("d1", "execute", "CATALOG_DB", "--remote",
                 "--command", sql, as_json=True),
        "n",
    )


def source_shards(out: Path):
    run = subprocess.run([
        sys.executable, str(WORKER / "scripts" / "make_museum_d1_import.py"),
        "--root", str(ROOT), "--out", str(out),
        "--expected", str(EXPECTED), "--chunk", "200",
    ], cwd=ROOT, capture_output=True, text=True)
    if run.returncode != 0:
        raise RuntimeError("Local museum rights/duplicate validation failed")
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    if (manifest.get("records") != EXPECTED or
            len(manifest.get("shards") or []) != SHARDS or
            manifest.get("d1_remote_import") != "REQUIRES_EXPLICIT_APPROVAL" or
            manifest.get("images_bundled") != 0 or
            manifest.get("personal_data") is not False):
        raise RuntimeError("D1 review manifest mismatch")
    result = []
    for shard in manifest["shards"]:
        filename = shard.get("filename")
        if not isinstance(filename, str) or not re.fullmatch(
                r"museum-[0-9]{4}[.]sql", filename):
            raise RuntimeError("Unsafe SQL shard filename")
        sqlfile = out / filename
        contents = sqlfile.read_text(encoding="utf-8")
        # Check only statement boundaries: titles legitimately contain words
        # like "Drop" or "Update" and must not trigger false SQL alarms.
        if re.search(r"(?m)^[ \t]*(BEGIN[ ]+TRANSACTION|COMMIT|DROP|DELETE|UPDATE|ATTACH)\s*;",
                     contents, re.I):
            raise RuntimeError("Unsafe D1 SQL statement in " + filename)
        n = contents.count("INSERT OR IGNORE INTO museum_works ")
        if n != shard.get("records") or n < 1 or n > 200:
            raise RuntimeError("Invalid SQL row count in " + filename)
        result.append((sqlfile, n))
    if len(result) != SHARDS or sum(n for _, n in result) != EXPECTED:
        raise RuntimeError("Invalid museum source cardinality")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true",
        help="Actually import into the owner's remote D1; otherwise read-only.")
    parser.add_argument("--confirm-id", default="",
        help="Must be the exact target UUID for --apply.")
    args = parser.parse_args()
    check_config()
    if args.apply and args.confirm_id != DATABASE_ID:
        raise RuntimeError("--apply requires --confirm-id " + DATABASE_ID)
    out = ROOT / "build" / "d1-museums"
    shards = source_shards(out)
    cloud_inventory()
    existing = remote_count("museum_works")
    index = remote_count("museum_works_fts")
    works = remote_count("works")
    works_index = remote_count("works_fts")
    if (existing, index, works, works_index) != (0, 0, 0, 0):
        raise RuntimeError("Remote database is no longer empty as verified; "
                           "stop rather than overwriting/duplicating data")
    print(f"D1_PREFLIGHT_PASS: UUID={DATABASE_ID}; MoMA=0; "
          f"museums=0; shards={len(shards)}; records={EXPECTED}", flush=True)
    if not args.apply:
        print("READ_ONLY_DONE. No Cloudflare records changed.")
        return

    # Record a recovery bookmark before writing; Time Travel is not an
    # unlimited-duration external backup and must not be assumed to be one.
    bookmark_raw = wrangler("d1", "time-travel", "info", "CATALOG_DB",
                           as_json=True)
    bookmark = json_result(bookmark_raw)
    if not bookmark:
        raise RuntimeError("D1 recovery bookmark unavailable; import blocked")
    bookmark_path = out / "preimport-time-travel.json"
    bookmark_path.write_text(json.dumps(bookmark, indent=2) + "\n", "utf-8")
    print("D1_RECOVERY_BOOKMARK_RECORDED: " + str(bookmark_path), flush=True)

    expected_rows = 0
    for i, (sql_path, count) in enumerate(shards, start=1):
        wrangler("d1", "execute", "CATALOG_DB", "--remote",
                 "--file", str(sql_path), "--yes")
        expected_rows += count
        actual = remote_count("museum_works")
        if actual != expected_rows:
            raise RuntimeError(f"Stopped after shard {i}: count={actual}, "
                               f"expected={expected_rows}")
        print(f"D1_IMPORT_SHARD_OK {i}/{SHARDS} rows={actual}", flush=True)

    final_index = remote_count("museum_works_fts")
    final_moma = remote_count("works")
    if final_index != EXPECTED or final_moma != 0:
        raise RuntimeError("Post-import index/MoMA integrity check failed")
    print(f"D1_REMOTE_IMPORT_SUCCESS {EXPECTED} museum works, "
          f"{final_index} FTS entries, MoMA unchanged.", flush=True)


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, ValueError) as exc:
        print("D1_IMPORT_BLOCKED: " + str(exc), file=sys.stderr)
        raise SystemExit(1)
