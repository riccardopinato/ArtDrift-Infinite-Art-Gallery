#!/usr/bin/env python3
"""Merge independent Art Drift OA research batches, without app content mutation."""
from __future__ import annotations
import json
from collections import Counter
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw

ROOT=Path(__file__).resolve().parents[1]
INPUT=ROOT/".artdrift_research/incoming"
OUTPUT=ROOT/"research/mass_bright/20261126"
PROVIDERS=("aic","cma","met")
def norm(t):
    from artdrift_bright_mass import cleaned
    return cleaned(t)

def combine():
    files=list(INPUT.rglob("review.json"))
    if not files:raise SystemExit("No downloaded batch evidence")
    per=Counter();rows=[];seen_ids=set();seen_sem=set();rows_seen=0;reject=0
    batch_stats=[];bad=[]
    for file in sorted(files):
        try:r=json.loads(file.read_text(encoding="utf-8"))
        except Exception as e:bad.append({"file":str(file),"reason":str(e)});continue
        p=r.get("provider")
        if p not in PROVIDERS:continue
        if r.get("public_release") is not False or r.get("runtime_imported")!=0:
            raise RuntimeError("Unexpected published batch")
        rows_seen+=int(r.get("images_probed") or 0)
        reject+=int(r.get("hold_count") or 0)
        batch_stats.append({k:r.get(k) for k in
            ("provider","shard","source_candidates","duplicates_against_live_and_nga",
             "eligible_to_probe","images_probed","color_verified_pass",
             "hold_count","unprobed_from_this_shard")})
        for w in r.get("works") or []:
            if w.get("source")!=p or w.get("runtime_visible") is not False:
                raise RuntimeError("Invalid staged work origin/publication")
            c=w["color_metrics"]
            if not(c["luminance"]>=.55 and c["dark_fraction"]<=.1
                   and c["vivid_fraction"]>=.18 and c["saturation"]>=.18
                   and c["bright_pass"] is True):
                raise RuntimeError("Non-bright artifact cannot enter shortlist")
            key=(w["source"],w["museum_native_id"])
            # Same title and artist may refer to different artworks; date guards collisions.
            subject=(norm(w["title"]),norm(w["artist"]),int(w["year"]))
            if key in seen_ids or subject in seen_sem:continue
            seen_ids.add(key);seen_sem.add(subject)
            rows.append(w);per[p]+=1
    rows.sort(key=lambda w:(-w["curation_score"],w["source"],w["museum_native_id"]))
    OUTPUT.mkdir(parents=True,exist_ok=True)
    result={"schema_version":1,"as_of":"2026-11-26",
            "sources":[{"provider":k,"selected_count":per[k]} for k in PROVIDERS],
            "batch_reports_received":len(files),
            "batch_reports_parsed":len(batch_stats),
            "images_probed":rows_seen,
            "color_or_fetch_rejections":reject,
            "combined_unique_bright_candidates":len(rows),
            "source_key_and_title_artist_year_deduplicated":True,
            "photo_color_thresholds":{"min_luminance":.55,"max_dark_fraction":.1,
                                      "min_vivid_fraction":.18,"min_saturation":.18},
            "publication_status":"HOLD_HUMAN_VISUAL_AND_TERRITORIAL_RIGHTS",
            "runtime_imported":0,
            "worldwide_rights_approved":0,
            "qa":"image raster sampled and host-verified; contact sheet per shard for final human QA",
            "batch_statistics":batch_stats,
            "invalid_reports":bad,
            "works":rows}
    (OUTPUT/"bright_mass_combined.json").write_text(
        json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    for p in PROVIDERS:
        items=[x for x in rows if x["source"]==p]
        (OUTPUT/f"bright_mass_{p}.json").write_text(
            json.dumps({"source":p,"selected_count":len(items),"works":items},
                       ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    # Contact sheets in batch artifacts remain inspectable, rebuild index
    # from their existing JPEGs without another network request.
    sheets=[]
    for file in sorted(INPUT.rglob("sheet.jpg")):
        try:
            with Image.open(file) as raw:
                im=raw.convert("RGB")
                im.thumbnail((1120,1200))
                sheets.append((file.parent.name,im.copy()))
        except Exception:pass
    if sheets:
        W=1140;H=1250;cols=2;rowsheets=(len(sheets)+cols-1)//cols
        canvas=Image.new("RGB",(cols*W,rowsheets*H),"white")
        draw=ImageDraw.Draw(canvas)
        for i,(label,img) in enumerate(sheets):
            xx=(i%cols)*W;yy=(i//cols)*H
            canvas.paste(img,(xx+(W-img.width)//2,yy+30))
            draw.text((xx+10,yy+8),label,fill="black")
        canvas.save(OUTPUT/"bright_mass_all_contact_sheets.jpg",quality=83,optimize=True)
    print(json.dumps({k:v for k,v in result.items() if k not in ("works","batch_statistics","invalid_reports")},
                     ensure_ascii=False,sort_keys=True))
    if len(rows)<20:
        print("WARN: fewer than 20 works, metadata may be truncated or APIs unavailable")
    return result

if __name__=="__main__":
    combine()
