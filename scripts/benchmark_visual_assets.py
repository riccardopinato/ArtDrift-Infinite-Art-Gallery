#!/usr/bin/env python3
"""Offline preview decode budget on a CI CPU, never Android FPS/network/RAM."""
import argparse, json, math, time
from collections import Counter
from pathlib import Path
from PIL import Image

def quantile(values,q):
    values=sorted(values)
    return round(values[math.ceil(q*(len(values)-1))],3)

def measure(root,out,samples=320):
    m=json.loads((root/"assets/museums/canvas_visual_color_v1.json").read_text())
    keys=m["selection"]
    assert len(keys)==2400 and len(set(keys))==2400
    records={}
    for f in ("assets/gallery/catalog.json","assets/museums/catalog.json",
              "assets/museums/catalog_global.json"):
        for row in json.loads((root/f).read_text()):
            records[(row.get("museum_source") or "aic")+":"+str(row["id"])]=row
    paths={}; sizes=[]; pixel_sizes=[]; sources=Counter()
    for key in keys:
        if key not in records:raise ValueError("Missing work: "+key)
        source,ident=key.split(":")
        if source=="aic":
            path=root/"assets/gallery/thumbs"/(ident+".webp")
        else:
            path=root/"assets/museums/thumbs"/(source+"_"+ident+".webp")
            if not path.exists():
                path=root/"web/museum_thumbs"/(source+"_"+ident+".webp")
        if not path.is_file():raise ValueError("Missing image: "+key)
        n=path.stat().st_size
        if n>25000:raise ValueError("Oversized image: "+key)
        with Image.open(path) as im:
            if im.format!="WEBP":raise ValueError("Wrong format "+key)
            w,h=im.size
        paths[key]=path;sizes.append(n);pixel_sizes.append(w*h*4)
        sources[source]+=1
    chosen=[keys[i*len(keys)//min(len(keys),samples)]
        for i in range(min(len(keys),samples))]
    times=[]
    for key in chosen:
        start=time.perf_counter()
        with Image.open(paths[key]) as im:
            im.load();im.convert("RGBA")
        times.append((time.perf_counter()-start)*1000)
    report={
        "environment":"Linux x86 GitHub CI CPU; NOT Android",
        "network_ms_measured":False,
        "actual_android_fps_measured":False,
        "actual_device_rss_measured":False,
        "image_count":len(keys),"sample_decodes":len(chosen),
        "decode_p50_ms":quantile(times,.50),
        "decode_p95_ms":quantile(times,.95),
        "decode_p99_ms":quantile(times,.99),
        "encoded_total_mib":round(sum(sizes)/1048576,3),
        "encoded_p95_kib":round(quantile(sizes,.95)/1024,2),
        "decoded_p95_preview_mib":round(quantile(pixel_sizes,.95)/1048576,3),
        "illustrative_40_thumbnails_raster_mib":round(40*quantile(pixel_sizes,.95)/1048576,2),
        "source_distribution":dict(sources),
        "commercial_release_cleared":False
    }
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2)+"\n")
    print("ARTDRIFT_OFFLINE_IMAGE_QA",json.dumps(report))
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--repo",type=Path,default=Path(__file__).resolve().parents[1])
    p.add_argument("--out",type=Path,default=Path("build/performance/benchmark.json"))
    p.add_argument("--sample",type=int,default=320)
    a=p.parse_args()
    measure(a.repo,a.out,a.sample)
