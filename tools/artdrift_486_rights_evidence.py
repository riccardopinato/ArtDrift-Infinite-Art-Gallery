#!/usr/bin/env python3
"""Per-file live rights evidence for 486 Art Drift candidate images. Research only."""
import argparse,collections,csv,html,json,re,time,urllib.error,urllib.parse,urllib.request
from datetime import datetime,timezone
from pathlib import Path
N=486
PIN="b82a4574db3d504141b6d2e95e403aa743c771e3"
DEATH={"serhii_vasylkivskyi":1917,"otto_modersohn":1943,
"claude_monet":1926,"gustave_caillebotte":1894,"ludvig_karsten":1926,
"alfred_sisley":1899,"harald_sohlberg":1935}
NAMES={"serhii_vasylkivskyi":["vasylkiv","vasilkov","васильків"],
"otto_modersohn":["modersohn"],"claude_monet":["monet"],
"gustave_caillebotte":["caillebotte"],"ludvig_karsten":["karsten"],
"alfred_sisley":["sisley"],"harald_sohlberg":["sohlberg"]}
SPECIAL="staedel:DE-MUS-048017/lido/1350"
STAED="https://sammlung.staedelmuseum.de/en/work/bank-of-the-seine-in-autumn"
API="https://commons.wikimedia.org/w/api.php"
def clean(x):
    return re.sub(r"\s+"," ",html.unescape(re.sub(r"<[^>]*>"," ",str(x or "")))).strip()[:850]
def cl(s):
    t=clean(s).lower()
    if any(v in t for v in ("noncommercial","non-commercial","by-nc","by nc")):return "NO_COMMERCIAL"
    if any(v in t for v in ("noderivatives","no-derivatives","by-nd","by nd")):return "NO_DERIVATIVES"
    if "cc0" in t:return "CC0"
    if any(v in t for v in ("cc by-sa","cc by sa","attribution-sharealike","attribution share alike")):return "CC_BY_SA"
    if any(v in t for v in ("cc by ","cc by-","attribution 4.0","attribution 3.0","attribution 2.0")):return "CC_BY"
    if any(v in t for v in ("public domain","no restrictions","pdm","pd-old")):return "PUBLIC_DOMAIN"
    return "UNKNOWN"
def inputs(q,s):
    a=json.loads(q.read_text(encoding="utf-8"))["complete_queue"]
    b=json.loads(s.read_text(encoding="utf-8"))["priority_shortlist"]
    names={x["identity"]:x for x in b}
    if len(a)!=N or len(b)!=N or len(names)!=N or len({x["source_identity"] for x in a})!=N:
        raise ValueError("Incomplete 486-image inventory")
    if set(names)!={x["source_identity"] for x in a}:raise ValueError("Unreconciled sources")
    for x in a:
        if not re.fullmatch(r"(?:commons:\d+|staedel:DE-MUS-048017/lido/1350)",x["source_identity"]):
            raise ValueError("Unknown ID")
        if x["artist_id"] not in DEATH or x.get("commercially_approved") is not False or x.get("runtime_visible") is not False:raise ValueError("Unsafe input")
    return a,names
def field(meta,k):
    obj=meta.get(k,{}) if isinstance(meta,dict) else {}
    return clean(obj.get("value","") if isinstance(obj,dict) else obj)
def live_query(ids):
    if not ids or len(ids)>25 or any(not re.fullmatch(r"\d+",str(x)) for x in ids):
        raise ValueError("Invalid batch")
    q=urllib.parse.urlencode({"action":"query","format":"json","formatversion":2,
        "prop":"imageinfo","iiprop":"extmetadata|url|size|sha1",
        "pageids":"|".join(ids),"maxlag":5})
    req=urllib.request.Request(API+"?"+q,headers={
        "User-Agent":"ArtDriftRightsEvidenceAudit/1.0 (github.com/riccardopinato/ArtDrift-Infinite-Art-Gallery)",
        "Accept":"application/json"})
    last="NO_RESPONSE"
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req,timeout=25) as resp:
                dest=urllib.parse.urlsplit(resp.geturl())
                if dest.scheme!="https" or dest.hostname!="commons.wikimedia.org":raise RuntimeError("REDIRECT_DOMAIN")
                if "json" not in resp.headers.get("Content-Type",""):raise RuntimeError("BAD_CONTENT_TYPE")
                raw=resp.read(3_000_000)
            obj=json.loads(raw)
            if obj.get("error"):raise RuntimeError("MW_"+str(obj["error"].get("code","ERROR")))
            pages=obj.get("query",{}).get("pages")
            if not isinstance(pages,list):raise RuntimeError("INVALID_RESPONSE")
            return {str(p["pageid"]):p for p in pages if p.get("pageid") is not None}
        except urllib.error.HTTPError as ex:
            last="HTTP_"+str(ex.code)
            if ex.code not in (429,500,502,503,504):break
        except (urllib.error.URLError,RuntimeError,ValueError,TimeoutError,OSError) as ex:
            last=type(ex).__name__+":"+str(ex)[:100]
        if attempt<2:time.sleep(3+attempt*7)
    raise RuntimeError(last)
def inspect(x,src,page=None,error=None):
    k=x["source_identity"]; aid=x["artist_id"]
    r={"source_identity":k,"artist_id":aid,"title":x.get("title"),
        "original_record_url":x.get("record_url"),
        "source_license_claim":x.get("image_license_claim"),
        "source_license_class":cl(x.get("image_license_claim")),
        "painter_death_year":DEATH[aid],
        "underlying_artwork_eu_70y_term":"LIKELY_EXPIRED_IF_AUTHORSHIP_CONFIRMED",
        "other_territories":"HOLD","live_checked":False,
        "license_issues":[],"reuse_requirements":[],"licence_mismatch":False,
        "commercially_approved":False,"runtime_visible":False,
        "publication_gate":"HOLD","evidence_tier":"NO_LIVE_FILE_EVIDENCE"}
    flags=r["license_issues"]
    if k==SPECIAL:
        r.update({"evidence_tier":"OFFICIAL_MUSEUM_OBJECT_PD_LICENSE_CONFLICT",
           "source_page":STAED,"museum_inventory":"1350",
           "museum_author":"Alfred Sisley","museum_picture_copyright":"Public Domain",
           "licence_mismatch":True})
        flags.extend(["UPSTREAM_CC_BY_SA_VS_MUSEUM_PD","FILE_DERIVATIVE_AND_PROVIDER_TERMS_REVIEW","TERRITORIAL_REVIEW"])
        return r
    r["source_page"]="https://commons.wikimedia.org/w/index.php?curid="+k.split(":")[1]
    if error:
        r["live_error"]=error;r["evidence_tier"]="LIVE_QUERY_FAILED";flags.append("LIVE_FILE_PAGE_UNAVAILABLE")
        return r
    if not page or page.get("missing") or page.get("invalid"):
        r["evidence_tier"]="FILE_PAGE_UNAVAILABLE";flags.append("FILE_PAGE_MISSING")
        return r
    if page.get("ns")!=6 or not page.get("title","").startswith("File:"):
        r["evidence_tier"]="NOT_A_FILE_PAGE";flags.append("NOT_A_FILE_PAGE")
        return r
    ii=(page.get("imageinfo") or [])
    if not ii:
        r["evidence_tier"]="NO_FILE_IMAGE_INFO";flags.append("NO_FILE_IMAGE_INFO")
        return r
    i=ii[0]; m=i.get("extmetadata") or {}
    r["live_checked"]=True
    r["evidence_tier"]="LIVE_FILE_METADATA_REVIEWED"
    r["source_page"]=i.get("descriptionurl") or r["source_page"]
    r["file_page_title"]=page["title"]
    r["file_sha1_live"]=i.get("sha1")
    r["file_sha1_previous"]=src.get("image_file_sha1")
    r["license_live"]=field(m,"LicenseShortName")
    r["license_url"]=field(m,"LicenseUrl")
    r["usage_terms"]=field(m,"UsageTerms")
    r["artist_credit"]=field(m,"Artist")
    r["photographic_credit"]=field(m,"Credit")
    r["source_field"]=field(m,"Source")
    r["attribution"]=field(m,"Attribution")
    r["restrictions"]=field(m,"Restrictions")
    r["attribution_required"]=field(m,"AttributionRequired")
    r["copyrighted_flag"]=field(m,"Copyrighted")
    r["license_class_live"]=cl(r["license_live"] or r["usage_terms"] or r["license_url"])
    l=r["license_class_live"];s=r["source_license_class"]
    if l!=s and {l,s}!={"PUBLIC_DOMAIN","CC0"}:
        r["licence_mismatch"]=True;flags.append("SOURCE_VS_LIVE_LICENSE_MISMATCH")
    if r["file_sha1_previous"] and r["file_sha1_live"] and r["file_sha1_previous"]!=r["file_sha1_live"]:
        flags.append("FILE_SHA1_CHANGED_SINCE_DISCOVERY")
    if not r["source_field"]:flags.append("ORIGINAL_FILE_SOURCE_FIELD_MISSING")
    r["painter_matched_in_artist_credit"]=any(n in
        (r["artist_credit"]+" "+r["photographic_credit"]).lower() for n in NAMES[aid])
    if not r["painter_matched_in_artist_credit"]:flags.append("PAINTER_ATTRIBUTION_NOT_EVIDENCED")
    if r["restrictions"]:flags.append("ADDITIONAL_FILE_RESTRICTIONS_RECORDED")
    if l=="NO_COMMERCIAL":
        r["evidence_tier"]="COMMERCIAL_USE_DISALLOWED_BY_LICENSE";flags.append("REJECT_COMMERCIAL")
    elif l in ("NO_DERIVATIVES","UNKNOWN"):
        r["evidence_tier"]="LICENSE_INSUFFICIENT_OR_RESTRICTED";flags.append("LICENSE_REQUIRES_MANUAL_REVIEW")
    elif l in ("CC_BY","CC_BY_SA"):
        r["evidence_tier"]="CONDITIONAL_CC_LICENSE_SOURCE_CONFIRMED"
        r["reuse_requirements"]=["ATTRIBUTION","LICENSE_URL","CREDIT_ORIGINAL_SOURCE","MARK_MODIFICATIONS"]
        if l=="CC_BY_SA":r["reuse_requirements"].append("SHAREALIKE_WHEN_APPLICABLE")
        if not (r["artist_credit"] or r["photographic_credit"] or r["attribution"]):
            flags.append("ATTRIBUTION_CREDIT_MISSING")
    elif l in ("PUBLIC_DOMAIN","CC0"):
        r["evidence_tier"]="LIVE_PD_CC0_CLAIM_TO_REVIEW"
        r["reuse_requirements"]=["IDENTIFY_WORK_AUTHOR_AND_SOURCE","CHECK_DIGITAL_REPRODUCTION_RIGHTS"]
    flags.extend(["WORK_AND_IMAGE_PROVENANCE","TERRITORY_AND_PROVIDER_TERMS"])
    return r
def shard_run(rows,sources,shard,nshards,out):
    subset=rows[shard::nshards];ids=[x["source_identity"].split(":")[1]
         for x in subset if x["source_identity"].startswith("commons:")]
    pages={};errors={}
    for off in range(0,len(ids),25):
        chunk=ids[off:off+25]
        try:pages.update(live_query(chunk))
        except (RuntimeError,ValueError,OSError) as ex:
            for x in chunk:errors[x]=str(ex)[:150]
        if off+25<len(ids):time.sleep(2.5)
    results=[inspect(x,sources[x["source_identity"]],
           pages.get(x["source_identity"].split(":")[1]),
           errors.get(x["source_identity"].split(":")[1])) for x in subset]
    out.mkdir(parents=True,exist_ok=True)
    (out/("rights_%02d.json"%shard)).write_text(json.dumps({
        "shard":shard,"total_shards":nshards,"count":len(results),
        "pin":PIN,"commercially_approved":0,"records":results
    },ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"shard":shard,"records":len(results),
        "live_file_metadata":sum(x["live_checked"] for x in results),
        "tiers":dict(collections.Counter(x["evidence_tier"] for x in results))}),flush=True)
def aggregate(rows,folder,out,nshards):
    got=[];seen=set()
    for shard in range(nshards):
        z=json.loads((folder/("rights_%02d.json"%shard)).read_text(encoding="utf-8"))
        if z["shard"]!=shard or z["total_shards"]!=nshards or z["count"]!=len(z["records"]) or z["pin"]!=PIN:
            raise ValueError("Truncated or inconsistent shard")
        for r in z["records"]:
            k=r["source_identity"]
            if k in seen or r["commercially_approved"] is not False or r["runtime_visible"] is not False:
                raise ValueError("Duplicate or unsafe clearance")
            seen.add(k);got.append(r)
    if len(got)!=N or seen!={x["source_identity"] for x in rows}:
        raise ValueError("486-image rights audit missing source IDs")
    got.sort(key=lambda x:(x["artist_id"],x["source_identity"]))
    summary={"as_of_utc":datetime.now(timezone.utc).isoformat(),
        "source_revision":PIN,"images_checked":N,"live_file_metadata":sum(x["live_checked"] for x in got),
        "tiers":dict(collections.Counter(x["evidence_tier"] for x in got)),
        "initial_claims":dict(collections.Counter(x["source_license_class"] for x in got)),
        "live_licences":dict(collections.Counter(x.get("license_class_live","NOT_RETRIEVED") for x in got)),
        "risk_flags":dict(collections.Counter(y for x in got for y in x["license_issues"])),
        "artists":{a:{"total":sum(x["artist_id"]==a for x in got),
            "live_checked":sum(x["artist_id"]==a and x["live_checked"] for x in got)} for a in DEATH},
        "rights_cleared_unconditionally":0,"commercially_approved":0,"runtime_imported":0,
        "global_territorial_review":"HOLD","publication_gate":"CLOSED"}
    out.mkdir(parents=True,exist_ok=True)
    (out/"rights_486_summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (out/"rights_486_per_item.json").write_text(json.dumps(got,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    with (out/"rights_486_review.csv").open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f);w.writerow(["id","artist","title","page","claim","live_license","tier","issues","reuse_terms","released"])
        for x in got:w.writerow([x["source_identity"],x["artist_id"],x["title"],x.get("source_page"),
            x["source_license_claim"],x.get("license_live"),x["evidence_tier"],
            ";".join(x["license_issues"]),";".join(x["reuse_requirements"]),False])
    print(json.dumps(summary,ensure_ascii=False),flush=True)
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--inventory",required=True,type=Path);p.add_argument("--source",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path);p.add_argument("--shard",type=int)
    p.add_argument("--shards",type=int,default=4);p.add_argument("--aggregate",action="store_true")
    a=p.parse_args();rows,sources=inputs(a.inventory,a.source)
    if a.aggregate:aggregate(rows,a.output,a.output/"aggregate",a.shards)
    else:
        if a.shard is None or not 0<=a.shard<a.shards:p.error("Invalid --shard")
        shard_run(rows,sources,a.shard,a.shards,a.output)
if __name__=="__main__":main()
