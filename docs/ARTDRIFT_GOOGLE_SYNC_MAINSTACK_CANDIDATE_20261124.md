# ArtDrift cloud favorites — main-stack reconciliation candidate, 24 November 2026

## Source of truth
- Old cloud logic and mocked edge-case tests: PR #41 `6e6a25f925ed8ac9f4c6ba0b7c83343c974d1e1a`, never merged, independently security-reviewed.
- Baseline: ArtDrift PR #59 `e9cab00fa20d6fc6087506c84c722d2c8c4fb7d0` (G2 10/10 candidate), core paired with GalleryDrift [PR #16](https://github.com/riccardopinato/GalleryDrift/pull/16).
- Factory baseline: `ede07c491e586215598ff68daec43e17d699aa51` Master v27.

## Live Supabase read-only evidence (24 Nov 2026)
- Dedicated `artdrift` project exists and is `ACTIVE_HEALTHY`; no new project, service or costs created.
- `public.artdrift_favorites` has RLS **enabled** and exact ownership policies for SELECT, INSERT, UPDATE; only `authenticated` has SELECT/INSERT/UPDATE grants, no `anon` grants and no DELETE grant. Data protected by `auth.uid()=user_id` and update `WITH CHECK`.
- Aggregate read-only count: **1 row, 0 active favorites, 1 tombstone**. Does **not** prove login or cross-device sync, and does not justify inspecting any identifiable account data.
- Supabase security advisor: one project warning, Leaked Password Protection Disabled; relevant to password flows. Review auth policy, not a reason to skip Google account tests.

## Product behavior
- Museum, search, favorites and full offline experience remain usable without sign-in or Supabase config. Google only starts if both `SUPABASE_URL` and `SUPABASE_PUBLISHABLE_KEY` are configured via build-time environment; publishable keys only, never service_role.
- Optional Android callback: `com.riccardopinato.artdrift://login-callback/`; Web uses clean current URL. Callback is declared by a source-controlled Android shell patch, not a manually generated project directory.
- Cloud queue/tombstones are durable, serialized per account, no unapproved guest import. Account A is hidden while account B is being loaded. User can explicitly import guest favorites only after accepting.
- **Do not restore old `ARTDRIFT_VISUAL_HOME_DEFAULT` camera alias** from #41; retain `artdrift.camera` and stable 4,500 legacy mapping. Search D1 cloud CTA and 635 HOLD catalog remain from #54/#58. Shared Drift Core unchanged from #59.
- No automatic production configuration, Supabase schema mutation, new Google OAuth provider, PII logs, photo sync or Play/AdMob activation.

## Gates before live-login certification
- [ ] Exact-head Flutter analyze/test Android, Web, core and internal ARM64, check offline account-disabled behavior.
- [ ] Validate Supabase Google OAuth provider in dashboard, allowed redirect URLs, Android app package + durable signing fingerprint and Web callback; build with the dedicated project's actual **public** config.
- [ ] Two independent real Google accounts A/B with RLS forced cross-user read/write denial, logout, token refresh and guest separation; real Android+Web devices, tombstone/delete propagation, offline queue and restore on new device.
- [ ] Confirm D1 search, museum 4,042 WebP, G2 visuals and QR? (no QR integration), and privacy disclosure remain unchanged.
- [ ] Rights and release signoff for art images, physical signature+upgrade; do not merge to main or release on CI alone.

**Outcome:** source candidate & simulated security tests only; `LIVE_GOOGLE_OAUTH=false`, `REAL_ACCOUNT_AB=false`, `CROSS_DEVICE_SYNC_CERTIFIED=false` until actual evidence.
