# ArtDrift — Integrated P0/P1 + five museal G2 screen components (24 November 2026)

**Scope:** candidate on top of PR #57, which itself is stacked on #55. Do not merge this review-only candidate while image rights/physical/source visual acceptance are unresolved. Factory Core baseline `ede07c491e586215598ff68daec43e17d699aa51`.

## Source reconciliation
- P0 #55: original 4,042 WebPs by immutable Git blob IDs; 1,142 unchanged; 2,900 additional. Cloudflare/D1/635 HOLD untouched.
- P1 #57: 2,400 color-curated real works **only for new installs**; legacy pinned source IDs/camera preserved. 4,500 original artwork IDs unchanged.
- G2 #56: portal and six-language strings added, retaining all new #54 D1 text strings.
- G2 design #40 cherry-picked as isolated ART_ONLY screen changes: **slot 4 detail metadata**, **slot 5 editorial favorites**, **slot 6 search atrium**, **slot 8 curator settings**, **slot 10 next/previous stable walnut frame**, and slot 9 portal from #56. Reference `Design-App/MOCK-STYLE-003` editorial archive/Vintage, ADATTATA; no imported third-party asset.
- The new **search atrium** includes its previously defined local curated collections, initial query persistence, and artist/title/subject filters; the #54 optional Cloudflare D1 discovery button and enabled search flag remain wired, unlike old #40 source.
- Artwork-detail museum frame uses the *same source artwork*, `BoxFit.contain`, true previous/next identity and captions, no fake picture. Favorites retain local data and have individual removal.
- No changes to shared `packages/drift_core`, no camera remap or modifications to GalleryDrift. The G2 canvas-only slots **1 (quiet overlay), 2 (anchored plaque), 3 (tile-origin flight), 7 (auto/speed controls)** remain separate work requiring core surface and consumer QA. This integration is **6/10 SOURCE_IMPLEMENTED** pending Flutter tests/visual.

## Validation
- Flutter analyze, widget tests for portal, favorites, detail and settings + search, Art collections, Web build, Android ARM64 internal APK on this exact source SHA.
- Confirm no D1 search regressions; account sync still opt-in and not integrated into this candidate.
- Compare real mock-ups 320/390/820 dp, keyboard-safe input, text scaling 1.0/1.4+, color/contrast and empty/loading/error states. Verify real-device 60/120 Hz p95, RAM and upgrade signature outside source CI.
- Rights and Pro/Ads gates remain unresolved; do not claim visual/physical approval or Store readiness.
