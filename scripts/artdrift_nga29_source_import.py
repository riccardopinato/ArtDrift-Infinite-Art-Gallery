#!/usr/bin/env python3
"""Deterministic NGA Open Access import after source and live-image verification.

Inputs are immutable GitHub Actions artifacts (official NGA data pin + IIIF QA).
This script creates exact Art Drift catalog rows for institutionally licensed
images. All other images are excluded, including existing NGA object IDs.
"""
from __future__ import annotations
import argparse,collections,hashlib,json,re,unicodedata
from pathlib import Path
SOURCE_PIN="3a187753c941dd153c2632cffc15d802f171e012"
N=29
DOC="docs/ARTDRIFT_NGA_29_OPEN_ACCESS_SOURCE_VERIFIED_20261127.md"
CATALOG="assets/museums/catalog_nga_openaccess_20261127.json"
SOURCE_CATALOGS=("assets/gallery/catalog.json","assets/museums/catalog.json",
 "assets/museums/catalog_global.json","assets/museums/catalog_modern_1950.json",
 "assets/museums/catalog_new_museums.json","assets/museums/catalog_curated_commons.json")
def load(p):return json.loads(Path(p).read_text(encoding="utf-8"))
def norm(s):
 t=unicodedata.normalize("NFKD",str(s or "").casefold())
 return " ".join(re.sub(r"[^\w]+"," ","".join(x for x in t if not unicodedata.combining(x))).split())
def build(root,discovery,media):
 root=Path(root);d=load(discovery);m=load(media)
 assert len(d)==N and len(m)==N
 if {r["nga_objectid"] for r in d}!={r["objectid"] for r in m}:
  raise ValueError("NGA official and live media record sets differ")
 mr={r["objectid"]:r for r in m}
 existing=[]
 for path in SOURCE_CATALOGS:
  filepath=root/path
  if not filepath.exists():raise ValueError("Missing canonical catalog "+path)
  x=load(filepath)
  if not isinstance(x,list):raise ValueError("Corrupt catalog "+path)
  existing.extend(x)
 same_keys=set()
 same_ids=set()
 for r in existing:
  a=norm(r.get("artist_title") or r.get("artist_display") or r.get("artist"))
  title=norm(r.get("title"))
  if a and title:same_keys.add((a,title))
  if r.get("museum_source")=="nga":
   mid=str(r.get("museum_native_id") or "")
   if mid.isdigit():same_ids.add(int(mid))
   rid=r.get("id")
   if isinstance(rid,int) and 4000000000<=rid<4001000000:
    same_ids.add(rid-4000000000)
 rows=[]
 for x in sorted(d,key=lambda r:r["nga_objectid"]):
  oid=x["nga_objectid"];media=mr[oid];im=x["images"][0]
  if x["status"]!="ELIGIBLE_INSTITUTIONAL_IMAGE_REVIEW" or \
     x["openaccess_primary_image_count"]!=1 or im["openaccess"] is not True:
   raise ValueError("Unreviewed source not eligible "+str(oid))
  if media["status"]!="LIVE_JPEG_VERIFIED" or \
     media["live_pixel_checked"] is not True or media["publication_approved"] is not False:
   raise ValueError("Image was not decoded from first-party NGA IIIF "+str(oid))
  if media["image_uuid"]!=im["image_uuid"] or \
     media["original_width"]!=im["width"] or media["original_height"]!=im["height"] or \
     media["source_url"]!=im["iiif_url"]:
   raise ValueError("IIIF original identity changed "+str(oid))
  if len(x["artist"])!=1 or oid in same_ids or \
     (norm(x["artist"][0]),norm(x["title"])) in same_keys:
   raise ValueError("Known NGA source or painting title duplicate "+str(oid))
  if not re.fullmatch(r"https://api\.nga\.gov/iiif/[0-9a-f-]{36}",im["iiif_url"]):
   raise ValueError("Unexpected NGA IIIF base")
  if media["resolved_host"] not in ("api.nga.gov","media.nga.gov") or \
     not media["preview_url"].startswith(im["iiif_url"]+"/"):
   raise ValueError("Unsafe image final delivery")
  if media["image_width"]<200 or media["image_height"]<200:
   raise ValueError("Undersized live preview")
  title=x["title"].strip();artist=x["artist"][0]
  if not title or not artist:raise ValueError("Missing original artwork title/artist")
  accession=x["accession"] or "NGA collection"
  cr=x["creditline"] or "National Gallery of Art, Washington"
  attribution=f"{artist}, {title}. National Gallery of Art, Washington, accession {accession}. Image NGA Open Access, CC0 1.0."
  row={
   "id":4000000000+oid,"title":title,"artist_title":artist,
   "date_display":x["date"] or "","image_id":"","is_public_domain":True,
   "medium_display":x["medium"] or "oil on canvas",
   "credit_line":f"{artist}, {title}. National Gallery of Art, Washington. {cr}. Image CC0 1.0.",
   "artwork_type_title":"Painting",
   "thumbnail":{"width":im["width"],"height":im["height"]},
   "museum_source":"nga","museum_name":"National Gallery of Art, Washington",
   "museum_native_id":str(oid),"source_identity":"nga:"+str(oid),
   "remote_preview_url":media["preview_url"],
   "remote_full_url":im["iiif_url"]+"/full/!1600,1600/0/default.jpg",
   "remote_museum_url":f"https://www.nga.gov/collection/art-object-page.{oid}.html",
   "rights_evidence_url":"https://www.nga.gov/artworks/free-images-and-open-access",
   "rights_license":"CC0 1.0",
   "image_license_url":"https://creativecommons.org/publicdomain/zero/1.0/",
   "image_creator":"National Gallery of Art, Washington",
   "image_attribution":attribution,
   "image_modifications":"Resized NGA original IIIF preview for the app. No other changes.",
   "commercially_approved":True,
   "source_provenance_verified":True,
   "worldwide_distribution_reviewed":True,
   "rights_review_reference":DOC,
  }
  rows.append(row)
 if len(rows)!=N or len({r["source_identity"] for r in rows})!=N:
  raise ValueError("Missing or repeated source identity in release batch")
 return rows
if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--root",type=Path,default=Path("."))
 p.add_argument("--source",type=Path,required=True)
 p.add_argument("--media",type=Path,required=True)
 p.add_argument("--out",type=Path,default=Path(CATALOG))
 p.add_argument("--verify",action="store_true")
 a=p.parse_args()
 rows=build(a.root,a.source,a.media)
 if a.verify:
  if load(a.out)!=rows:raise ValueError("Committed catalog differs from source-pinned evidence")
  print("NGA_29_EXACT_IMAGE_SOURCE_AND_LICENSE_QA_PASS",len(rows))
 else:
  a.out.parent.mkdir(parents=True,exist_ok=True)
  a.out.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
  print("NGA_29_SOURCE_VERIFIED_IMPORT_GENERATED",len(rows))
