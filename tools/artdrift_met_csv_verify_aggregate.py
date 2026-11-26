#!/usr/bin/env python3
"""Official Met CSV follow-up image QA aggregation, source-verified only."""
import json
from collections import Counter
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
IN=ROOT/".artdrift_research/met_verify_incoming"
OUT=ROOT/"research/mass_bright/20261126"
def main():
    reports=sorted(IN.rglob("review.json"))
    if not reports:raise RuntimeError("No Met verification reports")
    works={};counts=Counter();stats=[];holds=Counter()
    for p in reports:
        j=json.loads(p.read_text(encoding="utf-8"))
        if j.get("provider")!="met" or j.get("runtime_imported")!=0:
            raise ValueError("Invalid Met image validation provenance")
        stats.append({k:j.get(k) for k in ("shard","items_checked",
            "successful_painting_image_qa","held_or_rejected","hold_reasons")})
        counts["probed"]+=int(j["items_checked"])
        counts["passed_rows"]+=int(j["successful_painting_image_qa"])
        counts["held"]+=int(j["held_or_rejected"])
        for k,n in j.get("hold_reasons",{}).items():holds[k]+=n
        for w in j.get("works") or []:
            if not (w["source"]=="met" and
                    w["color_metrics"]["bright_pass"] is True and
                    w["color_metrics"]["dark_fraction"]<=.10 and
                    w["rights_status"].startswith("HOLD") and
                    w["curatorial_status"].startswith("HOLD") and
                    not w["runtime_visible"]):raise ValueError("Unverified Met image detected")
            works[str(w["museum_native_id"])]=w
    ordered=sorted(works.values(),key=lambda w:(-w["curation_score"],int(w["museum_native_id"])))
    out={"schema_version":1,"as_of":"2026-11-26","source":"Met OA full CSV + current official artwork API",
         "shards_received":len(reports),"official_items_checked":counts["probed"],
         "bright_verified_new_item_ids":len(ordered),"dark_or_invalid_items":counts["held"],
         "hold_reasons":dict(holds),"runtime_imported":0,"worldwide_rights_approved":0,
         "publication_status":"HOLD_FINAL_RIGHTS_AND_VISUAL_QA",
         "source_queue":"research/mass_bright/20261126/met_full_csv_scenic_queue.json",
         "verification_batch_stats":stats,"works":ordered}
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"met_full_csv_verified_bright.json").write_text(
        json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    sheets=sorted(IN.rglob("sheet.jpg"))
    if sheets:
        cols=2;W=1450;H=950
        canvas=Image.new("RGB",(cols*W,((len(sheets)+1)//cols)*H),"white")
        d=ImageDraw.Draw(canvas)
        for i,p in enumerate(sheets):
            with Image.open(p) as base:
                pic=base.convert("RGB")
            pic.thumbnail((1410,900))
            x=(i%cols)*W;y=(i//cols)*H
            canvas.paste(pic,(x+(W-pic.width)//2,y+34))
            d.text((x+10,y+10),p.parent.name,fill="black")
        canvas.save(OUT/"met_full_csv_verified_contact_sheets.jpg",
                    quality=85,optimize=True)
    print(json.dumps({k:v for k,v in out.items() if k not in ("works","verification_batch_stats")},
                     ensure_ascii=False,sort_keys=True))
if __name__=="__main__":main()
