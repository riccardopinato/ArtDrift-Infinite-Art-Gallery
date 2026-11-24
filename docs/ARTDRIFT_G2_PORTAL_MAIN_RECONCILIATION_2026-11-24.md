# G2 portal museum UI — isolated reconciliation (2026-11-24)

- Source: user-approved 10/10 G2 design ledger, slot 9; original PR #37 `57410a79ca270a804b76909cc86b6d812982ccd4`.
- Current target: ArtDrift `main@594e6e612fbefee731d96c436ceaf6e981776e75` after PR #54; no inherited stacked PR #33/#34/#35/#40 changes.
- Design-App user preference: `MOCK-STYLE-003` Vintage / editorial museale, **ADATTATA** to established dark/ivory/gold art direction; zero imported third-party assets. User explicitly approved the first two loading headlines and no artificial waiting.
- Introduces only the real `MuseumPortal` on catalogue loading/failure + six locale strings and existing retry callback; no change to `CatalogService`, network behavior, cache, favorites, canvas items, Drift Core, images, D1 archive, Cloudflare or GalleryDrift.
- Critical preservation: pre-existing #54 `cloudMuseum*` localization keys and read-only D1 search adapter remain present; localization is additive (six new keys per language).
- This source-only integration closes **G2 slot 9 at SOURCE_IMPLEMENTED** if tests pass. It does not by itself close G3 visual comparison, G4 physical QA or G5 stable-signing acceptance. Remaining G2 slots from PR #40 stay separately gated.
- Tests: copy from #37 for real loading/failed/retry and six distinct locales; run Flutter analyze/test and Web/Android on exact PR head. Compare the real screenshot to approved mockup before declaring VISUAL_APPROVED or merging source to main if review approval remains required.
