#!/usr/bin/env python3
"""Remove globally unreachable AIC previews; replace from official CMA CC0.

The 72 ORIGINAL AIC images remain safely bundled offline. This affects only
metadata-only global records with 7/7 observed HTTP 403 in live preview QA.
No commercial images without per-record rights, no developer API keys.
"""
import hashlib, json, time, urllib.request, urllib.parse, urllib.error
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/"assets/museums/catalog_global.json"
REPORT=ROOT/"assets/museums/global_report.json"
PINNED=ROOT/"assets/museums/catalog.json"
AIC_ORIGINAL=ROOT/"assets/gallery/catalog.json"
TARGET_TOTAL=4500
MAX_METADATA_BYTES=7_500_000
URL="https://openaccess-api.clevelandart.org/api/artworks/"
RIGHTS_URL="https://www.clevelandart.org/open-access"

def text(v):
    return v.strip() if isinstance(v,str) else ""

def json_get(url):
    req=urllib.request.Request(url,headers={
       "Accept":"application/json",
       "User-Agent":"ArtDrift-Global-Catalog/1.1 (rights-filtered metadata expansion)"
    })
    with urllib.request.urlopen(req,timeout=24) as r:
        if r.status!=200:raise ValueError("API http failure")
        b=r.read(9_000_001)
        if len(b)>9_000_000:raise ValueError("API page too large")
        return json.loads(b)

def one(row):
    if not isinstance(row,dict):return None
    if text(row.get("share_license_status")).upper()!="CC0":return None
    if "paint" not in text(row.get("type")).lower():return None
    try:
        native=int(row.get("id"))
        if native<1 or native>=950_000_000:return None
    except (ValueError,TypeError):return None
    title=text(row.get("title"))
    if not title:return None
    images=row.get("images") or {}
    if not isinstance(images,dict):return None
    web=images.get("web") or {}
    if not isinstance(web,dict):return None
    url=text(web.get("url"))
    try:
        parsed=urllib.parse.urlparse(url)
        if parsed.scheme!="https" or parsed.hostname!="openaccess-cdn.clevelandart.org" or parsed.username or parsed.password or parsed.port not in (None,443):
            return None
    except (TypeError,ValueError):return None
    creators=row.get("creators") or []
    author=next((text(x.get("description")) for x in creators
                if isinstance(x,dict) and text(x.get("description"))),"")
    keywords=row.get("keywords") or []
    tags=[x if isinstance(x,str) else text(x.get("name")) for x in keywords
          if isinstance(x,(str,dict))]
    mm=row.get("measurements") or ""
    measurements=str(mm)[:120] if mm else ""
    link=text(row.get("url"))
    if link and not link.startswith("https://www.clevelandart.org/"):
        link="https://www.clevelandart.org/"
    return {
      "id":20_000_000+native,"museum_native_id":str(native),
      "museum_source":"cleveland","museum_name":"Cleveland Museum of Art",
      "title":title[:230],"artist_title":author[:190],
      "date_display":text(row.get("creation_date"))[:80],
      "image_id":"","is_public_domain":True,"rights_license":"CC0",
      "rights_evidence_url":RIGHTS_URL,"artwork_type_title":"Painting",
      "medium_display":text(row.get("technique"))[:160],
      "dimensions_display":measurements,"place_of_origin":text(row.get("culture"))[:125],
      "credit_line":text(row.get("creditline"))[:180],
      "remote_preview_url":url,"remote_full_url":"",
      "remote_museum_url":link or "https://www.clevelandart.org/",
      "subject_terms":[text(t)[:70] for t in tags if text(t)][:12],
      "content_revision":"2026-11-21",
    }

def main():
    original=json.loads(DEST.read_text(encoding="utf-8"))
    pinned=json.loads(PINNED.read_text(encoding="utf-8"))
    aic=json.loads(AIC_ORIGINAL.read_text(encoding="utf-8"))
    existing=len(pinned)+len(aic)
    # Remove ONLY unbundled AIC remote IIIF, not approved 72 offline images.
    keep=[row for row in original if row.get("museum_source")!="aic"]
    removed=len(original)-len(keep)
    assert removed==0 or removed>=500, f"Unexpected AIC count: {removed}"
    keys={(x.get("museum_source","aic"),str(x.get("museum_native_id",x.get("id"))))
          for x in keep+pinned+aic}
    gained=0
    sourcepages=0
    # CMA Open Access API pages are independent; obey rate caps.
    for offset in range(1500,5400,300):
        if len(keep)+existing>=TARGET_TOTAL:break
        try:
            query=URL+"?"+urllib.parse.urlencode({
                 "q":"painting","cc0":"1","has_image":"1","limit":"300","skip":str(offset)})
            data=json_get(query)
            response=data.get("data") or []
            if not isinstance(response,list):continue
            sourcepages+=1
            for row in response:
                art=one(row)
                if not art:continue
                key=(art["museum_source"],art["museum_native_id"])
                if key in keys:continue
                keys.add(key)
                keep.append(art);gained+=1
                if len(keep)+existing>=TARGET_TOTAL:break
            print("CMA_ADDED",offset,gained,"total",len(keep)+existing,flush=True)
        except Exception as e:
            print("CMA_PAGE_HELD",offset,type(e).__name__,str(e)[:130],flush=True)
        time.sleep(.35)
    # Loss-free, source-distinct stable sorting; bring sources into every
    # 9-item content window via source rotation instead of ordering by CMA.
    bymuseum={}
    for item in keep:
        bymuseum.setdefault(item["museum_name"],[]).append(item)
    for rows in bymuseum.values():
        rows.sort(key=lambda item:hashlib.sha256(str(item["id"]).encode()).hexdigest())
    names=sorted(bymuseum)
    interleaved=[]
    for i in range(max(len(x) for x in bymuseum.values())):
        for name in names:
            rows=bymuseum[name]
            if i<len(rows):interleaved.append(rows[i])
    if len(interleaved)+existing<4300:
        raise SystemExit(f"FAIL CLOSED insufficient reliably displayable corpus {len(interleaved)+existing}")
    assert len({(x["museum_source"],x["museum_native_id"]) for x in interleaved})==len(interleaved)
    assert not any(x["museum_source"]=="aic" for x in interleaved)
    raw=json.dumps(interleaved,ensure_ascii=False,separators=(",",":")).encode("utf-8")+b"\n"
    if len(raw)>MAX_METADATA_BYTES:raise SystemExit("catalog metadata exceeded budget")
    DEST.write_bytes(raw)
    oldreport=json.loads(REPORT.read_text(encoding="utf-8"))
    counts={}
    for item in interleaved:
        counts[item["museum_name"]]=counts.get(item["museum_name"],0)+1
    report={**oldreport,
       "records_global":len(interleaved),
       "records_total":len(interleaved)+existing,
       "catalog_bytes":len(raw),
       "institutions":counts,
       "removed_unreachable_aic_remote":removed+oldreport.get("removed_unreachable_aic_remote",0),
       "replacement_cma_cc0_added":gained+oldreport.get("replacement_cma_cc0_added",0),
       "replacement_cma_pages_checked":sourcepages+oldreport.get("replacement_cma_pages_checked",0),
       "remote_images_only":len(interleaved),
       "remote_preview_sample_gate":"AIC remote 7/7 HTTP403 excluded; 8 other institution groups 56/56 pass",
       "original_aic_offline_preserved":len(aic),
       "image_qa":"sample of image HTTP 200 only; device and complete corpus QA open",
    }
    REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("GLOBAL_SANITIZE_SUCCESS",json.dumps(report,ensure_ascii=False),flush=True)

if __name__=="__main__":main()

# Observed 2026-11-21 source-image QA: eight non-AIC groups 56/56 passed.
