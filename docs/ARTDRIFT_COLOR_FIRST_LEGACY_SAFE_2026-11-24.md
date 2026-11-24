# ArtDrift P1 — Color-first, stable legacy cameras (24 November 2026)

## Baseline and source
- Depends on P0 `feat/artdrift-image-pack-main-5085-20261124@5b636fe27349088233ba1d6a100689d0e0bb5c39` (PR #55, 4,042 real WebP images).
- Curated source: PR #34 `feat/artdrift-integrated-preview-color-20261123` (2400 artist/source-ID-stable selections with 70.1% fewer automatically classified portraits), compiled asset `assets/museums/canvas_visual_color_v1.json` and existing `ArtVisualColorSelection` service.
- No downloads, color synthesis, substitutes, new artwork copyright grants or modification of 5,085 D1/635 HOLD.

## Product behavior
- First Android install without a stored `artdrift.camera` preference or pinned source IDs: uses the 2,400 **already verified image-backed** artwork IDs from the fixed color-first manifest. Source IDs remain exact; images come from PR #55 only.
- Existing Android install with a saved `artdrift.camera.x/y/zoom` and no source-ID playlist: pins and preserves **all 4,500 ordered original entries**, preventing the 4,500→2,400 modulo remap of world tiles that would otherwise follow the older #34 implementation. The existing camera key is unchanged.
- Existing persisted source-ID playlist is always respected, and new additions to the catalog do not append automatically. This is a required invariant until Drift Core implements stable insertion/rebalance without remapping.
- Web keeps the existing catalog list and world mapping. The full 4,500 entries remain available for local searching and detail; neither saved favorites nor the D1 read-only archive are changed.
- A missing/malformed curated manifest or any selection less than 300 true image-backed works falls back to the available local artwork list. If the entire offline package is unavailable it falls back to the original catalog, not to substituted images.

## Tests & acceptance
- Deterministic selector test for a fresh install, existing camera, re-install persistence and catalog growth.
- PR #34 original source manifest test adapted for the current **4,500**, not the obsolete 4,499 baseline. Requires exactly 2,400 unique image-backed entries and validates the sampled portrait reduction 525→157 and first-120 concentration limit.
- Exact-head Android/Web analyze/test & image rights integrity gate after PR #55 CI.
- **Draft until P0 is reconciled and physically tested.** This remains a candidate, not visual/physical/product-rights/Play certification; no public image distribution or production signing changes.

## Unfinished subfeatures
- Color themed **additional** canvas, separate camera and navigation are not included in this isolated home-only step. Review separately against approved G2 10/10, design-led source and both apps' core compatibility. Do not imply full PR #34 or #40 was integrated.
