# Art Drift — Nine independent museum harvest lanes (2026-11-26)

## Why
The preceding collection pipeline took tiny image samples before testing the
full metadata inventory. This generated misleading low counts. The new
independent per-museum branches all use a metadata-first collector and preserve
the difference between objects discovered, objects eligible for inspection,
actual image pixels tested and artwork visually/commercially approved.

## Architecture
- One shared core of source adapters, source-specific queries and QA.
- Nine separate branches/PRs; each has its own workflow and JSON result.
- Museum-specific CI concurrency groups: no colliding writes or simultaneous
  Städel OAI batch shards.
- Rijksmuseum: official Linked Art search, 21 independent thematic/artist
  queries and paginated date-filtered identifiers, bounded metadata inspection.
- Swedish Nationalmuseum: institutional Wikimedia Commons categories,
  paginated category members and supplementary searches, rights per file.
- Städel: official OAI active LIDO records; no tombstone-as-artwork.
- Finnish National Gallery, Birmingham, Belvedere, Paris Musées, Te Papa and
  Nasjonalmuseet: institutional public Commons categories and attributable
  searches are independent discovery paths, NOT replacements for restricted
  museum APIs. All these branches retain provenance/rights HOLD.
- All source lanes produce their own report in
  research/museums/20261126/lanes/results/{museum}.json, plus optional contact
  sheet for human review, never import into gallery assets/main.

## Evidence contract
Only claim real metadata/page counts or actual image/pixel checks as run.
No estimated catalog totals become imported counts. Preserve record/file IDs,
images, provenance and rights source; ambiguity marked HOLD. Search result
alone does not establish museum custody, image rights or suitability.
One technical color PASS is not a curated painting. Rights must be reviewed
per file in the intended territory, for a commercial app.

## Limits
Lanes run with explicit bounded --max-records and --max-image-checks and
polite serial pagination; errors 401/403/429 are reported, not bypassed.
This is a stage-one discovery improvement, NOT an exhaustive harvest of
nine entire museum catalogs. Open-access data mirrored historically must not
be mistaken for fresh institutional evidence.

Core baseline: App-Factory-Core main 842dfa073451ec247308ccb4afb8ead5349bcbd4.
Research source: PR #71 at 39f07f3959ec3730df13ef1d0eb6c77d2a6e1136.
