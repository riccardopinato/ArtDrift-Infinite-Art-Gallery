# Drift Core — optional G2 museum controls with Gallery default parity (2026-11-27)

Source of user-approved G2 interaction contract: Art Drift PR #59 @ e9cab00fa20d6fc6087506c84c722d2c8c4fb7d0; modern canonical Drift Core base: ff227d057981cfdfc14f0d472ba7c8069cab5425 already includes the 12% hover/touch #85 animated focus.
This PR ports the **minimum optional hooks** to the canonical shared Flutter package: stable source tile rect callbacks for tap/long-press, canvas gesture dismissal hook, museum Auto/Speed menu (25/50/75/100), contemplative quiet mode and exit, animated-zoom preservation. All additions default to NO-OP and `museumControls=false` for GalleryDrift.

No changes to world hashing, order, camera restore, source image IDs, JPG/WebP files, accounts or Cloudflare. Tests for gallery default, rect provenance, Auto speed, immersive restoration, gesture/hover remain mandatory.

Consumer lifecycle: first merge only after exact-head Art CI and separate GalleryDrift candidate pin/Android CI, then pin Gallery to merged Art SHA and reconfirm. This is shared Core only; Art consumer UI/plaque is a separate PR. No production images or public release.
