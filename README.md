# ArtDrift — Infinite Art Gallery

**An independent Android Flutter application for exploring art on an endless, touch-controlled canvas.**

## What the reference video tells us

The 47.5-second user-supplied reference shows a dark, edge-to-edge, dense mosaic of artworks. Scrolling/panning reveals different images. Selecting a painting opens an immersive dark detail view with a large full-frame image, artist/title, a concise description and close/previous/next actions. ArtDrift implements the **interaction concept**, not the website's branding, code, proprietary images, feed, curated metadata or text.

## Included in v0.1 source

- Two-dimensional pan and pinch zoom, optional fling momentum and reset.
- Stable world coordinates and deterministic mosaic assignment, including negative/very distant coordinates.
- Viewport culling (at most 180 mounted image tiles) and lower-resolution thumbnails.
- Artwork detail, zoom/pan, previous/next, an original factual caption, favorites and link to museum.
- Manually set Android Home, Lock or both wallpapers with confirmation (Android 7+).
- Art Institute of Chicago API metadata and IIIF images, only records flagged public domain (paintings with valid image ID). Cached catalog snapshot; first run requires internet.
- Dark original visual style, no login, no ads, no copied site assets.

## Known limitations / release gates

- The catalog is **not** a manually curated and individually rights-audited commercial release. Do not publish before provider terms, individual image rights and attribution are reviewed.
- A small subset of public-domain paintings is retrieved from the Art Institute of Chicago. Repetition is possible in distant canvas regions until an approved, versioned large catalog is built.
- Cached catalog metadata != offline images: images still require a network connection or Flutter image memory cache. A durable image cache/download manager is future scope.
- Zoom-out/scroll jank and native wallpaper behavior need real Android device tests.
- GitHub artifact is a **debug-signed APK for testing**, not a production-signed Google Play release.
- This is a **source prototype**, not an independently verified reproduction of all original website behavior.

## Build on Windows

Install Flutter, Android SDK, Java and Python. From the checkout root:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/bootstrap.ps1
```

Debug APK: `build/app/outputs/flutter-apk/app-debug.apk`.

## GitHub Actions

`.github/workflows/android.yml` runs Flutter analyze, widget/unit tests, and an Android debug APK build. The workflow unpacks initial source payload if necessary. Build artifacts are downloadable from the successful run's **Artifacts** section.

## Copyright and data

Art Institute of Chicago Open Access and IIIF: https://api.artic.edu/docs/ . Source museum supplies the rights flag, not ArtDrift. We do not copy AIC's Creative Commons Attribution 4.0 narrative `description`; the short text here is generated solely from metadata. The UI, code, names and interaction architecture of this app are independent work. Do not copy screenshots or media from the reference site.

Repository identity: `riccardopinato/ArtDrift-Infinite-Art-Gallery`.
