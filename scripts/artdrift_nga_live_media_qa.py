#!/usr/bin/env python3
"""Verify live NGA IIIF image delivery for 29 source-pinned OA candidates.

This is not a copyright approval; openaccess=1 was checked separately in the
signed-off official NGA dataset. Network failures remain HOLD.
"""
from __future__ import annotations
import argparse,collections,io,json,time,urllib.error,urllib.parse,urllib.request
from pathlib import Path
from PIL import Image,UnidentifiedImageError

SOURCE_SHA="3a187753c941dd153c2632cffc15d802f171e012"
N=29
SHARDS=4
ALLOWED_HOSTS={"api.nga.gov","media.nga.gov"}
def read(p):return json.loads(Path(p).read_text(encoding="utf-8"))
def write(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def probe(item):
 oo=item["nga_objectid"]
 imgs=item["images"]
 if len(imgs)!=1 or not imgs[0]["openaccess"]:
  raise ValueError("Missing authenticated single Open Access image for "+str(oo))
 image=imgs[0]
 base=image["iiif_url"].rstrip("/")
 parsed=urllib.parse.urlparse(base)
 if parsed.scheme!="https" or parsed.hostname not in ALLOWED_HOSTS or parsed.username or parsed.password:
  raise ValueError("Unsafe NGA IIIF source")
 target=base+"/full/!600,600/0/default.jpg"
 result={
  "objectid":oo,"image_uuid":image["image_uuid"],"artist":item["artist"],
  "title":item["title"],"rights_evidence":"OFFICIAL_PUBLISHED_IMAGES_OPENACCESS_1",
  "source_url":base,"preview_url":target,
  "original_width":image["width"],"original_height":image["height"],
  "live_pixel_checked":False,"publication_approved":False,"status":"HOLD_NETWORK",
 }
 for attempt in range(3):
  try:
   req=urllib.request.Request(target,headers={
    "User-Agent":"ArtDriftOfficialSourceQA/1.0 (github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery)",
    "Accept":"image/jpeg","Cache-Control":"no-cache"})
   with urllib.request.urlopen(req,timeout=22) as response:
    end=urllib.parse.urlparse(response.geturl())
    if end.hostname not in ALLOWED_HOSTS or end.scheme!="https":
     result["status"]="HOLD_CDN_REDIRECT";return result
    raw=response.read(5_000_000)
    if not raw.startswith(b"\xff\xd8"):
     result["status"]="HOLD_NOT_JPEG";return result
    with Image.open(io.BytesIO(raw)) as im:
     im.load()
     width,height=im.size
     if im.format!="JPEG" or min(width,height)<200:
      result["status"]="HOLD_PIXEL_QUALITY";return result
     result.update({"live_pixel_checked":True,"status":"LIVE_JPEG_VERIFIED",
      "image_width":width,"image_height":height,"image_format":im.format,
      "resolved_host":end.hostname,"jpeg_size":len(raw)})
    return result
  except urllib.error.HTTPError as ex:
   result["status"]="HOLD_HTTP_"+str(ex.code)
   if ex.code not in (429,500,502,503,504):break
  except (urllib.error.URLError,TimeoutError,OSError,UnidentifiedImageError) as ex:
   result["status"]="HOLD_NETWORK_"+type(ex).__name__
  if attempt<2:time.sleep(3+attempt*7)
 return result
def shard(source,out,index):
 arr=read(source)
 if len(arr)!=N or len({x["nga_objectid"] for x in arr})!=N:
  raise ValueError("Unexpected candidate count")
 selected=arr[index::SHARDS]
 rows=[]
 for item in selected:
  rows.append(probe(item))
  print(item["nga_objectid"],rows[-1]["status"],flush=True)
  time.sleep(1.0)
 write(Path(out)/f"nga_shard_{index:02d}.json",{
  "shard":index,"shards":SHARDS,"source_sha":SOURCE_SHA,
  "records":rows,"processed":len(rows),
  "commercially_approved_count":0,
 })
def aggregate(folder,out):
 rows=[]
 for n in range(SHARDS):
  x=read(Path(folder)/f"nga_shard_{n:02d}.json")
  if x["shard"]!=n or x["shards"]!=SHARDS or x["source_sha"]!=SOURCE_SHA or \
       x["processed"]!=len(x["records"]) or x["commercially_approved_count"]!=0:
   raise ValueError("Untrusted shard results")
  rows.extend(x["records"])
 if len(rows)!=N or len({x["objectid"] for x in rows})!=N:
  raise ValueError("Duplicate or missing candidate in aggregated validation")
 rows.sort(key=lambda x:x["objectid"])
 summary={"official_pin":SOURCE_SHA,"expected_candidates":N,
   "technical_delivery_pass":sum(x["live_pixel_checked"] for x in rows),
   "technical_hold":sum(not x["live_pixel_checked"] for x in rows),
   "status":dict(collections.Counter(x["status"] for x in rows)),
   "commercially_approved":0,
   "note":"No automatic rights release. Author and official OpenAccess image claim separately sourced."}
 write(Path(out)/"nga_29_live_media_review.json",rows)
 write(Path(out)/"nga_29_live_media_summary.json",summary)
 print(json.dumps(summary,ensure_ascii=False),flush=True)
if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--source",type=Path)
 p.add_argument("--out",type=Path,required=True)
 p.add_argument("--shard",type=int)
 p.add_argument("--aggregate",action="store_true")
 p.add_argument("--shard-dir",type=Path)
 a=p.parse_args()
 if a.aggregate:aggregate(a.shard_dir,a.out)
 else:
  if a.shard is None or not 0<=a.shard<SHARDS or not a.source:
   p.error("--source and --shard [0,3] required")
  shard(a.source,a.out,a.shard)
