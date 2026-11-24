# Museum-only release candidate — Art Drift

**Scope:** Backend/data and evidence only. Branch from verified `main` at `2dac51a6be98ed364d1e95983d1f330c84354ef7`, not from PR #41/#42/#43/#45. The release candidate deliberately excludes Google account, favorites synchronization, G2 UI, Flutter canvas and any other stacked UI changes.

Included:
- Existing 4,499 museum works plus 585 candidates (558 Smithsonian and 27 Commons), for 5,084 original catalog records; validated using the exporter from PR #43.
- Existing Worker read-only API and approved-only D1 endpoint with a `NOT EXISTS` guard against duplicated Cleveland native museum IDs.
- The D1 `artdrift_museum_ingest` schema, original rights audit tools, 28 proposed Cleveland full-image fixes, fingerprint and reconciliation checks. **No SQL to apply these fixes is run remotely.**
- 535 independently staged rows (233 Tate, 253 MoMA, 49 Cleveland) remain in the **already existing remote D1**, not bundled as a new import. All 535 remain HOLD, zero approved; the 49 Cleveland rows overlap with the 5,084 catalog, giving 5,570 distinct source/native identities when both datasets are reconciled.
- Local-only CI for 5,084 source rows, Worker, D1 schema, SQL exporter and rights tools. No Cloudflare deployment, `wrangler d1 execute`, OAuth secrets, API keys or image download.

**Not included:** `lib/**` Flutter integration, changes to `pubspec.yaml`, `lib/main.dart`, user accounts, Supabase, Google sync, G2 UX, remote D1 write operations, R2 uploads, public canvas activation. The 585 works in JSON are source data and are **not yet registered as Flutter bundled assets** in this independent branch. No user-visible new art is claimed.

**Before merging to main:** verify all tests, licensing and provenance, independent worker runtime behavior with both D1 schemas and the existing deployment configuration. Do not deploy Worker or enable any UI flag as a side effect of this PR. A separate Flutter museum-only UI integration is required for app visibility.

**Review dependencies:** supersedes only museum data/infra changes from #42, #43 and #45; not the full stacked PRs. Preserve #44 as audit of real D1 import, do not merge it separately.
