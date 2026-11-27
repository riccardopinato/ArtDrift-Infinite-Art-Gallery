#!/usr/bin/env python3
"""Art Drift 485 batch triage from pinned external QA artifacts.

One pass, 3 waves of at most 100. Evidence/staging ONLY. License assertions
and source file metadata are never converted into commercial permissions.
"""
from __future__ import annotations
import argparse,collections,csv,hashlib,html,json,re
from pathlib import Path

SOURCE_SHA="b82a4574db3d504141b6d2e95e403aa743c771e3"
SISLEY="commons:57672559"
EXCLUDE={"commons:6404635","commons:127400389"}
MET_HOLD={"commons:57670806","commons:57670842"}
ARTIST={
 "alfred_sisley":"Alfred Sisley","claude_monet":"Claude Monet",
 "gustave_caillebotte":"Gustave Caillebotte",
 "otto_modersohn":"Otto Modersohn","harald_sohlberg":"Harald Sohlberg",
 "serhii_vasylkivskyi":"Serhii Vasylkivskyi","ludvig_karsten":"Ludvig Karsten",
}
ORDER={k:n for n,k in enumerate(ARTIST)}
LANES=("A_FAST_TRACK_LUMINOUS","B_FAST_TRACK_OTHER","C_EXCEPTION_BATCH",
       "HOLD_MET_RIGHTS_CONFLICT","HOLD_MUSEUM_RIGHTS_CONFLICT","EXCLUDE_REPEATED_WORK")

def read(p):return json.loads(Path(p).read_text(encoding="utf-8"))
def index(seq):
 out={x["source_identity"]:x for x in seq}
 if len(out)!=len(seq):raise ValueError("Duplicated image identities")
 return out
def dump(p,obj):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def source_wiki_checked(w):
 return w.get("wiki_checked") is True and w.get("source_field") not in (
     None,"","NOT_AVAILABLE","NOT_EXTRACTED_FROM_WIKI")
def load_data(root):
 root=Path(root)
 paths={
   "inventory":root/"inputs/inventory.json",
   "rights":root/"rights/rights_486_per_item.json",
   "preflight":root/"preflight/final_486_queue.json",
   "wiki":root/"wiki/wiki_486_evidence.json",
   "pixel":root/"pixel/.artist-aggregate/review_queue.csv",
   "retry":root/"retry/retry_per_item.json",
 }
 inputs={k:p.read_bytes() for k,p in paths.items()}
 sha={k:hashlib.sha256(v).hexdigest() for k,v in inputs.items()}
 inv=index(read(paths["inventory"])["complete_queue"])
 rights=index(read(paths["rights"]))
 pre=index(read(paths["preflight"]))
 wiki=index(read(paths["wiki"]))
 retries=index(read(paths["retry"]))
 with paths["pixel"].open(encoding="utf-8",newline="") as f:
  px=index(list(csv.DictReader(f)))
 if not all(len(x)==486 for x in (inv,rights,pre,wiki,px)):
  raise ValueError("Original 486-source evidence corrupted")
 if len(retries)!=39:
  raise ValueError("Expected EXACTLY 39 original technical retrials")
 ids=set(inv)
 if any(set(x)!=ids for x in (rights,pre,wiki,px)) or not set(retries).issubset(ids):
  raise ValueError("Cross-source identity mismatch")
 if SISLEY not in ids or len(ids-{SISLEY})!=485:
  raise ValueError("First curated Sisley source cannot be lost")
 if not all(px[k]["result"]=="HOLD_TECHNICAL" for k in retries):
  raise ValueError("Retry may not overwrite earlier decoded pixel checks")
 if sum(x.get("result")=="PIXELS_OK_RIGHTS_AND_VISUAL_HOLD" for x in retries.values())!=12:
  raise ValueError("Changed retry results; stop instead of guessing")
 for k,row in retries.items():
  px[k]={"source_identity":k,"result":row["result"],
         "technical_color_class":row.get("technical_color_class","NOT_DECODED"),
         "record_url":row.get("record_url"),
         "error":row.get("technical_error") or row.get("error")}
 return inv,rights,pre,wiki,px,sha

def record(k,inventory,r,p,w,pix):
 if inventory["artist_id"] not in ARTIST:
  raise ValueError("Artist outside pinned selected seven")
 if inventory["artist_id"]!=r["artist_id"] or r["artist_id"]!=p["artist_id"]:
  raise ValueError("Artist identity drift across reports")
 flags=set(p.get("flags") or [])
 lic=r.get("license_class_live") or "NOT_RETRIEVED"
 pixel_ok=pix["result"]=="PIXELS_OK_RIGHTS_AND_VISUAL_HOLD"
 color=pix.get("technical_color_class") or "NOT_DECODED"
 no_dup=not p.get("similar_title_candidates")
 no_layer=not w.get("potential_layered_pd_plus_cc")
 author="PAINTER_NOT_CONFIRMED_FROM_EXTRACTED_AUTHOR_FIELD" not in flags
 source=source_wiki_checked(w)
 open_license=lic in ("PUBLIC_DOMAIN","CC0")
 no_conflict=not r.get("licence_mismatch") and "FILE_COPYRIGHTED_FLAG_WITH_OPEN_RIGHTS_CLAIM" not in flags
 painting=not any(n in flags for n in (
  "POSSIBLE_PHOTOGRAPH_NOT_PAINTER_ARTWORK",
  "REPRODUCTION_PRINT_FRAME_OR_NONPAINTING_TITLE"))
 stable=bool(r.get("file_sha1_live")) and r.get("file_sha1_live")==r.get("file_sha1_previous")
 eligible=all((pixel_ok,no_dup,no_layer,author,source,open_license,
               no_conflict,painting,stable))
 if k in EXCLUDE:lane="EXCLUDE_REPEATED_WORK"
 elif k in MET_HOLD:lane="HOLD_MET_RIGHTS_CONFLICT"
 elif k.startswith("staedel:"):lane="HOLD_MUSEUM_RIGHTS_CONFLICT"
 elif eligible:
  lane="A_FAST_TRACK_LUMINOUS" if color=="LUMINOUS_VISUAL_REVIEW" else "B_FAST_TRACK_OTHER"
 else:lane="C_EXCEPTION_BATCH"
 issues=[]
 for passed,flag in (
  (pixel_ok,"IMAGE_PREVIEW_NOT_DECODED"),
  (no_dup,"POSSIBLE_ALTERNATE_VERSION"),
  (no_layer,"LAYERED_PD_PAINTING_CC_PHOTO"),
  (author,"PAINTER_NOT_EVIDENCED_FROM_FILE_CREDITS"),
  (source,"ORIGINAL_SOURCE_FIELD_MISSING"),
  (open_license,"FILE_LICENSE_CC_OR_UNRECOGNIZED"),
  (no_conflict,"LICENSE_METADATA_CONFLICT"),
  (painting,"OBJECT_MAY_NOT_BE_ORIGINAL_PAINTING"),
  (stable,"FILE_SHA1_INCONSISTENT"),
 ):
  if not passed:issues.append(flag)
 if k in EXCLUDE:issues.append("SAME_SISLEY_PAINTING_ALREADY_STAGED")
 if k in MET_HOLD:issues.append("MET_API_NOT_OPEN_ACCESS")
 if k.startswith("staedel:"):issues.append("STADEL_FILE_RIGHTS_CONFLICT")
 url=r.get("source_page") or pix.get("record_url") or inventory.get("record_url")
 preview=inventory.get("preview_url") or ""
 if not isinstance(url,str) or not url.startswith("https://"):raise ValueError("Bad original file page")
 if not isinstance(preview,str) or not preview.startswith("https://"):
  # Städel has an object page rather than a Commons CDN file.
  if not k.startswith("staedel:"):raise ValueError("Bad preview URL for "+k)
  preview=""
 return {
  "source_identity":k,"artist_id":inventory["artist_id"],"artist":ARTIST[inventory["artist_id"]],
  "title":r.get("title") or inventory.get("title"),
  "source_page":url,"preview_url":preview,
  "license_claim":r.get("license_live") or r.get("source_license_claim"),
  "license_class":lic,"license_source_url":r.get("license_url") or "",
  "photo_credit":r.get("photographic_credit") or "",
  "painter_credit":r.get("artist_credit") or "",
  "source_excerpt":(w.get("source_field") or "")[:550],
  "file_sha1":r.get("file_sha1_live") or "",
  "color_class":color,"lane":lane,"issues":issues,
  "source_metadata_checked":source,
  "original_museum_rights_independently_authenticated":False,
  "commercially_approved":False,"runtime_visible":False,
 }
def build(root,out):
 inv,rights,pre,wiki,pixel,hashes=load_data(root)
 rows=[record(k,inv[k],rights[k],pre[k],wiki[k],pixel[k])
       for k in inv if k!=SISLEY]
 lane_sort={k:i for i,k in enumerate(LANES)}
 rows.sort(key=lambda r:(lane_sort[r["lane"]],ORDER[r["artist_id"]],str(r["title"]).casefold(),r["source_identity"]))
 fast=[x for x in rows if x["lane"] in LANES[:2]]
 for i,item in enumerate(fast):item["wave"]="FAST_%02d"%(i//100+1)
 for item in rows:
  if "wave" not in item:item["wave"]="EXCEPTIONS"
 summary={
  "schema_version":1,"source_pin":SOURCE_SHA,
  "original_486_distinct":486,"already_staged_Sisley":SISLEY,
  "remaining_485":485,"fasttrack_total":len(fast),
  "lanes":dict(collections.Counter(x["lane"] for x in rows)),
  "wave_counts":dict(collections.Counter(x["wave"] for x in fast)),
  "technical_pass_overall":sum(x["result"]=="PIXELS_OK_RIGHTS_AND_VISUAL_HOLD" for x in pixel.values()),
  "technical_hold_overall":sum(x["result"]!="PIXELS_OK_RIGHTS_AND_VISUAL_HOLD" for x in pixel.values()),
  "commercially_approved":0,"runtime_imported":0,"original_image_copyright_checked_manually":0,
  "evidence_inputs_sha256":hashes,"publication_gate":"CLOSED",
  "warning":"Research prioritization, not proof of copyright clearance or official museum authorization."
 }
 if len(rows)!=485 or len({x["source_identity"] for x in rows})!=485:
  raise ValueError("Triage row loss or duplicate")
 if not all(x["commercially_approved"] is False and x["runtime_visible"] is False for x in rows):
  raise ValueError("Unauthorized publication")
 if len(fast)<150 or len(fast)>400:
  raise ValueError("Unexpected fast-track count: review selection policy")
 out=Path(out);out.mkdir(parents=True,exist_ok=True)
 dump(out/"fasttrack_summary.json",summary)
 dump(out/"fasttrack_485.json",rows)
 dump(out/"fasttrack_eligible.json",fast)
 for n in range(3):dump(out/("FAST_%02d.json"%(n+1)),fast[n*100:(n+1)*100])
 with (out/"fasttrack_485.csv").open("w",encoding="utf-8",newline="") as f:
  writer=csv.writer(f)
  writer.writerow(["id","artist","title","lane","wave","license_claim","photo_credit","source_page","issues","commercially_approved"])
  for x in rows:
   writer.writerow([x["source_identity"],x["artist"],x["title"],x["lane"],x["wave"],
         x["license_claim"],x["photo_credit"],x["source_page"],";".join(x["issues"]),False])
 print(json.dumps(summary,ensure_ascii=False),flush=True)

def verify(out,which):
 out=Path(out);fast=read(out/"fasttrack_eligible.json")
 rows=read(out/"fasttrack_485.json")
 summary=read(out/"fasttrack_summary.json")
 if len(rows)!=485 or len({x["source_identity"] for x in rows})!=485:
  raise ValueError("485 records not reconciled")
 if len(fast)!=summary["fasttrack_total"]:
  raise ValueError("Fast-track output truncated")
 if summary["technical_pass_overall"]!=459 or summary["technical_hold_overall"]!=27:
  raise ValueError("First/second image download results mismatched")
 if summary["commercially_approved"]!=0 or summary["runtime_imported"]!=0:
  raise ValueError("Unsafe metadata flags")
 if any(x.get("commercially_approved") is not False or x.get("runtime_visible") is not False for x in rows):
  raise ValueError("Unreviewed candidate marked publishable")
 if which:
  wave=read(out/("FAST_%02d.json"%which))
  target=fast[100*(which-1):100*which]
  if wave!=target or len(wave)!=min(100,max(0,len(fast)-100*(which-1))):
   raise ValueError("Wave "+str(which)+" is truncated or not ordered")
  print("VERIFIED_FASTTRACK_WAVE",which,len(wave))
 else:
  if sum(len(read(out/("FAST_%02d.json"%n))) for n in (1,2,3))!=len(fast):
   raise ValueError("Wave coverage mismatch")
  print("FASTTRACK_485_COVERAGE_PASS",len(fast),summary["wave_counts"])

def main():
 p=argparse.ArgumentParser()
 p.add_argument("--root",type=Path,default=Path("."))
 p.add_argument("--out",type=Path,default=Path("fasttrack-results"))
 p.add_argument("--verify",type=int,choices=(0,1,2,3))
 a=p.parse_args()
 if a.verify is None:build(a.root,a.out)
 else:verify(a.out,a.verify)
if __name__=="__main__":main()
