# Art Drift v0.3.8 — QA candidate, no design changes (23 November 2026)

This QA-only branch starts from Art Drift PR #34 commit
`c89d426bb1c4129271df130f5ce18f35710273e4`.
It does not modify the approved canvas colors, layout, artwork mapping,
widget tree, Drift Core or Gallery Drift.

## Evidence already present at the parent candidate SHA
- Android analyze + Flutter test + internal ARM64 APK:
  https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/45097133021
- Visual selection integrity:
  https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/45097133006
- PR #33 verified 4,499 source records, including 4,042/4,042 matching museum WebPs:
  https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/pull/33
- PR #34 2,400 selected images and heuristic portrait rebalancing; NOT in main:
  https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/pull/34

## QA-only additions
The existing emulator lane is now exercised on the candidate source by a dedicated
branch. The smoke attempts an offline first launch with airplane mode and disabled
Wi-Fi/data, preserves initial and post-pan screenshots, performs exactly 48 swipes,
records process/PSS/gfxinfo, and fails if process or screenshot artifacts are missing
or a fatal exception appears. The JSON report explicitly leaves uncollected FPS and
visual review as NOT_VERIFIED. This does not constitute an Android physical benchmark.

## Outstanding acceptance gates
| Check | Current evidence | Status |
| --- | --- | --- |
| Source integrity and Android build | Exact candidate SHA CI | PASS |
| Curated 2,400 image IDs | Exact candidate SHA automated gates | PASS |
| Emulator first-launch offline and 48 gestures | This QA branch GitHub workflow | PENDING |
| Visual review of actual screenshots | Inspect generated before/after PNG | NOT_VERIFIED |
| Real Android fast pan/zoom, p95/p99, RAM, battery/thermal | Actual phone | NOT_VERIFIED |
| In-place update from installed APK | Same package, signing fingerprint, versionCode, real device | BLOCKED: stable key continuity |
| Commercial art-image redistribution rights | Per-item/provider legal review | NOT_CLEARED |
| Merge of stacked PRs | Separate exact-head CI, approvals and above gates | ON_HOLD |

Do not mark the app PHYSICALLY_ACCEPTED or PLAY_READY from an emulator PASS.
No artwork assets, data schema, UI design or camera mapping changed in this branch.
