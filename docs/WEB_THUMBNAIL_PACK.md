# Web-only museum thumbnail pack

The source gallery has 4,500 works but only 457 packaged previews. This
rights-gated pipeline fetches a limited batch of the 4,043 remote-only CC0/
public-domain records and writes real WebP thumbnails to the existing Art Drift
Web application. It does not crawl museum sites, copy non-CC0 records or add
binary thumbnails to Android APKs.

The generator enforces museum-approved HTTPS hosts, per-record rights metadata
and HTTPS evidence URLs, a 3 MB source cap, a 24 MB decompression pixel cap,
8 total workers and 2 workers per host. Each WebP is <= 24 KB and <= 256 px.
One batch tries up to 1,200 new artworks, records provider failures separately,
and writes an index only for generated files that exist.

Provider download terms, possible rate limiting and attribution conditions
require review before making a batch public. HTTP 403/404 or inaccessible
images are not added. This does not guarantee 100% local coverage.

The Web runtime prefers a same-origin local WebP when the manifest verifies
the exact artwork ID. It still uses official museum images for the full-size
viewer, and falls back to the museum for missing pack entries.

Do not call build PASS proof that images were downloaded; inspect the real
coverage report and generated binary assets on the feature branch before merge.
