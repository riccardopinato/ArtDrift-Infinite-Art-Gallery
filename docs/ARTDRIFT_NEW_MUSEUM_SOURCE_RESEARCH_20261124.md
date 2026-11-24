# Art Drift — Expansion evidence, not a claim of image reuse rights

Verified public sources (24 Nov 2026):
- Cleveland Museum of Art [official API](https://openaccess-api.clevelandart.org/) has documented `cc0`, `type`, `has_image`, `skip` and `limit` filters and per-object `share_license_status`. This branch queries a bounded painting-only sample and excludes artworks already in Art Drift's 5,085-entry catalog. Art images and underlying third-party rights are not auto-approved; **all new records remain HOLD**.
- [Smithsonian Open Access](https://www.si.edu/openaccess/faq): CC0-marked media may be reused including commercial, but third-party publicity/trademark and underlying rights remain possible. Existing 558 source candidates need per-object checking.
- [Wikimedia Commons reuse guidance](https://commons.wikimedia.org/wiki/Commons:Reusing_content_outside_Wikimedia/licenses/en): 27 existing CC BY/SA candidates need file-by-file attribution and applicable share-alike conditions.
- [Tate metadata](https://github.com/tategallery/collection): metadata only; images require separate authorization. Existing 233 HOLD remain metadata-only.
- [Finnish National Gallery open datasets](https://avoindata.suomi.fi/data/en_GB/dataset/kansallisgallerian-kokoelma-aineistot/resource/db63ba66-cf6d-4991-9735-8adcd4f7ebe7): metadata CC0; its public collection includes images of copyrighted works too. **HOLD new adapter** until per-image rights filtering proven.
- [Belvedere Open Content](https://sammlung.belvedere.at/opencontent/images): object-specific CC0/IIIF possible; **HOLD new adapter** until access and rights verified per item.
- [Paris Musées API terms](https://apicollections.parismusees.paris.fr/cgu): CC0 exceptions to otherwise copyrighted museum imagery; **HOLD API access/integration** until client credentials/policy checked.
- [Yale Center for British Art](https://britishart.yale.edu/using-images) is institutionally distinct from Yale University Art Gallery: open access with artwork and photo rights separated; **HOLD source adapter**.
This is a bounded new-art research wave from an already integrated museum, plus current first-party documentation of other new sources. No external user data, remote SQL, R2, web deployment or APK.
