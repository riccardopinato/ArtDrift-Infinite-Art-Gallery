# ArtDrift — rights and relevance review of 585 candidate works (24 November 2026)

This is an **automated metadata triage only**, not a copyright certification, not an image availability test, and not a product decision to delete 525 historic records. The app's primary canvas currently only accepts *Painting* entries; non-paintings (prints, photographs, drawings, etc.) remain preserved for a separate optional art archive. Candidate data remains HOLD.

Source: canonical 5,085 catalog records and exactly 585 entries in `assets/museums/catalog_new_museums.json` (Smithsonian 558) plus `assets/museums/catalog_modern_1950.json` (Wikimedia Commons 27). Reviewed in six disjoint waves of <=100, with exact source and museum-native identity. Cloudflare D1 contains 635 separate staging HOLD records, including 100 Cleveland metadata-only; it is **not** touched by this workflow.

### Deterministic candidate distribution
- **60 Painting** candidates for painting canvas source/media review: Smithsonian 33 and Commons 27.
- **525 non-Painting** preserved for separate archive/product-scope decisions: 232 prints, 120 drawings, 97 photographs, 38 textiles, 21 sculptures, 10 posters and 7 ceramics. These are **not** automatically suitable for painting-only canvas, but are not invalid art.
- **558 Smithsonian** candidate records lack an object-specific canonical `source_url` (generic institutional CC0 evidence is insufficient to verify specific object, artwork/media rights).
- **74** rows lack a creator field; **40** titles contain HTML markup, **2** contain QuickStatements `QS:` metadata artifacts. No title is automatically rewritten or artist invented.
- Licenses claimed: Smithsonian **558 CC0**; Commons **17 CC BY-SA 4.0, 7 CC BY-SA 3.0, 2 CC BY 3.0, 1 CC BY 4.0** (attribution, source terms and SA conditions require verification).
- All **585** image URLs are textual candidate pointers; no actual content download or media image-rights audit has been performed. **0/585 publishable** on these metadata-only checks.

### Quality and privacy
A deterministic CLI emits every source-ID in `triage-all.json`, `paintings-priority.json`, `separate-archive-review.json` and six `wave-XX.json` files, with source evidence, missing title/author warnings and rights flags. The code fails closed on duplicate IDs, unexpected license/provider, non-HOLD status and invalid URL syntax. Use exact source counts, no network API calls and no data mutations. Original source catalog is untouched.

Next genuine blockers: verify the **60** painting candidates against item-specific original museum/Commons records, attribution/license and actual image delivery; verify or add **558** official object links before claiming original-source provenance; review remaining non-paintings as separate art collection; stage 635 Cloudflare records only under their existing individual HOLD rules. No automatic image approval, remote SQL or production deploy permitted.

Factory: `App-Factory-Core@ede07c491e586215598ff68daec43e17d699aa51` Master v27. Source branch is stacked on PR #60, and this tooling should be merged only after its own CI and review gates.
