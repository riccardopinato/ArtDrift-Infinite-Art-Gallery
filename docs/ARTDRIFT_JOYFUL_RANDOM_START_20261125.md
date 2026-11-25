# Art Drift — Joyful/Vibrant discovery entry (2026-11-25)

Baseline: `main@594e6e612f`; candidate stacked on PR #66 `8ce3105eef09561165e851f4aa3ba078df403856`.
Factory baseline `842dfa073451ec247308ccb4afb8ead5349bcbd4`.

## Implemented
- Reuses PR #57's **2,400 image-backed color-selected** IDs and reviewed pixel-based manifest, with 525 → 157 machine-identified portraits (heuristic, NOT human-curated certification).
- Fresh Web/Android installs use the colorful playlist; legacy installs with recorded `artdrift.camera.x/y/zoom` pin the previous ordered catalog to avoid changing **coordinate → source image IDs**. Existing saved playlists never silently grow/reorder.
- Every successful *new app opening* starts from a new random region of the same infinite world. A lightweight 44-location candidate search biases available previews, metadata about landscape/seascape/gardens and visually modern periods. The prior launch region is excluded by distance. No fake image, substitution, random reorder or personal-device gallery access.
- The start position is Art-only. Drift Core gets a backward-compatible opt-in `initialWorldCenter` and still restores Auto speed; GalleryDrift does not opt in, retaining its camera behavior.
- Last manually browsed camera remains stored, but the opt-in random start intentionally overrides restored x/y/zoom on next opening. This is a user-requested behavior change and does not delete favorites or camera preference records.
- The catalog remains searchable in full. Original title, artist, source, date and rights evidence unchanged; no modification of Cloudflare D1 or image licenses.
- Existing color manifest reuses already packaged WebP; **zero newly licensed paintings in this step**. Additional modern works need independent, per-image rights and visual curation before inclusion.
- Refresh/error retry within a single app session does not teleport the canvas.

## QA gates
- Test 2,400 source IDs against the exact 4,500-work source catalog, full thumbnail availability, legacy placement, restart random choice, stable layout and shared-core default behavior.
- Flutter analyze, Drift Core + app tests, Android ARM64 + Web exact-head checks before merge; visual QA and Android physical follow.
- This is a Draft PR **stacked on #66**, itself Draft and blocked by #55 image rights, G2 visual and physical acceptance, and production signing. No public deploy or production merge authorized.

## Pixel QA enhancement — exact existing WebP pack
The initial real Flutter screenshots remained sepia-heavy. This revision decodes the already bundled 4,499 real WebP paintings, packs 4,500 source-key-ordered pixel chroma/brightness scores into a 6KB read-only manifest and verifies the exact catalog ID fingerprint (FNV-1a32 = 2742452096). Each image score is a byte from a fixed metric of saturation * brightness and vivid-pixel ratio; no network runtime image scans, no new images, no rights changes. On fresh installs it selects the **2,400 highest-quality visual candidates**, weighted for landscapes, flowers, modern visual periods and fewer portraits. Legacy ID playlists are unchanged. Random startup samples 44 regions and weights **actual pixel-based chromatic scores**, not only metadata. Original PR #57's 2,400-list is retained as fail-closed fallback if the catalog changes. Source-image classification remains a heuristic and the legal/physical gates remain HOLD.
