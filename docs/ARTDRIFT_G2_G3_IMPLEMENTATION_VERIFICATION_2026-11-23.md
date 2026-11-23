# Art Drift — G2 implementation / G3 evidence ledger

**Snapshot:** 23 November 2026 · **state: G2 CI GREEN, G3 PENDING VISUAL APPROVAL; G4/G5 NOT CERTIFIED**.

This file records the actual implementative work following the 10/10 approved
design mock-ups. It is **not** an authorization to publish, deploy over an
installed app, merge a stacked branch or call physical-device QA complete.

## 1. Canonical vs staged branches

| Branch or PR | Exact commit | Verification |
| --- | --- | --- |
| Canonical Art Drift `main` | `2dac51a6be98ed364d1e95983d1f330c84354ef7` | Untouched; v0.3.5+8 |
| Underlying candidate PR #35 | `c2d1d3e91cef0cee3005a0fdda151ff34ac903e9` | v0.3.8+11, stacked over #34/#33; unmerged |
| #37 — curator UI / search / favorites / portal | `57410a79ca270a804b76909cc86b6d812982ccd4` | [Android CI run 45176842553](https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/45176842553), **SUCCESS** |
| #38 — detail walnut frame + artwork tour | `67113f99a05ff97af973f70c50f68757ff70cb57` | [Android CI run 45177126583](https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/45177126583), **SUCCESS** |
| #39 — opt-in Core, quiet canvas/long press/Auto controls | `70e4f4352836d2f39e9c81b60da421640d004d46` | [Android CI run 45178068261](https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/45178068261), **SUCCESS** |
| #40 — integration including origin flight | `054a951d9639b3120e2f87a0b1eaa26afed939de` | [Android CI run 45179498179](https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/45179498179), **SUCCESS** |
| #40 — plus ad viewport simulator, HEAD snapshot | `10158a5bf9cdce9010a32afc6eff8cd2962f326d` | [Android CI run 45180815783](https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/45180815783), **SUCCESS**, incl. Core tests, Flutter tests, analyze, ARM64 build |
| Gallery Drift consumer QA PR #15 | `e1ee883a1f02ecc8ffbdc6f001be1c699576383c` | [Runs 45178984702](https://github.com/riccardopinato/GalleryDrift/actions/runs/45178984702) and [45178950980](https://github.com/riccardopinato/GalleryDrift/actions/runs/45178950980) **SUCCESS**; pin temporary only. Gallery `main@dde42c11d96ee6258670b01ce9e7b3c273cc56ab` untouched |

All PRs #33–#40 and Gallery #15 remain **DRAFT / NOT MERGED** at this snapshot. Test scripts added to dedicated QA branches are not part of candidate #40.

### Stages as distinct claims

- `DESIGN_APPROVED`: **10/10**, recorded in `ARTDRIFT_INTERACTIVE_MOCKUP_DECISIONS_2026-11-23.md`.
- `SOURCE_IMPLEMENTED_CANDIDATE`: **10/10 surfaces/interactions wired into #40** with the reservations below. A visual mock-up is not a screenshot-approved implementation merely because source code is present.
- `CI_GREEN_EXACT_HEAD`: **YES** at `10158a5bf9cdce9010a32afc6eff8cd2962f326d` on 45180815783.
- `VISUAL_APPROVED`: **NO**. Core canvas first screenshot reviewed, other 9 screen states and original visual references require acceptance.
- `PHYSICAL_ACCEPTED`: **UNVERIFIED**. User said to treat their phone checks as done, but no hardware identity, signer fingerprint, frame traces or before/after data verification were supplied. Treat as **user attestation**, not instrumented evidence.
- `PROMOTION_AUTHORIZED`: **NO**. Main and signatures unchanged.

## 2. Mock-up-by-mock-up traceability on #40

| Slot | Implemented candidate source | Remaining verification / caveat |
| --- | --- | --- |
| UX-01 Quiet Canvas | Core optional `museumControls`, immersion toggle and Art-only toolbar hidden while immersive | G3 physical gesture/accessibility, preserve camera, controls reappear |
| UX-02 Museal plaque | Optional long press returns **actual artwork plus rect**, Art-only overlaid real metadata and actions | G3 no tap/pinch/long-press gesture conflict, long captions/fontScale |
| UX-03 Tile→museum detail | `TileOriginFlight` route transform based on actual tile-local rect, identity-safe reverse fallback, walnut frame only in detail | **VISUAL HIGH-RISK:** animated surface currently transforms the route, not just artwork image; verify whether animation matches approved mock-up before accepting |
| UX-04 Room information | Ivory scrollable caption below / beside detail, metadata-derived expansion, source link and Android wallpaper preserved | G3 overflow, attribution and no fabricated description, 0/50/90 simulated ads |
| UX-05 Favorites archive | Editorial tile grid backed by original `Favorites` service with existing migration tests | G3 0/1/50+, cross-museum IDs, removal and returning to exact camera |
| UX-06 Search atrium | Ivory search surface, original local `GallerySearch`, original explicit international API opt-in, stateful query reopen | G3 keyboard, query, no unexpected remote request, mixed results |
| UX-07 Scroll control | Auto/Pausa + 25/50/75/100 popover, retains original physics and persisted `cameraKey.autoSpeed` | G4 real 60/120Hz; speed switching and pinch stop |
| UX-08 Curator settings | Six original locales, Pro/privacy/license and Android performance diagnostics retained | G3 scroll/contrast/keyboard/locale persistence; no fake Pro |
| UX-09 Museum portal | User-approved Italian two-line copy; six UI languages, actual catalog loading/error/retry | G3 startup/offline/retry and translation review |
| UX-10 Artwork tour | Previous/next and persistent walnut frame, factual caption, existing heart, wallpaper and museum action | G3 30 work switches, identity synchronization, Android vs web |

The canvas's original tile-to-workworld mapping, catalogs, source rights, photo permissions and Gallery Drift's default mode were not deliberately changed. Source non-interference is supported by tree diffs and tests; physical behavioral equivalence is still unproven.

## 3. Implemented synthetic ad viewport test (no advertising in app)

`lib/ui/art_ad_aware_viewport.dart`: `bannerHeight=0` by default; test-only positive height is read from `ARTDRIFT_QA_AD_BANNER_HEIGHT` as an integer compile-time define. Widget tests cover **0, 50, 90 dp** and appearance/disappearance without leaving a phantom gap. The child canvas fills only the region above the simulated banner. The canvas is not wired to AdMob, no banner is requested, no purchase/entitlement changes. **G3 still needs manual screenshot review of banner scenarios**.

## 4. Actual emulated Android evidence (canvas only)

[Run 45179716155](https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/45179716155) **SUCCESS**. Isolated QA branch `feat/artdrift-g2-visual-smoke-20261123` commit `8b67d57c1bf7b850570c93607f866b7c727eb3a5`, based on candidate `054a951d...` plus three QA-only files. Artifact **14821171420** `ArtDrift-G2-Visual-Smoke-Report` inspected:
- Android API35 x86_64 Pixel 6 emulator, 1080×2400 screenshots, software GPU, offline airline/wi-fi disabled.
- 48 scripted directional swipes, screenshot before, after first swipe and final **each distinct**, visible different paintings.
- App survived; AndroidRuntime fatal errors **0**; no Quickstep ANR dialog.
- PSS before **106423 KiB**; after **108439 KiB**.
- `gfxinfo` reported **2 frames**; p50/p95 48ms printed by tool are **statistically not valid** performance metrics. **FPS, p95/p99, real jank: NOT MEASURED**.
- Manual review: nonempty artwork mosaic, top-center brush search, heart/gear, compact Auto/speed, Immersione and recenter visible and intact. The capture does **not** prove 10/10 screen states or pixel match to approved prototypes.
- SHA-256 PNGs (before/mid/final): `ae416e61d2070cbcb4bdda3cd836d895f5df2a491f9b196e7e18f46f8a923b3a`, `349ff85f43c723bda007a0f672a6180adec18573de8a39b85fe4201cdc866538`, `59071fb05679d3e672bec82fa0f6ec5f86a89f8bb39f14ef477a9d555c8bcff4`.

### G3 additional capture harness

A separate branch `feat/artdrift-g3-ui-capture-20261123` is based on exact G2 `10158a5...` and adds ONLY `scripts/capture_artdrift_g3_ui.sh` and `.github/workflows/artdrift-g3-ui-capture.yml`. [Run 45181446813](https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/45181446813) was in progress at report creation. It seeks nine **intent-labelled** real screenshots (home/search/favorites/settings/detail/next/plaque/speed/immersion) with UI XML and log. Do not call each scenario accepted without inspecting resulting screenshots. No synthetic customer data is uploaded.

## 4b. G3 first nine screenshots — manual inspection, partial evidence

[Run 45181446813](https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/45181446813) completed **SUCCESS** on QA branch `feat/artdrift-g3-ui-capture-20261123@eeafb2c633b25f8c24b7712ebf86dff3e3277118`, based on candidate `10158a5...` (plus two test-only files). Downloaded artifact **14821867451**, `ArtDrift-G3-UI-Capture`, 8,450,035 compressed bytes, nine 1080×2400 PNG files, accessibility XML and zero-byte runtime fatal log. All PNGs are distinct; **capture success does not mean full visual approval**.

Manual image and UI-tree inspection:
- `01_home.png` — valid canvas with artworks, top-center brush, heart/gear, compact Auto, speed and recenter; normal banner-free canvas.
- `02_search_atrium.png` — valid ivory museum search overlay, local collection cards, keyboard visible on autofocus.
- `03_favorites.png` — valid empty archive state, no favorites on fresh QA emulator.
- `04_curator_settings.png` — valid ivory editorial screen with six languages and existing Pro/privacy/licenses in the scrollable section; performance diagnostics farther down (not demonstrated by this capture).
- `05_artwork_detail.png` — artwork in walnut/gold frame, parchment caption, heart; independent visual approval still required for frame tightness/margins.
- `06_next_artwork.png` — different actual artwork/title/metadata with fixed frame.
- `07_long_press_plaque.png` — actual long-press opens factual museum plaque with close, details and favorite controls.
- `08_auto_speed_menu.png` — **INVALID TEST CAPTURE**: opens artwork detail rather than the speed popover. The QA script tapped **x≈313, y=264** while the actual accessible speed button bounds were **[302,283]–[473,388]** on the 1080×2400 emulator; this is an **instrumentation-coordinate error, not evidence of a product bug**.
- `09_immersion.png` — verified full canvas without top toolbar/Auto controls, with `Mostra comandi` still reachable.

Corrective QA-only branch commit `2231d01854d6ed8564c98ada95e6b621750c8d66` changes the speed tap to **x≈389, y≈336** (inside the verified accessibility bounds); repeat [run 45182960994](https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/45182960994) started, final visual evidence pending.

**Evidential status:** `G3_PRELIMINARY_8_OF_9_CAPTURE_INTENTS_CONFIRMED`, not `VISUAL_APPROVED`. No golden against approved 10 designs, screen-size matrix, Ad-size screenshots, startup portal visual, accessibility or physical performance completed yet.

## 5. ARM64 QA artifact and non-upgradeable test signing

[CI 45180815783](https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/45180815783) artifact ID **14822215501**, archive `ArtDrift-Android-ARM64-internal-10158a5bf9cdce9010a32afc6eff8cd2962f326d`, internal APK:
- APK package: `com.riccardopinato.artdrift`.
- Size: **39,786,907 bytes**.
- SHA-256: `4c1b678cd25787763ef86a7240751a2bbe3467b949d0b10cbbd53a618027b5ca`.
- Signing class: `INTERNAL_TEST_ONLY`; Android Debug certificate SHA-256 `03675e760226b2d9d75564bebc05b716bca5cced87c6065cc9a5e6a21a6ea924`.
- The new test signer also differs from the G1 baseline QA signers. Therefore the APK is **NOT an in-place update candidate for the existing installed app**; no uninstallation, user-data migration, or installed-cert match has been performed.

## 6. Remaining gates and acceptance

- **G2 CI:** PASS at the exact declared SHA. A new code commit requires fresh CI.
- **G3 visual:** PENDING. Nine UI captures and side-by-side match to 10 approved mock-ups; 320/360/390/412dp, landscape, large font, accessibility, correct full-image aspect, history/returns, banner size interactions.
- **G4 performance:** NOT MEASURED physically. Same model/refresh, profile/release, three rounds pan/pinch/Auto/switch, p50/p95/p99/jank, PSS 10 min. Gfxinfo 2 sampled frames may not be used to pass this gate.
- **G5 safe upgrade:** BLOCKED_BY_INSTALLED_SIGNER_UNKNOWN and mismatched internal signing certs. Must verify user's actual installed cert/version and use compatible release signing without uninstall/data loss. The user attests phone checks have been done; report no unsupported success details.
- **Stacked PRs #33/#34/#35:** unchanged Draft; resolution plus explicit merge approval separate.
- **Gallery Drift PR #15:** QA-only; no propagation of new Core version to Gallery main.

**Overall: G2 CI PASS, G3/G4/G5 HOLD. No main merge and no public release authorized by this document.**
