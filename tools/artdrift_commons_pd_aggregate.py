#!/usr/bin/env python3
"""Merge open Commons raster-verified, explicitly PD/CC0 artist-search files."""
import json
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
IN=ROOT/".artdrift_research/commons_incoming"
OUT=ROOT/"research/mass_bright/20261126"
def run():
    files=sorted(IN.rglob("review.json"))
    if not files:raise RuntimeError("no Wikimedia Commons source reports")
    works={};stats=[];dupes=0
    for p in files:
        j=json.loads(p.read_text(encoding="utf-8"))
        if j.get("source")!="commons" or j.get("publish_to_app") is not False:
            raise ValueError("untrusted or incorrectly marked Commons source")
        stats.append({k:j.get(k) for k in ("shard","candidate_files","images_probed",
                                          "bright_raster_pass","dark_or_media_holds",
                                          "remaining_unprobed","search_stats")})
        for w in j.get("works") or []:
            if not(w["color_metrics"]["bright_pass"] and
                   w["color_metrics"]["dark_fraction"]<=.10 and
                   w["rights_status"].startswith("HOLD") and
                   w["curatorial_status"].startswith("HOLD") and
                   not w["runtime_visible"]):
                raise ValueError("invalid Commons staged image")
            id=str(w["file_pageid"])
            if id in works:dupes+=1
            works[id]=w
    items=sorted(works.values(),key=lambda w:(-w["curation_score"],w["file_pageid"]))
    OUT.mkdir(parents=True,exist_ok=True)
    j={"schema_version":1,"as_of":"2026-11-26","source":"commons",
       "shards_received":len(files),"total_unique_pd_bright_raster":len(items),
       "overlap_files_across_search_batches":dupes,"provider_did_not_claim_legal_clearance":True,
       "runtime_imported":0,"final_visual_review_pending":True,
       "attribution_verification_pending":True,
       "stats":stats,"works":items}
    (OUT/"commons_pd_bright_verified.json").write_text(json.dumps(j,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    sheets=sorted(IN.rglob("sheet.jpg"))
    if sheets:
        cols=2;W=1160;H=1230
        im=Image.new("RGB",(cols*W,((len(sheets)+1)//cols)*H),"white")
        d=ImageDraw.Draw(im)
        for i,p in enumerate(sheets):
            with Image.open(p) as raw:
                x=raw.convert("RGB");x.thumbnail((1120,1160))
            c=i%cols*W;r=i//cols*H
            im.paste(x,(c+(W-x.width)//2,r+35))
            d.text((c+6,r+12),p.parent.name,fill="black")
        im.save(OUT/"commons_pd_contact_sheets.jpg",quality=84,optimize=True)
    print(json.dumps({k:v for k,v in j.items() if k not in ("stats","works")},
                     ensure_ascii=False,sort_keys=True))
if __name__=="__main__":run()
