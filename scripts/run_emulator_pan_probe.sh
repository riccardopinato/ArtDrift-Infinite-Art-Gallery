#!/usr/bin/env bash
set -euo pipefail
mkdir -p build/performance/emulator

PKG="com.riccardopinato.artdrift"
APK="build/app/outputs/flutter-apk/app-release.apk"
test -s "$APK"
adb install -r "$APK"

# Force a fresh offline launch to exercise bundled thumbnail and catalog paths.
# This is emulator evidence; physical-device and full pixel review remain separate.
if ! adb shell cmd connectivity airplane-mode enable >/dev/null 2>&1; then
  adb shell settings put global airplane_mode_on 1
  adb shell am broadcast -a android.intent.action.AIRPLANE_MODE --ez state true >/dev/null 2>&1 || true
fi
adb shell svc wifi disable
adb shell svc data disable
adb shell settings get global airplane_mode_on | tr -d '\r' > build/performance/emulator/airplane_mode.txt
test "$(tr -d '\r\n' < build/performance/emulator/airplane_mode.txt)" = "1"

adb shell am force-stop "$PKG" || true
adb shell monkey -p "$PKG" -c android.intent.category.LAUNCHER 1
sleep 25

# An Android launcher ANR can cover Art Drift without crashing its process.
# Capture accessibility evidence and try one safe dismissal before recording.
capture_ui() {
  local dest="$1"
  adb shell uiautomator dump /sdcard/artdrift-g1-ui.xml >/dev/null 2>&1 || true
  adb shell cat /sdcard/artdrift-g1-ui.xml > "build/performance/emulator/$dest" 2>/dev/null || true
}
capture_ui ui_initial.xml
if grep -Eiq 'Quickstep|not responding|responding' build/performance/emulator/ui_initial.xml; then
  echo "system_dialog_initially_seen" > build/performance/emulator/system_dialog_recovery.txt
  adb shell input keyevent KEYCODE_BACK || true
  sleep 3
  adb shell am start -n "$PKG/.MainActivity" >/dev/null 2>&1 || true
  sleep 9
fi
capture_ui ui_before.xml
adb shell pidof "$PKG" > build/performance/emulator/pid_before.txt
test -s build/performance/emulator/pid_before.txt

# Preserve separate screenshots before and after interaction.
adb shell screencap -p /sdcard/artdrift-before.png
adb pull /sdcard/artdrift-before.png build/performance/emulator/screenshot_before.png
test -s build/performance/emulator/screenshot_before.png

adb shell dumpsys gfxinfo "$PKG" reset >/dev/null || true
adb shell dumpsys meminfo "$PKG" > build/performance/emulator/memory_before.txt
for i in $(seq 1 12); do
  adb shell input swipe 950 800 130 800 200
  if [[ "$i" -eq 1 ]]; then
    # Check movement at the first directional swipe, not only after
    # 12 symmetrical left/right/up/down cycles that may end at the origin.
    adb shell screencap -p /sdcard/artdrift-mid.png
    adb pull /sdcard/artdrift-mid.png build/performance/emulator/screenshot_mid.png
    capture_ui ui_mid.xml
  fi
  adb shell input swipe 130 800 950 800 200
  adb shell input swipe 500 1050 500 250 200
  adb shell input swipe 500 250 500 1050 200
done
echo 48 > build/performance/emulator/gestures_completed.txt

sleep 8
adb shell pidof "$PKG" > build/performance/emulator/pid_after.txt
test -s build/performance/emulator/pid_after.txt
adb shell dumpsys gfxinfo "$PKG" > build/performance/emulator/gfxinfo.txt
adb shell dumpsys gfxinfo "$PKG" framestats > build/performance/emulator/framestats.txt
adb shell dumpsys meminfo "$PKG" > build/performance/emulator/memory_after.txt
adb shell screencap -p /sdcard/artdrift-pan.png
adb pull /sdcard/artdrift-pan.png build/performance/emulator/screenshot.png
test -s build/performance/emulator/screenshot.png
capture_ui ui_after.xml
adb logcat -d -v brief -s AndroidRuntime:E flutter:E > build/performance/emulator/runtime_errors.log || true
echo "EMULATOR_OFFLINE_FIRST_LAUNCH_48_STROKES_COMPLETED"
