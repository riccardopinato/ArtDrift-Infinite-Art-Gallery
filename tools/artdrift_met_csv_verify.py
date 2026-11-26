#!/usr/bin/env python3
"""Verify Met full CSV landscape queue against current official item API/images.

This is a bounded rights/visual research operation only. NO runtime changes.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from PIL import Image,ImageDraw
from artdrift_bright_mass import (
    ROOT,host_ok,color_metric,image_check,scene_ok,cleaned,dates
)
QUEUE=ROOT/"research/mass_bright/20261126/met_full_csv_scenic_queue.json"
OUT=ROOT/".artdrift_research/met_csv_verify"
API="https://collectionapi.metmuseum.org/public/collection/v1/objects/"

def source(ident):
    if not isinstance(ident,str) or not ident.isdecimal():raise ValueError("Object ID")
    url=API+ident
    req=Request(url,headers={"User-Agent":"ArtDrift-PublicDomain-Raster-Research/1.0",
                             "Accept":"application/json"})
    with urlopen(req,timeout=20) as resp:
        if not host_ok(resp.url,"collectionapi.metmuseum.org"):
            raise ValueError("MET API redirect")
        data=resp.read(250001)
    if len(data)>250000:raise ValueError("Oversize Met item")
    return json.loads(data)

def verify(meta):
    ident=meta["museum_native_id"]
    try:
        obj=source(ident)
        if obj.get("isPublicDomain") is not True:return None,"NOT_PD_CURRENT"
        if str(obj.get("objectID") or "")!=ident:return None,"OBJECT_ID_MISMATCH"
        text=(cleaned(obj.get("classification"))+" "+cleaned(obj.get("objectName"))+
              " "+cleaned(obj.get("medium")))
        if "paint" not in text and "oil on canvas" not in text:
            return None,"NOT_PAINTING"
        title=str(obj.get("title") or "").strip()
        artist=str(obj.get("artistDisplayName") or "").strip()
        if not scene_ok(title,artist):return None,"HUMAN_OR_NOT_SCENIC"
        small=str(obj.get("primaryImageSmall") or "")
        large=str(obj.get("primaryImage") or "")
        if not host_ok(small,"images.metmuseum.org"):return None,"NO_OFFICIAL_IMAGE"
        if large and not host_ok(large,"images.metmuseum.org"):large=""
        year=dates(obj.get("objectDate"),obj.get("objectBeginDate"))
        if year is None or not 1850<=year<=1960:return None,"NO_MODERN_DATE"
        rec={"source":"met","museum_native_id":ident,
             "title":title,"artist":artist,"year":year,
             "date":obj.get("objectDate") or "",
             "museum":"The Metropolitan Museum of Art",
             "museum_url":obj.get("objectURL") or meta["museum_url"],
             "license":"CC0","rights_evidence_url":"https://www.metmuseum.org/hubs/open-access",
             "remote_preview_url":small,"remote_full_url":large,
             "artist_death_year_if_available":meta.get("artist_death_year_if_available"),
             "medium":obj.get("medium") or "",
             "artwork_type_title":"Painting",
             "rights_status":"HOLD_TERRITORIAL_AND_FINAL_VISUAL_REVIEW",
             "curatorial_status":"HOLD_CONTACT_SHEET_REVIEW",
             "runtime_visible":False,"worldwide_commercial_certified":False}
        try:
            color,sha,picture=image_check(rec)
        except HTTPError as e:
            return None,f"IMAGE_HTTP_{e.code}"
        except Exception as e:
            return None,f"IMAGE_ERROR_{str(e)[:95]}"
        if not color["bright_pass"]:return None,"DARK_OR_MUTED"
        rec["image_sha256"]=sha
        rec["color_metrics"]=color
        rec["curation_score"]=round(
            .29*color["luminance"]+.34*color["vivid_fraction"]+
            .22*color["saturation"]-.73*color["dark_fraction"],4)
        return (rec,picture),"PASS"
    except HTTPError as e:
        return None,f"MET_API_HTTP_{e.code}"
    except Exception as e:
        return None,f"MET_API_{str(e)[:95]}"

def run(shard,shards,max_items,workers):
    j=json.loads(QUEUE.read_text(encoding="utf-8"))
    if j["image_verified_count"]!=0 or j["runtime_imported"]!=0:
        raise ValueError("candidate metadata queue wrongly published")
    whole=j["works"]
    # Shard by queue item index rather than hash; first N sorted scenic metadata.
    window=[w for i,w in enumerate(whole[:shards*max_items])
            if i%shards==shard]
    res=[];holds=[];pics={};flags=Counter()
    with ThreadPoolExecutor(max_workers=workers) as exe:
        tasks={exe.submit(verify,w):w for w in window}
        for fut in as_completed(tasks):
            w=tasks[fut]
            result,status=fut.result()
            flags[status]+=1
            if result:
                record,picture=result
                res.append(record)
                pics[w["museum_native_id"]]=picture
            else:
                holds.append({"id":w["museum_native_id"],"title":w["title"],"reason":status})
    res.sort(key=lambda w:(-w["curation_score"],int(w["museum_native_id"])))
    path=OUT/f"batch_{shard:02d}";path.mkdir(parents=True,exist_ok=True)
    report={"schema_version":1,"as_of":"2026-11-26","provider":"met",
            "shard":shard,"shard_count":shards,"queue_total":len(whole),
            "items_checked":len(window),"successful_painting_image_qa":len(res),
            "held_or_rejected":len(holds),"hold_reasons":dict(flags),
            "runtime_imported":0,"rights_cleared_for_worldwide":0,
            "works":res,"holds":holds[:200]}
    (path/"review.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    if res:
        cols=8;W=180;H=176;head=res[:min(110,len(res))]
        canvas=Image.new("RGB",(cols*W,((len(head)+cols-1)//cols)*H),"white")
        draw=ImageDraw.Draw(canvas)
        for i,w in enumerate(head):
            img=pics.get(w["museum_native_id"])
            if img is None:continue
            x=i%cols*W;y=i//cols*H
            canvas.paste(img,(x+(W-img.width)//2,y+(138-img.height)//2))
            draw.text((x+3,y+140),w["title"][:25],fill="black")
            draw.text((x+3,y+156),w["museum_native_id"],fill="black")
        canvas.save(path/"sheet.jpg",quality=83,optimize=True)
    print(json.dumps({k:v for k,v in report.items() if k not in ("works","holds")},
                     ensure_ascii=False,sort_keys=True),flush=True)

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--shard",type=int,required=True)
    p.add_argument("--shards",type=int,default=8)
    p.add_argument("--max-per-shard",type=int,default=130)
    p.add_argument("--workers",type=int,default=2)
    a=p.parse_args()
    if not (0<=a.shard<a.shards<=12 and 10<=a.max_per_shard<=220
            and 1<=a.workers<=3):p.error("bounded")
    run(a.shard,a.shards,a.max_per_shard,a.workers)
