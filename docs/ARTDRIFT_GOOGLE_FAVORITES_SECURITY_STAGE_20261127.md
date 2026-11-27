# Art Drift — optional Google favorites security staging (reconciled 4008973c52e6 on 2026-11-27)

Source candidate #109 at `82622fd125ada0c7e16d1d94938dd1c61575e1c8`; current UI source-of-truth includes all G2 painting transitions (#111), 2,400-color canvas, 12 collections, Doppleganger and optional random launch. This branch is a clean source-port; it does NOT replace the main canvas or remove modern UI.

- Feature is disabled and **hidden** unless public build-time `SUPABASE_URL` (HTTPS) and `SUPABASE_PUBLISHABLE_KEY` are configured. The app always works offline and without login.
- User-specific favorite namespaces; guest favorites not overwritten or silently uploaded; guest import requires explicit consent. Offline edits use account-scoped persistent queue and soft-delete tombstones. RLS and per-user policies were read-only verified in the dedicated Art Drift Supabase project on 2026-11-27.
- Android callback is patched in generated AndroidManifest.xml; Web OAuth uses path strategy only when auth configured.
- No service-role key, cloud DDL, account migration, data transfer or public deployment in this change.
- **HOLD** pending physical signed Android OAuth callback, Web Google provider configuration, two independent real A/B account sessions and cross-device tombstone propagation, privacy/data-safety disclosure and rights signoff.
- Do not merge this Draft source candidate on CI alone. Supabase advisor notes password leak protection disabled: https://supabase.com/docs/guides/auth/password-security#password-strength-and-leaked-password-protection .
