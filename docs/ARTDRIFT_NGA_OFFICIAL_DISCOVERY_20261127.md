# Art Drift — Official NGA seven-artist Open Access discovery (research lane)

Canonical App Factory Master v27, baseline `f8b9f550c544735237f19cdd723bd2df667ceee6`. This branch is READ-ONLY with respect to the actual artwork catalog and release code. No new artwork, rights waiver, download, cloud service, release or SDK integration.

NGA official primary dataset: https://github.com/NationalGalleryOfArt/opendata, pinned commit `3a187753c941dd153c2632cffc15d802f171e012` (26 November 2026).

The metadata files are CC0, but **the photographs are NOT all freely reusable**. Official [NGA Data Dictionary](https://github.com/NationalGalleryOfArt/opendata/blob/main/documentation/Data%20Dictionary.txt) distinguishes image `openaccess=1` (no restrictions under the NGA Open Access program) from `openaccess=0` (fair-use/restricted). This pipeline joins artist IDs, painting objects, and NGA image-level rights by source-native ID, excludes restricted and non-primary photographs, and compares with all five Art Drift catalog files plus curated Commons.

**Artists:** Claude Monet, Alfred Sisley, Gustave Caillebotte, Otto Modersohn, Harald Sohlberg, Serhii Vasylkivskyi, Ludvig Karsten. No string matching of accidental title keywords is accepted as artist provenance.

Output includes source-per-image URL/IIIF UUID, record/artist/title, image-level Open Access evidence, dimensions, and reasons for existing/held status. All output `commercially_approved=false`, `runtime_visible=false`. A follow-on release implementation may admit only records with live image delivery, exact institution policy, dedup and technical review, using the existing app-specific `nga` provider or an explicit source-specific rights gate.

**Why this matters:** instead of rechecking hundreds of auction/Flickr uploads, this builds a primary-source shortlist from the museum's dataset with a clean image-specific rights field. Art Drift's shared infinite canvas engine is unchanged; GalleryDrift is untouched. No public deployment.
