# Art Drift G2 — Web preview deployment record

**Deployment status:** Vercel `READY` (preview only), verified through Vercel project/deployment API.  
**Exact source:** `279ec531760a6f202a8867a23c7dd0d38a743383`.  
**App:** `riccardopinato/ArtDrift-Infinite-Art-Gallery`; candidate PR [#40](https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/pull/40) remains **Draft**.

**Preview URL:** https://artdrift-preview-f7piu0ym2-riccardo121296-2789s-projects.vercel.app/  
**Owner inspector:** https://vercel.com/riccardo121296-2789s-projects/artdrift-preview/Ft6ojijHC1MoN1qHFQSgR5MzyD1x

## Evidence

- GitHub [Web Preview CI run #45207857733](https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery/actions/runs/45207857733): `completed/success` on **exact** source SHA `279ec531...`. Includes Flutter Web release build and tests.
- Dedicated, non-production GitHub branch `feat/artdrift-web-preview-g2-20261123` created from exact candidate commit, **no source code changes**.
- Existing Vercel project `artdrift-preview` (`prj_5uSDOixaGEOKJ3jNjBUQWQsJjPBR`) reused; no production alias overwritten.
- Vercel deployment `dpl_Ft6ojijHC1MoN1qHFQSgR5MzyD1x`: API status `READY`. The build ran pinned Flutter Web script `scripts/web_preview_build.sh` using the public repository's **exact SHA**, echoed `ARTDRIFT_G2_PREVIEW_READY_SHA=279ec531760a6f202a8867a23c7dd0d38a743383`, and completed `build/web` deployment.
- A first attempt using GitHub source integration `dpl_HUzEttqKyqEJp1YKxtoBnnm8sZtQ` failed `git_info_fail` because Vercel lacks a GitHub Login Connection; that failed URL is **NOT** the preview. The successful deployment used the project's established inline build-script workflow, cloned the exact public SHA, and deployed successfully.
- Vercel project configuration currently reports `ssoProtection.enabled=true` for previews. Owner may need to sign in via Vercel; **anonymous public HTTP accessibility has not been independently established** (external fetch denied/unavailable). Do not call the preview public or unprotected.
- Preview only: Android wallpaper action remains Android-specific. Browser image providers may be subject to CORS. No Store release, production signing, Play rollout, data migration or public-asset commercial rights clearance is implied.
- The web preview is **not** proof that Android installed-data upgrade is safe. APK signer continuity G5 remains separately unresolved.

## Handoff

Open the preview link, inspect Art Drift's museum layout on phone/desktop, and report any visual mismatch (a screenshot is optional, not a formal G3 prerequisite). PR #40 remains Draft pending product review; main and Gallery Drift main were not changed.
