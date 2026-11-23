#!/usr/bin/env python3
"""Evaluate an Art Drift Android emulator smoke, never fabricate FPS or physical QA."""
import argparse
import hashlib
import json
import re
from pathlib import Path


def match_number(data, pattern):
    m = re.search(pattern, data, flags=re.I | re.M)
    return int(m.group(1).replace(",", "")) if m else None


def parse(root: Path, out: Path):
    def read(name):
        path = root / name
        return path.read_text(errors="replace") if path.exists() else ""

    before = read("memory_before.txt")
    after = read("memory_after.txt")
    gfx = read("gfxinfo.txt")
    frames = read("framestats.txt")
    errors = read("runtime_errors.log")

    def total_pss(value):
        return (
            match_number(value, r"^\s*TOTAL PSS:\s*([\d,]+)")
            or match_number(value, r"^\s*TOTAL\s+([\d,]+)\s+")
        )

    rendered = match_number(gfx, r"Total frames rendered:\s*([\d,]+)")
    after_png = root / "screenshot.png"
    before_png = root / "screenshot_before.png"
    mid_png = root / "screenshot_mid.png"
    screenshot_before_bytes = before_png.stat().st_size if before_png.exists() else 0
    screenshot_after_bytes = after_png.stat().st_size if after_png.exists() else 0
    screenshot_mid_bytes = mid_png.stat().st_size if mid_png.exists() else 0
    sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None
    before_hash, mid_hash, after_hash = map(sha, (before_png, mid_png, after_png))
    ui_xml = "\\n".join(read(name).lower() for name in ("ui_before.xml", "ui_mid.xml", "ui_after.xml"))
    dialog_detected = ("quickstep" in ui_xml and "responding" in ui_xml) or "isn't responding" in ui_xml or "not responding" in ui_xml
    offline_flag = read("airplane_mode.txt").strip() == "1"
    started = bool(read("pid_before.txt").strip())
    survived = bool(read("pid_after.txt").strip())
    completed = match_number(read("gestures_completed.txt"), r"(\d+)")
    crash = "FATAL EXCEPTION" in errors
    failures = []
    if not offline_flag:
        failures.append("offline_mode_not_confirmed")
    if not started:
        failures.append("process_not_running_after_launch")
    if not survived:
        failures.append("process_not_running_after_pan")
    if completed != 48:
        failures.append("swipe_sequence_incomplete")
    if min(screenshot_before_bytes, screenshot_mid_bytes, screenshot_after_bytes) < 4096:
        failures.append("missing_or_tiny_screenshot")
    if before_hash and mid_hash and before_hash == mid_hash:
        failures.append("canvas_did_not_visibly_change_after_first_swipe")
    if dialog_detected:
        failures.append("system_anr_dialog_visible")
    if crash:
        failures.append("android_runtime_crash")

    info = {
        "environment": "Android emulator API 35, x86_64, software GPU, GitHub Linux runner",
        "physical_device": False,
        "offline_first_launch_airplane_setting_confirmed": offline_flag,
        "app_running_before": started,
        "app_running_after": survived,
        "swipe_gestures_completed": completed,
        "first_screenshot_bytes": screenshot_before_bytes,
        "mid_screenshot_bytes": screenshot_mid_bytes,
        "after_screenshot_bytes": screenshot_after_bytes,
        "screenshots_sha256": {"before": before_hash, "after_first_swipe": mid_hash, "after": after_hash},
        "canvas_changed_after_first_swipe": bool(before_hash and mid_hash and before_hash != mid_hash),
        "system_anr_dialog_visible": dialog_detected,
        "system_dialog_recovery_attempted": bool(read("system_dialog_recovery.txt").strip()),
        "memory_pss_before_kib": total_pss(before),
        "memory_pss_after_kib": total_pss(after),
        "frames_rendered_reported": rendered,
        "janky_frames_reported": match_number(gfx, r"Janky frames:\s*([\d,]+)"),
        "frame_p50_ms_reported": match_number(gfx, r"50th percentile:\s*([\d,]+)ms"),
        "frame_p90_ms_reported": match_number(gfx, r"90th percentile:\s*([\d,]+)ms"),
        "frame_p95_ms_reported": match_number(gfx, r"95th percentile:\s*([\d,]+)ms"),
        "frame_metrics_status": "AVAILABLE" if rendered and rendered > 0 else "NOT_VERIFIED",
        "framestats_available": bool(frames.strip()),
        "runtime_fatal_error": crash,
        "visual_review_status": "NOT_VERIFIED",
        "physical_device_status": "NOT_VERIFIED",
        "smoke_status": "PASS" if not failures else "FAIL",
        "failures": failures,
        "caveats": (
            "Airplane setting plus disabled Wi-Fi/data is emulator evidence, not a network packet audit. "
            "All three screenshots and one directional swipe are compared, but visual review is separate. "
            "Emulator memory/FPS do not certify a physical device. "
            "Unavailable gfxinfo percentile fields are null, not zero."
        ),
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(info, indent=2) + "\n")
    print("ARTDRIFT_V038_EMULATOR_PROBE", json.dumps(info))
    if failures:
        raise RuntimeError("Emulator smoke failed: " + ", ".join(failures))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--in", dest="input", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    parse(args.input, args.out)
