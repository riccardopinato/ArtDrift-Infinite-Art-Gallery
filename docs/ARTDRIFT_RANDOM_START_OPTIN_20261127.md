# Art Drift — optional random launch coordinates (2026-11-27)

Source design: PR #67 historical ArtJoyfulStart. This is a safe, scoped implementation over ArtDrift main `9b7681712fe65c13ec0e70baa066fff235249f67`. G2 museum controls, 12% hover/touch zoom, source native artwork IDs, 4,042 thumbnails, local favorites and Gallery camera persistence remain unmodified. NO bento remapping or new images.

- Optional, explicitly controlled setting (six languages), default OFF on all installations, preserving existing stored camera by default.
- When ON, each NEW app session chooses one of 96 world regions with real preview thumbnails and landscape/flower metadata, stays at least 1,100 world units away from the previous random start. There is NO re-randomization when refreshing catalog within that session.
- Canonical Drift Core gets only an optional `initialWorldCenter` parameter, default null and therefore keeps original GalleryDrift behavior. This user preference overrides the restored start viewport for that launch, but original camera preference keys are not deleted or remapped.
- Basic deterministic seeded tests cover reproducible score choice, no artwork source-ID reordering and no user preference override when OFF.
- Requires exact-head Art Web/Android CI and independent GalleryDrift pinned source CI. Device visual/motion acceptance separate.
