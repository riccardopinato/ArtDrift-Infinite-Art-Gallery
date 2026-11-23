#!/usr/bin/env python3
"""Recover exactly ONE named NPG public-domain item when the official IDS URL is 404.

No generic Wikimedia/aggregator import: only the Smithsonian CC0 accession
NPG.2007.11 and an explicitly identified Commons file are permitted. Verify
the per-file license and exact museum accession BEFORE downloading bytes.
"""
import hashlib
import io
import json
import os
from pathlib import Path
from urllib.parse import urlparse

import requests
from PIL import Image, ImageOps, UnidentifiedImageError

CATALOG=Path("assets/museums/catalog_global.json")
OUTPUT=Path("web/museum_thumbs/smithsonian_6452594389.webp")
REPORT=Path("docs/generated/NPG_2007_11_COMMONS_EXCEPTION_EVIDENCE.json")
FILENAME="Archibald Robertson - William Linn - NPG.2007.11 - National Portrait Gallery.jpg"
WIKI_TITLE="File:"+FILENAME
OFFICIAL_OBJECT="https://npg.si.edu/object/npg_NPG.2007.11"
COMMONS_PAGE="https://commons.wikimedia.org/wiki/File:Archibald_Robertson_-_William_Linn_-_NPG.2007.11_-_National_Portrait_Gallery.jpg"
API="https://commons.wikimedia.org/w/api.php"
HEADERS={"User-Agent":"ArtDrift/0.3 research rights-verified NPG one-image fallback (no batch commons import)","Accept":"application/json,image/jpeg"}
Image.MAX_IMAGE_PIXELS=24_000_000

def stop(reason,details=None):
 print("NPG_SINGLE_IMAGE_HOLD:",reason,flush=True)
 REPORT.parent.mkdir(parents=True,exist_ok=True)
 REPORT.write_text(json.dumps({
  "schema_version":1,"status":"HOLD","reason":reason,"details":details,
  "museum_native_id":"npg:npg_NPG.2007.11","official_object_url":OFFICIAL_OBJECT,
  "commons_file_page":COMMONS_PAGE,"commercial_release_cleared":False
 },indent=2,sort_keys=True)+"\n",encoding="utf-8")

def run():
 catalog=json.loads(CATALOG.read_text(encoding="utf-8"))
 rows=[row for row in catalog if row.get("museum_source")=="smithsonian"
       and row.get("id")==6452594389]
 if len(rows)!=1:raise SystemExit("NPG_ONE_ITEM_IDENTITY_MISMATCH")
 row=rows[0]
 if not (row.get("museum_native_id")=="npg:npg_NPG.2007.11" and
         row.get("title")=="William Linn" and
         "Archibald Robertson" in str(row.get("artist_title")) and
         row.get("is_public_domain") is True and
         row.get("rights_license")=="CC0" and
         row.get("rights_evidence_url")=="https://www.si.edu/openaccess" and
         row.get("remote_museum_url")==OFFICIAL_OBJECT):
  raise SystemExit("NPG_SOURCE_RIGHTS_IDENTITY_NOT_PROVEN")
 if OUTPUT.is_file() and 250<=OUTPUT.stat().st_size<=24000:
  print("NPG_EXACT_SOURCE_PRESENT",flush=True)
  return
 try:
  params={"action":"query","format":"json","prop":"imageinfo",
          "iiprop":"url|size|mime|extmetadata",
          "titles":WIKI_TITLE}
  with requests.get(API,params=params,headers=HEADERS,stream=True,
                    timeout=(6,12),allow_redirects=False) as response:
   if response.status_code!=200 or not response.headers.get("Content-Type","").lower().startswith("application/json"):
    stop("COMMONS_API_UNAVAILABLE",response.status_code);return
   raw=response.raw.read(500_001,decode_content=True)
  if len(raw)>500_000:
   stop("COMMONS_METADATA_TOO_LARGE");return
  pages=json.loads(raw)["query"]["pages"]
  matches=[p for p in pages.values() if p.get("title")==WIKI_TITLE]
  if len(matches)!=1 or len(matches[0].get("imageinfo",[]))!=1:
   stop("COMMONS_EXACT_FILE_IDENTITY_MISSING");return
  meta=matches[0]["imageinfo"][0]
  ext=meta.get("extmetadata") or {}
  def field(name):
   return str((ext.get(name) or {}).get("value","")).strip().lower()
  license_name=field("LicenseShortName")
  license_raw=field("License")
  copyrighted=field("Copyrighted")
  if not ("public domain" in license_name or "cc0" in license_name or
          "pd-art" in license_raw):
   stop("COMMONS_INDIVIDUAL_LICENSE_NOT_PUBLIC_DOMAIN",license_name);return
  if copyrighted not in ("false","0"):
   stop("COMMONS_COPYRIGHT_STATUS_NOT_UNRESTRICTED",copyrighted);return
  if meta.get("mime")!="image/jpeg" or int(meta.get("width",0))<200 or int(meta.get("height",0))<200 or int(meta.get("size",0))>2_000_000:
   stop("COMMONS_OBJECT_NOT_SUITABLE_THUMBNAIL");return
  url=meta.get("url","")
  uri=urlparse(url)
  if not (uri.scheme=="https" and uri.hostname=="upload.wikimedia.org" and
          uri.username is None and uri.password is None and uri.port in (None,443)):
   stop("COMMONS_MEDIA_HOST_NOT_APPROVED");return
  with requests.get(url,headers=HEADERS,stream=True,timeout=(6,12),
                    allow_redirects=False) as response:
   if response.status_code!=200 or not response.headers.get("Content-Type","").lower().startswith("image/"):
    stop("COMMONS_MEDIA_HTTP_ERROR",response.status_code);return
   fragments=[];n=0
   for block in response.iter_content(chunk_size=32768):
    n+=len(block)
    if n>2_000_000:
     stop("COMMONS_MEDIA_TOO_LARGE");return
    fragments.append(block)
  original=b"".join(fragments)
  with Image.open(io.BytesIO(original)) as image:
   if image.format!="JPEG" or getattr(image,"is_animated",False) or min(image.size)<200:
    stop("COMMONS_MEDIA_NOT_VALID_JPEG");return
   image=ImageOps.exif_transpose(image).convert("RGB")
   image.thumbnail((256,256),Image.Resampling.LANCZOS)
   encoded=b""
   for quality in (60,48,36):
    b=io.BytesIO()
    image.save(b,format="WEBP",quality=quality,method=4)
    if 250<=len(b.getvalue())<=24000:
     encoded=b.getvalue();break
   if not encoded:
    stop("COMMONS_WEBP_COMPRESSION_FAILED");return
  OUTPUT.parent.mkdir(parents=True,exist_ok=True)
  tmp=OUTPUT.with_suffix(".webp.tmp")
  tmp.write_bytes(encoded)
  os.replace(tmp,OUTPUT)
  report={
   "schema_version":1,"status":"SINGLE_OBJECT_IMAGE_DOWNLOADED",
   "source":"Wikimedia Commons, exact photographed NPG accession",
   "museum_native_id":"npg:npg_NPG.2007.11","official_object_url":OFFICIAL_OBJECT,
   "museum_rights":"CC0","museum_rights_url":"https://www.si.edu/openaccess",
   "commons_file_page":COMMONS_PAGE,"commons_file_title":WIKI_TITLE,
   "commons_license_short_name":license_name,
   "commons_license_raw":license_raw,
   "commons_copyrighted":copyrighted,
   "media_url":url,
   "original_media_sha256":hashlib.sha256(original).hexdigest(),
   "webp_sha256":hashlib.sha256(encoded).hexdigest(),
   "webp_size":len(encoded),
   "commercial_release_cleared":False,
   "caveat":"Individual museum CC0 and Commons per-file metadata are screening evidence, not independent jurisdictional legal clearance",
  }
  REPORT.parent.mkdir(parents=True,exist_ok=True)
  REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
  print("NPG_SINGLE_OBJECT_IMAGE_VERIFIED",report["webp_sha256"],flush=True)
 except (requests.RequestException,OSError,ValueError,KeyError,TypeError,UnidentifiedImageError) as exc:
  stop("COMMONS_VERIFICATION_OR_TRANSFER_FAILED",type(exc).__name__)

if __name__=="__main__":
 run()
