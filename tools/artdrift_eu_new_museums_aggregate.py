#!/usr/bin/env python3
"""Combine initial, verified non-US museum source art batches.

Source object cross-duplicates are held, never auto-publish images.
"""
from __future__ import annotations
import json
from collections import Counter
from pathlib import Path
from PIL import Image,ImageDraw
from artdrift_bright_mass import cleaned

ROOT=Path(__file__).resolve().parents[1]
INPUT=ROOT/".artdrift_eu/incoming"
OUT=ROOT/"research/museums/20261126"
PROVIDERS=("rijks","nationalmuseum_se","staedel")
def run():
    files=sorted(INPUT.rglob("review.json"))
    if not files:raise SystemExit("Missing per-museum evidence; no fabricated results")
    counted=Counter();stats=[];staged=[];held=[];seen_ids=set();seen_work=set()
    for path in files:
        obj=json.loads(path.read_text(encoding="utf-8"))
        source=obj.get("provider")
        if source not in PROVIDERS:continue
        if obj.get("runtime_imported")!=0 or obj.get("commercially_cleared")!=0:
            raise ValueError("Non-publishing European art research gate violated")
        counted[source+"_batch_count"]+=1
        counted[source+"_image_bright_raw"]+=obj.get("verified_images_bright",0)
        stats.append({"provider":source,"shard":obj.get("shard"),
                      "search_stats":obj.get("search_stats"),
                      "bright":obj.get("verified_images_bright"),
                      "errors":obj.get("source_errors",[])[:4]})
        for w in obj.get("works") or []:
            if w.get("source")!=source or w.get("runtime_visible") is not False:
                raise ValueError("Work provenance or runtime status broken")
            c=w.get("color_metrics",{})
            if not(c.get("luminance",0)>=.55 and c.get("dark_fraction",1)<=.20
                   and c.get("saturation",0)>=.18 and c.get("vivid_fraction",0)>=.18):
                raise ValueError("Image failed color policy")
            if c["dark_fraction"]>.15 and not (
                c["saturation"]>=.24 and c["vivid_fraction"]>=.30):
                raise ValueError("Non-vivid 15–20% work erroneously entered")
            key=(source,str(w["museum_native_id"]))
            artist=cleaned(w.get("artist"));title=cleaned(w.get("title"))
            semantic=(artist,title,w.get("year"))
            if key in seen_ids or (artist and title and semantic in seen_work):
                held.append({"id":w.get("museum_native_id"),"source":source,"reason":"POSSIBLE_EXACT_ARTWORK_DUPLICATE"})
                continue
            seen_ids.add(key)
            if artist and title:seen_work.add(semantic)
            staged.append(w)
    staged.sort(key=lambda w:(w["color_metrics"]["dark_fraction"],w["source"],str(w["museum_native_id"])))
    OUT.mkdir(parents=True,exist_ok=True)
    report={"schema_version":1,"as_of":"2026-11-26",
        "scope":"new museums in Europe; excludes four US catalogues and SMK",
        "us_museums_queried":0,
        "source_batch_reports_received":len(files),
        "sources":[{"provider":p,"shards_received":counted[p+"_batch_count"],
                    "bright_images_before_dedup":counted[p+"_image_bright_raw"]}
                   for p in PROVIDERS],
        "bright_images_after_preliminary_dedup":len(staged),
        "cross_source_possible_duplicates_held":held,
        "thresholds":{"preferred_dark_max":.15,"conditional_dark_max":.20,
                      "conditional_min_vivid_fraction":.30,
                      "conditional_min_saturation":.24},
        "rights_status":"HOLD_PER_OBJECT_LICENSE_TERRITORY_AND_VISUAL",
        "runtime_imported":0,"approved_for_commercial_app":0,
        "batch_reports":stats,"works":staged}
    (OUT/"new_european_museum_bright_batch1.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    sheets=sorted(INPUT.rglob("artworks_contact_sheet.jpg"))
    if sheets:
        cards=[]
        for p in sheets:
            with Image.open(p) as f:
                im=f.convert("RGB")
                im.thumbnail((1050,850),Image.Resampling.LANCZOS)
                cards.append((p.parent.parent.parent.name+" / "+p.parent.name,im.copy()))
        cols=2;W=1080;H=930
        canvas=Image.new("RGB",(cols*W,((len(cards)+cols-1)//cols)*H),"white")
        draw=ImageDraw.Draw(canvas)
        for i,(name,pic) in enumerate(cards):
            x=i%cols*W;y=i//cols*H
            draw.text((x+8,y+10),name,fill="black")
            canvas.paste(pic,(x+(W-pic.width)//2,y+40))
        canvas.save(OUT/"new_european_museums_contact_sheet.jpg",quality=85,optimize=True)
    print(json.dumps({k:v for k,v in report.items() if k not in
                      ("works","batch_reports","cross_source_possible_duplicates_held")},
                     sort_keys=True,ensure_ascii=False),flush=True)
    return report
if __name__=="__main__":run()
