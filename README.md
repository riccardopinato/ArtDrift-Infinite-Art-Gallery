# ArtDrift — Infinite Art Gallery

**An independent Android Flutter application for exploring art on an endless, touch-controlled canvas.**

## What the reference video tells us

The 47.5-second user-supplied reference shows a dark, edge-to-edge, dense mosaic of artworks. Scrolling/panning reveals different images. Selecting a painting opens an immersive dark detail view with a large full-frame image, artist/title, a concise description and close/previous/next actions. ArtDrift implements the **interaction concept**, not the website's branding, code, proprietary images, feed, curated metadata or text.

## Included in v0.2 source

- Two-dimensional pan and pinch zoom, optional fling momentum and reset.
- Stable world coordinates and deterministic mosaic assignment, including negative/very distant coordinates.
- Viewport culling (at most 180 mounted image tiles) and **72 verified genuine painting thumbnails in tiny bundled WebP files (~0.23 MB total)**. A metadata snapshot (~0.06 MB) lets the mosaic show paintings even on first boot and in airplane mode.
- Artwork detail, zoom/pan, previous/next, an original factual caption, favorites and link to museum.
- Manually set Android Home, Lock or both wallpapers with confirmation (Android 7+).
- Art Institute of Chicago Open Access metadata and IIIF images, only records flagged public domain (paintings with valid image ID). The **pinned initial catalog needs no internet**; opening a painting optionally downloads a better 843px version and retains its small preview as fallback.
- Dark original visual style, no login, no ads, no copied site assets.

## Known limitations / release gates

- The catalog is **not** a manually curated and individually rights-audited commercial release. Do not publish before provider terms, individual image rights and attribution are reviewed.
- A pinned set of 72 verified public-domain paintings from the Art Institute of Chicago appears immediately. Repetition is possible in distant canvas regions until an approved larger catalog is built.
- All **initial canvas previews remain visible offline** because they are tiny bundled WebP files; higher-resolution artwork/wallpaper still requires internet. A durable optional disk cache for full-resolution images remains future scope.
- Zoom-out/scroll jank and native wallpaper behavior need real Android device tests.
- GitHub artifacts are **testing APKs**, not production-signed Google Play releases. The ARM64 release-mode build uses the temporary Flutter scaffold signing identity, not persistent production signing.
- This is a **source prototype**, not an independently verified reproduction of all original website behavior.

## Build on Windows

Install Flutter, Android SDK, Java and Python. From the checkout root:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/bootstrap.ps1
```

Debug APK: `build/app/outputs/flutter-apk/app-debug.apk`.

## GitHub Actions

`.github/workflows/android.yml` runs Flutter analyze, tests validating every pinned image asset, and an optimized Android ARM64 **internal** APK signed with a non-production testing identity. Artifacts are downloadable from a successful run's **Artifacts** section. The previously generated universal debug APK remains available in its earlier run. Do not assume APKs signed on different runners can update each other in-place.

## Copyright and data

Art Institute of Chicago Open Access and IIIF: https://api.artic.edu/docs/ . Source museum supplies the rights flag, not ArtDrift. We do not copy AIC's Creative Commons Attribution 4.0 narrative `description`; the short text here is generated solely from metadata. The UI, code, names and interaction architecture of this app are independent work. Do not copy screenshots or media from the reference site.

Repository identity: `riccardopinato/ArtDrift-Infinite-Art-Gallery`.

## Image footprint

The 72 artwork thumbnails are source-pinned under `assets/gallery/thumbs/*.webp` (~239 KB raw combined). Their corresponding museum metadata lives in `assets/gallery/catalog.json` (~63 KB). **No high-resolution paintings ship in the APK**. See [docs/IMAGE_PIPELINE.md](docs/IMAGE_PIPELINE.md). The app memory image cache is capped at 48 MiB.
