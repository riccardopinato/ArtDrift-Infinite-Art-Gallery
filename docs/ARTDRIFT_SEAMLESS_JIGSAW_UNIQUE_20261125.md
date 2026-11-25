# Art Drift — Seamless Jigsaw, no local duplicate paintings

## Confirmed design intent — 25 November 2026

The previous PR #67 visual QA was insufficient: a desktop screenshot showed
several copies of the same paintings and large dark gaps around images.

### Art-only corrective layout
- Real 450x450 world macroblocks using six four-piece arrangements.\n- Each 450px block chooses its puzzle template using the actual image\n  width/height ratios of the four unique works. Landscape paintings receive\n  wider frames and portrait paintings receive taller frames; a bounded\n  visual-rhythm preference balances variation against cropping.
- The same S/M/L/XL tiles now cover every one of the nine 150px cells.
- No 5px gutters and no missing cells, including macroblock boundaries.
- The nested image widgets are forced to fill their tiles with
  width=height=infinity + BoxFit.cover; clipping prevents overspill.
- Tapping opens full artwork detail; unavoidable cropping in the mosaic
  does not alter the underlying painting.

### Repeat prevention
- The previous independent random hash for each work has been removed.
- 3,200 works are ranked and divided into four disjoint 800-work bands,
  ordered strongest color first. Four puzzle shapes are sorted largest
  first and assigned exactly one work per band.
- 2-D modular coordinate permutation is deterministic, restores the same
  artwork on revisit and has 800 distinct steps along each coordinate
  axis per band. The normal 12x12 desktop vicinity has no duplicate IDs.
- Infinite world with a *finite* catalog cannot have globally unique art
  for arbitrarily distant positions. After catalog cycling, paintings
  inevitably repeat, but never in the normal local viewing region.
- All favorites are still keyed to stable museum source identities,
  not to old world tile geometry. No database changes.
- GalleryDrift default world tile logic remains untouched; the shared
  core change adds clipping and forces its content to fit tile bounds.

### Gates
- New unit tests verify zero uncovered pixels, zero overlaps, local
  uniqueness, 3200/3200 distinct ID cycles horizontally and vertically,
  positive/negative distant windows and viewport-priority culling.
- Re-run full flutter analyze/test, real Chrome 390x844 and 820x1180
  screenshots, ARM64 APK build, and check protected Vercel alias SHA.
- Visual acceptance, physical-device QA and commercial rights clearance
  still block merging Draft PR #67 into main.
