# Art Drift — Doppelgänger: editorial QA gate (27 November 2026)

Scope: 87 currently published, offline-embedded pair candidates. All 87 rows
are marked `status: verified` in the legacy asset, but that status alone is
NOT proof of visual resemblance, independent asset-license certification or
acceptance by the product owner.

## Implemented in this change

- A permanent dataset integrity test checks 87 canonical unique IDs, required
  credits, URLs, WebP signatures and the rejected *exact pair* contract.
- Rejected historical pairings remain excluded; an individual person is not
  automatically banned from a different artwork pairing.
- In the game, a small localized counter shows round progress and correctly
  guessed pairs. A voluntary reveal does not increment the score; after the
  last round the session resets.
- Museum search gains Italian-to-English scene aliases; the 12 local collections
  gain bounded, explainable metadata tokens. No new AI/image recognition claims.

## Not verified here

- Independent image-by-image visual-similarity review for 87 pairs;
- provenance and license suitability of each copy in this specific app;
- third-party URL permanence or image subject identity;
- responsive Android screenshots and physical touch QA.

Do not infer `COPY_READY`, commercial clearance or visual approval from
passing schema tests. Keep questionable pairings in review; do not silently
delete without the product owner's explicit decision.
