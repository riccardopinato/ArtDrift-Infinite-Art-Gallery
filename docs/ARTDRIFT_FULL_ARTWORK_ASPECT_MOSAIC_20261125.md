# Art Drift — Full original paintings, zero cropping, zero mosaic holes

## Owner-supplied regression — 25 November 2026

The earlier bento v3 cropped the upper/lower portions of portrait paintings
(e.g. a full portrait with hat and torso was shown only as part of a face).
This was caused by a fixed rectangular puzzle layout and BoxFit.cover.

## Corrected Art-only layout: native-aspect justified strips

- Every image frame is sized from its original source width/height ratio.
  The gallery uses BoxFit.contain, never BoxFit.cover. Full museum paintings
  remain intact on the canvas; high-detail views open on tap.
- A mathematical constraint: four arbitrary image aspect ratios cannot
  generally all be preserved inside a fixed 450x450 bento block without
  cropping, gaps or distortion. This implementation replaces that grid
  with multiple horizontal stripes of varied heights and natural widths.
- Each row is fully packed from negative to positive infinity, with no empty
  cell, no fixed-width column and no horizontal/vertical gutter. Seams between
  neighboring rows are staggered by original picture widths.
- Color priority: the tallest rows take the highest scoring 25% from the
  authenticated 3,200-work source list; supporting rows display other bands.
- Identity is stable across zoom, pan, recenter and reopening. Four adjacent
  stripes cover all 3,200 works across their complete independent cycles.
  Neighboring visible areas avoid duplicates. Absolute never-repeat over an
  infinite plane would require infinitely many source works.
- A sparse O(visible rows + binary lookup + visible tiles) geometry index
  plus bounded 32-row LRU handles negative/distant coordinates and scrolling.
  No new packages, museum APIs, private photo access or database migration.
- Shared Drift Core renderer and GalleryDrift remain unchanged.

## Gating and tests

- Pixel-area coverage in arbitrarily offset windows including negative
  coordinates, no overlaps, stable artwork and tile IDs on revisit.
- Natural image aspect ratio checked for every visible tile, i.e. no cropping.
- Large desktop viewport no-repeat IDs, complete 3,200-source band cycling,
  small/mobile/distant viewports and render-cap priority.
- Run Flutter analyze/tests, Chrome-specific unit tests, browser screenshots
  at 390×844 and 820×1180 and Android ARM64 build for exact commit.
- User visual approval and physical Android acceptance pending; Draft PR #67
  remains unmerged and commercial image rights remain subject to audit.
