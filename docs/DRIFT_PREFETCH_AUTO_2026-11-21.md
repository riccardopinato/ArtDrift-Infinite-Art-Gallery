# Drift Core — buffered image warmup and Auto controls

Product decision: 21 November 2026 (Art Drift and Gallery Drift). Canonical
source is `packages/drift_core` in ArtDrift. Other consumers pin this commit.

## Core behavior
- Ahead-of-camera world-tile scan is separate from mounted/visible tiles.
- Read-ahead in the direction of auto travel: up to ~1.6 viewport heights
  beyond the visible region. Manual exploration warms both directions.
- New item IDs are submitted in batches of 8, every ~260 ms, keeping a bounded
  dedupe history of 256 identifiers (per image zoom tier).
- Actual image/network/native thumbnail I/O is owned and bounded by each app.
- Auto starts stopped. Control below the upper-left brand toggles run/pause.
  It scrolls vertically through new paintings/photographs.
- Speed button cycles 25, 50, 75, 100 percent (36, 72, 108, 144
  logical pixels/second). The choice persists per camera namespace.
- Auto stops on manual pan/pinch, tapping a tile or recentering.
- Controls fade to 32% opacity after three seconds of inactivity, remaining
  interactive. No overlay banner, background timer or user-photo uploads.
- Native/UI performance, texture loading, remote museum server throttles and
  actual disk/browser cache hit rate require device/browser QA; prefetch cannot
  guarantee every remote image is available at every network speed.

## App boundaries
- Art Drift: bundles warm locally; remote images use the same browser HTML
  strategy as their displayed tiles; Android uses a bounded Flutter image cache.
- Gallery Drift: native 420x420 thumbnails warm in an app-private bounded memory
  LRU queue; the app never reads or uploads assets outside selected albums.
- Gallery Drift pins the same Drift Core SHA and does not copy core code.
