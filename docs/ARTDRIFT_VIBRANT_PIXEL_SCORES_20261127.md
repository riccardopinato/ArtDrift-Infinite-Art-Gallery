# Art Drift — Pixel-derived vibrant museum discovery v2 (2026-11-27)

Source of first-party pixel manifest and deterministic fingerprint decoder: draft PR #67 `3eb53ec27b44c3b35842eabe878071e406e3cbfc`. Canonical base at `564396436d7b6d185b1bcf219ff7d00735b2b91d` includes all G2, #111 painting-only flight and #112 random camera preservation.

- A read-only 6KB manifest with chroma/brightness scores from the existing 4,499 source-identity-verified WebP thumbnails (4,500 catalog records), no remote pixel fetches or new images.
- Exact 4,500-artwork identity fingerprint and score byte count MUST match; any catalog addition, missing thumbnail or schema mismatch falls back to existing `ArtVisualColorSelection`. Never apply stale scores to a different work.
- Only fresh installs receive the 2,400 highest measured-color images. Existing saved `artdrift.canvas.offline.v1.keys` and legacy camera source-ID ordering win unconditionally; favorites unchanged.
- Opt-in random-region visits may now prefer bright image-backed existing paintings; user-saved camera location is preserved by canonical #112.
- Scores are a visual heuristic, NOT independent rights certifications; commercial_release_cleared=false in the source manifest. No Store deployment authorization, release-flag change, new usage permission, D1 mutation or account activation.
- Exact-head Web/Android/flutter tests including manifest fingerprint and guest-camera regression are mandatory; physical color/contrast acceptance remains separate.
