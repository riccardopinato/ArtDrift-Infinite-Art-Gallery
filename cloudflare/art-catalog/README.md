# Art Drift — Unified D1 museum catalog / MoMA P1 staging

Status: CODE + LOCAL SQL PREPARATION ONLY. No Cloudflare remote import,
Worker production deployment or R2 image upload occurs automatically.

This integration is based on PR #42 (5,084 existing catalog records) and
PR #28 (the initial Cloudflare MoMA Worker). The app canvas, Supabase
favorites, local image pack and Google login remain unchanged.

## Architecture

- D1 museum_works + museum_works_fts: source-traceable, searchable copy of
  5,084 gallery and museum records; source_key retains source:id identity.
- D1 works + works_fts: MoMA metadata-only P1, currently NOT imported.
  All 161,038 full-catalog SQL shards are EXCLUDED from the migration.
- Worker: read-only, input-bounded and paginated API, 24 results per page.
- R2: reserved for separately rights-cleared thumbnails; no MoMA image.
- Supabase: optional Google sign-in and owner-specific favorite sync ONLY.

## Read-only API

- GET /health: Worker configuration, NOT evidence D1 is populated
- GET /api/v1/museums: institution names and record counts
- GET /api/v1/museum-search?q=...&scope=all&cursor=0: indexed museum search
- GET /api/v1/search?q=...: MoMA P1 when approved and imported
- GET /api/v1/works/:id: MoMA metadata detail

## Reproducible local preparation (no cloud writes)

From repository root:

    node --test cloudflare/art-catalog/test/*.test.mjs
    python3 -m unittest discover -s cloudflare/art-catalog/scripts -p 'test_*.py' -v
    python3 cloudflare/art-catalog/scripts/make_museum_d1_import.py --root . --out build/d1-museums --expected 5084 --chunk 200

The GitHub Action prepares the same temporary SQL shards as an INTERNAL
review artifact. It does not issue Cloudflare requests and never builds MoMA
SQL from the full source.

## Cloudflare target registered (23 November 2026)

The Cloudflare D1 console URL supplied by the owner contains the database UUID
`4e7cb3bf-bf3c-480d-9789-93072e70274c`; this exact ID is now pinned
in `wrangler.jsonc` with the pre-existing expected database name
`artdrift-moma-cc0`. **The URL itself is not authenticated API access:**
name, account ownership, schema, table contents and environment are not yet
independently verified. Before touching remote D1, inspect the dashboard and
confirm that the displayed database name matches the Wrangler configuration.

Safe read-only D1 Console inspection:

```sql
SELECT type, name FROM sqlite_master
WHERE type IN ('table','view')
ORDER BY type, name;
```

If tables exist, review whether `works`, `museum_works` and their FTS
indexes contain data before planning migrations. **Do not run an import or
`wrangler deploy` based on the URL alone.** No account ID, API token or
Cloudflare secret is stored in this repository.

## Safe 5,084-record import from the owner's Windows PC

The D1 console was checked by the owner: works=0, works_fts=0, and
museum_works=0 after adding the non-destructive museum schema. The SQL
shards have been updated for Cloudflare's Wrangler import syntax (no
explicit BEGIN TRANSACTION or COMMIT). Direct CLI login happens only in
the owner's browser, never in ChatGPT.

Run in PowerShell from a checkout of this exact feature branch:

    git checkout feat/artdrift-d1-unified-catalog-20261123
    cd cloudflare/art-catalog
    npm install
    npx wrangler login
    cd ../..
    py cloudflare/art-catalog/scripts/import_museum_remote.py

The default Python operation is **read-only on Cloudflare**. It validates
all 5,084 local source records, rerenders 26 SQL files, checks the active
Cloudflare account for D1 UUID `4e7cb3bf-bf3c-480d-9789-93072e70274c`
and expected name `artdrift-moma-cc0`, then confirms both MoMA and
museum counts/indexes remain zero. **If any check fails, do not import.**

After reviewing the preflight result and D1 Free row-write quota, the
owner can explicitly start the import on that exact database ID:

    py cloudflare/art-catalog/scripts/import_museum_remote.py --apply --confirm-id 4e7cb3bf-bf3c-480d-9789-93072e70274c

The script captures a D1 Time Travel bookmark in
`build/d1-museums/preimport-time-travel.json` before writing, runs the 26
SQL shards sequentially, and checks remote row count after each shard.
Each failure stops immediately. It never imports MoMA and never writes
to Supabase or R2. Save the bookmark; Time Travel's retention is limited.
Do not share API tokens or OAuth credentials in chat.

On success it should say: `D1_REMOTE_IMPORT_SUCCESS 5084 museum works,
5084 FTS entries, MoMA unchanged.` Verify again in the D1 dashboard with:

    SELECT (SELECT COUNT(*) FROM museum_works) AS museums,
           (SELECT COUNT(*) FROM museum_works_fts) AS museum_fts,
           (SELECT COUNT(*) FROM works) AS moma;

Expected: museums=5084; museum_fts=5084; moma=0.

A *successful D1 data import does not deploy the Worker or turn on the
D1 cloud search button in Flutter*. Those are separate gated steps.
Official Wrangler instructions:
https://developers.cloudflare.com/d1/wrangler-commands/

## Controlled activation — explicit owner approval required

Verify the real Cloudflare account, D1 database ID and prior migrations.
Apply schema.sql and museum_schema.sql to an ISOLATED TEST D1 only after
review. Import museum-NNNN.sql shards in numeric order with Wrangler and
inspect the final count, search latency, license data and daily quota.
No production changes are authorized by preparation alone.

Example command only, NOT executed by CI:

    cd cloudflare/art-catalog
    npx wrangler d1 execute artdrift-moma-cc0 --remote --file=./museum_schema.sql

Avoid duplicate database creation; do not commit Wrangler credentials.
Cloudflare Free D1 daily limits are enforced, and FTS/index writes increase
row-write usage. Official docs:
https://developers.cloudflare.com/d1/platform/pricing/

## MoMA P1 hold

The prior 161,038-row importer is now fail-closed. It requires a reviewed
JSON array of exactly 15,294 P1 MoMA ObjectIDs:

    python3 cloudflare/art-catalog/scripts/make_d1_import.py --input Artworks.csv --out build/moma-p1 --allowlist approved-p1-ids.json --approved-count 15294

This allowlist is NOT committed yet. No MoMA D1 import is ready. The MoMA
CSV SHA256 and source-commit check remain mandatory; source metadata CC0
does NOT grant rights to the artwork images.

## Flutter release gate

Museum D1 browsing is opt-in via build-time HTTPS
ARTDRIFT_CATALOG_API_BASE. The MoMA P1 button additionally requires
ARTDRIFT_ENABLE_MOMA_P1=true after P1 deployment. Without either, the
offline-first gallery and user favorites behave exactly as before.

Pending: D1 live upload/test, Cloudflare Worker staging deployment,
remote image delivery on devices, source-specific commercial rights QA,
load and quota tests, and optional real account tests. No main merge,
no production deploy and no R2 photo publication at this stage.
