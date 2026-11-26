#!/usr/bin/env python3
"""Discover art from genuinely NEW, non-US museums with official evidence.

RIJKS: 2026 Linked Art Search API + 3-hop IIIF, non-login.
NATIONALMUSEUM SE: Museum-official Wikimedia category/search with per-file PD.
STAEDEL: OAI-PMH LIDO official item/CC BY-SA 4.0, with attribution required.
Only research/HOLD staged. Color limits preferred <=15%, conditional 15-20%
if saturated/vivid. Never modify ArtDrift runtime or assets.
"""
from __future__ import annotations
import argparse,hashlib,io,json,re,time,unicodedata,urllib.error,urllib.parse,urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
from PIL import Image,ImageDraw,ImageOps

ROOT=Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0,str(ROOT/"tools"))
from artdrift_bright_mass import color_metric,main_keys,cleaned
from artdrift_dark_threshold_ab import pixel_eligible,color_tier
from artdrift_commons_pd_bright import licenses,strip_html,safe_thumb
OUT=ROOT/".artdrift_eu/batches"
API_HOSTS={"data.rijksmuseum.nl","iiif.micr.io","commons.wikimedia.org",
           "thumb.wikimedia.org","sammlung.staedelmuseum.de"}
ART_URL_LICENSE={
 "rijks":"https://data.rijksmuseum.nl/about/",
 "nationalmuseum_se":"https://www.nationalmuseum.se/en/explore-art-and-design/images",
 "staedel":"https://sammlung.staedelmuseum.de/en/oai/guide"}
Image.MAX_IMAGE_PIXELS=20_000_000

SCENE=("landscape","landschap","landskab","landskap","blom","flower","blossom",
 "garden","tuin","have","garten","strand","beach","meer","sea","zee","hav",
 "havet","seascape","river","rivier","flod","skov","wald","woods","woodland",
 "forest","boom","bomen","trees","tree","träd","traed","berg","mountain",
 "mountains","field","feld","mark","meadow","wei","park","kust","coast",
 "kusten","zomer","sommar","summer","spring","voorjaar","frühling","fruhling",
 "riverbank","rijn","rhein","sun","sol","sky","himmel","skyline",
 "village","dorp","dorf","blume","blueten","blüte","bloem","bos","stilleben",
 "stilleven","still life","fruit","frucht","weide","stranden","hafen","haven",
 "harbor","harbour","bucht","bay","allee","alley","alé","allé",
 "natuur","natur","nature","fjord","archipel","skärgård","skar",
 "rivier","vijver","strand","solnedgang","sunset","sonnen","water",
 "boats","boot","schiff","ships","zeilboot","fruits")
AVOID=("portrait","portret","portraet","portra","portratt","porträt","portrait",
 "portrait of","self","zelfportret","portrait","portræt","portrait","kind",
 "meisje","woman","women","female","man","men","mann","girl","boy",
 "frau","fräulein","madchen","mädchen","lady","figures","figure",
 "mensen","vrouw","vrouwen","kvinna","kvinnor","soldier","soldaat",
 "nude","naked","bath","bather","sitzend","sittend","sitting",
 "sleeping","death","nacht","night","nocturne","black","dark","dunkel",
 "storm","stormy","battle","krieg","war","sketch","studie","study","etching",
 "drawing","tekening","zeichnung","print","grafik","photo","photograph",
 "gravure","lithograph","akvarel","aquarel","watercolor","watercolour")
SCENE_RE=re.compile(r"\b(?:"+"|".join(re.escape(cleaned(x)) for x in sorted(set(SCENE),key=len,reverse=True) if cleaned(x))+r")\b",re.I)
AVOID_RE=re.compile(r"\b(?:"+"|".join(re.escape(cleaned(x)) for x in sorted(set(AVOID),key=len,reverse=True) if cleaned(x))+r")\b",re.I)
YEAR_RE=re.compile(r"(?<!\d)(?:18|19)\d{2}(?!\d)")
STOP_PART=("[No Photo]","anonymous")
RIJKS_QUERIES=(
 ("landschap","bloemen","tuin","zee","strand","bomen"),
 ("zomer","park","veld","rivier","kust","natuur"),
 ("Monet","Toorop","Mondrian","Gestel","Jongkind","Sluijters")
)
NAT_QUERIES=(
 ("landskap","flowers","blommor","landscape","summer"),
 ("hav","sea","garden","strand","sol"),
 ("winter","skog","träd","meadow","mountain")
)

def allow(url,hosts=API_HOSTS):
    try:
        p=urllib.parse.urlsplit(str(url))
        return (p.scheme=="https" and p.hostname in hosts and
                not p.username and not p.password and p.port in (None,443))
    except ValueError:return False

def fetch(url,limit=1_300_000,timeout=20):
    if not allow(url):raise ValueError("unapproved museum source URI")
    req=urllib.request.Request(url,headers={
        "User-Agent":"ArtDrift-EuropeanOpenMuseums-Research/1.0",
        "Accept":"application/json,text/xml,image/jpeg,image/png,image/webp"})
    with urllib.request.urlopen(req,timeout=timeout) as response:
        if not allow(response.url):raise ValueError("unapproved redirected host")
        content=response.read(limit+1)
        if len(content)>limit:raise ValueError("oversize response")
        return content

def jget(url):
    return json.loads(fetch(url,limit=1_600_000))

def date_year(text):
    years=[int(y) for y in YEAR_RE.findall(str(text or "")[:200])]
    if not years:return None
    # Source may include a creation interval; do not accept artist lifespans.
    if min(years)<1850 or max(years)>1960:return None
    return min(years)

def scene_title(title):
    t=cleaned(title)
    if not t or AVOID_RE.search(t):return False
    return bool(SCENE_RE.search(t) or any(w in t for w in (
         "sommerlandskap","sommarlandskap","zomerlandschap","herfstlandschap","fruhlingslandschaft",
         "berglandschap","blomster","bloemen","landschaf","sommarlandskap")))

def author_year_from_doc(text):
    # Only metadata creation date fields, never artist birth/death dates.
    x=strip_html(text)
    if not x or len(x)>350:x=x[:350]
    years=[int(y) for y in YEAR_RE.findall(x)]
    if not years:return None
    y=years[0]
    return y if 1850<=y<=1960 else None

def image_raster(url):
    if not allow(url):raise ValueError("untrusted artwork image")
    raw=fetch(url,limit=1_500_000,timeout=18)
    if len(raw)<512:raise ValueError("image too small")
    with Image.open(io.BytesIO(raw)) as obj:
        if obj.format not in ("JPEG","PNG","WEBP"):
            raise ValueError("unexpected image format")
        color=color_metric(obj)
        preview=ImageOps.exif_transpose(obj.convert("RGB"))
        preview.thumbnail((148,136),Image.Resampling.LANCZOS)
        thumb=preview.copy()
    return color,hashlib.sha256(raw).hexdigest(),thumb

def display_name(items):
    for x in items:
        if not isinstance(x,dict):continue
        if x.get("type")=="Name":
            lang=x.get("language") or []
            if any(l.get("id","").endswith("300388277") for l in lang if isinstance(l,dict)):
                return str(x.get("content") or "")
    return next((str(x.get("content") or "") for x in items
                 if isinstance(x,dict) and x.get("type")=="Name"),"")

def rijks_artist(obj):
    out=obj.get("produced_by") or {}
    for part in out.get("part") or []:
        for person in part.get("carried_out_by") or []:
            notation=person.get("notation") or []
            en=next((n.get("@value") for n in notation if n.get("@language")=="en"),None)
            if en:return str(en)
        for item in part.get("referred_to_by") or []:
            c=str(item.get("content") or "")
            if c.lower().startswith("painter:"):return c.split(":",1)[1].strip()
    return ""

def rijks_year(obj):
    ts=(obj.get("produced_by") or {}).get("timespan") or {}
    if not ts:
        for p in (obj.get("produced_by") or {}).get("part") or []:
            ts=p.get("timespan") or {}
            if ts:break
    y=ts.get("begin_of_the_begin") or ""
    return date_year(y)

def rijks_ident(obj):
    for i in obj.get("identified_by") or []:
        if i.get("type")!="Identifier":continue
        if any(x.get("id")=="https://id.rijksmuseum.nl/22015218"
               for x in i.get("classified_as") or []):
            return str(i.get("content") or "")
    return ""

def rijks_object(ident):
    if not re.fullmatch(r"https://id.rijksmuseum.nl/\d+",str(ident)):
        raise ValueError("unsafe Rijks object id")
    raw=ident.replace("id.rijksmuseum.nl","data.rijksmuseum.nl")
    obj=jget(raw+"?_profile=la-framed")
    title=display_name(obj.get("identified_by") or [])
    artist=rijks_artist(obj)
    year=rijks_year(obj)
    if not year or not scene_title(title):return None
    object_number=rijks_ident(obj)
    if not object_number:return None
    shown=obj.get("shows") or []
    if not shown:return None
    v=shown[0].get("id") or ""
    if not re.fullmatch(r"https://id.rijksmuseum.nl/\d+",v):return None
    visual=jget(v.replace("id.rijksmuseum.nl","data.rijksmuseum.nl")+"?_profile=la-framed")
    digital=(visual.get("digitally_shown_by") or [])
    if not digital:return None
    u=digital[0].get("id") or ""
    if not re.fullmatch(r"https://id.rijksmuseum.nl/\d+",u):return None
    record=jget(u.replace("id.rijksmuseum.nl","data.rijksmuseum.nl")+"?_profile=la-framed")
    urls=[str(x.get("id") or "") for x in record.get("access_point") or []]
    image=next((x for x in urls if re.fullmatch(
        r"https://iiif\.micr\.io/[A-Za-z0-9_-]{3,28}/full/max/0/default\.jpg",x)),None)
    if not image:return None
    base=image.split("/full/")[0]
    return {"source":"rijks","museum_native_id":object_number,
            "title":title,"artist":artist,"year":year,"museum":"Rijksmuseum, Amsterdam",
            "museum_url":f"https://www.rijksmuseum.nl/en/collection/{urllib.parse.quote(object_number)}",
            "record_api_url":raw,
            "remote_preview_url":base+"/full/280,/0/default.jpg",
            "remote_full_url":image,
            "rights_evidence_url":ART_URL_LICENSE["rijks"],
            "image_license_per_item":"UNVERIFIED__CHECK_PD_CC0_ON_OBJECT",
            "source_data_model":"Linked Art 2026 3-hop IIIF",
            "copyright_hold":"HOLD_PER_OBJECT_LICENSE_AND_COUNTRY"}

def search_rijks(q):
    from urllib.parse import urlencode
    param={"type":"painting","imageAvailable":"true"}
    if q in ("Monet","Toorop","Mondrian","Gestel","Jongkind","Sluijters"):
        param["creator"]=q
    else:param["title"]=q
    uri="https://data.rijksmuseum.nl/search/collection?"+urlencode(param)
    result=jget(uri)
    return [x.get("id") for x in result.get("orderedItems") or []
            if isinstance(x,dict) and x.get("id")],int((result.get("partOf") or {}).get("totalItems") or 0)

def run_rijks(shard,max_images):
    search_terms=RIJKS_QUERIES[shard]
    ids={};stats=Counter();failed=[]
    for term in search_terms:
        try:
            arr,total=search_rijks(term)
            stats["search_listed"]+=len(arr)
            stats["search_catalog_matches"]+=total
            for k in arr:
                if k:ids.setdefault(k,[]).append(term)
        except Exception as ex:failed.append({"query":term,"reason":str(ex)[:130]})
        time.sleep(.1)
    keys,names=main_keys()
    distinct=sorted(ids,key=lambda s:hashlib.sha256(s.encode()).hexdigest())
    selected=distinct[:max_images]
    result=[];holds=[];thumbs={}
    # Linked Art calls fan out to three downstream API requests per work.
    with ThreadPoolExecutor(max_workers=3) as exe:
        futures={exe.submit(rijks_object,item):item for item in selected}
        for fut in as_completed(futures):
            ident=futures[fut]
            try:
                rec=fut.result()
                if rec is None:stats["metadata_not_modern_scenic_or_image"]+=1;continue
                if ("rijks",rec["museum_native_id"]) in keys or (
                    cleaned(rec["title"]),cleaned(rec["artist"])) in names:
                    stats["duplicates_existing_artdrift"]+=1;continue
                try:c,sha,img=image_raster(rec["remote_preview_url"])
                except Exception as ex:
                    holds.append({"id":rec["museum_native_id"],"reason":"IMAGE_UNAVAILABLE_"+str(ex)[:130]});continue
                rec["image_sha256"]=sha;rec["color_metrics"]=c
                tier=color_tier(c)
                if tier.startswith("HOLD"):
                    holds.append({"id":rec["museum_native_id"],"reason":tier,"title":rec["title"],"metrics":c});continue
                rec["color_tier"]=tier
                rec["curatorial_status"]="HOLD_VISUAL_CHECK"
                rec["runtime_visible"]=False
                rec["commercially_approved"]=False
                result.append(rec);thumbs[rec["museum_native_id"]]=img
            except Exception as ex:
                holds.append({"id":ident.rsplit("/",1)[-1],
                              "reason":"API_"+str(ex)[:160]})
    stats["unique_source_identifiers"]=len(distinct)
    return result,holds,stats,thumbs,failed

def commons_search(term,limit=50):
    q=urllib.parse.urlencode({"action":"query","format":"json","formatversion":2,
        "generator":"search","gsrsearch":f'intitle:"Nationalmuseum" {term}',
        "gsrnamespace":6,"gsrlimit":limit,"prop":"imageinfo",
        "iiprop":"url|mime|extmetadata|sha1",
        "iiurlwidth":320,"iilimit":1})
    response=jget("https://commons.wikimedia.org/w/api.php?"+q)
    return (response.get("query") or {}).get("pages") or []

def common_license(data):
    valid,lic=licenses(data)
    return valid,lic

def sweden_object(page):
    title=str(page.get("title") or "")
    if "Nationalmuseum" not in title or not title.startswith("File:"):return None
    if not scene_title(title.split(" (",1)[0]):return None
    info=(page.get("imageinfo") or [{}])[0]
    if info.get("mime") not in ("image/tiff","image/jpeg","image/png","image/webp"):
        return None
    ext=info.get("extmetadata") or {}
    license_ok,lic=common_license(ext)
    if not license_ok:return None
    url=str(info.get("thumburl") or "")
    if not safe_thumb(url):return None
    title_value=title.removeprefix("File:").split(" (",1)[0]
    year=author_year_from_doc((ext.get("DateTimeOriginal") or {}).get("value"))
    if year is None:return None  # date must come from this artwork, not artist
    artist=strip_html((ext.get("Artist") or {}).get("value") or "")
    artist=re.sub(r"\s+"," ",artist).strip()[:110]
    if not artist or any(x in cleaned(artist) for x in ("unknown","anonymous")):
        return None
    return {"source":"nationalmuseum_se",
            "museum_native_id":str(page.get("pageid")),"title":title_value,
            "artist":artist,"year":year,
            "museum":"Nationalmuseum, Stockholm",
            "museum_url":"https://commons.wikimedia.org/w/index.php?curid="+str(page["pageid"]),
            "remote_preview_url":url,
            "remote_full_url":str(info.get("url") or ""),
            "rights_evidence_url":ART_URL_LICENSE["nationalmuseum_se"],
            "image_license_per_item":lic["license_name"],
            "rights_file_source":"Wikimedia Commons file PDM/CC0 in museum category/search",
            "source_file_sha1":info.get("sha1") or "",
            "copyright_hold":"HOLD_ARTIST_DEATH_TERRITORY_AND_CROSS_PROVIDER"}

def run_sweden(shard,max_images):
    terms=NAT_QUERIES[shard]
    stats=Counter();pages={};failed=[]
    for term in terms:
        try:
            results=commons_search(term)
            stats["search_listed"]+=len(results)
            for item in results:
                if isinstance(item.get("pageid"),int):pages[item["pageid"]]=item
        except Exception as ex:failed.append({"query":term,"reason":str(ex)[:160]})
        time.sleep(.15)
    ids,names=main_keys()
    old=ROOT/"research/mass_bright/20261126/commons_pd_bright_verified.json"
    prior=json.loads(old.read_text(encoding="utf-8"))
    prior_commons_ids={str(x["file_pageid"]) for x in prior["works"]}
    pool=list(pages.values())
    pool.sort(key=lambda p:hashlib.sha256(str(p["pageid"]).encode()).hexdigest())
    accepted=[];holds=[];thumbs={}
    for page in pool[:max_images]:
        rec=sweden_object(page)
        if rec is None:
            stats["metadata_or_license_not_eligible"]+=1;continue
        if rec["museum_native_id"] in prior_commons_ids:
            stats["prior_commons_duplicate"]+=1;continue
        if (cleaned(rec["title"]),cleaned(rec["artist"])) in names:
            stats["runtime_title_artist_duplicate"]+=1;continue
        try:c,sha,picture=image_raster(rec["remote_preview_url"])
        except Exception as ex:
            holds.append({"id":rec["museum_native_id"],"reason":"NO_IMAGE_"+str(ex)[:110]});continue
        if color_tier(c).startswith("HOLD"):
            holds.append({"id":rec["museum_native_id"],"reason":"DARK_OR_MUTED","metrics":c});continue
        rec.update(color_metrics=c,image_sha256=sha,color_tier=color_tier(c),
            curatorial_status="HOLD_FURTHER_VISUAL_QA",runtime_visible=False,
            commercially_approved=False)
        accepted.append(rec);thumbs[rec["museum_native_id"]]=picture
    stats["unique_institution_files_search"]=len(pages)
    return accepted,holds,stats,thumbs,failed

NS={"oai":"http://www.openarchives.org/OAI/2.0/",
    "lido":"http://www.lido-schema.org"}
def staedel_records():
    url="https://sammlung.staedelmuseum.de/api/oai?verb=ListRecords&metadataPrefix=lido"
    records=[]
    for page in range(2):
        raw=fetch(url,limit=2_800_000,timeout=30)
        root=ET.fromstring(raw)
        records.extend(root.findall(".//oai:record",NS))
        token=root.find(".//oai:resumptionToken",NS)
        if token is None or not token.text:break
        url=("https://sammlung.staedelmuseum.de/api/oai?"+
             urllib.parse.urlencode({"verb":"ListRecords","resumptionToken":token.text}))
        time.sleep(.2)
    return records

def staedel_parse(record):
    # LIDO metadata harvested under OAI official contract; CC0 metadata, CC BY-SA image.
    e=record.find(".//lido:lido",NS)
    if e is None:return None
    ident=e.find(".//lido:lidoRecID",NS)
    if ident is None or not (ident.text or "").strip():return None
    key=(ident.text or "").strip()
    tags=[x.text.strip() for x in e.findall(".//lido:titleSet/lido:appellationValue",NS)
          if x.text and x.text.strip()]
    title=next((x for x in tags if scene_title(x)),None)
    if not title:return None
    dates=[x.text or "" for x in e.findall(".//lido:earliestDate",NS)]
    yr=next((date_year(x) for x in dates if date_year(x)),None)
    if yr is None:return None
    actors=[x.text.strip() for x in e.findall(".//lido:displayActorInRole",NS)
            if x.text and x.text.strip()]
    artist=actors[0] if actors else ""
    links=[x.text.strip() for x in e.findall(".//lido:linkResource",NS)
           if x.text and x.text.strip()]
    image=next((x for x in links if allow(x)),None)
    if not image:return None
    return {"source":"staedel","museum_native_id":key,
            "title":title,"artist":artist,"year":yr,"museum":"Städel Museum, Frankfurt",
            "museum_url":"https://sammlung.staedelmuseum.de/en",
            "remote_preview_url":image,"remote_full_url":image,
            "image_license_per_item":"CC BY-SA 4.0",
            "rights_evidence_url":ART_URL_LICENSE["staedel"],
            "copyright_hold":"HOLD_CC_BY_SA_SHARE_ALIKE_IMPL_AND_CROSS_PROVIDER"}

def run_staedel(shard,max_images):
    stats=Counter();holds=[];accepted=[];thumbs={};failed=[]
    try:records=staedel_records()
    except Exception as ex:return [],[],stats,{},[{"reason":str(ex)[:150]}]
    stats["oai_records_read"]=len(records)
    recs=[staedel_parse(x) for x in records]
    recs=[x for x in recs if x]
    stats["modern_scenic_image_metadata"]=len(recs)
    keys,names=main_keys()
    for rec in recs[shard::3][:max_images]:
        if (cleaned(rec["title"]),cleaned(rec["artist"])) in names:
            stats["duplicate_main"]+=1;continue
        try:c,sha,img=image_raster(rec["remote_preview_url"])
        except Exception as ex:
            holds.append({"id":rec["museum_native_id"],"reason":"IMAGE_HOST_OR_FORMAT_HOLD_"+str(ex)[:140]});continue
        if color_tier(c).startswith("HOLD"):
            holds.append({"id":rec["museum_native_id"],"reason":"DARK_OR_MUTED","metrics":c});continue
        rec.update(color_metrics=c,image_sha256=sha,color_tier=color_tier(c),
                   curatorial_status="HOLD_FINAL_VISUAL_LICENSE_AND_CREDIT",
                   runtime_visible=False,commercially_approved=False)
        accepted.append(rec);thumbs[rec["museum_native_id"]]=img
    return accepted,holds,stats,thumbs,failed

def save(provider,shard,works,holds,stats,images,errors):
    uniq={w["museum_native_id"]:w for w in works}
    filtered=list(uniq.values())
    filtered.sort(key=lambda v:(v["color_metrics"]["dark_fraction"],v["title"].lower()))
    out=OUT/provider/f"batch_{shard:02d}"
    out.mkdir(parents=True,exist_ok=True)
    report={"schema_version":1,"as_of":"2026-11-26","provider":provider,
            "shard":shard,"excluded_museum_keys":["nga","met","cma","aic","smk"],
            "search_stats":dict(stats),"source_errors":errors[:12],
            "verified_images_bright":len(filtered),
            "holds":holds[:90],
            "title_author_and_image_license_gates":True,
            "pixel_thresholds":{"preferred_dark_max":.15,"conditional_dark_max":.20,
                                "conditional_min_saturation":.24,
                                "conditional_min_vivid":.30},
            "commercially_cleared":0,"runtime_imported":0,"works":filtered}
    (out/"review.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    if filtered:
        cols=5;W=190;H=181
        sheet=Image.new("RGB",(cols*W,((min(60,len(filtered))+cols-1)//cols)*H),"white")
        painter=ImageDraw.Draw(sheet)
        for i,w in enumerate(filtered[:60]):
            im=images.get(w["museum_native_id"])
            if im is None:continue
            x=i%cols*W;y=i//cols*H
            sheet.paste(im,(x+(W-im.width)//2,y+(136-im.height)//2))
            painter.text((x+2,y+140),w["title"][:25],fill="black")
            painter.text((x+2,y+157),w["source"]+" "+str(w["year"]),fill="black")
        sheet.save(out/"artworks_contact_sheet.jpg",quality=84,optimize=True)
    print(json.dumps({k:v for k,v in report.items() if k not in ("works","holds")},
                     sort_keys=True,ensure_ascii=False),flush=True)
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--provider",choices=["rijks","nationalmuseum_se","staedel"],required=True)
    p.add_argument("--shard",type=int,required=True)
    p.add_argument("--max-images",type=int,default=45)
    a=p.parse_args()
    if not 0<=a.shard<=2 or not 5<=a.max_images<=100:p.error("bounded")
    f={"rijks":run_rijks,"nationalmuseum_se":run_sweden,
       "staedel":run_staedel}[a.provider]
    works,holds,stats,images,errors=f(a.shard,a.max_images)
    save(a.provider,a.shard,works,holds,stats,images,errors)
if __name__=="__main__":main()
