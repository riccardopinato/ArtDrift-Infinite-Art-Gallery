# Art Drift — WebP wave 03 (22 November 2026)

This request is recorded on the PREPARATION branch before starting the
automatic thumbnail-pack workflow. No extra push is permitted on the active
generation branch until its own commit is complete.

## Verified previous wave
- Source snapshot: Wave 02 commit 63b7143292baa7e294d442daa2ded1221e7b6d36.
- Packaged global painting thumbnails: 2,250.
- Global paintings still without thumbnail: 1,793 of 4,043.
- Strict policy eligible for new source downloads: 3,543; HOLD 500.
- 96 older bundled images still need per-image redistribution review.

## Wave03 contract
- Attempt at most 1,200 *missing* painting images sourced only from the
  pre-screened official Met, Cleveland, NGA, Rijksmuseum and Smithsonian hosts.
- Use source-specific CC0 or public-domain flags and HTTPS rights-evidence URLs,
  strict redirects/size/MIME checks and actual WebP decoding/encoding.
- Preserve all 2,250 existing files, do not substitute a different painting.
- Report counts downloaded, rejected, missing and held, including by source.
- GitHub Actions creates the new commit only on the isolated feature branch.
- Branch serialization prevents races between two runs producing output to
  the same ref; no force pushes.
- Source-policy heuristics are NOT image-level or commercial legal clearance.
- Only promote files into app main after manifest and image QA, rights review,
  Android/Web final-head CI and physical device acceptance.
