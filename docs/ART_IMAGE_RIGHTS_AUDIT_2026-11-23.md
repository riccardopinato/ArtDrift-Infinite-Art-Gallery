# Art Drift — deterministic rights and coverage screen (23 November 2026)

**NOT a commercial legal certification.** Every artwork still has
`commercial_release_cleared=false` pending image-specific rights review.

- Global catalog records: **4043**
- Actual manifest entries: **3632**
- Missing real image assets: **411**
- Missing from source-policy-eligible providers: **7**
- Missing behind source/image-rights HOLD: **404**
- Already packaged requiring image-specific rights review: **96**
- Manifest image bytes invalid: **0**
- Valid but very thin previews needing visual review: **27**

## Per-object evidence

Full itemized entries, identity, declared license, official image/evidence
URLs, SHA-256 of verified WebP bytes, gate verdict and explicit commercial
release status: `docs/generated/ART_IMAGE_ITEM_RIGHTS_AUDIT.json`.

Source-policy-eligible means **allowed for bounded download**, not legal
approval of a product. A CC0 metadata declaration does not by itself
clear artwork-specific photographs or provider trademarks.

## Remaining gates

1. Retry the policy-eligible missing images with safe official URLs; keep
   HTTP/403/404, tiny or invalid images as actual failures, never substitutes.
2. For source-policy HOLD rows, record explicit object/image license evidence
   from official museum pages before any new media file is downloaded.
3. Human/legal image-specific review before commercial distribution, plus
   device benchmarks, stable signing and Play disclosures.
