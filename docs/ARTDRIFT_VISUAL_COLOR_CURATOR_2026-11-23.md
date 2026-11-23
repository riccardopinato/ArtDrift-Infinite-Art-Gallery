# Art Drift — selezione visiva con miniature reali (23/11/2026)

Scope: **Art Drift only**. This feature branch is stacked on PR #26
(full 4,499-WebP pack), and must not merge before its base is reconciled.

## Verified evidence
- Source museum catalog: 4,500 entries, 4,499 existing bundled WebP files
  across gallery/museum thumbs and web/museum_thumbs, approx. 19.8 MB total.
- Full run of deterministic script build_visual_first_collection.py:
  4,016 available and usable images after image decoding, source-policy
  eligibility and exclusion of tiny/corrupt/extremely dark/mostly blank assets.
- V2 selected **1,200** paintings from **801** represented artist labels:
  **936 bright/chromatic** and **264 quieter/pause**.
- **11 Van Gogh / 7 Matisse** image-backed artworks are represented.
- Excluded 483 thin/broken previews and 1 missing preview from palette ranking,
  not deleted from the catalog or original assets.
- Pixel metrics: vivid-pixel ratio, HSV saturation, bright-colored area,
  hue entropy, grayscale contrast and sepia/dark penalties.
- Source art is not replaced with lookalikes; existing museums/official
  item source records remain intact. MoMA CC0 **metadata does NOT include
  artwork image rights**: no MoMA images were downloaded or incorporated.
- Preview contact sheet is an internal CI artifact; human aesthetic approval
  is limited to this sampled contact sheet, NOT all 1,200 works.
- The per-work CSV audit and screenshot are available in GitHub Actions
  workflow "Art Drift - visual-first pixel analysis and 1200 image mosaic".

## User experience and performance
- New Android installations receive the 1,200-item colorful local
  preview playlist by default. Existing Android installations keep the
  previously persisted artwork/camera mapping (no surprise re-order).
- All users can open **Cerca → Colori e capolavori**, with an independent
  camera, to explore the curated images on the existing infinite canvas.
- All 4,500 metadata records remain searchable; curated image pool is NOT
  a destructive filter.
- No additional image bytes are packaged by this PR: it reuses the approx.
  19.8 MB preview pack in its PR #26 base, adds small JSON playlist only.
- Visible Flutter image decode remains limited by the shared canvas
  viewport/render cap, image memory cap and directional prefetch already
  present in the canonical shared Core. No new image-host requests
  at startup or extra cloud subscription.

## Remaining gates
- Physical Android cold-start, long scroll, memory p95, low-end device and
  stale-image/error tests. A CI build is NOT a measured latency guarantee.
- Per-image commercial re-use and provider terms must be reviewed before
  Play Store publication; existing source-policy CC0 flags are not final
  legal certification.
- UI/visual review of more than 120 preview samples.
- Rebase/merge dependency PRs #18 → #23 → #26 first.
- This feature does not import anything into the user's Cloudflare D1
  database and does not create R2, Workers or a paid service.
