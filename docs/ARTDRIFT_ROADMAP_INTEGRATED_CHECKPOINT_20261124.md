# Art Drift — Roadmap integrated review checkpoint (2026-11-24)

Original main: `7b46ee8d2ec4c060eb235e11c9aba875ae7171de`; review branch merges independent lanes #47, #48, #49, #50, #51.

**Evidence achieved**:
- 5,085 original museum identities, 585 Smithsonian/Commons candidate records in 6 batches, all rights/image-delivery HOLD pending object-level review.
- Cloudflare existing D1: one already-source Smithsonian *William Linn* row imported after exact 5,084/535-HOLD/49-overlap gate; remote verified 5,085 museums and 5,085 FTS, 535 HOLD, zero published. No other D1 records automatically approved or imported. [Verified run](https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/45307817730).
- Flutter archive: opt-in, metadata-only, correct official sources and 6 UI locales. Excludes Google sync and never changes canonical Drift Core, Gallery, canvas world coordinates, user favorites.
- 457 shipped previews decoded, 100 comparison cards, 12 official sources sampled with 10 retrieved in individual run. Rights and screenshot approvals separate.
- First-party Cleveland API candidate acquisition: 100 NEW source painting IDs with media status CC0 and independent underlying rights/delivery HOLD. The 100 NEW Cleveland candidates were subsequently uploaded to existing D1 as `METADATA_ONLY` with image and license fields blank, all `HOLD`; remote read-back PASS in [Action 45309465406](https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/45309465406).
- Real Web viewport screenshots from separate CI available for review; **not** user-approved mockup parity and not physical device evidence.
- This integration CI includes **NO APK** commands, device builds, Cloudflare production deployment, remote writes or source approval.

**Still blocked**: 585 existing candidate rights and media review, 100 new Cleveland candidate underlying-rights review, 486 Tate/MoMA metadata-only records without image licenses, 10/10 user mockups physical/UI comparison and approval, live provider variations and image CDN policy. Never label these CERTIFIED based solely on green CI.

### Remote staging snapshot after the new Cleveland research wave
- Existing museum works and FTS5: **5,085** each.
- Separate additional staging records: **635**, all **635 HOLD**, **0 publishable**.
- Exactly **100** additional Cleveland native identities, all `METADATA_ONLY` (blank source image URLs and license fields); previous **49** Cleveland are overlaps with the source catalog.
- Total distinct source-native IDs across both namespaces: **5,085 + 635 − 49 = 5,671**. This is NOT a count of approved artwork images.
- One-shot stage upload run: [45309465406](https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/45309465406). No Cloudflare Worker deployment or publication. All future new media require separate per-image legal review.

### Actual rendered visual evidence (NOT APPROVED)
- [Flutter Web Chromium screenshots (GitHub Actions)](https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/45308145630), exact screen artifact ID `14882655461`, PNG 390×844 SHA256 `79dc14d85e3cdde4631eefaaf32ba10cb3b39b9ef48d56dca5fd39bb1e3cdbdf`, PNG 820×1180 SHA256 `330aa013504eade1045982db79cc7b911b1c1c632027a9644c67ab9161368147`.
- Inspected both raster captures: top-center search pill, dark mosaic and basic actions rendered; several wide dark tiles present **museum glyph/text instead of imagery**; noticeable clusters of portraits and low-resolution historic source photos. The UI has not incorporated all ten approved G2 mockups. These deficiencies are **visual review findings**, not CI failures and not a license to silently remap existing camera/tile IDs.
- **Visual state:** `SCREENSHOT_CAPTURED / REVIEW_REQUIRED` (neither `VISUAL_APPROVED` nor `PHYSICAL_ACCEPTED`). Correct by a future artwork-ID-stable visual source/thumbnail plan rather than by shuffling tile indices.
