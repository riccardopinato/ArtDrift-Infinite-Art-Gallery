#!/usr/bin/env python3
"""NGA color-first landscape research, NOT a runtime catalog publisher.

Official NGA Open Data objects.csv JOIN published_images.csv by object ID.
ONLY primary images with openaccess=1, Painting, scenic titles, a dated work.
Bounded remote image bytes are decoded and scored. Results are always HOLD.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
import re
import unicodedata
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import urlopen, Request
from PIL import Image, ImageOps

ROOT=Path(__file__).resolve().parents[1]
NGA_SHA="2470472572fdca2a24a741bb50eaba7301c47fa9"
URL=f"https://raw.githubusercontent.com/NationalGalleryOfArt/opendata/{NGA_SHA}/data/"
RIGHTS="https://www.nga.gov/artworks/free-images-and-open-access"
OUT=ROOT/".artdrift_research/nga_color"
TITLE_POS=("landscape","garden","gardens","flowers","flower","orchard","bloom",
           "meadow","valley","wheat","fields","field","harbor","harbour","port",
           "river","seine","sea","coast","shore","beach","water","boats","boat",
           "farmhouse","farm","road","sunflower","lilies","spring","summer",
           "mountain","view","village","hills","hill","tree","trees","brittany",
           "provence","cove","tropez","lake","canal","sailboat","window",
           "irises","dahlia","parc","park","countryside","country")
TITLE_AVOID=("portrait","self-portrait","head of","woman","women","lady","girl","girls",
             "man ","men ","peasant","seamstress","figures","figure of","couple",
             "child","children","mother","daughter","son ","nude","bather",
             "caricature","photograph","dusk","twilight","nocturne","night",
             "moonlight","imitator","portrait study")
ARTISTS=("claude monet","vincent van gogh","paul cezanne","paul gauguin",
         "georges seurat","paul signac","auguste renoir","pierre auguste renoir",
         "camille pissarro","alfred sisley","berthe morisot","henri matisse",
         "andre derain","raoul dufy","pierre bonnard","edouard vuillard",
         "henri rousseau","paul serusier","henri moret","theodore robinson",
         "john singer sargent","charles guilloux","georges lacombe",
         "maurice denis","henri edmond cross","gustave loiseau","robert del aunay",
         "robert delaunay","ferdinand hodler","marc chagall","amedeo modigliani",
         "odilon redon","felix vallotton","max pechstein","fernand leger",
         "wassily kandinsky","paul klee","piet mondrian","otto mueller",
         "suzanne valadon","henri lebasque","mary cassatt")
SCENIC_WEIGHTS={"garden":5,"flowers":5,"orchard":5,"landscape":5,"sunflower":5,
                "fields":4,"coast":4,"sea":4,"meadow":5,"bloom":5,"village":4,
                "harbor":4,"river":3,"water":2,"tree":2,"view":2,"window":2}
csv.field_size_limit(16_000_000)
Image.MAX_IMAGE_PIXELS=16_000_000

def ascii_text(s):
    return unicodedata.normalize("NFKD",str(s or "")).encode("ascii","ignore").decode().lower()

def safe(url,host):
    if not isinstance(url,str):return False
    try:
        p=urlsplit(url)
        return p.scheme=="https" and p.hostname==host and not p.username and not p.password and p.port in (None,443)
    except ValueError:return False

def image_url(iiif):
    if not safe(iiif,"api.nga.gov"):return None
    base=iiif.removesuffix("/info.json").rstrip("/")
    if not base.startswith("https://api.nga.gov/iiif/"):return None
    return base+"/full/256,/0/default.jpg"

def stream_csv(name):
    url=URL+name
    if not safe(url,"raw.githubusercontent.com"):raise ValueError("CSV_UNTRUSTED_HOST")
    req=Request(url,headers={"User-Agent":"ArtDrift-Research-OpenData/1.0",
                              "Accept":"text/csv"})
    resp=urlopen(req,timeout=90)
    if not safe(resp.url,"raw.githubusercontent.com"):
        resp.close();raise ValueError("CSV_REDIRECT_UNTRUSTED")
    txt=io.TextIOWrapper(resp,encoding="utf-8-sig",newline="")
    return txt,csv.DictReader(txt)

def year(row):
    display=str(row.get("displaydate") or "")
    years=[int(x) for x in re.findall(r"(?<!\d)(?:18|19|20)\d{2}(?!\d)",display)]
    if not years or min(years)<1870 or min(years)>1955 or max(years)>1955:
        return None
    return min(years)

def title_score(title,artist,yr):
    t=ascii_text(title)
    if any(x in t for x in TITLE_AVOID):return 0
    matches=[term for term in TITLE_POS if term in t]
    if not matches:return 0
    # No portraits; no monochrome text and no technical reproductions.
    score=4+sum(SCENIC_WEIGHTS.get(k,1) for k in matches)
    if any(a in ascii_text(artist) for a in ARTISTS):score+=6
    if yr>=1900:score+=4
    if yr>=1920:score+=1
    return score

def catalog_keys():
    found=set()
    for path in (ROOT/"assets/museums/catalog.json",
                 ROOT/"assets/museums/catalog_global.json"):
        if not path.is_file():continue
        for item in json.loads(path.read_text(encoding="utf-8")):
            if item.get("museum_source")=="nga":
                found.add(str(item.get("museum_native_id") or ""))
    return found

def load_objects():
    existing=catalog_keys()
    candidates={}
    stream,rows=stream_csv("objects.csv")
    scanned=0
    try:
        for row in rows:
            scanned+=1
            if "paint" not in ascii_text(row.get("classification")):
                continue
            native=str(row.get("objectid") or "").strip()
            if not native.isdecimal() or native in existing:continue
            yr=year(row)
            if yr is None:continue
            title=str(row.get("title") or "").strip()
            artist=str(row.get("attribution") or "").strip()
            score=title_score(title,artist,yr)
            if any(z in ascii_text(artist) for z in ("imitator","after ","school of","follower of")):continue
            if score<10:continue
            candidates[native]={"native_id":native,"title":title,"artist":artist,
                                "date":str(row.get("displaydate") or ""),
                                "year":yr,"classification":row.get("classification"),
                                "medium":row.get("medium") or "","metadata_score":score,
                                "nga_url":"https://www.nga.gov/artworks/"+native}
    finally:stream.close()
    return scanned,existing,candidates

def join_open_access(candidates):
    stream,rows=stream_csv("published_images.csv")
    scanned=0; flags=Counter(); images={}
    try:
        for row in rows:
            scanned+=1
            native=str(row.get("depictstmsobjectid") or "").strip()
            if native not in candidates:continue
            if str(row.get("openaccess") or "")!="1":
                flags["restricted"]+=1
                continue
            typ=ascii_text(row.get("viewtype"))
            if typ and typ!="primary":continue
            base=str(row.get("iiifurl") or "").strip()
            url=image_url(base)
            if not url:flags["not_official_iiif"]+=1;continue
            if native in images:continue
            images[native]={"preview":url,
                            "full":base.removesuffix("/info.json").rstrip("/")+
                                   "/full/1000,/0/default.jpg",
                            "image_uuid":row.get("uuid"),"openaccess":1,
                            "published_image_width":row.get("width"),
                            "published_image_height":row.get("height")}
    finally:stream.close()
    return scanned,flags,images

def color_measure(source):
    image=ImageOps.exif_transpose(source.convert("RGB"))
    # Inspected artwork interior, avoids pale mats and surrounding whitespace.
    w,h=image.size
    if min(w,h)<48:raise ValueError("LOW_RES_MEDIA")
    margin=int(min(w,h)*0.06)
    image=image.crop((margin,margin,w-margin,h-margin))
    image.thumbnail((112,112))
    pix=list(image.getdata())
    if not pix:raise ValueError("EMPTY_PIXELS")
    n=len(pix)
    total_l=0.0;total_s=0.0;dark=0;vivid=0
    for r,g,b in pix:
        v=max(r,g,b)/255
        s=(max(r,g,b)-min(r,g,b))/max(r,g,b) if max(r,g,b) else 0
        light=(.2126*r+.7152*g+.0722*b)/255
        total_l+=light;total_s+=s
        if light<.31:dark+=1
        if s>.26 and light>.43:vivid+=1
    lum=total_l/n;sat=total_s/n;darkfrac=dark/n;vividfrac=vivid/n
    return {"luminance":round(lum,4),"saturation":round(sat,4),
            "dark_fraction":round(darkfrac,4),"vivid_fraction":round(vividfrac,4),
            "bright_color_pass":lum>=.50 and darkfrac<=.28 and vividfrac>=.16}

def probe(item,images):
    img=images[item["native_id"]]["preview"]
    if not safe(img,"api.nga.gov"):raise ValueError("UNTRUSTED_IMAGE_URL")
    req=Request(img,headers={"User-Agent":"ArtDrift-ColorResearch/1.0",
                             "Accept":"image/jpeg,image/png,image/webp"})
    with urlopen(req,timeout=18) as r:
        if not safe(r.url,"api.nga.gov"):raise ValueError("IMAGE_REDIRECT")
        if not r.headers.get("Content-Type","").lower().startswith("image/"):
            raise ValueError("NON_IMAGE_MIME")
        raw=r.read(1_500_001)
    if not 500<=len(raw)<=1_500_000:raise ValueError("IMAGE_BYTES_LIMIT")
    with Image.open(io.BytesIO(raw)) as source:
        if source.format not in ("JPEG","PNG","WEBP"):raise ValueError("IMAGE_FORMAT")
        color=color_measure(source)
        thumb=ImageOps.exif_transpose(source.convert("RGB"))
        thumb.thumbnail((132,132),Image.Resampling.LANCZOS)
    return color,hashlib.sha256(raw).hexdigest(),thumb

def research(max_probe,max_accepted,workers):
    obj_scan,existing,objs=load_objects()
    img_scan,flags,imgs=join_open_access(objs)
    poolrows=[item for native,item in objs.items() if native in imgs]
    poolrows.sort(key=lambda x:(-x["metadata_score"],x["artist"].lower(),int(x["native_id"])))
    accepted=[];holds=[];samples={}
    top=poolrows[:max_probe]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        fs={pool.submit(probe,item,imgs):item for item in top}
        for f in as_completed(fs):
            item=fs[f]
            try:
                color,sha,thumb=f.result()
                if not color["bright_color_pass"]:
                    holds.append({"id":item["native_id"],"reason":"DARK_OR_LOW_COLOR",
                                  "metrics":color})
                    continue
                out={**item,"id":4_000_000_000+int(item["native_id"]),
                     "museum_source":"nga","museum_native_id":item["native_id"],
                     "museum_name":"National Gallery of Art, Washington",
                     "rights_license":"Public Domain / NGA Open Access",
                     "rights_evidence_url":RIGHTS,"source_dataset_sha":NGA_SHA,
                     "source_image_uuid":imgs[item["native_id"]]["image_uuid"],
                     "remote_preview_url":imgs[item["native_id"]]["preview"],
                     "remote_full_url":imgs[item["native_id"]]["full"],
                     "image_sha256":sha,"color_metrics":color,
                     "has_portrait_subject":False,"public_domain_image_flag":True,
                     "publication_status":"HOLD_FINAL_RIGHTS_AND_ART_QA",
                     "runtime_visible":False}
                out["curation_score"]=round(
                    color["luminance"]*.33+color["saturation"]*.28+
                    color["vivid_fraction"]*.44-color["dark_fraction"]*.65+
                    min(0.12,item["metadata_score"]/160),4)
                accepted.append(out)
                samples[item["native_id"]]=thumb
            except Exception as ex:
                holds.append({"id":item["native_id"],"reason":str(ex)[:130]})
    accepted.sort(key=lambda x:(-x["curation_score"],int(x["native_id"])))
    accepted=accepted[:max_accepted]
    # Still-life/no-landscape loopholes avoided by strict title semantics.
    result={"schema_version":1,"as_of":"2026-11-25","source":"NGA official open data",
            "dataset_sha":NGA_SHA,"objects_rows_scanned":obj_scan,
            "images_rows_scanned":img_scan,"previous_nga_ids":len(existing),
            "scene_candidate_objects":len(objs),
            "scene_candidates_with_primary_openaccess_image":len(poolrows),
            "images_probed":len(top),"downloaded_and_color_pass":len(samples),
            "selected_bright_landscape_works":len(accepted),
            "excluded_or_failed_image_checks":len(holds),
            "open_access_flag_stats":dict(flags),
            "portrait_count":0,"runtime_imported":0,"commercial_worldwide_approved":0,
            "selection_rule":{"date_range":"1870-1955","classification":"Painting",
                              "subject":"scenic title; portrait excluded",
                              "luminance_min":0.50,"dark_fraction_max":0.28,
                              "vivid_fraction_min":0.16},
            "works":accepted,"hold_samples":sorted(holds,key=lambda x:x["id"])[:150]}
    return result,samples

def contact_sheet(works,samples,path):
    from PIL import ImageDraw
    rowset=works[:min(80,len(works))]
    if not rowset:return
    cols=8;rows=(len(rowset)+cols-1)//cols;W=164;H=170
    sheet=Image.new("RGB",(cols*W,rows*H),"white")
    draw=ImageDraw.Draw(sheet)
    for i,work in enumerate(rowset):
        thumb=samples.get(work["museum_native_id"])
        if thumb is None:continue
        x=(i%cols)*W;y=(i//cols)*H
        sheet.paste(thumb,(x+(W-thumb.width)//2,y+(136-thumb.height)//2))
        draw.text((x+4,y+139),work["title"][:22],fill="black")
        draw.text((x+4,y+154),str(work["museum_native_id"]),fill="black")
    sheet.save(path,format="JPEG",quality=83,optimize=True)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--max-probe",type=int,default=130)
    p.add_argument("--max-accepted",type=int,default=100)
    p.add_argument("--workers",type=int,default=4)
    a=p.parse_args()
    if not 1<=a.max_probe<=250 or not 1<=a.max_accepted<=150 or not 1<=a.workers<=4:
        p.error("LIMITS")
    out,samples=research(a.max_probe,a.max_accepted,a.workers)
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"nga_bright_review.json").write_text(
        json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    contact_sheet(out["works"],samples,OUT/"nga_bright_contact_sheet.jpg")
    print(json.dumps({k:v for k,v in out.items() if k not in ("works","hold_samples")},
                     ensure_ascii=False,sort_keys=True))
    if out["selected_bright_landscape_works"]<10:
        raise SystemExit("INSUFFICIENT_BRIGHT_OPEN_ACCESS_WORKS")

if __name__=="__main__":
    main()
