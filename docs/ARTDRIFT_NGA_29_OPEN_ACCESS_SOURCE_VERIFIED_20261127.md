# Art Drift — 29 NGA paintings, licensed per-image Open Access (27 Nov 2026)

**Official museum data SHA:** `3a187753c941dd153c2632cffc15d802f171e012` (NGA Open Data updated 26 Nov 2026). Factory SHA `f8b9f550c544735237f19cdd723bd2df667ceee6`, Master v27, Golden Index v31.

## Origin, image rights, exact verification

Official [National Gallery of Art Open Data](https://github.com/NationalGalleryOfArt/opendata), CC0 metadata alone does **not** make every linked image reusable. For **each of these 29 records**:
- The source dataset joins `objects.csv`, `constituents.csv`, `objects_constituents.csv` (role=artist), and `published_images.csv` at a pinned official commit.
- The object is classified **Painting**, with a single matching painter among the seven target artists.
- **The specific primary image** has `openaccess=1`, the museum's explicit image-rights gate (not metadata-level CC0).
- The official NGA IIIF endpoint `https://api.nga.gov/iiif/{uuid}` was downloaded in [GitHub Actions live QA](https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/45971101406), **29/29 JPEG successfully decoded**, HTTPS NGA hosts, dimensions and source UUID verified.
- All existing Art Drift catalogs (the existing 4,500 works plus 5 curated Commons) were cross-checked against NGA native `objectID` and artist/title; **7 existing NGA objects removed** from the 36 NGA paintings found, leaving **29 new NGA source identities**.
- The museum's policy https://www.nga.gov/artworks/free-images-and-open-access allows reuse of its Open Access images, including commercial uses. License in Art Drift: **CC0 1.0 for the exact NGA image**.
- Exact NGA object page link uses historical stable route `https://www.nga.gov/collection/art-object-page.<objectId>.html` which the institution redirects to the current object URL.

## Integration, image-host and quality gates

A deterministic generator `scripts/artdrift_nga29_source_import.py` combines exact source artifacts from run 45970465626 and media verification run 45971101406. The committed catalog `assets/museums/catalog_nga_openaccess_20261127.json` must reproduce **29 distinct verified records** byte-for-byte before any enabled build.

The album metadata includes title, artist, collection attribution, NGA object ID, medium, date, image UUID, legal statement, link to license and direct NGA IIIF image. The primary 600px preview was *decoded live*, while the larger 1600px IIIF view uses the same Open Access endpoint; the large variant still requires on-device assessment. No photograph is bundled into the APK: the payload is lightweight.

The source-specific Flutter getter `curatedNgaRightsEvidenceComplete` checks source-native ID, exact NGA rights notice, official CDN host, source and attribution, explicit file-specific sign-off. The independent build-time switch `ARTDRIFT_ENABLE_INSTITUTIONAL_NGA` is **OFF by default**, preventing silent change to the original canvas and preserving its 4,500 artworks.

- Normal app: 4,500 items.
- Test APK: `ARTDRIFT_ENABLE_CURATED_COMMONS=true` + `ARTDRIFT_ENABLE_INSTITUTIONAL_NGA=true` -> **4,534** paintings (5 Commons already curated + 29 new NGA).
- Existing NGA files on the legacy museum catalog are not modified; this is art-specific and does not change `packages/drift_core` or `GalleryDrift`.
- Image creator, source, CC0 and credits are shown in the existing details UI. Wallpaper export is disabled for these 29 records to keep the credit journey intact.

**Evidence boundary:** CI proof of NGA source/license and live IIIF sample is stronger than Wikimedia uploader self-report, but does not prove a full-size image is perfect, certify the store listing, physical phone performance or all regional cultural heritage obligations. No automatic public Play Store release.

## Wave QA

The importer checks 29/29 source/file pairs against pinned official images and rejects missing/changed IDs, copyright claims, image dimensions, CDN host changes and existing-catalog duplication. Flutter Web/Android analyze/test/build run **once** for this full batch, not 29 times.
