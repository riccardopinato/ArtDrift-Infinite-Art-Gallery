#!/usr/bin/env bash
set -euo pipefail
OUT=build/g3/flight
mkdir -p "$OUT"
PKG=com.riccardopinato.artdrift
APK=build/app/outputs/flutter-apk/app-release.apk
test -s "$APK"
adb install -r "$APK"
adb shell svc wifi disable || true
adb shell svc data disable || true
adb shell am force-stop "$PKG" || true
adb shell monkey -p "$PKG" -c android.intent.category.LAUNCHER 1 >/dev/null
sleep 20
adb shell pidof "$PKG" > "$OUT/pid_before.txt"
test -s "$OUT/pid_before.txt"
size="$(adb shell wm size | tr -d '\r' | grep -oE '[0-9]+x[0-9]+' | tail -1)"
[[ "$size" =~ ^([0-9]+)x([0-9]+)$ ]]
W="${BASH_REMATCH[1]}"
H="${BASH_REMATCH[2]}"
echo "$size" > "$OUT/display_size.txt"
adb exec-out screencap -p > "$OUT/01_before_open.png"
test "$(stat -c%s "$OUT/01_before_open.png")" -gt 10000

# One launch and one screenrecord rather than many force-stop/relaunch cycles
# to reduce memory pressure and graphics instability on the runner.
adb shell screenrecord --size 540x1200 --bit-rate 2500000 --time-limit 9 \
  /sdcard/artdrift-g3-originflight.mp4 > "$OUT/screenrecord.log" 2>&1 &
recorder=$!
sleep 1
adb shell input tap "$((W/2))" "$((H*40/100))"  # real tile -> viewer
sleep 1
adb shell input tap "$((W*95/100))" "$((H*6/100))" # X top-right -> same tile
sleep 1
adb shell input tap "$((W/2))" "$((H*40/100))"  # second entrance
sleep 1
adb shell input tap "$((W*96/100))" "$((H*35/100))" # next artwork
sleep 1
adb shell input tap "$((W*95/100))" "$((H*6/100))" # X -> neutral fade
wait "$recorder"
adb pull /sdcard/artdrift-g3-originflight.mp4 "$OUT/02_museum_tile_flight.mp4"
test "$(stat -c%s "$OUT/02_museum_tile_flight.mp4")" -gt 25000
adb exec-out screencap -p > "$OUT/03_after_close.png"
test "$(stat -c%s "$OUT/03_after_close.png")" -gt 10000
adb shell pidof "$PKG" > "$OUT/pid_after.txt"
test -s "$OUT/pid_after.txt"
adb logcat -d -v brief -s AndroidRuntime:E flutter:E > "$OUT/runtime_errors.log" || true
python3 - "$OUT" <<'PY'
import hashlib, json, sys
from pathlib import Path
p=Path(sys.argv[1])
video=p/'02_museum_tile_flight.mp4'
errors=(p/'runtime_errors.log').read_text(errors='replace')
result={
 'source':'G3 isolated Android API35 x86_64 software GPU screenrecord',
 'code_sha':'ff6932ae23405b42e19b7ac4a2c6287e2ca0c4a5',
 'video_bytes':video.stat().st_size,
 'video_sha256':hashlib.sha256(video.read_bytes()).hexdigest(),
 'before_png_sha256':hashlib.sha256((p/'01_before_open.png').read_bytes()).hexdigest(),
 'after_png_sha256':hashlib.sha256((p/'03_after_close.png').read_bytes()).hexdigest(),
 'fatal_exception':'FATAL EXCEPTION' in errors,
 'status':'VIDEO_CAPTURED_PENDING_MANUAL_REVIEW',
 'warning':'A captured video is NOT proof of correct gestures, timing, or a passed G3/G4 gate; inspect actual frames.',
}
(p/'report.json').write_text(json.dumps(result,indent=2)+'\n')
print('G3_FLIGHT_VIDEO',json.dumps(result))
if result['fatal_exception']: raise SystemExit('Flutter/Android fatal in log')
PY
