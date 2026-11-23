# Art Drift — maxi-step integration ledger (22 Nov 2026)

Status: development PR #23, NOT merged to main, not physical-device or Play certified.
Base: PR #18. Package: 0.3.6+9, internal-test ARM64 signing until separately proven.

## Source changes
- 457 original artwork previews and 1,142 global WebPs incorporated from
  previously validated assets for Android visual-first rendering.
- Full 4,500-record metadata catalog remains searchable; the default native
  canvas presents only images with real local previews.
- Persisted per-artwork source IDs preserve an established mosaic on upgrades.
- Shared Drift Core renders on-screen tiles first when its bounded limit is
  reached and warms ahead of manual pan or Auto. One canonical engine, Gallery
  Drift consumer candidate PR #13.
- Scope-indexed lexical metadata search avoids repeatedly reconstructing
  documents and feature hashes on every keystroke.
- Localized themed museum/date/subject collections, independent camera,
  collection-specific detail navigation.
- Tap-to-toggle contemplation mode in artwork detail.
- Settings: user-initiated frame-time p50/p95/p99 and decoded-image cache,
  report copied locally; not remote analytics and not device RSS.
- Web output avoids a duplicate copy of the images already hosted at the
  museum_thumbs URL. Core source files and bundle are preserved.

## AD audit ledger
| ID | New work | Remaining gate |
| --- | --- | --- |
| AD-01 | Existing 1,142 global WebPs reused; separate 1,200-attempt source-gated wave #21 | Missing actual images and image rights checks |
| AD-02 | Offline image-backed mosaic source | Physical fast pan and cold start |
| AD-03 | Official-provider policy and source checks | Per-image commercial redistribution review |
| AD-04 | Same-art local fallback retained | Real 403/CORS/outage telemetry |
| AD-05 | Persistent artwork-ID playlist and viewport priority | User-controlled catalogue expansion |
| AD-06 | Cached localized metadata search and thematic groups | Relevance/subject coverage QA |
| AD-07 | Opt-in local frame times and cache bytes | Physical device jank, CPU/GPU/RSS tests |
| AD-08 | Existing signed workflow preserved | Signing secrets, certificate and in-place update proof |
| AD-09 | Theme/period/museum collections from real fields | Hand-curated movements and artwork review |
| AD-10 | Existing source metadata and factual captions retained | Editorial completeness and translations |

## Device acceptance scenario (NOT executed by CI)
1. First install, offline start, long horizontal and vertical scroll, deep zoom,
   reverse direction and Auto at each speed, no incorrect-art placeholders.
2. Open collection, back, detail, favorites, museum and wallpaper confirmation.
   Cover 360px and tablet, gesture pinch/pan, rotation and app resume.
3. Capture actual local frame-time percentiles, full process RSS (external tool),
   battery/thermal, first-paint time, on-screen image failure ratios.
4. Test LTE with blocked URLs, HTTP 403/404 and intermittent network.
5. Verify stable signing certificate SHA-256, APK/source hashes, versionCode and
   data-safe upgrade without uninstalling the existing app.

No material in this PR is blanket legal certification of third-party image or
museum trademark rights.
