#!/usr/bin/env python3
"""Large, bounded, non-publishing color-first Art Drift museum discovery.

Official primary OA/CC0 images only. Source-level filters -> real pixel
verification -> artist/title/source dedup -> human QA HOLD. Never alter runtime.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
import re
import sys
import time
import unicodedata
from collections import Counter
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
from urllib.parse import urlencode,urlsplit
from urllib.request import Request,urlopen
from PIL import Image,ImageOps,ImageDraw

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/".artdrift_research/bright_mass"
SOURCES={
 "aic":{"api":"api.artic.edu","image":"www.artic.edu",
        "museum":"Art Institute of Chicago","license":"Public Domain",
        "evidence":"https://www.artic.edu/open-access/open-access-images"},
 "cma":{"api":"openaccess-api.clevelandart.org",
        "image":"openaccess-cdn.clevelandart.org",
        "museum":"Cleveland Museum of Art","license":"CC0",
        "evidence":"https://www.clevelandart.org/open-access"},
 "met":{"api":"collectionapi.metmuseum.org",
        "image":"images.metmuseum.org",
        "museum":"The Metropolitan Museum of Art","license":"CC0",
        "evidence":"https://www.metmuseum.org/hubs/open-access"},
}
# AO user preference: saturated modern imagery, landscapes, gardens, sea, flowers.
SCENE=("landscape","garden","flower","blossom","orchard","meadow","field",
       "wheat","haystack","river","beach","shore","seascape","sea","ocean",
       "harbor","harbour","port","coast","coastal","mountain","mountains",
       "hill","hills","valley","lake","island","wood","woods","tree","trees",
       "forest","village","farm","farmhouse","cottage","countryside",
       "sky","cloud","sunlit","sunset","sunrise","provence","brittany",
       "giverny","auvers","argenteuil","collioure","riverbank","riverbanks",
       "sunflower","roses","lilies","lily","spring","summer","tulip",
       "dahlia","irises","bridge","road","path","house","houses","rooftops",
       "windmill","windmills","palms","palmtree","cypress","boulevard",
       "waterfront","sailboats","sailboat","boats","boat","pond","waterfall",
       "flowers","pond","lilac","hydrangea","bouquet","vase",
       "still life","still-life","fruit","apples","lemons","oranges",
       "water lilies","waterlilies","pine","cherry blossom","mosaic",
       "sunshine","landscapes","parks","park","orchards","meadows")
# Exclude human-centric works without incorrectly blocking words like "Manet".
AVOID=("portrait","self portrait","self-portrait","woman","women","man","men",
       "girl","girls","boy","boys","family","father","mother","son","daughter",
       "children","child","baby","babies","lady","ladies","figure","figures",
       "nude","bather","bathers","dancer","dancers","performer","performers",
       "seated","sitting","standing","a couple","couple","naked","worker",
       "workers","fishermen","fisherman","soldiers","saints","madonna",
       "holy","angel","angels","virgin","christ","crucifixion","sketch",
       "study of a","study for","horseman","horsemen","riders","rider",
       "interior with","genre scene","crowd","crowds","party","picnic",
       "nocturne","at night","nightfall","night","dark","black",
       "stormy","storm","moonlight","moonlit","at dusk","dusk","twilight",
       "war","battle","fire","burning","death","funeral","cemetery")
SCENE_RE=re.compile(r"\b(?:"+"|".join(re.escape(w) for w in sorted(set(SCENE),key=len,reverse=True))+r")\b")
AVOID_RE=re.compile(r"\b(?:"+"|".join(re.escape(w) for w in sorted(set(AVOID),key=len,reverse=True))+r")\b")
IMAGE_DARK_MAX=.10
IMAGE_LUMINANCE_MIN=.55
IMAGE_VIVID_MIN=.18
IMAGE_SATURATION_MIN=.18
Image.MAX_IMAGE_PIXELS=20_000_000

# These terms are distributed across independent batches. No sequential,
# tiny, one-at-a-time loop: metadata searches and image checks run bounded parallel.
AIC_TERMS=[
 ("landscape","garden","seascape","flowers","monet","pissarro"),
 ("flower","orchard","river","beach","van gogh","renoir"),
 ("impressionism","meadow","forest","brittany","cezanne","gauguin"),
 ("still life","spring","summer","coast","seurat","signac"),
 ("village","blossom","mountain","countryside","sisley","morisot"),
 ("sky","sunflower","harbor","sunset","redon","bonnard"),
]
MET_TERMS=[
 ("landscape","impressionism","garden"),
 ("flower","blossom","still life"),
 ("sea","coast","beach"),
 ("monet","pissarro","renoir"),
 ("van gogh","gauguin","seurat"),
 ("mountain","river","trees"),
]
def norm(s):
    return unicodedata.normalize("NFKD",str(s or "")).encode("ascii","ignore").decode().lower()

def cleaned(s):
    return re.sub(r"[^a-z0-9]+"," ",norm(s)).strip()

def host_ok(url,expected):
    if not isinstance(url,str):return False
    try:
        p=urlsplit(url)
        return (p.scheme=="https" and p.hostname==expected
                and not p.username and not p.password and p.port in (None,443))
    except ValueError:return False

def request_json(url,host,limit=9_000_000,attempts=3):
    if not host_ok(url,host):raise ValueError("unsafe API URL")
    last=None
    for at in range(attempts):
        try:
            req=Request(url,headers={"User-Agent":"ArtDrift-OpenAccess-Research/1.0",
                                     "Accept":"application/json"})
            with urlopen(req,timeout=23) as resp:
                if not host_ok(resp.url,host):raise ValueError("redirect not whitelisted")
                payload=resp.read(limit+1)
            if len(payload)>limit:raise ValueError("API response oversized")
            return json.loads(payload)
        except Exception as err:
            last=err
            if at+1<attempts:time.sleep(.5*(at+1))
    raise RuntimeError(str(last)[:170])

def dates(text, start=None):
    if isinstance(start,int) and 1850<=start<=1960:return start
    found=[int(x) for x in re.findall(r"(?<!\d)(?:18|19)\d{2}(?!\d)",str(text or ""))]
    if not found:return None
    # Ignore lifespan dates if mistakenly mixed with creation dates: only creation date passed here.
    if min(found)<1850 or max(found)>1960:return None
    return min(found)

def scene_ok(title,artist):
    t=cleaned(title)
    a=cleaned(artist)
    if not t or AVOID_RE.search(t):return False
    if any(s in a for s in (" imitator "," follower "," school of "," after ",
                            " anonymous","unknown artist","unidentified")):return False
    return bool(SCENE_RE.search(t))

def main_keys():
    keys=set();names=set();fail=[]
    paths=["assets/gallery/catalog.json","assets/museums/catalog.json",
           "assets/museums/catalog_global.json",
           "research/nga/20261125/nga_bright_review.json",
           "research/nga/20261126/nga_bright_wave2_review.json"]
    for path in paths:
        p=ROOT/path
        if not p.is_file():
            fail.append(path);continue
        try:
            obj=json.loads(p.read_text(encoding="utf-8"))
            data=obj if isinstance(obj,list) else obj.get("works",[])
            for item in data:
                src=item.get("museum_source","aic")
                if src=="cleveland":src="cma"
                if src in ("nga","aic","cma","met"):
                    ident=item.get("museum_native_id")
                    if ident is None:ident=item.get("id") if src=="aic" else None
                    if ident is not None:keys.add((src,str(ident)))
                title=item.get("title")
                artist=item.get("artist_title") or item.get("artist") or item.get("artist_display")
                if title and artist:names.add((cleaned(title),cleaned(artist)))
        except Exception as e:raise RuntimeError(f"catalog unreadable {path}: {e}")
    # Mandatory: all actual runtime catalog files present.
    assert not any(x in fail for x in paths[:3]),"Missing runtime catalog for dedup: "+str(fail)
    assert len(keys)>600,("Bad catalog dedup coverage",len(keys))
    return keys,names

def color_metric(src):
    im=ImageOps.exif_transpose(src.convert("RGB"))
    w,h=im.size
    if min(w,h)<48:raise ValueError("image too small")
    # Remove narrow white border but not actual dark pixels of artwork.
    m=round(min(w,h)*.04)
    im=im.crop((m,m,w-m,h-m))
    im.thumbnail((110,110))
    pixels=list(im.getdata());N=len(pixels)
    dark=0;vivid=0;sum_l=0.;sum_s=0.;very_dark=0
    for r,g,b in pixels:
        high=max(r,g,b);low=min(r,g,b)
        s=(high-low)/high if high else 0.
        l=(.2126*r+.7152*g+.0722*b)/255.
        sum_l+=l;sum_s+=s
        dark+=l<.31
        very_dark+=l<.20
        vivid+=(s>.26 and l>.43)
    lm=sum_l/N;sm=sum_s/N;df=dark/N;vf=vivid/N
    # Reject big dark patches even when small colorful accents drive avg.
    return {"luminance":round(lm,4),"saturation":round(sm,4),
            "dark_fraction":round(df,4),"very_dark_fraction":round(very_dark/N,4),
            "vivid_fraction":round(vf,4),
            "bright_pass":lm>=IMAGE_LUMINANCE_MIN and
                          sm>=IMAGE_SATURATION_MIN and
                          df<=IMAGE_DARK_MAX and vf>=IMAGE_VIVID_MIN}

def image_check(item):
    url=item["remote_preview_url"]
    host=SOURCES[item["source"]]["image"]
    if not host_ok(url,host):raise ValueError("image host mismatch")
    req=Request(url,headers={"User-Agent":"ArtDrift-ColorRaster/1.0","Accept":"image/jpeg"})
    with urlopen(req,timeout=15) as response:
        if not host_ok(response.url,host):raise ValueError("unsafe image redirect")
        if not response.headers.get("Content-Type","").lower().startswith("image/"):
            raise ValueError("not image content")
        raw=response.read(1_300_001)
    if not 512<=len(raw)<=1_300_000:raise ValueError("image bytes out of bound")
    with Image.open(io.BytesIO(raw)) as source:
        if source.format not in ("JPEG","PNG","WEBP"):raise ValueError("unexpected image format")
        color=color_metric(source)
        image=ImageOps.exif_transpose(source.convert("RGB"))
        image.thumbnail((146,138),Image.Resampling.LANCZOS)
    return color,hashlib.sha256(raw).hexdigest(),image

def aic_discover(shard):
    terms=AIC_TERMS[shard]
    fields=("id,title,artist_title,date_display,date_start,date_end,"
            "image_id,is_public_domain,artwork_type_title,medium_display")
    data={};stats=Counter()
    for term in terms:
        for page in range(1,5):
            q=urlencode({"q":term,"query[term][is_public_domain]":"true",
                "fields":fields,"limit":100,"page":page})
            try:d=request_json("https://api.artic.edu/api/v1/artworks/search?"+q,SOURCES["aic"]["api"])
            except Exception as e:
                stats["api_failed"]+=1;print("AIC_API_HOLD",term,page,str(e)[:100],flush=True);break
            rows=d.get("data") or []
            stats["records_seen"]+=len(rows)
            for obj in rows:
                ident=obj.get("id")
                if not isinstance(ident,int) or ident<=0:continue
                if obj.get("is_public_domain") is not True:continue
                if norm(obj.get("artwork_type_title"))!="painting":continue
                iid=str(obj.get("image_id") or "")
                if not re.fullmatch(r"[0-9a-fA-F-]{16,64}",iid):continue
                yr=dates(obj.get("date_display"),obj.get("date_start"))
                if yr is None:continue
                title=str(obj.get("title") or "").strip();artist=str(obj.get("artist_title") or "").strip()
                if not scene_ok(title,artist):continue
                prev=f"https://www.artic.edu/iiif/2/{iid}/full/256,/0/default.jpg"
                item={"source":"aic","museum_native_id":str(ident),"title":title,
                      "artist":artist,"year":yr,"date":obj.get("date_display"),
                      "medium":obj.get("medium_display") or "",
                      "remote_preview_url":prev,
                      "remote_full_url":f"https://www.artic.edu/iiif/2/{iid}/full/1000,/0/default.jpg",
                      "museum_url":f"https://www.artic.edu/artworks/{ident}",
                      "image_id":iid,"license":"Public Domain"}
                data[item["museum_native_id"]]=item
            if len(rows)<100:break
            time.sleep(.1)
    return list(data.values()),dict(stats)

def cma_discover(shard):
    # 6 independent offset windows of up to ~1000 returned paintings.
    stats=Counter();records={}
    for page in range(5):
        skip=(shard*5+page)*180
        p=urlencode({"type":"Painting","cc0":"","has_image":1,"limit":180,
                     "skip":skip})
        url="https://openaccess-api.clevelandart.org/api/artworks/?"+p
        try:d=request_json(url,SOURCES["cma"]["api"],limit=15_000_000)
        except Exception as e:
            stats["api_failed"]+=1;print("CMA_API_HOLD",skip,str(e)[:120],flush=True);continue
        rows=d.get("data") or []
        stats["records_seen"]+=len(rows)
        for obj in rows:
            if norm(obj.get("share_license_status"))!="cc0":continue
            if norm(obj.get("type"))!="painting":continue
            ident=obj.get("id")
            if not isinstance(ident,int) or ident<=0:continue
            date=obj.get("creation_date") or ""
            yr=dates(date, obj.get("sortable_date") if isinstance(obj.get("sortable_date"),int) else None)
            if yr is None:continue
            title=str(obj.get("title") or "").strip()
            artists=obj.get("creators") or []
            artist=next((str(a.get("description") or "") for a in artists if isinstance(a,dict)),"")
            if not scene_ok(title,artist):continue
            img=(obj.get("images") or {}).get("web") or {}
            image=str(img.get("url") or "")
            if not host_ok(image,SOURCES["cma"]["image"]):continue
            item={"source":"cma","museum_native_id":str(ident),"title":title,
                  "artist":artist,"year":yr,"date":date,
                  "medium":obj.get("technique") or "",
                  "remote_preview_url":image,"remote_full_url":image,
                  "museum_url":obj.get("url") or "https://www.clevelandart.org/open-access",
                  "license":"CC0"}
            records[item["museum_native_id"]]=item
        if len(rows)<180:break
        time.sleep(.12)
    return list(records.values()),dict(stats)

def met_discover(shard):
    # Met v1.1 search returns IDs, v1 per-object detailed CC0 metadata; bounded.
    stats=Counter();seen=set()
    for term in MET_TERMS[shard]:
        q=urlencode({"q":term,"hasImages":"true","limit":450,"offset":0,
                     "departmentId":11})
        try:d=request_json("https://collectionapi.metmuseum.org/public/collection/v1.1/search?"+q,
                           SOURCES["met"]["api"],limit=3_000_000)
        except Exception as e:
            stats["search_failed"]+=1;print("MET_SEARCH_HOLD",term,str(e)[:120],flush=True);continue
        for v in d.get("objectIDs") or []:
            if isinstance(v,int):seen.add(v)
    ids=sorted(seen,key=lambda x:hashlib.sha256(str(x).encode()).digest())[:230]
    stats["object_ids"]=len(ids)
    data={}
    def task(ident):
        try:
            obj=request_json(f"https://collectionapi.metmuseum.org/public/collection/v1/objects/{ident}",
                             SOURCES["met"]["api"],limit=240000,attempts=2)
            if obj.get("isPublicDomain") is not True:return None
            kind=(norm(obj.get("classification"))+" "+norm(obj.get("objectName"))+
                  " "+norm(obj.get("medium")))
            if "paint" not in kind and "oil on canvas" not in kind:return None
            title=str(obj.get("title") or "").strip();artist=str(obj.get("artistDisplayName") or "").strip()
            yr=dates(obj.get("objectDate"),obj.get("objectBeginDate"))
            if yr is None or not scene_ok(title,artist):return None
            image=str(obj.get("primaryImageSmall") or "")
            if not host_ok(image,SOURCES["met"]["image"]):return None
            return {"source":"met","museum_native_id":str(ident),"title":title,
                    "artist":artist,"year":yr,"date":obj.get("objectDate") or "",
                    "medium":obj.get("medium") or "","remote_preview_url":image,
                    "remote_full_url":image,"museum_url":obj.get("objectURL") or
                    "https://www.metmuseum.org/hubs/open-access","license":"CC0"}
        except Exception:return None
    with ThreadPoolExecutor(max_workers=5) as ex:
        fs=[ex.submit(task,ident) for ident in ids]
        for future in as_completed(fs):
            obj=future.result()
            if obj:data[obj["museum_native_id"]]=obj
    stats["records_with_scenic_title_and_cc0"]=len(data)
    return list(data.values()),dict(stats)

def write_sheet(works,thumbs,path,limit=100):
    selection=works[:limit]
    if not selection:return
    cols=8;W=178;H=176
    im=Image.new("RGB",(cols*W,((len(selection)+cols-1)//cols)*H),"white")
    painter=ImageDraw.Draw(im)
    for i,w in enumerate(selection):
        picture=thumbs.get(w["museum_native_id"])
        if picture is None:continue
        x=(i%cols)*W;y=(i//cols)*H
        im.paste(picture,(x+(W-picture.width)//2,y+(138-picture.height)//2))
        painter.text((x+3,y+141),w["title"][:24],fill="black")
        painter.text((x+3,y+155),w["source"]+":"+w["museum_native_id"],fill="black")
    im.save(path,"JPEG",quality=85,optimize=True)

def run(provider,shard,cap,workers):
    keys,names=main_keys()
    if provider=="aic":candidates,stats=aic_discover(shard)
    elif provider=="cma":candidates,stats=cma_discover(shard)
    elif provider=="met":candidates,stats=met_discover(shard)
    else:raise ValueError("provider")
    fresh=[];dups=[]
    for w in candidates:
        ident=(w["source"],w["museum_native_id"])
        semantic=(cleaned(w["title"]),cleaned(w["artist"]))
        if ident in keys or semantic in names:
            dups.append({"id":w["museum_native_id"],"reason":"ALREADY_IN_APP"});continue
        fresh.append(w)
    fresh.sort(key=lambda w:hashlib.sha256(
        (w["museum_native_id"]+w["source"]).encode()).digest())
    # Shards bound to cap (not claim exhaustive).
    chosen=fresh[:cap]
    holds=[];accepted=[];thumbnails={}
    with ThreadPoolExecutor(max_workers=workers) as ex:
        tasks={ex.submit(image_check,w):w for w in chosen}
        for fut in as_completed(tasks):
            w=tasks[fut]
            try:
                color,sha,thumbnail=fut.result()
                if not color["bright_pass"]:
                    holds.append({"id":w["museum_native_id"],"reason":"DARK_OR_MUTED",
                                  "metrics":color})
                    continue
                w={**w,"color_metrics":color,"image_sha256":sha,
                   "license_evidence_url":SOURCES[provider]["evidence"],
                   "museum":SOURCES[provider]["museum"],
                   "rights_status":"IMAGE_OPEN_ACCESS__FINAL_TERRITORY_REVIEW_REQUIRED",
                   "curatorial_status":"HOLD_CONTACT_SHEET_REVIEW",
                   "runtime_visible":False,"worldwide_commercial_certified":False}
                w["curation_score"]=round(.28*color["luminance"]+.36*color["vivid_fraction"]+
                   .20*color["saturation"]-.66*color["dark_fraction"],4)
                accepted.append(w);thumbnails[w["museum_native_id"]]=thumbnail
            except Exception as exc:
                holds.append({"id":w["museum_native_id"],"reason":str(exc)[:160]})
    accepted.sort(key=lambda w:(-w["curation_score"],w["museum_native_id"]))
    folder=OUT/provider/f"batch_{shard:02d}"
    folder.mkdir(parents=True,exist_ok=True)
    report={"schema_version":1,"as_of":"2026-11-26",
            "provider":provider,"shard":shard,"api":"official OA museum",
            "search_statistics":stats,"source_candidates":len(candidates),
            "duplicates_against_live_and_nga":len(dups),
            "eligible_to_probe":len(fresh),"images_probed":len(chosen),
            "color_verified_pass":len(accepted),"hold_count":len(holds),
            "unprobed_from_this_shard":max(0,len(fresh)-len(chosen)),
            "thresholds":{"luminance_min":IMAGE_LUMINANCE_MIN,
                          "dark_fraction_max":IMAGE_DARK_MAX,
                          "vivid_fraction_min":IMAGE_VIVID_MIN,
                          "saturation_min":IMAGE_SATURATION_MIN},
            "public_release":False,"runtime_imported":0,"open_access_policy":SOURCES[provider]["evidence"],
            "works":accepted,"holds":holds[:120]}
    (folder/"review.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    write_sheet(accepted,thumbnails,folder/"sheet.jpg")
    print(json.dumps({k:v for k,v in report.items() if k not in ("works","holds")},
                     ensure_ascii=False,sort_keys=True),flush=True)
    # No hard quota: empty discovery is NOT a success false-positive; mark failure.
    if len(accepted)==0:raise SystemExit("ZERO_COLOR_VERIFIED_WORKS")

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--provider",choices=SOURCES,required=True)
    a.add_argument("--shard",type=int,required=True)
    a.add_argument("--max-images",type=int,default=260)
    a.add_argument("--workers",type=int,default=5)
    v=a.parse_args()
    if not(0<=v.shard<=5 and 10<=v.max_images<=400 and 1<=v.workers<=6):
        a.error("out-of-bounds max images / workers / shards")
    run(v.provider,v.shard,v.max_images,v.workers)

if __name__=="__main__":
    main()
