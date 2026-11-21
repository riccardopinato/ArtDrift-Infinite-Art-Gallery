# Art Drift — Web remote-image incident (21 November 2026)

The original preview had 457 bundled WebP thumbnails and 4,043 metadata-only
images from museum origins. Browsers enforcing CORS rejected some remote
image requests: canvas tiles became broken-image placeholders and the detail
viewer displayed "Immagine non raggiungibile".

## Correction

- Art-only renderer chooses `WebHtmlElementStrategy.fallback` on the Web,
  so museum images rejected by a CORS fetch can use HTML `img` elements.
  Native Android remains `never`, preserving its existing image pipeline.
- Detail viewer retries the official low-resolution preview after a distinct
  full-resolution source fails, where one is present.
- A genuinely inaccessible image (HTTP 403/404, origin blocks, missing file)
  is identified by its own artwork title and museum, not another artwork.
- Hide Android system-wallpaper action from the browser UI.
- No open proxy, no new third-party image host, no paid API or change to
  catalog licensing. No modifications to Drift Core or Gallery Drift.

## Evidence gates

- `flutter analyze`, targeted fallback tests and full app tests.
- Android build to ensure regression-free mobile compilation.
- Flutter Web release build and Vercel preview, followed by visual browser QA.
- Provider HTTP restrictions and Flutter HTML platform-view overhead remain
  runtime limits. A green build does not guarantee 4,043 image origins work.

Official Flutter API:
https://api.flutter.dev/flutter/widgets/Image/Image.network.html
https://api.flutter.dev/flutter/painting/WebHtmlElementStrategy.html
