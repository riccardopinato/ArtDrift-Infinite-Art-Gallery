#!/usr/bin/env bash
set -euo pipefail
OUT="build/g3/captures"
PKG="com.riccardopinato.artdrift"
APK="build/app/outputs/flutter-apk/app-release.apk"
mkdir -p "$OUT"
test -s "$APK"
adb install -r "$APK"

# Test-only emulator: no personal gallery, AdMob, account, purchase or cleanup.
adb shell cmd connectivity airplane-mode enable >/dev/null 2>&1 || true
adb shell svc wifi disable || true
adb shell svc data disable || true

size="$(adb shell wm size | tr -d '\r' | grep -oE '[0-9]+x[0-9]+' | tail -1)"
if [[ "$size" =~ ^([0-9]+)x([0-9]+)$ ]]; then
  W="${BASH_REMATCH[1]}"; H="${BASH_REMATCH[2]}"
else
  echo "No valid emulator display size: $size" >&2; exit 1
fi
echo "$size" > "$OUT/display_size.txt"
tap() { adb shell input tap "$1" "$2"; }
snapshot() {
  local name="$1"
  adb exec-out screencap -p > "$OUT/${name}.png"
  test "$(stat -c%s "$OUT/${name}.png")" -gt 10000
  adb shell uiautomator dump /sdcard/artdrift-g3.xml >/dev/null 2>&1 || true
  adb shell cat /sdcard/artdrift-g3.xml > "$OUT/${name}.xml" 2>/dev/null || true
}
home() {
  adb shell am force-stop "$PKG" || true
  adb shell monkey -p "$PKG" -c android.intent.category.LAUNCHER 1 >/dev/null
  sleep 9
  adb shell pidof "$PKG" >/dev/null
}
home
snapshot 01_home
# On-screen coordinates are derived from the emulator resolution and correspond
# to the original top-center brush, top-right heart and gear controls.
tap "$((W/2))" "$((H*8/100))"
sleep 3
snapshot 02_search_atrium
home
tap "$((W*81/100))" "$((H*8/100))"
sleep 3
snapshot 03_favorites
home
tap "$((W*92/100))" "$((H*8/100))"
sleep 3
snapshot 04_curator_settings
home
# A real tile on the current initial canvas, not a mocked image.
tap "$((W/2))" "$((H*40/100))"
sleep 5
snapshot 05_artwork_detail
tap "$((W*96/100))" "$((H*35/100))"
sleep 2
snapshot 06_next_artwork
home
adb shell input swipe "$((W/2))" "$((H*40/100))" "$((W/2))" "$((H*40/100))" 850
sleep 3
snapshot 07_long_press_plaque
home
# Verified via UIA 1080×2400: speed button bounds [302,283]–[473,388].
# Aim at center (36% width, 14% height), not at artwork above the button.
tap "$((W*36/100))" "$((H*14/100))"
sleep 2
snapshot 08_auto_speed_menu
home
tap "$((W*13/100))" "$((H*84/100))"
sleep 2
snapshot 09_immersion

# Prove the canvas returns after closing original artwork, then after a
# next-artwork switch. Image download/position may differ; review manually.
home
snapshot 10_camera_before_detail
tap "$((W/2))" "$((H*40/100))"
sleep 2
tap "$((W*5/100))" "$((H*6/100))"
sleep 2
snapshot 11_canvas_after_original_close
home
tap "$((W/2))" "$((H*40/100))"
sleep 2
tap "$((W*96/100))" "$((H*35/100))"
sleep 1
tap "$((W*5/100))" "$((H*6/100))"
sleep 2
snapshot 12_canvas_after_changed_close

# A real-screen video is needed to inspect the 330 ms entry/exit path.
# Screenrecord remains test-only; no user photos or personal content.
home
adb shell screenrecord --size 540x1200 --bit-rate 2800000 --time-limit 9 \
    /sdcard/artdrift-g3-flight.mp4 >/dev/null 2>&1 &
recorder=$!
sleep 1
tap "$((W/2))" "$((H*40/100))"
sleep 1
tap "$((W*5/100))" "$((H*6/100))"
sleep 1
tap "$((W/2))" "$((H*40/100))"
sleep 1
tap "$((W*96/100))" "$((H*35/100))"
sleep 1
tap "$((W*5/100))" "$((H*6/100))"
wait "$recorder" || true
adb pull /sdcard/artdrift-g3-flight.mp4 "$OUT/13_origin_flight.mp4" || true

adb logcat -d -v brief -s AndroidRuntime:E flutter:E > "$OUT/runtime_errors.log" || true

python3 - "$OUT" <<'PY'
import hashlib,json,sys
from pathlib import Path
out=Path(sys.argv[1])
files=sorted(out.glob('*.png'))
items={p.stem: {'size_bytes':p.stat().st_size,
                'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
       for p in files}
fatal='FATAL EXCEPTION' in (out/'runtime_errors.log').read_text(errors='replace')
if len(items)!=12 or fatal:
    raise SystemExit(f'CAPTURE_BAD count={len(items)} fatal={fatal}')
if len({v['sha256'] for v in items.values()}) < 3:
    raise SystemExit('CAPTURE_BAD insufficient distinct visual states')
report={
 'scope':'G3 preliminary visual evidence on emulator, not device QA',
 'target':'Art Drift integrated G2, unmerged',
 'display':(out/'display_size.txt').read_text().strip(),
 'screenshots':items,
 'runtime_fatal_error':fatal,
 'status':'CAPTURED_PENDING_HUMAN_REVIEW',
 'notes':'Twelve ADB coordinate-based screenshots plus best-effort frame transition video. Names are intended scenarios, not proof of their success; inspect PNG/XML/video. No 10/10 golden agreement or device acceptance implied.',
}
(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print('ARTDRIFT_G3_CAPTURE',json.dumps(report))
PY
