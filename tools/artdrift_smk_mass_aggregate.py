#!/usr/bin/env python3
"""Collect independent SMK Danish-color landscape slices for Art Drift."""
import json
from pathlib import Path
from collections import Counter
from PIL import Image,ImageDraw
from artdrift_bright_mass import cleaned
ROOT=Path(__file__).resolve().parents[1]
IN=ROOT/".artdrift_research/smk_incoming"
OUT=ROOT/"research/mass_bright/20261126"
def main():
    files=sorted(IN.rglob("review.json"))
    if not files:raise RuntimeError("no SMK batch reports")
    unique={};dupes=0;stats=[];fatal=[]
    for file in files:
        try:j=json.loads(file.read_text(encoding="utf-8"))
        except Exception as e:fatal.append(str(e));continue
        if j["source"]!="smk" or j["runtime_imported"]!=0:
            raise RuntimeError("untrusted SMK provenance")
        stats.append({k:j.get(k) for k in ("batch","search_statistics",
            "eligible_unique_non_main","images_probed","verified_bright_works",
            "hold_count","unprobed")})
        for w in j.get("works") or []:
            if not (w["color_metrics"]["bright_pass"] and
                    w["color_metrics"]["dark_fraction"]<=.10 and
                    w["rights_status"].startswith("HOLD") and
                    w["curatorial_status"].startswith("HOLD") and
                    not w["runtime_visible"]):
                raise RuntimeError("unverified or published art in batch")
            key=w["museum_native_id"].casefold()
            if key in unique:
                dupes+=1
                if w["curation_score"]>unique[key]["curation_score"]:unique[key]=w
            else:unique[key]=w
    items=sorted(unique.values(),key=lambda w:(-w["curation_score"],w["museum_native_id"].casefold()))
    OUT.mkdir(parents=True,exist_ok=True)
    j={"schema_version":1,"source":"smk","as_of":"2026-11-26",
       "batches_received":len(files),"statistics":stats,"duplicate_overlap_between_shards":dupes,
       "verified_bright_unique":len(items),"invalid_reports":fatal,
       "runtime_imported":0,"territorial_rights_approved":0,
       "publication_status":"HOLD_FINAL_VISUAL_AND_RIGHTS_AUDIT",
       "works":items}
    (OUT/"smk_megabatch_verified.json").write_text(json.dumps(j,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    sheets=list(IN.rglob("sheet.jpg"))
    if sheets:
        cols=2;W=1180;H=1250
        preview=Image.new("RGB",(cols*W,((len(sheets)+1)//cols)*H),"white")
        draw=ImageDraw.Draw(preview)
        for n,p in enumerate(sorted(sheets)):
            with Image.open(p) as raw:
                img=raw.convert("RGB");img.thumbnail((1140,1190))
                x=n%cols*W;y=n//cols*H
                preview.paste(img,(x+(W-img.width)//2,y+40))
                draw.text((x+12,y+10),p.parent.name,fill="black")
        preview.save(OUT/"smk_all_contact_sheets.jpg",quality=83,optimize=True)
    print(json.dumps({k:v for k,v in j.items() if k not in ("works","statistics","invalid_reports")},
                     ensure_ascii=False,sort_keys=True))
    if not items:raise SystemExit("NO_SMK_VERIFIED_WORKS")
if __name__=="__main__":main()
