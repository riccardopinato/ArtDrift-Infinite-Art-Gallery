# ArtDrift web preview

This branch introduces a browser preview, not Android/Google Play production certification.

- Android remains the primary consumer; no changes to the shared Drift Core.
- Web caches refreshed art metadata in browser SharedPreferences. Android keeps its atomic support-directory cache.
- Wallpaper application is **Android only**; browsers must not claim it can set the phone wallpaper.
- Full-resolution external museum images and live museum API searches may require CORS permissions from each provider. Bundled paintings remain visible independently of those services.
- Run `bash scripts/web_preview_build.sh` with Flutter 3.50.1 available, or let the script install the pinned release.
- Web CI separately runs shared-core tests, app tests, analysis, and release-mode compilation.
- Vercel preview requires a successful deployment and live HTTP verification; successful CI alone is not a hosted website.
