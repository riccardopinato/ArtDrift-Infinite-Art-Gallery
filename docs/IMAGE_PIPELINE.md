# ArtDrift v0.2 — small, real images from verified sources

**Problem corrected:** prior APK v0.1 contained no images or metadata and attempted multiple online searches on every fresh install. A valid Flutter build did not prove any artwork could actually appear.

## Image source and license
- Provider: **Art Institute of Chicago Open Access** metadata and IIIF.
- Source filtered at generation: \`is_public_domain=true\`, \`artwork_type_title=Painting\`, valid \`image_id\`, and a verified successfully decoded image.
- Source museum ID/title/artist/date/credit are kept in \`assets/gallery/catalog.json\`.
- No imagery, feed, editorial text or branding is scraped from anotherboring.day.
- AIC asks for sequential requests with approximately one second between image downloads; the one-time generator respects this.
- Verify provider terms and rights before commercial release. Curatorial narratives aren't copied from the museum.

## APK / network strategy
1. \`scripts/build_seed_gallery.py\`: **one-time** asset generation and pinning in the repository; not invoked during regular Android CI, so builds remain reproducible.
2. Bundle at most 72 valid artworks as **tiny WebP previews**, no more than **2 MB combined** (max 45 KB each). Images are ~200px and are saved as genuine artwork (not abstract placeholders).
3. Boot \`CatalogService.bundled()\` in milliseconds, without waiting for remote API and regardless of network state.
4. Canvas shows local previews at ordinary zoom, so no cellular download per scroll. At deep zoom, IIIF 400px requested and the bundled preview remains displayed while it loads/fails.
5. Tapping an artwork fetches IIIF 843px only for that image, while showing the local preview in the interim, including in airplane mode.
6. Wallpaper fetches 843px on explicit action; does not add image bytes to APK.
7. Bound Flutter decoded-image RAM cache to 48 MiB. Disk footprint is the tiny pinned previews + app code; there is no automatic unbounded HD image disk cache.
8. Test gates assert image assets really exist, museum record rights flags, metadata consistency and compressed preview sum below 2 MiB.

## Limitations
- Still a finite initial collection reused across the virtually infinite canvas; expand with a versioned/artwork-ID-stable catalog later.
- Image source can change remotely; a larger detail may be unavailable offline while the tiny preview remains.
- CI tests and APK build do not equal physical-device verification; jank, contrast, OEM wallpaper and update-in-place remain separate acceptance gates.
