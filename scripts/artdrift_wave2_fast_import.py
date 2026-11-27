#!/usr/bin/env python3
"""485-image batch reassessment; only two new primary-source CC0 releases.
Never infer publication rights from a generic Commons public-domain label.
"""
import argparse,collections,csv,hashlib,json,re,unicodedata
from pathlib import Path
from difflib import SequenceMatcher

PREVIOUS={"commons:52129968","commons:52132342","commons:80548151"}
SISLEY="commons:57672559"
NEW={"commons:80538945":("3fee3f38886a5d158113e35db113e4f20e9e6ed7","Ludvig Karsten"),
     "commons:81308959":("8f3f33e2b9387b296a06cb87f7ef80ec329d7dcf","Claude Monet")}
DUPLICATES={"commons:6404635","commons:127400389"}
MET_HOLD={"commons:57670806","commons:57670842"}
CATALOGS=("assets/gallery/catalog.json","assets/museums/catalog.json",
 "assets/museums/catalog_global.json","assets/museums/catalog_modern_1950.json",
 "assets/museums/catalog_new_museums.json")
def load(p):return json.loads(Path(p).read_text(encoding="utf-8"))
def save(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def normalized(s):
 s=unicodedata.normalize("NFKD",str(s or "").lower())
 return " ".join(re.sub(r"[^\w]+"," ","".join(c for c in s if not unicodedata.combining(c))).split())
def stage(root,srcfile,out):
 rows=load(srcfile)
 if len(rows)!=485 or len({r["source_identity"] for r in rows})!=485:
  raise ValueError("485 unique source files required")
 source={r["source_identity"]:r for r in rows}
 needed=set(NEW)|PREVIOUS|DUPLICATES|MET_HOLD
 if SISLEY in source or not needed.issubset(source):raise ValueError("Source identities drifted")
 if any(r.get("commercially_approved") is not False for r in rows):
  raise ValueError("Old research must not grant commercial rights")
 catalog=load(Path(root)/"assets/museums/catalog_curated_commons.json")
 ids={r["source_identity"] for r in catalog}
 if len(catalog)!=6 or len(ids)!=6 or ids!={SISLEY}|PREVIOUS|set(NEW):
  raise ValueError("Six and only six institutionally reviewed files must be present")
 byid={r["source_identity"]:r for r in catalog}
 for cid,(sha,artist) in NEW.items():
  s=source[cid];r=byid[cid]
  if s["file_sha1"]!=sha or s["artist"]!=artist or r["artist_title"]!=artist or \
     r["id"]!=int(cid.split(":")[1]) or r["museum_native_id"]!=cid.split(":")[1] or \
     r["rights_license"]!="CC0 1.0" or r["commercially_approved"] is not True or \
     r["source_provenance_verified"] is not True or r["worldwide_distribution_reviewed"] is not True or \
     r["remote_museum_url"]!=s["source_page"] or not r.get("image_attribution") or \
     not r["remote_full_url"].startswith("https://upload.wikimedia.org/wikipedia/commons/") or \
     not r["remote_preview_url"].startswith("https://thumb.wikimedia.org/wikipedia/commons/thumb/") or \
     not (Path(root)/r["rights_review_reference"]).is_file():
   raise ValueError("Unverifiable release sign-off "+cid)
 if any(r.get("artdrift_research_only") for r in catalog):
  raise ValueError("Research-only entry in public catalog")
 # Duplicate painting checks on all existing museum catalogs, independent of file hash.
 prior=[]
 for path in CATALOGS:
  f=Path(root)/path
  if not f.exists():raise ValueError("Missing canonical catalog "+path)
  data=load(f)
  if not isinstance(data,list):raise ValueError("Invalid museum catalog "+path)
  prior.extend(data)
 for cid in NEW:
  r=byid[cid];a=normalized(r["artist_title"]);t=normalized(r["title"])
  for x in prior:
   artist=normalized(x.get("artist_title") or x.get("artist_display") or x.get("artist"))
   title=normalized(x.get("title"))
   if a==artist and title and (t==title or
         (min(len(t),len(title))>12 and SequenceMatcher(None,t,title).ratio()>=0.95)):
    raise ValueError("Existing same-work candidate: "+cid+" / "+str(x.get("id")))
 result=[]
 for r in rows:
  cid=r["source_identity"]
  if cid in PREVIOUS:status="PREVIOUSLY_APPROVED"
  elif cid in NEW:status="NEW_APPROVED_INSTITUTIONAL_CC0"
  elif cid in DUPLICATES:status="EXCLUDED_DUPLICATE"
  elif cid in MET_HOLD:status="HOLD_MET_NOT_OPEN_ACCESS"
  elif cid.startswith("staedel:"):status="HOLD_MUSEUM_FILE_RIGHTS_CONFLICT"
  else:status="HOLD_SOURCE_OR_IMAGE_LICENSE"
  result.append({"source_identity":cid,"artist":r["artist"],"title":r["title"],
     "file_sha1":r["file_sha1"],"rights_claim":r.get("license_claim"),
     "source_page":r["source_page"],"source_excerpt":r.get("source_excerpt"),
     "disposition":status,"commercially_approved_in_this_batch":cid in NEW})
 cnt=collections.Counter(x["disposition"] for x in result)
 if cnt["PREVIOUSLY_APPROVED"]!=3 or cnt["NEW_APPROVED_INSTITUTIONAL_CC0"]!=2 or \
    cnt["EXCLUDED_DUPLICATE"]!=2 or sum(cnt.values())!=485:
  raise ValueError("Approval counts changed "+str(cnt))
 out=Path(out);out.mkdir(parents=True,exist_ok=True)
 for i in range(5):save(out/f"wave_{i+1:02d}.json",result[i*100:(i+1)*100])
 save(out/"wave2_485_per_item.json",result)
 summary={"source_records":485,"previous_approved_in_source":3,"new_approved":2,
   "hold_or_excluded_in_source":480,"duplicated_versions_excluded":2,
   "total_public_catalog":6,"not_approved_in_original_486":480,
   "wave_sizes":[100,100,100,100,85],"original_existing_catalog_rows":len(prior),
   "status":dict(cnt),"sha256_source":hashlib.sha256(Path(srcfile).read_bytes()).hexdigest(),
   "gate":"ALL_UNREVIEWED_REMAIN_HOLD","new_verified_ids":sorted(NEW)}
 save(out/"wave2_summary.json",summary)
 with (out/"wave2_485.csv").open("w",encoding="utf-8",newline="") as f:
  w=csv.writer(f);w.writerow(["source_identity","artist","title","status","license_claim","source_url"])
  for r in result:w.writerow([r["source_identity"],r["artist"],r["title"],r["disposition"],r["rights_claim"],r["source_page"]])
 print(json.dumps(summary,ensure_ascii=False),flush=True)
def verify(out,which):
 p=Path(out);allrows=load(p/"wave2_485_per_item.json")
 if len(allrows)!=485 or len({x["source_identity"] for x in allrows})!=485:
  raise ValueError("Incomplete original batch")
 for i in ([which] if which else range(1,6)):
  chunk=load(p/f"wave_{i:02d}.json")
  if len(chunk)!=(100 if i<5 else 85) or chunk!=allrows[(i-1)*100:i*100]:
   raise ValueError("Invalid wave "+str(i))
 summary=load(p/"wave2_summary.json")
 if summary["new_approved"]!=2 or summary["hold_or_excluded_in_source"]!=480:
  raise ValueError("Publication accounting changed")
 print("FAST_TRACK_WAVE_2_PASS",which or "ALL",flush=True)
if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--root",default=".")
 p.add_argument("--source",type=Path)
 p.add_argument("--out",type=Path,default=Path("wave2-result"))
 p.add_argument("--verify",type=int,choices=(0,1,2,3,4,5))
 args=p.parse_args()
 if args.verify is None:
  if not args.source:p.error("--source required")
  stage(args.root,args.source,args.out)
 else:verify(args.out,args.verify)
