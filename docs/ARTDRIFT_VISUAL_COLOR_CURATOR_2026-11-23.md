# Art Drift — integrated color canvas v0.3.7+10, source-only candidate

Consolidation base: PR #33, clean catalog **4,499** works, exact proven
4,042/4,042 real global WebP assets and 457 original previews.
No changes to the Gallery Drift repository or canonical shared Drift Core.

## Pixel-screened canvas
- Evaluated **4,016** already available pixel-decodable images, held back
  483 too thin/unusable previews without deleting catalog records.
- Selected **2,400** paintings, **1,248** distinct artist labels.
- **1,684 colorful / 716 quieter** works selected according to HSV,
  bright-color fraction, entropy, contrast, darkness/sepia penalties.
- **11 Van Gogh / 8 Matisse** in palette, with original artwork identity.
- Every one of the 2,400 images is an actual bundled thumbnail, not a MoMA
  metadata-only record or AI-generated replacement.
- A visual contact sheet of 120 first images is a sampling aid; algorithmic
  pixel scores do NOT prove all 2,400 paintings are beautiful.
- New Android installs use this playlist on canvas by default; existing
  Android installs retain pinned artwork IDs to avoid remapping locations.
  Search > Colori e capolavori exposes a dedicated gallery for everybody.
- Web preview only: ARTDRIFT_PREVIEW_COLOR_HOME=1 enables visual Home
  using independent camera storage key; default Flutter build unaffected.
- Normal full catalog searches retain all 4,499 work entries.

## Measured limits and source rights
- 2,400 thumbnails cover 11.174 MiB of encoded WebP; in GitHub Linux CPU
  benchmark, 320 sampled decodes had p50=0.704ms and p95=1.10ms.
  These values are NOT Android FPS, cold-start seconds, network speed or
  physical device RAM.
- Android emulator sweep gathers process PSS, gfxinfo and screenshot on
  software GPU; the device certificate still requires physical phone.
- Source-policy license/provenance and exact-image identity gates remain
  enforced from PR #33. All commercial_release_cleared flags remain FALSE.
- MoMA metadata CC0 is not an image license; no unauthorized MoMA images.
- Existing Vercel Hobby project can host a **preview** with SSO; it is
  not an assertion of public commercial release.
- User Cloudflare D1 remains untouched and has no imported records.

## Signing and update-in-place
- VersionName 0.3.7 and versionCode 10 are build identifiers, not
  evidence of certificate continuity. Internal GitHub APK may use a
  different key from the device's installed APK.
- Do not uninstall the prior app or claim in-place update without comparing
  package ID, signing cert SHA-256, and versionCode against installed app.
- Production-signing workflow requires user-managed GitHub secrets and
  the actual existing app certificate, never ad hoc new keystore.
- Prior to Play release: review each image's commercial redistribution
  rights in its jurisdiction and the physical-device QA in issue #31.

## Portrait-share revision (23 Nov 2026)
- User-requested **70% reduction of portraits in the 2,400-work color canvas**.
- Reproducible automated classification: explicit portrait titles, likely
  sitter titles, and small-image frontal face detection (OpenCV Haar,
  face rectangle at least 2.5% of the preview area).
- The algorithm retains about 30% of flagged portraits, prioritizing vivid
  high-quality examples and diverse artists, replacing the other entries
  with actual existing image-backed, source-policy-approved works.
- The total remains 2,400; the original full museum catalog, actual WebP
  files, Cloudflare D1 and existing saved canvas placements are untouched.
- This is **heuristic** screening, not full human certification. False positives
  and negatives are possible, especially in historical narrative scenes.
- Run the exact image generator and inspect its portrait_policy manifest and
  contact sheet before describing the exact removal count.
