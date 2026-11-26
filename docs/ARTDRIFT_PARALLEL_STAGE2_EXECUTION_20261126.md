# Art Drift — Stage 2 execution checkpoint (26 November 2026)

## Completed and checked
- Per-museum result preservation: 9/9 independent workflows PASS. Each uses
  `tools/artdrift_parallel_museum_reconcile.py` and an offline visual HOLD queue.
- Source crashes/rate-limited or incomplete replay cannot erase previous file IDs,
  measured pixel hashes or retained source evidence. Strict `commercially_approved=0`.
- Commons API uses a resumable `query_progress` cursor and stops requesting
  the host after HTTP 429; this was verified via offline tests and one controlled
  Finnish replay, not merely specified as a plan.
- Global source audit: **4,256 retained research records** from nine branches,
  **11 exact cross-museum file clusters** (4,245 provisional file clusters).
  These are not verified unique paintings, not proven museum custody.
- Latest independent Rijks source run: **343** distinct search IDs;
  **53** scenic/media candidates after full metadata analysis, versus 46
  earlier; **2** automatic color PASS. 2 malformed API object payloads are
  recorded as errors, not silently counted as absent works.
- Finnish controlled replay: HTTP 429 occurred after partial Commons scan;
  preserved **591** distinct museum research candidates, **9** technical color
  PASS in cumulative evidence. Recorded the exact continuation cursor for
  `Ateneum landscape` at `gsroffset=150`, so a later permitted source
  run can continue rather than rerequest pages 0–149. This does not certify
  the result as Finnish museum-owned or rights-cleared.
- Städel OAI `scope:major` ListIdentifiers: **1,040 active OAI identifiers**,
  **601 deleted headers**, **4 pages**, no fetch errors, fully exhausted
  the *set iteration* (not the whole museum) with no images downloaded.
  Expanded official-source study now has a second workflow for a bounded,
  stratified GetRecord subset. No release-rights clearance.

## GitHub evidence
- Core: https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/pull/74
- Nine isolated PRs: #75 through #83.
- Global exact-file audit: https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/blob/research/artdrift-parallel-harvest-core-20261126/research/museums/20261126/lanes/global_cross_museum_dedupe.json
- Global dedup CI: https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/45858479966
- Rijks incremental source CI: https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/45859048571
- Finnish rate-limit-protected CI: https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/45859073058
- Städel OAI identifier preflight: https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/45859496688
- Städel stratified metadata research: https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/45859723699

## Follow-ups — DO NOT MISSTATE
- All Commons results need institution validation beyond title and search;
  metadata provenance can still be misleading, even for a category.
- No license, copyright territory, period or visual approval is implied by
  a tech color PASS, Commons PD label or metadata retrieval.
- Don't sum raw source hits; use exact file/hash clusters and separately review
  semantic artwork duplicates.
- Exclude accidental PDF, decorative scans, people-centred images and artist
  birth dates mistaken for artwork dates.
- Throttle per host. For Commons, resume missing cursors only when host permits.
- Städel per-image downloads require independent attribution/CC BY-SA assessment.
- No PR merge, no app runtime import, no APK change, no publication.

Official Städel docs:
https://sammlung.staedelmuseum.de/en/oai/guide
https://sammlung.staedelmuseum.de/en/concept
