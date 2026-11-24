# Art Drift — Roadmap integrated review checkpoint (2026-11-24)

Original main: `7b46ee8d2ec4c060eb235e11c9aba875ae7171de`; review branch merges independent lanes #47, #48, #49, #50, #51.

**Evidence achieved**:
- 5,085 original museum identities, 585 Smithsonian/Commons candidate records in 6 batches, all rights/image-delivery HOLD pending object-level review.
- Cloudflare existing D1: one already-source Smithsonian *William Linn* row imported after exact 5,084/535-HOLD/49-overlap gate; remote verified 5,085 museums and 5,085 FTS, 535 HOLD, zero published. No other D1 records automatically approved or imported. [Verified run](https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/45307817730).
- Flutter archive: opt-in, metadata-only, correct official sources and 6 UI locales. Excludes Google sync and never changes canonical Drift Core, Gallery, canvas world coordinates, user favorites.
- 457 shipped previews decoded, 100 comparison cards, 12 official sources sampled with 10 retrieved in individual run. Rights and screenshot approvals separate.
- First-party Cleveland API candidate acquisition: 100 NEW source painting IDs with media status CC0 and independent underlying rights/delivery HOLD. No images downloaded, no D1 write for new records.
- Real Web viewport screenshots from separate CI available for review; **not** user-approved mockup parity and not physical device evidence.
- This integration CI includes **NO APK** commands, device builds, Cloudflare production deployment, remote writes or source approval.

**Still blocked**: 585 existing candidate rights and media review, 100 new Cleveland candidate underlying-rights review, 486 Tate/MoMA metadata-only records without image licenses, 10/10 user mockups physical/UI comparison and approval, live provider variations and image CDN policy. Never label these CERTIFIED based solely on green CI.
