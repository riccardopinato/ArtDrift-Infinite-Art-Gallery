# Art Drift — color-first canvas: stable-ID-safe rollout (2026-11-27)

Donor from #67 source SHA 3eb53ec27b44c3b35842eabe878071e406e3cbfc. Original 2,400 painted image source IDs measured from the existing thumbnail pack; historical automated portrait count 525 -> 157, not manual visual certification. Source manifest references no newly downloaded media.

- On a **fresh** installation, the first infinite mosaic uses only the 2,400 preferred image-backed IDs in deterministic source-pinned order. The full museum dataset remains searchable and available to detail/favorites.
- Existing camera `artdrift.camera.x/y/zoom` or saved ordered source-ID playlist ALWAYS wins, not reordered, not reset. No forced random start in this source-only stage.
- Source-native artwork IDs survive; unknown/missing IDs are ignored, rights invalid records are excluded by the current CatalogService. No changes to Drift Core, GalleryDrift, world coordinate algorithm or persisted favorites.
- Technical tests: first-install/color subset, legacy camera preservation, duplicate detection, manifest authenticity and thumbnail-backed integrity. Any invalid manifest fails closed to previous canvas catalog.
- A per-launch random start requires a separate shared Core opt-in with Gallery consumer QA and an explicit preference respecting existing installations. Not combined with this safe first stage.
- Current UI direction remains user-approved dark canvas, parchment/ivory/gold overlays from Design-App MOCK-STYLE-003 and editorial baseline, not a copied reference image.
