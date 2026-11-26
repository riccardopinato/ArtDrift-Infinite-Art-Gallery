# Art Drift — curated Commons rights-gate, 27 November 2026

**Technical enablement only. No new painting is published or imported.**

The previous research [PR #84](https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/pull/84) discovered 486 images from seven painters. Pixel QA [PR #89](https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/pull/89) and [PR #90](https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/pull/90) decoded **459**, while **27** remained HTTP 429. Rights QA [PR #91](https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/pull/91) found 440 Commons PD, 6 CC0, 19 CC BY, 20 CC BY-SA, plus one unresolved Städel photo; final provenance [PR #92](https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/pull/92) found incomplete independent rights verification and suspected duplicates.

The new staging file `assets/museums/catalog_curated_commons.json` contains **[]**. Existing bundled and worldwide records remain 4,500. No thumbnails, images or artwork data were added.

## New per-image metadata and legal separation

`is_public_domain` refers only to the **underlying painting**. `rights_license` describes the **specific digital image**. A Commons candidate must be independently approved and meet all of these conditions before its record can appear on the canvas:

- `museum_source: commons`; numeric `id`; exact `source_identity: commons:<id>`; matching `museum_native_id`; `artwork_type_title: Painting`; artist and original painting public-domain status confirmed.
- `commercially_approved: true`, `source_provenance_verified: true`, `worldwide_distribution_reviewed: true` **only after independent documentary review**, plus a review trace in `rights_review_reference`.
- Image copyright and legal conditions specified in `rights_license`. The app supports explicit PD/CC0, CC BY and CC BY-SA 2.0–4.0 (including 2.5), while noncommercial / no-derivatives / unknown permissions cannot pass.
- A per-file `image_attribution`, `credit_line`, `rights_evidence_url` and `remote_museum_url` from official Commons File pages, with allowed Wikimedia image hosts; CC BY / BY-SA additionally requires an exact matching Creative Commons `image_license_url` canonical link.
- Image/photo credit `image_creator` and modification notice `image_modifications` are carried through to the detail screen.
- Wallpaper exporting is disabled for this new provider because direct wallpaper files cannot preserve attribution notices in an appropriate manner.

The Städel image stays blocked regardless of a metadata toggle due to conflicting rights declarations and conditions.

## No silent false license

For legacy museum works without `rights_license`, the detail screen now displays **Licenza immagine da verificare** rather than incorrectly claiming CC0. Approved existing Art Institute of Chicago works retain their documented public-domain fallback.

## Verification

Flutter unit tests simulate both a fully signed-off *synthetic test record* (which does not appear in the app) and unapproved source files. A separate QA gate confirms the local curated Commons catalog remains empty. Android and web Flutter build/test are required before merge. No automatic production release/deploy or Play Store publication.

**This PR is a code-only prerequisite, not legal clearance for any of the 486 images.**
