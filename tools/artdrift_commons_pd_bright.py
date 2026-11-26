#!/usr/bin/env python3
"""Curated 19th/early-20th century PD paintings on Wikimedia Commons.

Artist rosters have death <=1955 (EU term 70y expired by 2026).
Require explicit file public-domain/CC0 licence in Commons metadata,
real image thumb decoded and <10% dark area. Research HOLD only.
"""
from __future__ import annotations
import argparse
import hashlib
import html
from html.parser import HTMLParser
import io
import json
import re
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
from urllib.parse import urlencode,urlsplit,quote
from urllib.request import Request,urlopen
from PIL import Image,ImageOps,ImageDraw
from artdrift_bright_mass import cleaned,color_metric,host_ok,scene_ok,main_keys

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/".artdrift_research/commons_mass"
API="https://commons.wikimedia.org/w/api.php"
UA="ArtDrift-Curatorial-OpenData/1.0 (https://github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery)"
# Only artists deceased no later than 1955: EU life+70 in PD as of 2026.
ARTISTS=(
 (("Claude Monet",1926),("Alfred Sisley",1899),("Camille Pissarro",1903),("Berthe Morisot",1895)),
 (("Vincent van Gogh",1890),("Paul Cezanne",1906),("Paul Gauguin",1903),("Henri Rousseau",1910)),
 (("Georges Seurat",1891),("Paul Signac",1935),("Henri-Edmond Cross",1910),("Henri Moret",1913)),
 (("Henri Matisse",1954),("Andre Derain",1954),("Raoul Dufy",1953),("Albert Marquet",1947)),
 (("Wassily Kandinsky",1944),("Paul Klee",1940),("Robert Delaunay",1941),("Piet Mondrian",1944)),
 (("Edvard Munch",1944),("Ernst Ludwig Kirchner",1938),("Franz Marc",1916),("August Macke",1914)),
 (("Odilon Redon",1916),("Pierre Bonnard",1947),("Edouard Vuillard",1940),("Paul Serusier",1927)),
 (("John Singer Sargent",1925),("William Merritt Chase",1916),("Frederick Carl Frieseke",1939),("Theodore Robinson",1896)),
)
SUBJECTS=("landscape","garden","flowers","seascape","still life")
NEGATIVE=("portrait","self portrait","woman","women","man","men","girl",
          "boy","people","figures","child","nude","naked","lady","seated",
          "sketch","drawing","etching","print","poster","illustration",
          "photo of","photograph","black","dark","night","nocturne",
          "sketchbook","museum room","museum interior","framed")
Image.MAX_IMAGE_PIXELS=20_000_000

class HTMLText(HTMLParser):
    def __init__(self):super().__init__();self.parts=[]
    def handle_data(self,data):self.parts.append(data)
def strip_html(value):
    x=HTMLText()
    try:x.feed(str(value or ""))
    except Exception:return ""
    return html.unescape(" ".join(x.parts))

def licenses(meta):
    def txt(key):return strip_html((meta.get(key) or {}).get("value") if isinstance(meta.get(key),dict) else "")
    name=txt("LicenseShortName").strip().lower()
    url=txt("LicenseUrl").strip().lower()
    copyrighted=txt("Copyrighted").strip().lower()
    is_pd=(name in ("public domain","cc0","cc zero","pd") or
           "creativecommons.org/publicdomain/zero/" in url or
           "creativecommons.org/publicdomain/mark/" in url)
    return is_pd and copyrighted not in ("true","1"),{"license_name":name,"license_url":url,"copyrighted":copyrighted}

def safe_thumb(url):
    try:
        u=urlsplit(url)
        return (u.scheme=="https" and
                u.hostname in ("upload.wikimedia.org","thumb.wikimedia.org")
                and u.path.startswith("/wikipedia/commons/") and
                not u.username and not u.password and u.port in (None,443))
    except ValueError:return False

def api(q):
    if not host_ok(API,"commons.wikimedia.org"):raise RuntimeError("unsafe API")
    p=urlencode({"action":"query","format":"json","formatversion":"2",
                 "generator":"search","gsrsearch":q,"gsrnamespace":6,
                 "gsrlimit":50,"prop":"imageinfo",
                 "iiprop":"url|mime|extmetadata|size|sha1",
                 "iiurlwidth":320,"iilimit":1})
    req=Request(API+"?"+p,headers={"User-Agent":UA,
        "Accept":"application/json"})
    with urlopen(req,timeout=30) as resp:
        if not host_ok(resp.url,"commons.wikimedia.org"):
            raise RuntimeError("unexpected redirect")
        data=resp.read(14_000_001)
    if len(data)>14_000_000:raise RuntimeError("oversized Commons API")
    obj=json.loads(data)
    if obj.get("error"):raise RuntimeError(str(obj["error"])[:170])
    return (obj.get("query") or {}).get("pages") or []

def title_relevant(filename,artist):
    f=cleaned(filename)
    if any(re.search(r"\b"+re.escape(x)+r"\b",f) for x in NEGATIVE):return False
    last=cleaned(artist).split()[-1] # pass search artist surname evidence
    return (last in f or cleaned(artist) in f)

def discover(shard):
    rows={};stats=Counter()
    for artist,death in ARTISTS[shard]:
        if death>1955:raise RuntimeError("artist territory cutoff")
        for subject in SUBJECTS:
            q=f'"{artist}" {subject}'
            try:pages=api(q)
            except Exception as e:
                stats["api_errors"]+=1
                print("COMMONS_QUERY_HOLD",q,str(e)[:150],flush=True)
                continue
            stats["files_found"]+=len(pages)
            for page in pages:
                if not isinstance(page,dict) or page.get("ns")!=6:continue
                filename=str(page.get("title") or "")
                if not filename.startswith("File:") or not title_relevant(filename,artist):continue
                info=(page.get("imageinfo") or [{}])[0]
                mime=str(info.get("mime") or "")
                if mime not in ("image/jpeg","image/png","image/webp"):continue
                ext=info.get("extmetadata") or {}
                pd,lic=licenses(ext)
                if not pd:stats["non_pd_files"]+=1;continue
                preview=str(info.get("thumburl") or "")
                if not safe_thumb(preview):
                    stats["bad_thumbnail"]+=1
                    if stats["bad_thumbnail"]<=2:
                        print("COMMONS_UNHANDLED_THUMB",repr(preview[:200]),flush=True)
                    continue
                att=strip_html((ext.get("Artist") or {}).get("value") or "")
                last=cleaned(artist).split()[-1]
                author_source=("explicit_commons_artist" if last in cleaned(att)
                               else "commons_file_title_only")
                # Filename and query must agree on specific painter; source
                # metadata could name photographer, so preserve attribution confidence.
                key=str(page.get("pageid") or "")
                if not key.isdigit():continue
                src={"source":"commons","file_pageid":int(key),
                     "file_title":filename,"museum_native_id":key,
                     "title":filename.removeprefix("File:").rsplit(".",1)[0],
                     "artist":artist,"artist_death_year":death,
                     "artist_attribution_evidence":author_source,
                     "artist_metadata":att[:230],
                     "artist_is_eu_public_domain_by_year":True,
                     "subject_search":subject,
                     "remote_preview_url":preview,
                     "remote_full_url":str(info.get("url") or ""),
                     "museum_url":"https://commons.wikimedia.org/wiki/"+
                        quote(filename.replace(" ","_"),safe=":/_()-"),
                     "rights_license":lic["license_name"],
                     "rights_evidence_url":lic["license_url"],
                     "file_sha1":info.get("sha1") or "",
                     "runtime_visible":False,"worldwide_commercial_certified":False}
                rows[key]=src
            time.sleep(.15)
    return list(rows.values()),dict(stats)

def thumb_probe(w):
    url=w["remote_preview_url"]
    if not safe_thumb(url):raise ValueError("unapproved Wikimedia image")
    req=Request(url,headers={"User-Agent":UA,"Accept":"image/jpeg,image/png"})
    # Wikimedia's own 2026 thumbnail CDN now uses thumb.wikimedia.org.
    # Keep one low-rate media request per worker; do not retry 429.
    time.sleep(.8)
    with urlopen(req,timeout=18) as resp:
        if not safe_thumb(resp.url):raise ValueError("unexpected media redirect")
        if not resp.headers.get("Content-Type","").lower().startswith("image/"):
            raise ValueError("bad MIME")
        raw=resp.read(1_300_001)
    if len(raw)>1_300_000 or len(raw)<512:raise ValueError("bad media bytes")
    with Image.open(io.BytesIO(raw)) as img:
        if img.format not in ("JPEG","PNG","WEBP"):raise ValueError("not raster")
        color=color_metric(img)
        im=ImageOps.exif_transpose(img.convert("RGB"))
        im.thumbnail((144,136),Image.Resampling.LANCZOS)
        out=im.copy()
    return color,hashlib.sha256(raw).hexdigest(),out

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--shard",type=int,required=True)
    a.add_argument("--max-images",type=int,default=240)
    a.add_argument("--workers",type=int,default=4)
    opt=a.parse_args()
    if not (0<=opt.shard<8 and 1<=opt.workers<=5 and 1<=opt.max_images<=350):
        a.error("bounds")
    all_items,stats=discover(opt.shard)
    items=sorted(all_items,key=lambda w:hashlib.sha256(
        str(w["file_pageid"]).encode()).digest())[:opt.max_images]
    accepted=[];holds=[];images={}
    with ThreadPoolExecutor(max_workers=opt.workers) as ex:
        jobs={ex.submit(thumb_probe,w):w for w in items}
        for f in as_completed(jobs):
            w=jobs[f]
            try:
                color,sha,img=f.result()
                if not color["bright_pass"]:
                    holds.append({"id":w["file_pageid"],"reason":"DARK_OR_MUTED",
                                  "color_metrics":color});continue
                rec={**w,"color_metrics":color,"image_sha256":sha,
                     "curatorial_status":"HOLD_VISUAL_AND_ARTIST_ATTRIBUTION",
                     "rights_status":"HOLD_COUNTRY_BY_COUNTRY",
                     "museum":"Wikimedia Commons (community-sourced file)",
                     "curation_score":round(.28*color["luminance"]+
                                          .36*color["vivid_fraction"]+
                                          .20*color["saturation"]-
                                          .66*color["dark_fraction"],4)}
                accepted.append(rec);images[w["museum_native_id"]]=img
            except Exception as e:
                holds.append({"id":w["file_pageid"],"reason":str(e)[:150]})
    accepted.sort(key=lambda w:(-w["curation_score"],w["file_pageid"]))
    dest=OUT/f"batch_{opt.shard:02d}"
    dest.mkdir(parents=True,exist_ok=True)
    report={"schema_version":1,"source":"commons","as_of":"2026-11-26",
            "shard":opt.shard,"artists":ARTISTS[opt.shard],
            "search_stats":stats,"candidate_files":len(all_items),
            "images_probed":len(items),"bright_raster_pass":len(accepted),
            "dark_or_media_holds":len(holds),
            "remaining_unprobed":max(0,len(all_items)-len(items)),
            "black_and_white_portraits_filtered_by_title":True,
            "explicit_file_pd_or_cc0":True,
            "publish_to_app":False,"country_licence_audit":False,
            "works":accepted,"holds":holds[:100]}
    (dest/"review.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    if accepted:
        cols=8;W=170;H=172;entries=accepted[:96]
        canvas=Image.new("RGB",(cols*W,((len(entries)+cols-1)//cols)*H),"white")
        draw=ImageDraw.Draw(canvas)
        for i,w in enumerate(entries):
            img=images.get(w["museum_native_id"])
            if img is None:continue
            x=(i%cols)*W;y=(i//cols)*H
            canvas.paste(img,(x+(W-img.width)//2,y+(136-img.height)//2))
            draw.text((x+3,y+140),w["title"][:22],fill="black")
            draw.text((x+3,y+155),"commons:"+w["museum_native_id"],fill="black")
        canvas.save(dest/"sheet.jpg",quality=85,optimize=True)
    print(json.dumps({k:v for k,v in report.items() if k not in ("works","holds")},
                     ensure_ascii=False,sort_keys=True),flush=True)
    if not accepted:raise SystemExit("NO_COMMONS_PD_BRIGHT_IMAGES_VERIFIED")
if __name__=="__main__":main()
