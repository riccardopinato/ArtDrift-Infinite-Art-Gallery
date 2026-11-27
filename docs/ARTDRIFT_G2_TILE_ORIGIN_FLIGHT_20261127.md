# Art Drift — G2 painting-only origin flight (2026-11-27)

Source: original first-party G2 flight from historical PR #59 commit `e9cab00fa20d6fc6087506c84c722d2c8c4fb7d0`, re-integrated on current main `9b7681712fe65c13ec0e70baa066fff235249f67` with existing current `ArtworkDetail` and curated Commons/NGA per-image license controls left unchanged.

- The original **painting preview only** moves from the tapped source tile rectangle to the detail's existing framed art region; the whole route does not scale like a card. Factual caption/controls softly fade underneath.
- Source tile rect is converted from canvas-local to global screen logical pixels. Source-ID stays unchanged, and the same record remains selected. On prev/next the notifier prevents wrong-art reverse motion.
- Search/collection non-tile openings use the existing safe fade. The collection canvas passes the tile's original group and its own camera key.
- Reduced-motion immediately uses fade, not a flight; zero animation interval on accessibility request.
- No changes to canonical Drift Core or Gallery consumer, artwork images, licenses, online catalog, favorites or wallpaper.
- Exact-head Web/Android CI and real phone screenshots/gesture parity are required before public launch; this is source implementation only.
