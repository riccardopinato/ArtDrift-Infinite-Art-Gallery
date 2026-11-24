# ArtDrift G2 safe-install internal test APK (2026-11-24)
- QA source `c3c9befd6d3979f68c19451820a0dfea757aa7c7`, PR #60 stacked on #59/#58.
- This workflow builds the same Flutter ArtDrift screens but overrides only the Android `applicationId` to `com.riccardopinato.artdrift.preview` **after** generating the shell; it does not mutate normal app product sources.
- Distinct Android package permits installation next to existing ArtDrift and cannot replace production user data. Original icon preserved with manifest label `ArtDrift QA`. The OAuth callback scheme is changed to `com.riccardopinato.artdrift.preview` to avoid intercepting the production sign-in redirect. The app has no Supabase configuration: **Google sign-in is intentionally NOT tested with this preview**.
- Build with product CI's Flutter version and optimize ARM64; verify the actual appId from APK (AAPT), signer (apksigner), sha256 and tests on exact source.
- Internal signing only, unrelated to the certificate installed on user's device; do not confuse APK QA with a safe in-place *update* of the production package.
- Art image commercial usage remains HOLD, so the artifact is for private evaluation, **not** public redistribution/Play Store. Do not enable real ads or production deploy.
- On-device acceptance still requires real phone actions, screenshot parity, pan/zoom, frame time, RAM/thermal, restore/camera and accessibility, recorded separately.
