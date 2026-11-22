# Art Drift — WebP thumbnail wave 02 (2026-11-22)

Requested through a specifically scoped source-policy-gated feature branch.

- Baseline existing: 1,142 validated global WebP thumbs, 2,901 metadata-only
  global records, plus the independent original bundled preview pack.
- New automated attempts: up to 1,200 missing source-eligible rows, not a claim
  of 1,200 successes.
- Eligible new sources only: The Met, Cleveland, National Gallery of Art,
  Rijksmuseum and Smithsonian, with source-specific license/evidence checks.
- All other sources HOLD pending image-level rights verification.
- Preserve legacy manifest entries for existing images, including those whose
  release clearance has not yet been re-audited.
- No duplicate image substitution; HTTP, decoding and rights failures are
  recorded and leave that artwork unmodified.
- The workflow commits generated assets to this feature branch only.
- Merge only after generated image QA, exact-head Android/Web CI and legal
  distribution review; never auto-publish.

No background completion or guaranteed totals are claimed.
