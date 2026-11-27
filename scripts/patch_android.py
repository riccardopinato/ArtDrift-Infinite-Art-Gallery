#!/usr/bin/env python3
"""Patch a Flutter-generated Android shell with required platform features."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
manifest = root / 'android/app/src/main/AndroidManifest.xml'
if not manifest.exists():
    raise SystemExit('Missing Android shell. Run flutter create --platforms=android first.')
source = manifest.read_text(encoding='utf-8')
for permission in ('android.permission.INTERNET', 'android.permission.SET_WALLPAPER'):
    if permission not in source:
        source = source.replace('<application',
            f'<uses-permission android:name="{permission}" />\n    <application', 1)
if '<uses-permission android:name="android.permission.INTERNET"' not in source:
    raise SystemExit('Failed to install internet permission')
# Android browser OAuth callback is opt-in and never uses private credentials.
if 'android:scheme="com.riccardopinato.artdrift"' not in source:
    callback = '''
            <intent-filter android:autoVerify="false">
                <action android:name="android.intent.action.VIEW" />
                <category android:name="android.intent.category.DEFAULT" />
                <category android:name="android.intent.category.BROWSABLE" />
                <data android:scheme="com.riccardopinato.artdrift"
                    android:host="login-callback" />
            </intent-filter>
'''
    if '</activity>' not in source:
        raise SystemExit('Missing MainActivity for OAuth callback')
    source = source.replace('</activity>', callback + '        </activity>', 1)
manifest.write_text(source, encoding='utf-8')

native = root / 'android_source/MainActivity.kt'
dst = root / 'android/app/src/main/kotlin/com/riccardopinato/artdrift/MainActivity.kt'
dst.parent.mkdir(parents=True, exist_ok=True)
dst.write_bytes(native.read_bytes())
print('Native bridge and manifest installed. minSdk Android 24 required.')

# Flutter-generated gradle files can use Kotlin DSL or Groovy DSL.
for script in (root / 'android/app/build.gradle.kts',
               root / 'android/app/build.gradle'):
    if not script.exists():
        continue
    gradle = script.read_text(encoding='utf-8')
    if 'minSdk = flutter.minSdkVersion' in gradle:
        gradle = gradle.replace('minSdk = flutter.minSdkVersion', 'minSdk = 24')
    if 'minSdkVersion flutter.minSdkVersion' in gradle:
        gradle = gradle.replace('minSdkVersion flutter.minSdkVersion', 'minSdkVersion 24')
    script.write_text(gradle, encoding='utf-8')
