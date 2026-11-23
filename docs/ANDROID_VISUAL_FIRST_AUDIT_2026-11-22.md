# Art Drift — audit closure ledger, Android visual-first (22 Nov 2026)

Source baseline: ArtDrift main `586b3009308d7b09883f63a4dd80cdae208712c5`;
App Factory Core main `ede07c491e586215598ff68daec43e17d699aa51`.
Branch: `feat/artdrift-android-visual-first-20261122`.
Canonical shared Drift Core unchanged; GalleryDrift remains pinned independently.
This document records scope and evidence, not physical or legal certification.

## Goal and actual rendering policy
Android is the priority platform. A freshly installed client reads 457 original
packaged artwork thumbnails and the existing 1,142 verified small WebP museum
thumbnails from the same Flutter bundle. The canvas uses only artworks with a
real local image on normal zoom (no metadata-only blank tiles); remote-only
artworks remain in the complete 4,500-item search/detail catalog.
The existing 48 MiB decoded-image RAM bound, viewport culling and the 3-concurrent
prefetch queue remain active. Deep zoom can request the official larger image
while keeping the exact artwork's local preview visible.
The packaged 1,142 additional WebPs occupy about 5.05 MB raw (compressed APK
size must be measured, not inferred). No new paid or proxy service is used.

The on-device artwork sequence is pinned by catalogKey in shared preferences:
the shared core maps world positions by list index modulo list length.
This prevents a newly added artwork/thumbnail from reshuffling previously
observed locations. It also means an existing installation deliberately does
not discover newly previewed items in its mosaic automatically; search still
finds them. Permanent global ID-stable consistent hashing is future shared
core work requiring paired GalleryDrift validation.

## Audit item matrix
| ID | Category | Status after scoped PR | Remaining acceptance gate |
| --- | --- | --- | --- |
| AD-01 | ART_ONLY | PARTIAL: reused 1,142 existing extra WebP images | Generate/review missing 2,901; source and rights checks |
| AD-02 | ART_ONLY | SOURCE_IMPLEMENTED: Android bundles real WebPs; visual-first canvas | Android build and physical fast-scroll/offline acceptance |
| AD-03 | ART_ONLY | NOT CERTIFIED: source provenance static gate only | Museum-by-museum commercial distribution and artwork/image legal review |
| AD-04 | ART_ONLY | PARTIAL: same-work local fallback, preserved visible retry | Verify real 403/CORS/outage telemetry and providers |
| AD-05 | ART_ONLY workaround + SHARED_CORE long-term | SOURCE_IMPLEMENTED: persisted artwork-ID playlist on Android | Exact-head CI and upgrade test; shared consistent-hash solution later |
| AD-06 | ART_ONLY | NOT ADDRESSED by performance PR | Search relevance/subject/filters dataset and UX validation |
| AD-07 | SHARED_CORE + device | NOT MEASURED | Real device frame timing FPS/p95/jank, RAM, offline+3G tests |
| AD-08 | ART_ONLY release | NOT CERTIFIED | Stable signed workflow, correct keystore/cert, update-in-place physical test |
| AD-09 | ART_ONLY | NOT ADDRESSED | Curation and collections UX/rights sign-off |
| AD-10 | ART_ONLY | NOT ADDRESSED | Editorial standard, translations and per-work quality checks |

## Fail-closed controls
- `scripts/verify_mobile_thumbnail_pack.py` checks manifest identity, file
  existence, RIFF/WebP headers, bounded size and associated source claims.
  It does **not** establish legal rights or actual image visual fidelity.
- Tests cover new Android asset-bundle access and pinned canvas identities.
- CI must pass exact integrated head SHA before merge; draft PR otherwise.
- Physical benchmarks target at least entry-level Android and midrange Xiaomi:
  cold start; 60s normal and fast pan; repeat after app restart; LTE/slow/offline;
  sustained zoom; 200% system font; rotate; peak image RAM; frame p90/p95/p99,
  long frames/jank, dropped frames, visible-empty-image ratio and battery heat.
- Not a store release, not a promise of zero failed image requests. The canvas
  guarantees real local previews for its fresh-install selected set as long
  as the bundle passes the static/runtime tests.
- Never replace an artwork with a different artwork as a placeholder.
