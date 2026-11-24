# Museum-only release candidate — Art Drift

**Scope:** Backend/data and evidence only. Branch from verified `main` at `2dac51a6be98ed364d1e95983d1f330c84354ef7`, not from PR #41/#42/#43/#45. The release candidate deliberately excludes Google account, favorites synchronization, G2 UI, Flutter canvas and any other stacked UI changes.

Included:
- Current main contains 4,500 existing museum works (one more than the historical stacked #43 baseline) plus 585 candidates (558 Smithsonian and 27 Commons), for 5,085 original catalog records; validated using the exporter from PR #43.
- Existing Worker read-only API and approved-only D1 endpoint with a `NOT EXISTS` guard against duplicated Cleveland native museum IDs.
- The D1 `artdrift_museum_ingest` schema, original rights audit tools, 28 proposed Cleveland full-image fixes, fingerprint and reconciliation checks. **No SQL to apply these fixes is run remotely.**
- 535 independently staged rows (233 Tate, 253 MoMA, 49 Cleveland) remain in the **already existing remote D1**, not bundled as a new import. All 535 remain HOLD, zero approved; the 49 Cleveland rows overlap with the 5,085 catalog, giving a provisional 5,571 distinct identities only if the additional main record is not already among the 535 staged entries; verify independently.
- Local-only CI for 5,085 source rows, Worker, D1 schema, SQL exporter and rights tools. No Cloudflare deployment, `wrangler d1 execute`, OAuth secrets, API keys or image download.

**Not included:** `lib/**` Flutter integration, changes to `pubspec.yaml`, `lib/main.dart`, user accounts, Supabase, Google sync, G2 UX, remote D1 write operations, R2 uploads, public canvas activation. The 585 works in JSON are source data and are **not yet registered as Flutter bundled assets** in this independent branch. No user-visible new art is claimed.

**Before merging to main:** verify all tests, licensing and provenance, independent worker runtime behavior with both D1 schemas and the existing deployment configuration. Do not deploy Worker or enable any UI flag as a side effect of this PR. A separate Flutter museum-only UI integration is required for app visibility.

**Review dependencies:** supersedes only museum data/infra changes from #42, #43 and #45; not the full stacked PRs. Preserve #44 as audit of real D1 import, do not merge it separately.

## Independent CI baseline reconciliation
The first independent CI failed closed on a real baseline difference: current `main` has **4,500** pre-existing catalog entries rather than the **4,499** in stacked PR #43. Therefore 4,500 + 585 = **5,085** source records. The count gate was updated without removing the extra original artwork. Cross-table dedup against the 535 remote staged entries must be rechecked on this baseline before asserting a final distinct total. No Cloudflare writes were performed.
