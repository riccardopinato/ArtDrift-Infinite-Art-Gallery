#!/usr/bin/env python3
"""Mass-rights dossier, 100+100+83 parallel, explicit institutional review only.

The 283 historical Commons metadata records do NOT self-authorize commercial
publication. Three decisions below are source-specific documentary sign-offs.
All other 280 files keep a rights/provenance HOLD.
"""
from __future__ import annotations
import argparse,collections,csv,json,re,unicodedata
from pathlib import Path
SOURCE_SHA="b82a4574db3d504141b6d2e95e403aa743c771e3"
APPROVED={
 "commons:52129968":{
  "sha1":"38fb99a2c7afd5a6706d2a86d132793a2c0c9e76",
  "artist":"Claude Monet","museum":"Nationalmuseum",
  "policy":"https://www.nationalmuseum.se/en/explore-art-and-design/images/rights-and-reproductions",
  "object":"https://collection.nationalmuseum.se/en/collection/item/19182/"},
 "commons:52132342":{
  "sha1":"2cd1f172b5080d6fcca4a59ffb7f87eb656f9f24",
  "artist":"Harald Sohlberg","museum":"Nationalmuseum",
  "policy":"https://www.nationalmuseum.se/en/explore-art-and-design/images/rights-and-reproductions",
  "object":"https://collection.nationalmuseum.se/en/collection/item/25961/"},
 "commons:80548151":{
  "sha1":"8beb36d01da8505d20cd6bdb3afbb428001219bd",
  "artist":"Claude Monet","museum":"Yale University Art Gallery",
  "policy":"https://guides.library.yale.edu/openaccess",
  "object":"https://artgallery.yale.edu/collections/objects/25976"}
}
HOLD_MET="commons:2294013"
SECONDARY=re.compile(
 r"sotheby|christie|lempertz|dorotheum|ketterer|auction|auktion|auktionshaus|"
 r"liveauction|artnet|artsy|mutualart|bonhams|van.ham|hampel|e-bay|instagram|"
 r"facebook|pinterest|wikiart|alfredsisley[.]org|absolute|galerie|gallery|"
 r"flickr|flicker|york|yorck|repro|book",re.I)
MUSEUM=re.compile(
 r"museum|mus[eé]|nationalmuseum|yale|metmuseum|nga[.]gov|collection|harvard|"
 r"artizon|fng[.]fi|polamuseum|kunsten[.]dk|navigart|marmottan|smithsonian|openaccess",
 re.I)
UPLOADER=re.compile(r"own\W|own work|uploader|user:",re.I)
EXPECTED={
 "CERTIFIED_INSTITUTIONAL_PD_FILE":3,
 "HOLD_SECONDARY_OR_COMMERCIAL_SOURCE":188,
 "HOLD_UNCONFIRMED_PROVENANCE":48,
 "HOLD_UPLOADER_OR_PHOTO_LICENSE":25,
 "HOLD_MUSEUM_FILE_LICENSE":18,
 "HOLD_MET_NOT_OPEN_ACCESS":1,
}
def read(path):return json.loads(Path(path).read_text(encoding="utf-8"))
def write(path,obj):
 p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def decision(x):
 identity=x["source_identity"]
 if not re.fullmatch(r"commons:\d+",identity):raise ValueError("Unexpected source ID")
 if x.get("commercially_approved") is not False or x.get("runtime_visible") is not False:
  raise ValueError("Previously unreviewed source already published")
 if x.get("lane") not in ("A_FAST_TRACK_LUMINOUS","B_FAST_TRACK_OTHER"):
  raise ValueError("Expected Fast Track source only")
 if x["license_class"] not in ("PUBLIC_DOMAIN","CC0") or not x["source_page"].startswith("https://commons.wikimedia.org/"):
  raise ValueError("Input image missing stable public-domain/CC0 claim")
 excerpt=((x.get("source_excerpt") or "")+" "+(x.get("photo_credit") or "")).lower()
 if identity in APPROVED:
  ref=APPROVED[identity]
  if x["file_sha1"]!=ref["sha1"] or x["artist"]!=ref["artist"] or (
     not x.get("source_metadata_checked") or x.get("issues")
  ):raise ValueError("Institutionally sourced item changed: "+identity)
  if ref["museum"]=="Nationalmuseum" and "nationalmuseum" not in excerpt:
   raise ValueError("Mismatch original Nationalmuseum photographer")
  if ref["museum"]=="Yale University Art Gallery" and "yale" not in excerpt:
   raise ValueError("Mismatch Yale museum source")
  cls="CERTIFIED_INSTITUTIONAL_PD_FILE"
 elif identity==HOLD_MET:
  cls="HOLD_MET_NOT_OPEN_ACCESS"
 elif SECONDARY.search(excerpt):
  cls="HOLD_SECONDARY_OR_COMMERCIAL_SOURCE"
 elif MUSEUM.search(excerpt):
  cls="HOLD_MUSEUM_FILE_LICENSE"
 elif UPLOADER.search(excerpt):
  cls="HOLD_UPLOADER_OR_PHOTO_LICENSE"
 else:cls="HOLD_UNCONFIRMED_PROVENANCE"
 return {
  "source_identity":identity,"artist":x["artist"],"title":x["title"],
  "wave":x["wave"],"status":cls,
  "source_page":x["source_page"],"license_class":x["license_class"],
  "source_excerpt":x.get("source_excerpt"),"photo_credit":x.get("photo_credit"),
  "file_sha1":x["file_sha1"],
  "museum_object":APPROVED.get(identity,{}).get("object"),
  "museum_policy":APPROVED.get(identity,{}).get("policy"),
  "independent_source_review":identity in APPROVED,
  "commercially_approved":identity in APPROVED,
  "runtime_visible":False,
 }
def wave(input_path,outdir,wave_id):
 arr=read(input_path)
 expected=100 if wave_id in (1,2) else 83
 if len(arr)!=expected:raise ValueError("Wrong wave size")
 if any(x.get("wave")!=f"FAST_{wave_id:02d}" for x in arr):
  raise ValueError("Shuffled wave")
 result=[decision(x) for x in arr]
 if len({x["source_identity"] for x in result})!=expected:
  raise ValueError("Duplicate ID inside wave")
 out=Path(outdir);out.mkdir(parents=True,exist_ok=True)
 write(out/f"verified_wave_{wave_id:02d}.json",{
  "wave":wave_id,"count":expected,"records":result,
  "status_counts":dict(collections.Counter(x["status"] for x in result))
 })
 print(json.dumps({"wave":wave_id,"count":expected,
   "status":dict(collections.Counter(x["status"] for x in result))}),flush=True)
def aggregate(wavedir,outdir):
 rows=[]
 for n in (1,2,3):
  part=read(Path(wavedir)/f"verified_wave_{n:02d}.json")
  expected=100 if n!=3 else 83
  if part["wave"]!=n or part["count"]!=expected or len(part["records"])!=expected:
   raise ValueError("Missing or incomplete wave")
  rows.extend(part["records"])
 ids=[x["source_identity"] for x in rows]
 if len(rows)!=283 or len(set(ids))!=283:raise ValueError("283 incomplete / duplicate sources")
 counts=dict(collections.Counter(x["status"] for x in rows))
 if counts!=EXPECTED:raise ValueError("Reconciliation policy drift: "+str(counts))
 ready=[x for x in rows if x["status"]=="CERTIFIED_INSTITUTIONAL_PD_FILE"]
 if {x["source_identity"] for x in ready}!=set(APPROVED):
  raise ValueError("Approval whitelist changed")
 if any((x["commercially_approved"] is not (x in ready) or x["runtime_visible"] is not False) for x in rows):
  raise ValueError("Unexpected clearance or visibility")
 hold=[x for x in rows if x not in ready]
 result={
  "total":283,"waves":[100,100,83],"new_documentary_approved":3,
  "held":280,"status_counts":counts,"approved_source_ids":sorted(APPROVED),
  "photo_and_museum_provenance_must_be_verified_separately":True,
  "source_revision":SOURCE_SHA,
  "release_gate":"ONLY_THREE_DOCUMENTED_RECORDS_MAY_ENTER_CURATED_CATALOG",
  "global_play_store_release_auto_approved":False
 }
 out=Path(outdir);out.mkdir(parents=True,exist_ok=True)
 write(out/"rights_batch_283_summary.json",result)
 write(out/"rights_batch_283_per_item.json",rows)
 write(out/"rights_batch_3_approved.json",ready)
 write(out/"rights_batch_280_hold.json",hold)
 with (out/"rights_batch_283.csv").open("w",encoding="utf-8",newline="") as f:
  w=csv.writer(f)
  w.writerow(["source_identity","artist","title","wave","status","file_sha1","museum_object","museum_policy"])
  for x in rows:w.writerow([x["source_identity"],x["artist"],x["title"],x["wave"],
      x["status"],x["file_sha1"],x["museum_object"],x["museum_policy"]])
 print(json.dumps(result,ensure_ascii=False),flush=True)

def norm(s):
 return " ".join(re.sub(r"[^\w]+"," ",unicodedata.normalize("NFKC",s.casefold())).split())
def validate_catalog(approved_path,root):
 ready=read(approved_path)
 catalog=read(Path(root)/"assets/museums/catalog_curated_commons.json")
 if len(ready)!=3 or len(catalog)!=4:raise ValueError("Expected 3 new plus Met/Sisley")
 byid={r["source_identity"]:r for r in catalog}
 if len(byid)!=4 or set(byid)!=(set(APPROVED)|{"commons:57672559"}):
  raise ValueError("Unauthorized, duplicated or missing catalog entry")
 for sid,proof in APPROVED.items():
  v=byid[sid]
  if (v["id"]!=int(sid.split(":")[1]) or v["museum_native_id"]!=sid.split(":")[1] or
      v["source_identity"]!=sid or v["artist_title"]!=proof["artist"] or
      v["rights_license"]!="Public Domain" or
      v["commercially_approved"] is not True or
      v["source_provenance_verified"] is not True or
      v["worldwide_distribution_reviewed"] is not True or
      not v.get("image_attribution") or
      v["remote_museum_url"] != next(x["source_page"] for x in ready if x["source_identity"]==sid)):
   raise ValueError("Catalog rights record does not match signed review "+sid)
  rfile=Path(root)/v["rights_review_reference"]
  if not rfile.is_file():raise ValueError("Missing traceable review document")
 if any(r.get("artdrift_research_only") for r in catalog):
  raise ValueError("Research images in commercial catalog")
 # Existing source catalogs must not already contain the same artwork.
 source_paths=[
  "assets/gallery/catalog.json","assets/museums/catalog.json",
  "assets/museums/catalog_global.json",
  "assets/museums/catalog_modern_1950.json",
  "assets/museums/catalog_new_museums.json"
 ]
 previous=[]
 for path in source_paths:
  obj=read(Path(root)/path)
  if not isinstance(obj,list):raise ValueError("Bad original catalog "+path)
  previous.extend(obj)
 colliding=[]
 for v in catalog[1:]:
  title=norm(v["title"]);author=norm(v["artist_title"])
  for e in previous:
   author_existing=norm(str(e.get("artist_title") or e.get("artist_display") or ""))
   title_existing=norm(str(e.get("title") or ""))
   if (author in author_existing or author_existing in author) and (
        title==title_existing or (len(title)>13 and title in title_existing and
          len(title_existing)-len(title)<12)):
    colliding.append((v["source_identity"],e.get("id"),str(e.get("title"))[:100]))
 if colliding:raise ValueError("Existing artwork version candidate duplicates: "+str(colliding[:8]))
 print("BATCH_3_CATALOG_LICENSE_AND_DUPLICATE_CHECK_PASS",
       "new",len(ready),"existing",len(previous),flush=True)

def main():
 p=argparse.ArgumentParser()
 p.add_argument("--action",choices=("wave","aggregate","catalog"),required=True)
 p.add_argument("--input",type=Path);p.add_argument("--out",type=Path)
 p.add_argument("--wave",type=int,choices=(1,2,3));p.add_argument("--wave-dir",type=Path)
 p.add_argument("--root",type=Path,default=Path("."))
 a=p.parse_args()
 if a.action=="wave":wave(a.input,a.out,a.wave)
 elif a.action=="aggregate":aggregate(a.wave_dir,a.out)
 else:validate_catalog(a.input,a.root)
if __name__=="__main__":main()
