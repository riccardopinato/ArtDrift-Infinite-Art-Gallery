#!/usr/bin/env bash
set -euo pipefail
mkdir -p build/performance/emulator
PKG="com.riccardopinato.artdrift"
APK="build/app/outputs/flutter-apk/app-release.apk"
adb install -r "$APK"
adb shell monkey -p "$PKG" -c android.intent.category.LAUNCHER 1
sleep 25
adb shell pidof "$PKG" > build/performance/emulator/pid_before.txt
adb shell dumpsys gfxinfo "$PKG" reset > /dev/null || true
adb shell dumpsys meminfo "$PKG" > build/performance/emulator/memory_before.txt
# Alternate swipe directions; app is offline-first with native WebP previews.
for i in $(seq 1 12); do
  adb shell input swipe 950 800 130 800 200
  adb shell input swipe 130 800 950 800 200
  adb shell input swipe 500 1050 500 250 200
  adb shell input swipe 500 250 500 1050 200
done
sleep 8
adb shell pidof "$PKG" > build/performance/emulator/pid_after.txt
adb shell dumpsys gfxinfo "$PKG" > build/performance/emulator/gfxinfo.txt
adb shell dumpsys gfxinfo "$PKG" framestats > build/performance/emulator/framestats.txt
adb shell dumpsys meminfo "$PKG" > build/performance/emulator/memory_after.txt
adb shell screencap -p /sdcard/artdrift-pan.png
adb pull /sdcard/artdrift-pan.png build/performance/emulator/screenshot.png
adb logcat -d -v brief -s AndroidRuntime:E flutter:E > build/performance/emulator/runtime_errors.log || true
echo "EMULATOR_PAN_48_STROKES_COMPLETED"
