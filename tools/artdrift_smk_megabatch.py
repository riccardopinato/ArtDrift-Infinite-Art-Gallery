#!/usr/bin/env python3
"""SMK National Gallery of Denmark: true large-batch modern colorful painting study.

Search official per-object public_domain+rights+painting, verify iip.smk.dk
IIIF pixels, reject dark imagery, dedup runtime and pending PR68 research.
Research-only: NEVER add to Flutter runtime automatically.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import re
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
from urllib.parse import urlencode,urlsplit
from urllib.request import Request,urlopen
from PIL import Image,ImageOps,ImageDraw
from artdrift_bright_mass import color_metric,cleaned,host_ok

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/".artdrift_research/smk_mass"
SOURCE="https://api.smk.dk/api/v1/art/search/?"
RIGHT="https://www.smk.dk/en/article/smk-open/"
# Danish+English subject words, but NOT mandatory if explicit artist/style.
TITLE_GOOD=(
 "landskab","landscape","blomster","blomst","blomstring","flowers","flower",
 "hav","havet","havn","havnen","harbor","harbour","sea","seascape","coast",
 "strand","kyst","water","vand","sø","soe","lake","river","flod",
 "skov","træ","trae","tree","wood","forest","strand","have","garden",
 "marker","mark","fields","field","eng","meadow","valley","dal",
 "bjerg","mountain","bakke","hill","hills","farm","gaard","gård","gaard",
 "landsby","village","hus","house","vinter","forår","spring","sommer","summer",
 "maj","juni","july","juli","august","sol","sun","sunny","sunset","sunrise",
 "korn","wheat","road","vej","sti","path","park","rose","roser","roses",
 "hortensia","stilleben","still life","stilleben","frugt","fruits","fruit",
 "æbler","apples","frugter","citron","orange","buket","bouquet",
 "vinmark","vineyard","winter","mølle","windmill","island","øen",
 "kystlandskab","strandbred","klitter","dunes","blå","blaa","blue",
 "gul","yellow","rød","red","røde","grøn","green","farve","color",
 "udsigt","view","fjord","fugle","birds","både","boats","boat",
 "seine","giverny","provence","brittany","bretagne","fauvism",
 "expressionism","impressionism",
)
AVOID=(
 "portræt","portrait","self portrait","selvportræt","nøgen","nude",
 "kvinde","kvinder","woman","women","pige","piger","girl","girls",
 "mand","mænd","man","men","dreng","drenge","boy","boys","barn","børn",
 "children","child","baby","dame","lady","figurer","figure","figures",
 "dans","dance","dancer","dancers","person","ansigt","head","face",
 "brystbillede","hoved","study","studie","skitse","sketch",
 "aften","night","nocturne","dusk","twilight","dark","black",
 "mørk","nat","natten","moonlight","battle","war","krig",
 "interiør","interior","kirke","saint","saints","christ",
)
SEARCHES=(
 ("*","landskab","blomster","have","skov","strand","sea"),
 ("*","hav","landscape","sommer","mark","coast","flowers"),
 ("*","træer","havn","park","flod","garden","roses"),
 ("*","landsby","sø","bjerge","valley","water","orchard"),
 ("*","forår","kyst","blomstring","spring","harbor","meadow"),
 ("*","eng","vand","sol","sunflower","sunset","stilleben"),
 ("*","fauvism","impressionism","expressionism","bright","summer","garden"),
 ("*","oliefarve","maleri","oil","landscapes","flowers","frugt"),
)
GOOD_RE=re.compile(r"\b(?:"+"|".join(re.escape(cleaned(x)) for x in sorted(set(TITLE_GOOD),key=len,reverse=True) if cleaned(x))+r")\b")
AVOID_RE=re.compile(r"\b(?:"+"|".join(re.escape(cleaned(x)) for x in sorted(set(AVOID),key=len,reverse=True) if cleaned(x))+r")\b")
Image.MAX_IMAGE_PIXELS=20_000_000

def date_year(raw):
    val=str(raw or "")
    found=[int(x) for x in re.findall(r"(?<!\d)(?:18|19)\d{2}(?!\d)",val)]
    if not found or min(found)<1850 or max(found)>1960:return None
    return min(found)

def title_valid(name):
    t=cleaned(name)
    if not t or AVOID_RE.search(t):return False
    # Danish compounds such as "Sommerlandskab" or "Kystlandskab" have no
    # word boundaries inside the joined noun; keep them without opening
    # the gate for portraits or other human-centric morphology.
    if any(bad in t for bad in ("portraet","portra","portrait","kvind",
         "piger","dreng","figurer","nogen","mork","nocturne")):
        return False
    return bool(GOOD_RE.search(t)) or any(
        good in t for good in
        ("landskab","blomster","strand","skov","sommer","have","kyst","roser",
         "meadow","landscape","garden","orchard"))

def prior_ids():
    ids=set()
    for rel in ("assets/museums/catalog.json","assets/museums/catalog_global.json"):
        obj=json.loads((ROOT/rel).read_text(encoding="utf-8"))
        for w in obj:
            if w.get("museum_source")=="smk" and w.get("museum_native_id"):
                ids.add(str(w["museum_native_id"]).casefold())
    p=ROOT/"research/mass_bright/20261126/smk_related_pr68_exclusions.json"
    obj=json.loads(p.read_text(encoding="utf-8"))
    ids|={str(x).casefold() for x in obj["smk_existing_research_ids"]}
    return ids

def request(q,offset,count=100):
    qs=urlencode({"keys":q,"filters":"[public_domain:true],[has_image:true]",
                  "offset":offset,"rows":count})
    url=SOURCE+qs
    if not host_ok(url,"api.smk.dk"):raise ValueError("bad API")
    req=Request(url,headers={"User-Agent":"ArtDrift-BrightLandscape-Curated/1.0",
                             "Accept":"application/json"})
    with urlopen(req,timeout=28) as resp:
        if not host_ok(resp.url,"api.smk.dk"):raise ValueError("redirect not official")
        raw=resp.read(12_000_001)
    if len(raw)>12_000_000:raise ValueError("SMK API giant response")
    return json.loads(raw)

def compatible(obj):
    if not isinstance(obj,dict):return None
    if obj.get("public_domain") is not True or not obj.get("has_image"):return None
    rights=str(obj.get("rights") or "")
    if not ("creativecommons.org/publicdomain/mark/" in rights or
            "creativecommons.org/publicdomain/zero/" in rights):return None
    ty=" ".join(str(x.get("name") or "") for x in obj.get("object_names") or []
                if isinstance(x,dict)).lower()
    if not ("maleri" in ty or "painting" in ty):return None
    ident=str(obj.get("object_number") or obj.get("id") or "").strip()
    if not ident or len(ident)>80:return None
    media=str(obj.get("image_iiif_id") or "").rstrip("/")
    if not host_ok(media,"iip.smk.dk") or "/iiif/" not in media:return None
    title=next((str(x.get("title") or "").strip() for x in obj.get("titles") or []
                if isinstance(x,dict) and x.get("title")),"")
    if not title_valid(title):return None
    artistdata=obj.get("artist") or []
    artist=next((s.strip() for s in artistdata if isinstance(s,str) and s.strip()),"")
    if any(x in cleaned(artist) for x in (" unknown"," anonymous","imitator",
                                          "copy after","school of")):return None
    dates=obj.get("production_date") or []
    ds=" ".join(str(x.get("period") or "") for x in dates if isinstance(x,dict))
    year=date_year(ds)
    if year is None:return None
    return {"source":"smk","museum_native_id":ident,
            "title":title,"artist":artist,"year":year,"date":ds,
            "rights_license":"Public Domain Mark / CC0",
            "rights_evidence_url":rights,"classification":"Painting",
            "museum":"SMK – National Gallery of Denmark",
            "remote_preview_url":media+"/full/300,/0/default.jpg",
            "remote_full_url":media+"/full/1000,/0/default.jpg",
            "museum_url":f"https://open.smk.dk/en/artwork/image/{ident}",
            "medium":", ".join(str(x) for x in (obj.get("techniques") or [])[:2])[:150]}

def image_probe(w):
    url=w["remote_preview_url"]
    if not host_ok(url,"iip.smk.dk"):raise ValueError("bad IIIF")
    req=Request(url,headers={"User-Agent":"ArtDrift-Research-Only/1.0","Accept":"image/jpeg"})
    with urlopen(req,timeout=20) as resp:
        if not host_ok(resp.url,"iip.smk.dk"):raise ValueError("redirect not iip.smk.dk")
        if not resp.headers.get("Content-Type","").lower().startswith("image/"):
            raise ValueError("not image")
        raw=resp.read(1_400_001)
    if len(raw)<512 or len(raw)>1_400_000:raise ValueError("image byte bounds")
    with Image.open(io.BytesIO(raw)) as image:
        if image.format not in ("JPEG","PNG","WEBP"):raise ValueError("not raster")
        color=color_metric(image)
        im=ImageOps.exif_transpose(image.convert("RGB"))
        im.thumbnail((144,136),Image.Resampling.LANCZOS)
        im=im.copy()
    return color,hashlib.sha256(raw).hexdigest(),im

def run(shard,probe_max,workers):
    excluded=prior_ids()
    items={};stats=Counter()
    qs=SEARCHES[shard]
    for j,q in enumerate(qs):
        # Star pages reach independent sequential windows, targeting full SMK.
        page_n=7 if q=="*" else 4
        baseoffset=(shard*700 if q=="*" else (shard%3)*400)
        for p in range(page_n):
            offset=baseoffset+p*100
            try:d=request(q,offset)
            except Exception as e:
                stats["failed_pages"]+=1
                print("SMK_PAGE_HOLD",shard,q,offset,str(e)[:100],flush=True)
                continue
            records=d.get("items") or []
            stats["rows_seen"]+=len(records)
            for row in records:
                item=compatible(row)
                if item is None:continue
                id=item["museum_native_id"].casefold()
                if id in excluded:stats["duplicates_existing"]+=1;continue
                items[id]=item
            if len(records)<100:break
            time.sleep(.06)
    pool=sorted(items.values(),key=lambda x:hashlib.sha256(
        x["museum_native_id"].lower().encode()).digest())
    subset=pool[:probe_max]
    acc=[];holds=[];thumbs={}
    with ThreadPoolExecutor(max_workers=workers) as exe:
        futures={exe.submit(image_probe,w):w for w in subset}
        for f in as_completed(futures):
            item=futures[f]
            try:
                color,sha,im=f.result()
                if not color["bright_pass"]:
                    holds.append({"id":item["museum_native_id"],"reason":"DARK_OR_MUTED",
                                  "metrics":color});continue
                rec={**item,"color_metrics":color,"image_sha256":sha,
                     "curatorial_status":"HOLD_VISUAL_QA",
                     "rights_status":"HOLD_TERRITORY_CHECK",
                     "runtime_visible":False,"worldwide_commercial_certified":False}
                rec["curation_score"]=round(.28*color["luminance"]+
                    .36*color["vivid_fraction"]+.20*color["saturation"]-
                    .66*color["dark_fraction"],4)
                acc.append(rec);thumbs[item["museum_native_id"]]=im
            except Exception as e:
                holds.append({"id":item["museum_native_id"],"reason":str(e)[:140]})
    acc.sort(key=lambda w:(-w["curation_score"],w["museum_native_id"].casefold()))
    out=OUT/f"batch_{shard:02d}"
    out.mkdir(parents=True,exist_ok=True)
    report={"schema_version":1,"as_of":"2026-11-26","source":"smk",
            "batch":shard,"query_set":list(qs),"search_statistics":dict(stats),
            "eligible_unique_non_main":len(pool),"images_probed":len(subset),
            "verified_bright_works":len(acc),"hold_count":len(holds),
            "unprobed":max(0,len(pool)-len(subset)),
            "thresholds":{"lum_min":.55,"max_dark_fraction":.10,
                          "vivid_min":.18,"sat_min":.18},
            "runtime_imported":0,"global_clearance":0,
            "works":acc,"holds":holds[:150]}
    (out/"review.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    if acc:
        cols=8;W=176;H=172;entries=acc[:min(96,len(acc))]
        sheet=Image.new("RGB",(cols*W,((len(entries)+cols-1)//cols)*H),"white")
        draw=ImageDraw.Draw(sheet)
        for i,w in enumerate(entries):
            img=thumbs.get(w["museum_native_id"])
            if img is None:continue
            x=i%cols*W;y=i//cols*H
            sheet.paste(img,(x+(W-img.width)//2,y+(136-img.height)//2))
            draw.text((x+3,y+139),w["title"][:25],fill="black")
            draw.text((x+3,y+153),w["museum_native_id"][:25],fill="black")
        sheet.save(out/"sheet.jpg",quality=86,optimize=True)
    print(json.dumps({k:v for k,v in report.items() if k not in ("works","holds")},
                     ensure_ascii=False,sort_keys=True),flush=True)
    if len(acc)==0:raise SystemExit("NO_VERIFIED_IN_SMK_SHARD")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--shard",type=int,required=True)
    p.add_argument("--max-images",type=int,default=230)
    p.add_argument("--workers",type=int,default=4)
    a=p.parse_args()
    if not(0<=a.shard<=7 and 15<=a.max_images<=400 and 1<=a.workers<=5):
        p.error("bounds")
    run(a.shard,a.max_images,a.workers)
