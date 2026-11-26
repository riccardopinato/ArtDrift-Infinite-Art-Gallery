#!/usr/bin/env python3
"""Art Drift release preflight: all 486 per-file evidence records, fail-closed.

Source pins: Commons rights audit 45907246535; pixels 45905782588;
PR84 image identities b82a4574db3d504141b6d2e95e403aa743c771e3.
This program never grants commercial publication permission.
"""
from __future__ import annotations
import argparse,collections,html,itertools,json,re,time,urllib.error,urllib.parse,urllib.request
from pathlib import Path
from difflib import SequenceMatcher

def ratio(a,b):
 return 100*SequenceMatcher(None,a,b).ratio()

PIN="b82a4574db3d504141b6d2e95e403aa743c771e3"
N=486
ARTISTS={
 "claude_monet":("monet",),"otto_modersohn":("modersohn",),
 "alfred_sisley":("sisley",),"harald_sohlberg":("sohlberg",),
 "serhii_vasylkivskyi":("vasylkiv","vasilkov","васильків"),
 "gustave_caillebotte":("caillebotte",),"ludvig_karsten":("karsten",)}
CATALOGS=("assets/gallery/catalog.json","assets/museums/catalog.json",
 "assets/museums/catalog_global.json","assets/museums/catalog_modern_1950.json",
 "assets/museums/catalog_new_museums.json")
ARTIFACT=re.compile(r"(catalogue|catalog|trichromogravure|lithograph|etching|engraving|facsimile|exhibition poster|postcard|poster|with frame|framed|reproduction|photograph of painting|scanned book)",re.I)
NOT_PAINTING=re.compile(r"(monet.s home|pedder building|hk central|art market|gallery interior)",re.I)

def load(path):return json.loads(Path(path).read_text(encoding="utf-8"))
def save(path,data):
 p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def normalized(s):
 return " ".join(re.sub(r"[^\w]+"," ",str(s or "").casefold()).split())
def core_title(name,artist):
 s=normalized(re.sub(r"\.(?:jpg|jpeg|png|tiff|webp)$","",str(name or ""),flags=re.I))
 for a in ARTISTS[artist]:
  s=re.sub(r"\b"+re.escape(a)+r"\b"," ",s)
 return " ".join(s.split())
def pinned_reports(rights,sharddir):
 d=load(Path(rights)/"rights_486_summary.json")
 if d.get("source_revision")!=PIN or d.get("images_checked")!=N:raise ValueError("Wrong pinned rights audit")
 rows=load(Path(rights)/"rights_486_per_item.json")
 if len(rows)!=N:raise ValueError("Truncated rights audit")
 rights_index={x["source_identity"]:x for x in rows}
 qa=[]
 for j in range(18):
  part=load(Path(sharddir)/("shard_%02d.json"%j))
  if part.get("shard")!=j or part.get("shards")!=18 or part.get("processed")!=len(part["rows"]):
   raise ValueError("Swapped or truncated pixel QA shard")
  qa.extend(part["rows"])
 qa_index={x["source_identity"]:x for x in qa}
 if len(rights_index)!=N or len(qa_index)!=N or set(rights_index)!=set(qa_index):
  raise ValueError("Mixed, duplicated or missing artist image IDs")
 if any(x.get("commercially_approved") is not False for x in rows+qa):
  raise ValueError("Unapproved source entered release path")
 return rights_index,qa_index
def potential_pairs(rows):
 by_artist=collections.defaultdict(list)
 for r in rows:by_artist[r["artist_id"]].append(r)
 matches=collections.defaultdict(list);pairs=[]
 for artist,items in by_artist.items():
  for a,b in itertools.combinations(items,2):
   an,bn=core_title(a["title"],artist),core_title(b["title"],artist)
   if min(len(an),len(bn))<14:continue
   score=ratio(an,bn)
   if score>=91:
    matches[a["source_identity"]].append(b["source_identity"])
    matches[b["source_identity"]].append(a["source_identity"])
    pairs.append({"artist":artist,"a":a["source_identity"],"b":b["source_identity"],
      "title_a":a["title"],"title_b":b["title"],"score":round(score,1),
      "identity_verified":False})
 return matches,pairs
def catalog_review(candidates,root):
 current=[]
 for path in CATALOGS:
  f=Path(root)/path
  if not f.exists():raise ValueError("Missing runtime catalog "+path)
  data=load(f)
  if not isinstance(data,list):raise ValueError("Invalid runtime catalog "+path)
  for row in data:
   if not isinstance(row,dict):continue
   who=normalized(row.get("artist_title") or row.get("artist_display"))
   for painter,aliases in ARTISTS.items():
    if any(alias in who for alias in aliases):
     current.append({"painter":painter,"title":row.get("title"),"key":str(row.get("museum_source") or "aic")+":"+str(row.get("id")),"catalog":path})
 duplicates=collections.defaultdict(list)
 by_artist=collections.defaultdict(list)
 for x in current:by_artist[x["painter"]].append(x)
 for r in candidates:
  artist=r["artist_id"];t=core_title(r["title"],artist)
  if len(t)<9:continue
  for x in by_artist[artist]:
   existing=normalized(x["title"])
   if len(existing)<8:continue
   score=ratio(t,existing)
   if score>=86:
    duplicates[r["source_identity"]].append({"existing":x["key"],"catalog":x["catalog"],
     "title":x["title"],"similarity":round(score,1),"not_proven_same_work":True})
 return duplicates,len(current)
def prepare(rights,shards,root,out):
 rights_index,qa_index=pinned_reports(rights,shards)
 rows=list(rights_index.values())
 if any(r["artist_id"] not in ARTISTS for r in rows):raise ValueError("Unexpected painter")
 semantic,pairs=potential_pairs(rows)
 runtime,runt_count=catalog_review(rows,root)
 results=[]
 for k in sorted(rights_index):
  r=rights_index[k];q=qa_index[k]
  if r["artist_id"]!=q["artist_id"]:raise ValueError("Artist identity mismatch")
  licence=r.get("license_class_live") or "MUSEUM_CLAIM_CONFLICT"
  flags=[]
  if not r.get("source_field"):flags.append("SOURCE_ABSENT_FROM_EXTRACTED_METADATA_RECHECK_FILE_WIKITEXT")
  if not r.get("painter_matched_in_artist_credit"):flags.append("PAINTER_NOT_CONFIRMED_FROM_EXTRACTED_AUTHOR_FIELD")
  if r.get("licence_mismatch"):flags.append("LICENSE_METADATA_CONFLICT")
  if r.get("copyrighted_flag")=="True" and licence in ("PUBLIC_DOMAIN","CC0"):
   flags.append("FILE_COPYRIGHTED_FLAG_WITH_OPEN_RIGHTS_CLAIM")
  if licence in ("CC_BY","CC_BY_SA"):
   flags.append("REQUIRE_FULL_PHOTO_CREDIT_LINK_VERSION_AND_CHANGE_NOTICE")
  if licence=="CC_BY_SA":flags.append("SHAREALIKE_CONDITIONS_ON_ADAPTATIONS_IF_APPLICABLE")
  if q["result"]!="PIXELS_OK_RIGHTS_AND_VISUAL_HOLD":
   flags.append("PREVIEW_IMAGE_NOT_TECHNICALLY_CHECKED")
  pixel=q.get("pixel") or {}
  if pixel and min(pixel.get("width",0),pixel.get("height",0))<300:
   flags.append("PREVIEW_SHORT_SIDE_UNDER_300")
  if ARTIFACT.search(r["title"]):flags.append("REPRODUCTION_PRINT_FRAME_OR_NONPAINTING_TITLE")
  if NOT_PAINTING.search(r["title"]):flags.append("POSSIBLE_PHOTOGRAPH_NOT_PAINTER_ARTWORK")
  if semantic[k]:flags.append("POSSIBLE_DUPLICATE_OR_ALTERNATE_VERSION_IN_486")
  if runtime[k]:flags.append("POSSIBLE_DUPLICATE_WITH_EXISTING_RUNTIME")
  flags.extend(["PROVENANCE_AND_ORIGINAL_FILE_PAGE_NOT_YET_CONFIRMED",
    "TERRITORIAL_AND_MUSEUM_TERMS_NOT_YET_CONFIRMED",
    "APP_SOURCE_HOST_AND_ATTRIBUTION_UI_NOT_YET_SUPPORTED"])
  results.append({"source_identity":k,"artist_id":r["artist_id"],"title":r["title"],
     "source_file_page":r.get("source_page"),"source_file_sha1":r.get("file_sha1_live"),
     "licence_category":licence,"license_url":r.get("license_url"),
     "artist_credit":r.get("artist_credit"),"photo_credit":r.get("photographic_credit"),
     "preview_status":q["result"],"preview_color":q.get("technical_color_class"),
     "similar_title_candidates":sorted(set(semantic[k])),
     "runtime_collision_suspicions":runtime[k][:8],"flags":flags,
     "commercially_approved":False,"runtime_visible":False,
     "rights_cleared_worldwide":False,"release_gate":"HOLD_MANUAL_FINAL_SOURCE_AND_LICENSE_REVIEW"})
 if len(results)!=N:raise ValueError("Missing item in final checks")
 counter=collections.Counter(f for r in results for f in r["flags"])
 summary={"total":N,"source_pin":PIN,"initial_rights_run":45907246535,
   "initial_pixel_run":45905782588,"semantic_title_pairs":len(pairs),
   "semantic_title_candidates":sum(bool(r["similar_title_candidates"]) for r in results),
   "existing_catalog_artist_rows":runt_count,
   "possible_runtime_overlaps":sum(bool(r["runtime_collision_suspicions"]) for r in results),
   "flags":dict(counter),"commercially_approved":0,"runtime_imported":0,
   "release_ready":0,"publication_gate":"CLOSED",
   "note":"Similarity and licence labels are review evidence, not proof of same work or cleared rights."}
 save(Path(out)/"final_486_queue.json",results)
 save(Path(out)/"possible_same_title_pairs.json",pairs)
 save(Path(out)/"final_summary.json",summary)
 print(json.dumps(summary,ensure_ascii=False),flush=True)

def parse_fields(wiki):
 result={}
 for name in ("source","author","artist","description","date","permission"):
  x=re.search(r"(?im)^[ \t]*\|[ \t]*"+name+r"[ \t]*=[ \t]*(.*?)[ \t]*$",wiki)
  if x:result[name]=re.sub(r"\s+"," ",html.unescape(x.group(1).strip()))[:650]
 return result
def query_wikitext(ids):
 if not ids or len(ids)>10 or any(not re.fullmatch(r"\d+",str(n)) for n in ids):
  raise ValueError("Unsafe batch")
 query=urllib.parse.urlencode({"action":"query","format":"json","formatversion":"2",
  "prop":"revisions","rvprop":"content","rvslots":"main",
  "pageids":"|".join(ids),"maxlag":"5"})
 req=urllib.request.Request("https://commons.wikimedia.org/w/api.php?"+query,headers={
  "User-Agent":"ArtDriftRightsOriginalSourceEvidence/1.0 (github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery)",
  "Accept":"application/json"})
 failure="UNKNOWN"
 for attempt in range(3):
  try:
   with urllib.request.urlopen(req,timeout=30) as resp:
    loc=urllib.parse.urlparse(resp.geturl())
    if loc.hostname!="commons.wikimedia.org" or loc.scheme!="https":
     raise RuntimeError("REDIRECTED_OUT_OF_COMMONS")
    data=json.loads(resp.read(6000000))
   if data.get("error"):
    failure="MW_"+str(data["error"].get("code","ERROR"))
   else:
    pages=data.get("query",{}).get("pages")
    if not isinstance(pages,list):raise RuntimeError("INVALID_RESPONSE")
    return {str(p["pageid"]):p for p in pages if "pageid" in p}
  except urllib.error.HTTPError as ex:
   failure="HTTP_"+str(ex.code)
   if ex.code not in (429,500,502,503,504):break
  except (urllib.error.URLError,RuntimeError,ValueError,OSError) as ex:
   failure=type(ex).__name__+":"+str(ex)[:100]
  if attempt<2:time.sleep(4+attempt*7)
 raise RuntimeError(failure)
def review_wiki(source,page=None,error=None):
 k=source["source_identity"]
 out={"source_identity":k,"file_url":source.get("source_file_page"),
  "source_field":"NOT_AVAILABLE","author_field":"NOT_AVAILABLE",
  "wiki_checked":False,"original_primary_source_authenticated":False,
  "commercially_approved":False,"runtime_visible":False,"publication_gate":"HOLD",
  "issues":[]}
 if k.startswith("staedel:"):
  out["issues"].append("MUSEUM_PD_VS_UPSTREAM_CC_BY_SA_TO_RECONCILE")
  return out
 if error:
  out["issues"].append("LIVE_COMMONS_WIKITEXT_ERROR")
  out["live_error"]=error
  return out
 if not page or page.get("ns")!=6:
  out["issues"].append("FILE_PAGE_MISSING")
  return out
 rev=page.get("revisions") or []
 slot=(rev[0].get("slots") or {}).get("main") if rev else None
 wiki=(slot or {}).get("content") if isinstance(slot,dict) else None
 if not isinstance(wiki,str):
  out["issues"].append("WIKITEXT_NOT_RETRIEVED");return out
 fields=parse_fields(wiki)
 out.update({"wiki_checked":True,"revision_id":rev[0].get("revid"),
  "source_field":fields.get("source","NOT_EXTRACTED_FROM_WIKI"),
  "author_field":fields.get("author") or fields.get("artist") or "NOT_EXTRACTED_FROM_WIKI",
  "file_description_fragment":fields.get("description","")[:300]})
 if not fields.get("source"):out["issues"].append("SOURCE_NEEDS_COMPLEX_TEMPLATE_OR_MUSEUM_VERIFICATION")
 if not (fields.get("author") or fields.get("artist")):
  out["issues"].append("AUTHOR_NEEDS_COMPLEX_TEMPLATE_OR_MUSEUM_VERIFICATION")
 # Fields are self-reported by uploaders. Never infer primary source authenticity.
 out["issues"].append("EXTRACTED_FILE_FIELDS_NOT_INDEPENDENT_PRIMARY_SOURCE_VERIFICATION")
 return out
def wiki_shard(queue,shard,shards,out):
 rows=load(queue)
 if len(rows)!=N or len({r["source_identity"] for r in rows})!=N:
  raise ValueError("Truncated source queue")
 selected=rows[shard::shards]
 ids=[r["source_identity"].split(":")[1] for r in selected if r["source_identity"].startswith("commons:")]
 pages={};errors={}
 for i in range(0,len(ids),10):
  group=ids[i:i+10]
  try:pages.update(query_wikitext(group))
  except (ValueError,RuntimeError,OSError) as ex:
   for item in group:errors[item]=str(ex)[:150]
  if i+10<len(ids):time.sleep(2.5)
 found=[review_wiki(r,pages.get(r["source_identity"].split(":")[1]),
                  errors.get(r["source_identity"].split(":")[1])) for r in selected]
 save(Path(out)/("wiki_%02d.json"%shard),{"shard":shard,"shards":shards,
    "count":len(found),"records":found,"approved":0})
 print(json.dumps({"shard":shard,"count":len(found),
   "wiki_checked":sum(r["wiki_checked"] for r in found)},ensure_ascii=False),flush=True)
def reconcile(queue,folder,out,shards):
 src=load(queue)
 ids={r["source_identity"] for r in src}
 if len(src)!=N or len(ids)!=N:raise ValueError("Invalid target source set")
 seen={}
 for i in range(shards):
  obj=load(Path(folder)/("wiki_%02d.json"%i))
  if obj["shard"]!=i or obj["shards"]!=shards or obj["approved"]!=0 or obj["count"]!=len(obj["records"]):
   raise ValueError("Inconsistent shard")
  for row in obj["records"]:
   k=row["source_identity"]
   if k in seen or row.get("commercially_approved") is not False:raise ValueError("Unsafe or duplicate record")
   seen[k]=row
 if set(seen)!=ids:raise ValueError("Missing source identities")
 summary={"total":N,"commons_wiki_pages_checked":sum(r["wiki_checked"] for r in seen.values()),
  "source_field_present_in_wikitext":sum(r["wiki_checked"] and r["source_field"]!="NOT_EXTRACTED_FROM_WIKI" for r in seen.values()),
  "author_field_present_in_wikitext":sum(r["wiki_checked"] and r["author_field"]!="NOT_EXTRACTED_FROM_WIKI" for r in seen.values()),
  "missing_wikitext_or_page":sum(r["source_identity"].startswith("commons:") and not r["wiki_checked"] for r in seen.values()),
  "commercially_approved":0,"runtime_imported":0,"release_ready":0,
  "publication_gate":"CLOSED"}
 save(Path(out)/"wiki_486_summary.json",summary)
 save(Path(out)/"wiki_486_evidence.json",[seen[k] for k in sorted(seen)])
 print(json.dumps(summary,ensure_ascii=False),flush=True)
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--action",choices=("prepare","wiki","reconcile"),required=True)
 p.add_argument("--rights",type=Path);p.add_argument("--pixels",type=Path)
 p.add_argument("--root",type=Path);p.add_argument("--queue",type=Path)
 p.add_argument("--shard",type=int);p.add_argument("--shards",type=int,default=4)
 p.add_argument("--wiki-dir",type=Path);p.add_argument("--out",type=Path,required=True)
 a=p.parse_args()
 if a.action=="prepare":prepare(a.rights,a.pixels,a.root,a.out)
 elif a.action=="wiki":
  if a.shard is None or not 0<=a.shard<a.shards:p.error("Invalid --shard")
  wiki_shard(a.queue,a.shard,a.shards,a.out)
 else:reconcile(a.queue,a.wiki_dir,a.out,a.shards)
if __name__=="__main__":main()
