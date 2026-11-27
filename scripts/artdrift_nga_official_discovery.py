#!/usr/bin/env python3
"""NGA Open Access seven-artists discovery from official SHA-pinned dataset.

This script distinguishes openaccess=1 on the image from the CC0 license on
museum *metadata*. All discovered works are research candidates, not approved
in the application, until exact image delivery and painting deduplication pass.
"""
from __future__ import annotations
import argparse,collections,csv,hashlib,json,re,unicodedata,urllib.parse
from pathlib import Path
ARTISTS={
 "claude monet":"Claude Monet",
 "alfred sisley":"Alfred Sisley",
 "gustave caillebotte":"Gustave Caillebotte",
 "otto modersohn":"Otto Modersohn",
 "harald sohlberg":"Harald Sohlberg",
 "serhii vasylkivskyi":"Serhii Vasylkivskyi",
 "ludvig karsten":"Ludvig Karsten",
}
PIN="3a187753c941dd153c2632cffc15d802f171e012"
CATALOGS=("assets/gallery/catalog.json","assets/museums/catalog.json",
 "assets/museums/catalog_global.json","assets/museums/catalog_modern_1950.json",
 "assets/museums/catalog_new_museums.json","assets/museums/catalog_curated_commons.json")
def norm(s):
 t=unicodedata.normalize("NFKD",str(s or "").casefold())
 return " ".join(re.sub(r"[^\w]+"," ","".join(x for x in t if not unicodedata.combining(x))).split())
def as_rows(p):
 with Path(p).open(encoding="utf-8-sig",newline="") as f:
  rd=csv.DictReader(f,restval="")
  if not rd.fieldnames:raise ValueError("Missing official CSV header: "+str(p))
  for r in rd:
   if None in r:raise ValueError("Malformed NGA CSV record in "+str(p))
   yield {str(k).strip().lower():str(v or "").strip() for k,v in r.items()}
def intval(x):
 try:return int(x)
 except(ValueError,TypeError):return None
def issue_code(url):
 uri=urllib.parse.urlparse(url or "")
 if uri.scheme!="https" or uri.username or uri.password or (uri.port and uri.port!=443):
  return "BAD_IIIF_HTTPS_URL"
 if uri.hostname not in ("api.nga.gov","media.nga.gov"):
  return "UNSUPPORTED_IIIF_HOST"
 return None
def build(nga,art,out):
 nga=Path(nga);art=Path(art)
 sources=["constituents.csv","objects_constituents.csv","objects.csv","published_images.csv"]
 for s in sources:
  if not (nga/s).is_file() or (nga/s).stat().st_size<2000:
   raise ValueError("Official NGA data missing/truncated: "+s)
 hashes={s:hashlib.sha256((nga/s).read_bytes()).hexdigest() for s in sources}
 artists={}
 for r in as_rows(nga/"constituents.csv"):
  artist=norm(r.get("forwarddisplayname") or r.get("preferreddisplayname"))
  if artist not in ARTISTS:continue
  cid=intval(r.get("constituentid"))
  if cid is None:continue
  artists[cid]=ARTISTS[artist]
 if "Claude Monet" not in set(artists.values()):raise ValueError("Artist lookup broken")
 object_artist=collections.defaultdict(set)
 for r in as_rows(nga/"objects_constituents.csv"):
  cid=intval(r.get("constituentid"));oid=intval(r.get("objectid"))
  if cid is None or oid is None or cid not in artists:continue
  if norm(r.get("roletype")) not in ("artist",) and norm(r.get("role")) not in ("artist","painter"):
   continue
  object_artist[oid].add(artists[cid])
 objects={}
 for r in as_rows(nga/"objects.csv"):
  oid=intval(r.get("objectid"))
  if oid not in object_artist:continue
  category=norm(r.get("visualbrowserclassification") or r.get("classification"))
  if not (category=="painting" or category=="paintings"):
   continue
  if norm(r.get("isvirtual")) not in ("0","false",""):
   continue
  objects[oid]=r
 existing=[]
 for p in CATALOGS:
  filepath=art/p
  if not filepath.exists():raise ValueError("Missing existing Art Drift catalog "+p)
  x=json.loads(filepath.read_text(encoding="utf-8"))
  if not isinstance(x,list):raise ValueError("Invalid catalog "+p)
  existing.extend(x)
 same_nga_ids=set()
 other_titles=collections.defaultdict(set)
 for r in existing:
  provider=norm(r.get("museum_source"))
  ident=str(r.get("museum_native_id") or "")
  if provider=="nga":
   if ident.isdigit():same_nga_ids.add(int(ident))
   srcid=intval(r.get("id"))
   if srcid is not None and 4000000000<=srcid<4001000000:
    same_nga_ids.add(srcid-4000000000)
  key=(norm(r.get("artist_title") or r.get("artist_display") or r.get("artist")),
       norm(r.get("title")))
  if all(key):other_titles[key].add(str(r.get("id")))
 images={}
 image_counts=collections.Counter()
 for img in as_rows(nga/"published_images.csv"):
  oid=intval(img.get("depictstmsobjectid"))
  if oid not in objects:continue
  image_counts["artist_painting_images"]+=1
  if img.get("openaccess")!="1":
   image_counts["not_openaccess"]+=1;continue
  image_counts["openaccess"]+=1
  if norm(img.get("viewtype")) not in ("primary",""):
   image_counts["alternate_views"]+=1;continue
  if issue_code(img.get("iiifurl")):
   image_counts["untrusted_host"]+=1;continue
  uuid=img.get("uuid") or ""
  if not re.fullmatch(r"[a-zA-Z0-9-]{25,64}",uuid):continue
  item={
   "object_id":oid,"image_uuid":uuid,"iiif_url":img.get("iiifurl"),
   "thumbnail":img.get("iiifthumburl"),
   "openaccess":True,"viewtype":img.get("viewtype"),
   "width":intval(img.get("width")),"height":intval(img.get("height")),
   "maxpixels":intval(img.get("maxpixels")),
  }
  images.setdefault(oid,[]).append(item)
 outrows=[]
 for oid,obj in sorted(objects.items()):
  authors=sorted(object_artist[oid]);title=obj.get("title") or ""
  media=images.get(oid,[])
  if oid in same_nga_ids:stage="EXISTING_NGA_OBJECT"
  elif any((norm(author),norm(title)) in other_titles for author in authors):
   stage="POSSIBLE_EXISTING_TITLE"
  elif not media:stage="NO_OPEN_ACCESS_PRIMARY_IMAGE"
  elif len(authors)!=1:stage="AUTHOR_ATTRIBUTION_REVIEW"
  elif len(media)!=1:stage="MULTIPLE_PRIMARY_IMAGES_REVIEW"
  elif not media[0]["width"] or not media[0]["height"] or min(media[0]["width"],media[0]["height"])<300:
   stage="LOW_RESOLUTION_OR_DIMENSION_MISSING"
  else:stage="ELIGIBLE_INSTITUTIONAL_IMAGE_REVIEW"
  outrows.append({
   "nga_objectid":oid,"source_identity":"nga:"+str(oid),"title":title,
   "artist":authors,"artwork_type":"painting",
   "date":obj.get("displaydate"),"accession":obj.get("accessionnum"),
   "medium":obj.get("medium"),"creditline":obj.get("creditline"),
   "institution_object_url":"https://www.nga.gov/artworks/"+str(oid),
   "image_policy":"https://www.nga.gov/artworks/free-images-and-open-access",
   "openaccess_primary_image_count":len(media),
   "images":media[:6],"status":stage,
   "rights_metadata_source":"published_images.csv openaccess=1",
   "commercially_approved":False,"runtime_visible":False,
  })
 counts=collections.Counter(x["status"] for x in outrows)
 if not outrows or any(x["commercially_approved"] or x["runtime_visible"] for x in outrows):
  raise ValueError("Image review fail closed")
 out=Path(out);out.mkdir(parents=True,exist_ok=True)
 def dump(path,obj):
  p=out/path;p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 dump("nga_7artists_all.json",outrows)
 eligible=[r for r in outrows if r["status"]=="ELIGIBLE_INSTITUTIONAL_IMAGE_REVIEW"]
 dump("nga_7artists_new_openaccess_candidates.json",eligible)
 summary={
 "official_repository":"NationalGalleryOfArt/opendata","official_source_pin":PIN,
 "official_source_sha256":hashes,"artists_found":sorted(set(artists.values())),
 "artist_paintings_in_official_data":len(outrows),"status_counts":dict(counts),
 "eligible_new_primary_image_review":len(eligible),
 "images_eligible_for_immediate_commercial_merge":0,
 "published_images_reject_counts":dict(image_counts),
 "source_catalog_items_checked":len(existing),
 "notes":"Only openaccess=1 image-level rights, not blanket CC0 metadata. Candidate imaging URLs require live response and dedup verification before export."
 }
 dump("nga_7artists_summary.json",summary)
 with (out/"nga_7artists_candidates.csv").open("w",encoding="utf-8",newline="") as f:
  w=csv.writer(f);w.writerow(["nga_id","artist","title","status","date","accession","openaccess_images","institutional_url"])
  for r in outrows:w.writerow([r["nga_objectid"],";".join(r["artist"]),r["title"],r["status"],r["date"],r["accession"],r["openaccess_primary_image_count"],r["institution_object_url"]])
 print(json.dumps(summary,ensure_ascii=False),flush=True)

if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--nga",type=Path,required=True)
 p.add_argument("--art",type=Path,default=Path("."))
 p.add_argument("--out",type=Path,default=Path("nga-official-discovery"))
 a=p.parse_args()
 build(a.nga,a.art,a.out)
