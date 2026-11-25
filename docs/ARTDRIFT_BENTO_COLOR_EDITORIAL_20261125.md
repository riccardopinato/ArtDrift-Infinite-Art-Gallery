# Art Drift — Color Editorial Mosaic, Art-only v2

## Scope (development candidate)
- A deterministic world of 450×450 macroblocks, each subdivided into a
  3×3 bento mosaic. Four size classes: S (145×145), M (145×295 or
  295×145), L (295×295 and 145×445), XL (445×295 / 295×445).
- 4,499 real locally packaged WebPs were independently re-scored for vivid non-sepia colors, luminosity, hue variety, blue-green/red contrast, plus landscape/flower subject suitability. A contact sheet of the top 80 was visually checked. 800 top images are stored as an exact source-catalog fingerprint-bound priority index; non-hero paintings are supporting frames. The index adds no new image binaries.\n- The *real* offline-image pixel chroma/brightness manifest, bound to exact
  museum source IDs, ranks works for size. XL gets top 12%; L gets next 24%;
  M next 39%; S supporting 25%. Aspect matching reduces bad cropping.
- All S/M/L/XL use BoxFit.cover in the canvas to eliminate dark letterboxing; the full artwork remains available in the detail view. Shape-aware selection minimizes cropping. Prefetch and
  rendering share exactly the same Art-only geometry; the generic core is
  backward-compatible and GalleryDrift stays pinned to original columns.
- For *fresh* installations, 800 additional, source-traceable, already
  packaged and image-backed paintings are admitted from the existing
  4,500-record museum catalog: Art canvas 2400 -> 3200. These are NOT
  800 newly imported paintings from an external museum.
- Old saved playlists retain the previous ordered IDs and append 800
  verified extras at most once. The new visible layout/positions deliberately
  supersedes the old Art tile coordinates. Favorites/search still use museum IDs.
- The random starting-region scorer now weights the actual image area,
  favoring genuinely bright XL/L scenes without shifting artwork source IDs.

## Safety and release
- No new museum network scraping, no unlicensed image files, no imported
  post-1950 works, no GalleryDrift device-photo changes, no database migration.
- Entire preview stays protected behind Vercel authentication.
- Build/test success does not count as real-device approval, legal clearance
  for commercial distribution, user visual acceptance or Play readiness.
- Future genuine new painting imports need explicit catalog IDs, provider
  per-image rights evidence, independently validated thumbnails and QA.
