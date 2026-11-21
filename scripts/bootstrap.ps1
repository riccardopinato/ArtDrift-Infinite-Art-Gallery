$ErrorActionPreference = 'Stop'
flutter create --project-name artdrift --org com.riccardopinato --platforms=android .
if ($LASTEXITCODE -ne 0) { throw 'flutter create failed' }
python scripts/patch_android.py
if ($LASTEXITCODE -ne 0) { throw 'Android patch failed' }
flutter pub get
if ($LASTEXITCODE -ne 0) { throw 'flutter pub get failed' }
flutter analyze --no-fatal-infos
if ($LASTEXITCODE -ne 0) { throw 'flutter analyze failed' }
flutter test
if ($LASTEXITCODE -ne 0) { throw 'flutter test failed' }
flutter build apk --debug
if ($LASTEXITCODE -ne 0) { throw 'APK build failed' }
Write-Host 'APK: build/app/outputs/flutter-apk/app-debug.apk'
