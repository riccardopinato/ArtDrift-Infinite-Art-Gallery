#!/usr/bin/env python3
"""Parse Android emulator data; never report emulator stats as physical-device FPS."""
import argparse,json,re
from pathlib import Path

def match_number(data,pattern):
    m=re.search(pattern,data,flags=re.I|re.M)
    return int(m.group(1).replace(",","")) if m else None

def parse(root,out):
    def read(name):
        file=root/name
        return file.read_text(errors="replace") if file.exists() else ""
    before=read("memory_before.txt")
    after=read("memory_after.txt")
    gfx=read("gfxinfo.txt")
    frames=read("framestats.txt")
    errors=read("runtime_errors.log")
    # TOTAL PSS is Android system process measure, not Flutter image cache.
    def total_pss(text):
        return (match_number(text,r"^\s*TOTAL PSS:\s*([\d,]+)") or
                match_number(text,r"^\s*TOTAL\s+([\d,]+)\s+"))
    info={
      "environment":"Android emulator API 35, x86_64, software GPU, GitHub Linux runner",
      "physical_device":False,
      "swipe_gestures":48 if gfx else 0,
      "app_running_after":bool(read("pid_after.txt").strip()),
      "memory_pss_before_kib":total_pss(before),
      "memory_pss_after_kib":total_pss(after),
      "frames_rendered_reported":match_number(gfx,r"Total frames rendered:\s*([\d,]+)"),
      "janky_frames_reported":match_number(gfx,r"Janky frames:\s*([\d,]+)"),
      "frame_p50_ms_reported":match_number(gfx,r"50th percentile:\s*([\d,]+)ms"),
      "frame_p90_ms_reported":match_number(gfx,r"90th percentile:\s*([\d,]+)ms"),
      "frame_p95_ms_reported":match_number(gfx,r"95th percentile:\s*([\d,]+)ms"),
      "framestats_available":bool(frames.strip()),
      "android_runtime_errors_detected":"FATAL EXCEPTION" in errors,
      "caveats":"Software GPU emulator cannot substitute physical device RAM/FPS. Missing gfxinfo measurements are null, not zero."
    }
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(info,indent=2)+"\n")
    print("ARTDRIFT_EMULATOR_PROBE",json.dumps(info))
    if info["android_runtime_errors_detected"]:raise RuntimeError("Android crash in logcat")
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--in",dest="input",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    parse(args.input,args.out)
