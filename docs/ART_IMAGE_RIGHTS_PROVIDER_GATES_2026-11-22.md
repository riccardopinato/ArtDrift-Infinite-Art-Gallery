# Art Drift — image-redistribution policy gates (2026-11-22)

Status: **source-policy reconnaissance, NOT commercial-release certification**.
Automated selection never replaces the artwork's own record/image license.
A general CC0 metadata license is not necessarily an image license.
Brand names/trademarks and third-party privacy/personality rights remain separate.

## Official source references
| Source | Verified policy reference | New automated WebP wave |
| --- | --- | --- |
| The Met | https://www.metmuseum.org/hubs/open-access and https://www.metmuseum.org/policies/frequently-asked-questions-image-and-data-resources | ELIGIBLE only for records marked CC0/Open Access |
| Cleveland | https://www.clevelandart.org/open-access-api and https://www.clevelandart.org/open-access | ELIGIBLE only for CC0 image records |
| NGA | https://www.nga.gov/artworks/free-images-and-open-access | ELIGIBLE for provider-reported public domain/Open Access, with disclaimer |
| Rijksmuseum | https://data.rijksmuseum.nl/policy/ | ELIGIBLE for Public Domain Mark/CC0 object data/image provenance |
| Smithsonian | https://www.si.edu/termsofuse and https://www.si.edu/openaccess | ELIGIBLE only for CC0-designated media |
| Getty | https://www.getty.edu/projects/open-content-program/faqs/ and https://data.getty.edu/museum/collection/docs/ | HOLD until **individual image** is demonstrably in Getty Open Content/CC0; not every Getty media URL qualifies |
| SMK | https://connect.smk.dk/om/rettigheder and https://blog.smk.dk/how-to-do-things-with-data-creative-re-use-of-smks-digitized-collection | HOLD for new wave: per-image rights can differ |
| Mia | https://new.artsmia.org/copyright-and-image-access | HOLD for new wave until image-specific terms; general site images have use restrictions |
| Walters | https://thewalters.org/about/policies/rights-reproductions/ | HOLD for new wave pending verified object-level exception checks |
| Art Institute Chicago | https://api.artic.edu/docs/ | Separate bundled seed workflow; confirm image availability and individual public-domain eligibility |

## Operational separation
1. **Existing pack**: keep all 1,142 manifest entries and files intact, including
   sources not approved for *new* fetching. Do not silently drop artwork from
   the current gallery. Their eventual commercial distribution must be audited.
2. **New downloads**: allow only five checked providers, exact known official
   image URL host, public-domain/CC0 image metadata, expected evidence host and
   a bounded file size with actual WebP re-encode. Other providers remain HOLD.
3. **Network**: provider-friendly bounded worker pool, explicit redirects and
   transport validation. HTTP 403/404 and decode failures remain errors, not
   an excuse to substitute another artwork or a generic stock image.
4. **Release gate**: verify identity, license, official image URL, rights proof,
   source/provenance, attribution disclosures where applicable, derivative
   integrity and current terms before Play Store distribution.
5. **No guaranteed complete pack**: a failed or restricted host may leave a
   catalog painting as metadata/remote-only. Preserve correct counts.

This document describes a policy-screening heuristic and source references,
not legal advice or a per-object rights clearance.
