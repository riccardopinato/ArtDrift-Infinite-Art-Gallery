#!/usr/bin/env python3
"""Materialize 283 unapproved Commons cards for an INTERNAL research APK only."""
import argparse,json,re
from pathlib import Path
BAD={"commons:6404635","commons:127400389","commons:57670806","commons:57670842"}
def convert(input_path,output_path):
 data=json.loads(Path(input_path).read_text(encoding="utf-8"))
 if not isinstance(data,list) or len(data)!=283:
  raise ValueError("Exactly 283 Fast Track entries required")
 entries=[];seen=set()
 for x in data:
  identity=x["source_identity"]
  if identity in seen or identity in BAD or identity=="commons:57672559":
   raise ValueError("Duplicate or excluded identity")
  if x.get("lane") not in ("A_FAST_TRACK_LUMINOUS","B_FAST_TRACK_OTHER"):
   raise ValueError("Exception source cannot enter review canvas")
  if x.get("license_class") not in ("PUBLIC_DOMAIN","CC0") or \
      x.get("commercially_approved") is not False or \
      x.get("source_metadata_checked") is not True:
   raise ValueError("Source license or rights gate failed")
  m=re.fullmatch(r"commons:([0-9]+)",identity)
  if not m:raise ValueError("Unrecognized Commons ID")
  n=int(m.group(1))
  page=x["source_page"];preview=x["preview_url"]
  if not page.startswith("https://commons.wikimedia.org/") or \
     not (preview.startswith("https://thumb.wikimedia.org/wikipedia/commons/") or
          preview.startswith("https://upload.wikimedia.org/wikipedia/commons/")):
   raise ValueError("Untrusted image URI")
  lic="CC0 1.0" if x["license_class"]=="CC0" else "Public Domain"
  photographer=(x.get("photo_credit") or "")[:250]
  painter=x["artist"]
  title=re.sub(r"\.(?:jpg|jpeg|png|tiff|webp)$","",x["title"],flags=re.I)
  title=title[:190].strip() or "Senza titolo"
  attr=("Opera: "+painter+". Riproduzione: "+
        (photographer or "vedi crediti originali su Wikimedia Commons")+
        ". Dichiarazione file: "+lic+".")
  row={
   "id":n,"title":title,"artist_title":painter,
   "date_display":"","image_id":"","is_public_domain":True,
   "artwork_type_title":"Painting",
   "museum_source":"commons","museum_name":"Wikimedia Commons (revisione)",
   "museum_native_id":str(n),"source_identity":identity,
   "remote_preview_url":preview,"remote_museum_url":page,
   "rights_evidence_url":page,"rights_license":lic,
   "image_license_url":"https://creativecommons.org/publicdomain/zero/1.0/" if lic=="CC0 1.0" else "",
   "image_creator":photographer,
   "image_attribution":attr,"credit_line":attr,
   "artdrift_research_only":True,
   "commercially_approved":False,
   "source_provenance_verified":False,
   "worldwide_distribution_reviewed":False,
   "artdrift_qa_wave":x.get("wave"),
  }
  seen.add(identity);entries.append(row)
 if len(entries)!=283 or len(seen)!=283:raise ValueError("Missing or repeated records")
 dest=Path(output_path);dest.parent.mkdir(parents=True,exist_ok=True)
 dest.write_text(json.dumps(entries,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print("INTERNAL_CANDIDATES_STAGED",len(entries))
def verify(output_path):
 rows=json.loads(Path(output_path).read_text(encoding="utf-8"))
 if len(rows)!=283 or len({x["source_identity"] for x in rows})!=283:
  raise ValueError("Broken research set")
 for x in rows:
  if x.get("commercially_approved") is not False or x.get("artdrift_research_only") is not True:
   raise ValueError("Publication gate breached")
 print("283_RESEARCH_ONLY_PUBLICATION_GUARD_PASS")
if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--source",type=Path)
 p.add_argument("--out",type=Path,required=True)
 p.add_argument("--verify",action="store_true")
 a=p.parse_args()
 if a.verify:verify(a.out)
 else:
  if a.source is None:p.error("--source is required")
  convert(a.source,a.out)
