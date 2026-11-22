# Art Drift — faster museum image delivery (Web-first)

Scope: Art Drift only. Drift Core and Gallery Drift remain unchanged.

## Confirmed baseline
- 4,500 records; 457 bundled WebP thumbnails and 4,043 remote-only images
- Museum URLs remain the sole image providers. No proxy, paid API or bulk scrape.
- Existing Web strategy is HTML <img> for CORS-restricted origin hosts.
- Old prefetch used `precacheImage(NetworkImage)`, which is not a reliable
  reuse path for images displayed in Web HTML platform views.

## Applied optimization
- Browser-only speculative warmer creates a real HTML ImageElement and attaches
  load/error handlers before setting the **same URL** used by a visible tile.
  In this way the browser can reuse its own HTTP cache when origin headers
  permit. The image bytes are not fetched through a CORS-only Dart HTTP call.
- Native Android continues warming a resized Flutter ImageProvider.
- At most 3 speculative requests at once and 18 queued; 256-entry LRU of
  timed success/failure backoffs, preventing noisy repeats to blocked hosts.
- Failures are retried after 20 seconds on a later encounter, successes
  rechecked after 4 minutes. Rejected speculative requests are not cached.
- Visible Image.network requests render immediately, without waiting for the
  speculative queue; speculative concurrency is lower than before.
- Each mounted visible image has at most one delayed retry (1.6s) for temporary
  transport failures, and continues trying the official same-artwork preview
  before showing metadata fallback.
- The full-screen viewer uses the same museum's small official image while the
  larger candidate loads. The museum attribution and image rights stay intact.

## Intentional exclusions and release limitations
- No developer-managed permanent copy/cache of third-party media until
  museum-specific hotlink and cache/redistribution rights are reviewed.
- The browser's HTTP cache is controlled by each museum's headers; no promise
  that every warmup is retained or will be fast on every connection.
- A 403/404, hotlink denial, source outage or large remote preview remains
  outside the app's direct control.
- Multiple browser <img> platform views have rendering overhead.
- CI Web/Android and deterministic bounds tests are required. Browser/network
  performance QA and physical Android QA remain separate gates.
