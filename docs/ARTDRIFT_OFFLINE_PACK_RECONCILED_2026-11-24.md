# ArtDrift — 4,042 WebP offline reconciliation (24 November 2026)

## Baselines and deliberately limited scope
- Factory: `riccardopinato/App-Factory-Core@ede07c491e586215598ff68daec43e17d699aa51`, Master v27, Golden Index v31.
- Art `main` parent: `594e6e612fbefee731d96c436ceaf6e981776e75` (PR #54).
- Source of **existing, verified WebP blobs**: PR #33 `1d7c8f7a010add291948e8a4fc102436abc361c6`.
- Current `web/museum_thumbs/` already had 1,142 WebPs; source #33 has **4,042**, retains all 1,142 byte-identically, and adds 2,900. The only changed existing file is the versioned `manifest.json`.
- Reuse the complete immutable source Git tree for this asset folder (no re-encoding, fetching by URL, generated substitute art, or unresolved file swaps).

## Consumer behavior
- `web/museum_thumbs/` is declared as a Flutter asset for Android, preserving the separate existing Web static path.
- Android reads a strictly schema-checked manifest from `rootBundle`; each artwork resolves to `web/museum_thumbs/{museum_source}_{id}.webp` **only by its own canonical source ID**. Web continues to use same-origin URLs.
- Nearby image warming stays bounded; detail and favorites use the same-work miniature until higher resolution is available. Frame-time and image failure reports are **opt-in/local only**, not user analytics.
- **Do not reorder the primary canvas items**. `lib/main.dart`, original `CatalogService`, `MuseumCatalog`, `assets/museums/catalog_global.json`, and canonical `Drift Core` stay byte-identical to the current main. Existing `artdrift.camera` and the tile-to-record mapping remain unchanged.
- Original canvas source: 4,500 known artwork records (72 original AIC + 385 other already-local + 4,043 remote-only). The new 4,042 verified remote WebPs mean **4,499/4,500 source entries have local images**, while the single remaining Smithsonian `William Linn / npg:npg_NPG.2007.11` keeps an honest no-image state. This source-level count does not prove physical zero-holes or FPS.
- The **585** new Smithsonian/Commons candidate records from #46/#54 and **635 HOLD stage records** are unchanged; no newly reviewed image rights are implied by catalog counts. Cloudflare D1 and the D1 Flutter opt-in archive introduced by #54 remain unchanged. GalleryDrift continues to pin its current shared engine SHA.

## Source QA and no-go gates
1. Run `python scripts/verify_mobile_thumbnail_pack.py`: exact IDs, non-orphan files, source flags, license evidence URLs, WebP headers and size limit, manifest/files complete set; log pack count, source counts and compressed bytes.
2. Flutter analyze/test for app and canonical Core, Chrome Web source tests, Web release build, internal Android ARM64 build on **same exact PR head**. If a test assumes old manifest counts, adjust only with verified data, not by weakening rights/source checks.
3. Inspect real images in actual runtime (Android/Web), camera persisted after upgrading, 48+ directional pans, pinch and taps, 60/120 Hz frame timing + system RAM/thermal; ensure no unrelated painting is substituted on failure.
4. **Commercial image-rights clearance is NOT certified** by source open-access flags, provider links, CI success or the previous per-item audit. The `commercial_release_cleared=false` restriction of PR #33 still applies for Store/public release.
5. Do **not** merge while inherited source #33's visual, physical and rights release gates are unresolved; do not deploy to production, change Google OAuth, auto-publish images, alter Cloudflare or modify GalleryDrift.

This is a candidate recovery of already-generated artwork bytes, not a new image provenance sign-off or production-ready application.
