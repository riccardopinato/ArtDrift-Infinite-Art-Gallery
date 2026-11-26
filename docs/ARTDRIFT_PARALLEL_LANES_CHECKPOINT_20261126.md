# Art Drift — Parallel museum harvest checkpoint
Date: 2026-11-26, Europe/Rome. Research-only; zero runtime/gallery imports.

## Branch layout
Shared engine: [PR #74](https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/pull/74) stacked on [PR #71](https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/pull/71). Nine museum-specific DRAFT PRs, no merge.

| Museum | PR | Latest source sample | Image pixels inspected | Technical color-PASS | Raw first-sweep retained |
|---|---:|---|---:|---:|---|
| Rijksmuseum | #75 | 343 IDs discovered; 260 full records requested; 46 scenic with media | 46 | 2 | previous 57-ID sweep archived |
| Nationalmuseum Stockholm | #76 | rate-limited recheck 500 files; 500 provenance confirmed | 68 | 0 | first sweep 1,306 unique Commons files, 108 images checked, 1 color-PASS |
| Städel | #77 | 58 active LIDO records; 5 scenic/media | 5 | 0 | single run |
| Finnish National Gallery | #78 | 448 Commons file IDs; 438 provenance matches | 90 | 8 | first sweep 591 IDs |
| Birmingham Museums Trust | #79 | rate-limited recheck 500 Commons IDs; 500 source matches | 79 | 9 | first sweep 797 IDs |
| Belvedere | #80 | 441 Commons IDs; 372 source matches | 15 | 1 | first sweep 583 IDs |
| Paris Musées | #81 | 398 Commons IDs; 244 source matches | 19 | 0 | first sweep 597 IDs, unconfirmed files incl. PDFs |
| Te Papa | #82 | 308 Commons IDs; 152 source matches | 4 | 0 | first sweep 307 IDs, includes unrelated false positives |
| Nasjonalmuseet | #83 | 429 Commons IDs; 228 source matches | 90 | 10 | first sweep 429 IDs incl. Finnish false match |

**IMPORTANT** These are counts from distinct limited runs, NOT counts of new unique artworks. The first- and second-sweep numbers MUST NOT be summed. Per-museum technical color-PASS is not a curated image or a commercial approval; some files are older than preferred 1850–1960 period, subject-inappropriate, or have territory/license/provenance HOLD. Cross-museum duplicates not yet resolved. Latest source samples have varying query coverage due to Wikimedia HTTP 429; the first-sweep JSON blobs were deliberately retained on each original branch as `research/museums/20261126/lanes/snapshots/{provider}_first_discovery.json` (except Städel single run). The latest report remains `research/museums/20261126/lanes/results/{provider}.json`.

## Work actually completed
1. Shared metadata-first adapters, bounded safe source clients and source/rights evidence fields built and tested.
2. Nine physically separate source branches and CI workflows, each with a separate GitHub PR and artifacts. Main untouched.
3. Rijks broadened to official creation-date search without title filter: 57 -> 343 discovered source IDs.
4. Nationalmuseum sampled an institutional Commons collection of 1,306 file IDs in first run, rather than a tiny title-only pool. This includes many non-eligible files; it is NOT 1,306 approved paintings.
5. Official Städel OAI + single source lane working, without false 'museum empty'.
6. Each Commons branch separates search hit, museum provenance, supported image MIME, per-file rights, pixel check and aesthetic color tier. Files such as unrelated PDFs are not approved.
7. Preserved first sweep by immutable source-branch commit/blob and an additional snapshot file in each applicable branch. No source data deleted due to rate-limited later runs.
8. Resolved GitHub Actions generated-report add/add rebase race for Nationalmuseum and Birmingham; both reruns ultimately PASS.

## Workflow evidence
- Shared-core QA: https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/45855343896
- Rijks broad run: https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/45855214345
- Nationalmuseum completed rerun: https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/45855937571
- Städel: https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/45854882804
- Finnish: https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/45855396784
- Birmingham: https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/45855752416
- Belvedere: https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/45855390964
- Paris Musées: https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/45855403591
- Te Papa: https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/45855413262
- Nasjonalmuseet: https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/45855418814

## Remaining gates
- Do not retry rate-limited Wikimedia API from all branches at once. Resume only missing query pages with fair-use pacing, backoff, and per-host throttling, preserving previous candidate IDs.
- Compare first snapshot and latest source IDs; implement deterministic idempotent union and dedupe before claiming complete scans.
- Use authoritative museum object IDs and page-level rights rather than assuming Commons search query confirms museum custody.
- Separate colors from aesthetics: visualize near-misses, reject portraits/monochrome/people-centred files, check 1850–1960 and per-image provenance; keep 15%-20% darkness policy.
- Validate cross-museum duplicates (same work/photograph), licensing/territories, author and attribution.
- Only after these steps admit any image to catalog assets; currently 0 approved and 0 runtime imports.

This is a research checkpoint, not a certificate of exhaustive discovery or ready-to-merge application changes.
