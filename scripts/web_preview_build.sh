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
# A private Vercel preview may opt into the new chromatic Home; regular
# production/Android builds keep current persisted canvas behavior.
if [[ "${ARTDRIFT_PREVIEW_COLOR_HOME:-0}" == "1" ]]; then
  flutter build web --release --base-href / --dart-define=ARTDRIFT_VISUAL_HOME_DEFAULT=true
else
  flutter build web --release --base-href /
fi
# Android ships the validated WebP bundle as Flutter assets. On Web, these
# same files are already served from /museum_thumbs/ and loaded as URLs.
# Drop only the redundant Flutter asset copies in the generated output.
# Do not touch the authoritative source files or the Web URL thumbnail pack.
if [[ -s build/web/museum_thumbs/manifest.json ]]; then
  rm -rf build/web/assets/web/museum_thumbs
fi
