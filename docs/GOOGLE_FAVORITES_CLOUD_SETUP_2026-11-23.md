# Art Drift — Google account and private cloud favorites

**Status (2026-11-23):** DEDICATED SUPABASE BACKEND CREATED, schema and least-privilege grants applied and statically verified. **Google OAuth NOT ENABLED** and Android/Web cross-account end-to-end sync **NOT CERTIFIED**. No existing Anna Supabase resource was modified.

## Verified hosted backend (2026-11-23)

- Project: `artdrift`, ref `waewxkexxykffsounhrj`, region `eu-central-1`.
- Organization: `riccardopinato's Org` (Free). Provider quoted **USD 0/month** for this project.
- Dashboard: https://supabase.com/dashboard/project/waewxkexxykffsounhrj
- Public API URL (NOT a secret): `https://waewxkexxykffsounhrj.supabase.co`
- Google OAuth **authorized redirect URI** to configure in Google Cloud:
  `https://waewxkexxykffsounhrj.supabase.co/auth/v1/callback`
- Supabase redirect allowlist still needs an approved HTTPS Web origin and
  `com.riccardopinato.artdrift://login-callback/`.
- Migrations applied to Art Drift ONLY:
  `20261123165019_artdrift_favorites_v1` and
  `artdrift_favorites_least_privilege`.
- Verified: `public.artdrift_favorites` exists, RLS enabled, 3 user-owned
  SELECT/INSERT/UPDATE policies, zero initial rows, anon has no table privileges.
  Authenticated users have **SELECT/INSERT/UPDATE only**: DELETE, TRUNCATE,
  TRIGGER and REFERENCES are not granted. Supabase Security Advisor: no lints.
- The original SQL template was corrected to **REVOKE ALL from authenticated
  before GRANT SELECT, INSERT, UPDATE**. This matters because Supabase
  default privileges may include TRUNCATE, which is NOT controlled by RLS.
- Provider-based E2E verification remains blocked until Google Cloud credentials,
  Supabase Auth provider settings, redirect allowlist, Web/Android builds and
  two real Google identities/devices are configured and tested.
- A valid publishable key exists in Supabase; obtain it from the Dashboard.
  It is public-client configuration, **not** a Google client secret or
  `service_role` key. Do not publish privileged credentials.



## Architecture

- Guest mode: original `artdrift.favorites.keys.v2`,
  `artdrift.favorites.snapshots.v2` and numeric legacy v1 migration stay
  unchanged, with full offline browsing and favorites.
- Google account: Supabase Flutter OAuth via system browser, restored session
  and Android app link `com.riccardopinato.artdrift://login-callback/`.
  Web redirect returns to the same origin. Provider credentials must be set in
  Supabase Dashboard; Google client **secret is never placed in Flutter**.
- Cloud: `public.artdrift_favorites`, composite PK
  `(user_id, artwork_key)`, RLS enforcing `(select auth.uid()) = user_id`
  on SELECT/INSERT/UPDATE, no anonymous access, no direct DELETE.
  The `is_favorite=false` tombstone preserves cross-device removals.
- Local per-account cache: `artdrift.favorites.account.<uid>.*`.
  Pending writes: `artdrift.sync.pending.<uid>.v1`.
  The active account only sees its own cache. Sign-out returns to the guest
  collection, not the previous user's favorites.
- Sync: local changes become durable pending operations BEFORE upload; batch
  upserts then authoritative fetch; queued edits overlay stale remote rows.
  Errors leave queue intact, and retry runs on resume / periodic 90s interval /
  manual "Sync now". A successful GitHub build does NOT prove real OAuth or
  cross-device sync until backend tests.
- First login does **not** silently mix anonymous or previous-account data.
  "Import device favorites" requires explicit user confirmation, is non-
  destructive, and retains guest originals. Imports do not erase cloud rows.
- Identity: name and email are provided by Google/Supabase Auth; no raw Google
  tokens are written to app favorites or synced as artwork metadata. Locally
  stored session credentials are managed by `supabase_flutter` itself.
- No artwork images are uploaded; only provider-qualified artwork IDs and
  bounded factual metadata already present in Art Drift. Shared Drift Core
  and Gallery Drift stay untouched.

## Production setup checklist (required; not simulated)

1. **DONE (2026-11-23):** Create a dedicated `artdrift` project in the Free
   organization, EU region; quoted cost USD 0/month. No Anna project reused.
2. **SCHEMA DONE / LIVE ACCOUNT TEST PENDING:** Schema and least-privilege
   remediation applied, RLS/policies/grants inspected, Security Advisor clean.
   Still test with real user A/B: cross-account SELECT/UPDATE isolation,
   guest denial, own upserts, tombstones and reload on another device.
3. Enable Google provider in Supabase Auth. In Google Cloud configure
   consent screen, domain verification as applicable, and a Web OAuth Client.
   Put Google Client ID+SECRET only in **Supabase Auth provider settings**.
   Google's authorized redirect URI is
   `https://<SUPABASE_PROJECT_REF>.supabase.co/auth/v1/callback`.
4. In Supabase Auth redirect allowlist set an **approved stable HTTPS Web
   preview/production address** and
   `com.riccardopinato.artdrift://login-callback/`. Avoid unbounded wildcard
   domains; temporary Vercel deployment URLs change over time.
5. Build client with **publishable** parameters only:
   `--dart-define=SUPABASE_URL=https://<project-ref>.supabase.co` and
   `--dart-define=SUPABASE_PUBLISHABLE_KEY=sb_publishable_...`.
   Never embed `sb_secret_...`, `service_role` or Google client secret.
   The code intentionally leaves Google login inactive when not configured.
6. Test actual OAuth on Android **and Web**, login cancellation, reload,
   guest→account import, account A→B→A, offline favorite/remove/retry,
   fresh device cloud restoration and server-side RLS; use an unmodified
   app package/signature compatibility plan to preserve installed data.
7. Update hosted privacy notice / Play Data Safety and confirm provider
   data-processing/legal requirements before production deployment.

## CI / limitations

The PR runs Flutter analyze, existing and new tests, plus Android internal
APK. The existing Web Preview CI runs Flutter Web tests and build. Real login
cannot pass without external Google Console OAuth consent configuration.
Do not call `SYNC_CERTIFIED` merely from mocked gateway tests.

Rationale and source baseline: App Factory Core
`ede07c491e586215598ff68daec43e17d699aa51`,
`GOLDEN_GOOGLE_AUTH_SUPABASE_FLUTTER_v1` (COPY-READY, provider sensitive),
verified against current Supabase Flutter OAuth and RLS guidance.
