# Art Drift — MoMA on Cloudflare, metadata only

Status: candidate code, not a live deployment.

- **D1** stores 161,038 MoMA work records (source commit
  6ca06d4cc92dd39b57cec63278a63059cfa6c1a6, CC0 metadata).
- **Workers** exposes read-only indexed FTS5 search in pages of 24;
  bounded user input and parameterized SQL, query cache 60s/edge 600s.
- **R2 + custom CDN domain** is reserved for independently RIGHTS-CLEARED
  WebP thumbnails; none of the MoMA source images is covered by metadata
  CC0 and no images are imported by the pipeline.
- **Flutter** adds optional MoMA search to the existing search sheet only
  when the app is built with an explicit HTTPS Worker URL. Opening an
  image-less result leads to its official MoMA page; it never creates
  blank tiles in the infinite canvas.
- Art Drift's current offline images, tile identity, prefetch and viewport
  are unchanged. Gallery Drift and the shared Core are unchanged.

## Safe setup — explicit account action required

1. Create or connect an account on the Cloudflare Free tier; check usage
   dashboard and alerts. This PR does **not** create cloud resources.
2. Install Node 22 or newer; cd cloudflare/art-catalog; npm install.
3. Run npx wrangler login, then npx wrangler d1 create artdrift-moma-cc0.
4. Paste the database UUID into wrangler.jsonc and keep credentials outside
   GitHub. Run npx wrangler d1 execute artdrift-moma-cc0 --remote --file=./schema.sql.
5. Download the latest successful workflow artifact
   ArtDrift-MoMA-D1-SQL from GitHub Actions.
6. Import SQL shards in numeric order using
   npx wrangler d1 execute artdrift-moma-cc0 --remote --file=./import-0001.sql,
   changing filename for each shard. Monitor D1 daily rows-written.
   Free tier: 100,000 rows written/day, 5,000,000 rows read/day,
   500 MB **per database** and 5 GB across the account. Index writes may
   increase the chargeable row write count. Our export creates 322,076
   source insert statements, so import across several days on the free
   plan, not all at once. **No forced paid upgrade.**
7. Check SQL SELECT COUNT(*) FROM works returns 161038 and a few sample
   searches from Wrangler. Only then, and with account owner's approval,
   run npx wrangler deploy to expose the Worker publicly.
8. Build an *internal* Art Drift test with
   flutter build apk --release --dart-define=ARTDRIFT_CATALOG_API_BASE=https://YOUR-WORKER.workers.dev
   Before deployment, no endpoint exists; normal app search still works.

## Fast, rights-cleared images

An R2 bucket is optional initially: MoMA CC0 metadata does NOT authorize
the 161k images. For images with independently verified permission, create
an R2 bucket and attach a custom domain, then activate Cloudflare Cache.
Use deterministic immutable WebP object names and metadata proof; target
256–420 px, about 10–30KB per thumbnail. Use
Cache-Control: public, max-age=31536000, immutable only on content-hashed
immutable keys. Prefetch just near-future visible tiles. Validate device
latency, cache hit rate, errors and battery before claiming speed.

The development r2.dev URL is NOT intended for production traffic.
Do not bulk scrape the MoMA website or proxy licensed images.
Google Drive 15 GB is fine for private backup; it is not a scalable public
CDN (per-file download throttling, no optimized edge cache).
