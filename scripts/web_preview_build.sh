#!/usr/bin/env bash
set -euo pipefail
if ! command -v flutter >/dev/null 2>&1; then
  FLUTTER_ROOT="${TMPDIR:-/tmp}/artdrift-flutter-3.50.1"
  if [[ ! -x "$FLUTTER_ROOT/bin/flutter" ]]; then
    git clone --depth 1 --branch 3.50.1 https://github.com/flutter/flutter.git "$FLUTTER_ROOT"
  fi
  export PATH="$FLUTTER_ROOT/bin:$PATH"
fi
flutter --version
flutter config --enable-web
flutter create --project-name artdrift --org com.riccardopinato --platforms=web .
rm -f test/widget_test.dart
flutter pub get

# Supabase is an OPTIONAL, account-scoped capability. Vercel preview receives
# public client settings via project environment variables (never privileged
# service_role, sb_secret_* or Google OAuth client secrets). Without either
# variable, keep the guest experience; with only one, FAIL the build.
dart_defines=()
if [[ -n "${SUPABASE_URL:-}" || -n "${SUPABASE_PUBLISHABLE_KEY:-}" ]]; then
  if [[ ! "${SUPABASE_URL:-}" =~ ^https://[a-z0-9-]+[.]supabase[.]co/?$ ]]; then
    echo "::error::SUPABASE_URL is missing or is not an HTTPS Supabase project origin" >&2
    exit 1
  fi
  if [[ "${SUPABASE_PUBLISHABLE_KEY:-}" != sb_publishable_* ]]; then
    echo "::error::Missing or invalid Supabase public client key; never use service_role/secret" >&2
    exit 1
  fi
  dart_defines+=("--dart-define=SUPABASE_URL=${SUPABASE_URL}")
  dart_defines+=("--dart-define=SUPABASE_PUBLISHABLE_KEY=${SUPABASE_PUBLISHABLE_KEY}")
  echo "ARTDRIFT_CLOUD_BUILD_CONFIG=ENABLED (public client configuration only)"
else
  echo "ARTDRIFT_CLOUD_BUILD_CONFIG=DISABLED (offline guest mode)"
fi

# Cloudflare D1 exposes only PUBLIC museum metadata via a read-only Worker.
# The only accepted endpoint in this PR is the explicitly tested staging API.
# Existing Web/Android production builds remain offline-first unless opted in.
if [[ -n "${ARTDRIFT_CATALOG_API_BASE:-}" ]]; then
  if [[ "${ARTDRIFT_CATALOG_API_BASE}" != "https://artdrift-catalog-staging.riccardopinato.workers.dev" ]]; then
    echo "::error::ARTDRIFT_CATALOG_API_BASE is not the approved staging Worker" >&2
    exit 1
  fi
  dart_defines+=("--dart-define=ARTDRIFT_CATALOG_API_BASE=${ARTDRIFT_CATALOG_API_BASE}")
  echo "ARTDRIFT_D1_PREVIEW=ENABLED (public read-only museum discovery)"
else
  echo "ARTDRIFT_D1_PREVIEW=DISABLED (offline-first catalog remains available)"
fi

# A private Vercel preview may opt into the new chromatic Home; regular
# production/Android builds keep current persisted canvas behavior.
if [[ "${ARTDRIFT_PREVIEW_COLOR_HOME:-0}" == "1" ]]; then
  flutter build web --release --base-href / "${dart_defines[@]}" --dart-define=ARTDRIFT_VISUAL_HOME_DEFAULT=true
else
  flutter build web --release --base-href / "${dart_defines[@]}"
fi
# Android ships the validated WebP bundle as Flutter assets. On Web, these
# same files are already served from /museum_thumbs/ and loaded as URLs.
# Drop only the redundant Flutter asset copies in the generated output.
# Do not touch the authoritative source files or the Web URL thumbnail pack.
if [[ -s build/web/museum_thumbs/manifest.json ]]; then
  rm -rf build/web/assets/web/museum_thumbs
fi
