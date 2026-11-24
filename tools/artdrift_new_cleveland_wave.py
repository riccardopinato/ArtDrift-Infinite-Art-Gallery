#!/usr/bin/env python3
"""Acquire a bounded NEW CC0 Cleveland painting candidate wave from official API.
Produces provenance metadata only, all HOLD; no image downloads or D1 writes.
"""
import argparse,html,json,re,sys,time
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlencode,urlparse
from urllib.request import Request,urlopen
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"cloudflare/art-catalog/scripts"))
from make_museum_d1_import import SOURCES

API="https://openaccess-api.clevelandart.org/api/artworks/"
POLICY="https://www.clevelandart.org/open-access"
TERMS=("landscape","still life","seascape","flowers","abstract","garden")
HOSTS={"openaccess-cdn.clevelandart.org","www.clevelandart.org","clevelandart.org"}

def safe_image(value):
    if not isinstance(value,str):return ""
    p=urlparse(value)
    return value if p.scheme=="https" and p.hostname in HOSTS and not p.username and not p.password and p.port in (None,443) else ""

def clean(value,max_length=280):
    return re.sub(r"\s+"," ",html.unescape(str(value or "")).replace("<em>","").replace("</em>","")).strip()[:max_length]

def candidate(item):
    if not isinstance(item,dict) or item.get("share_license_status")!="CC0":return None
    if clean(item.get("type")).lower()!="painting":return None
    try: ident=int(item["id"])
    except (KeyError,ValueError,TypeError):return None
    if ident<=0:return None
    images=item.get("images") or {}
    if not isinstance(images,dict):return None
    web=images.get("web") or {}
    if not isinstance(web,dict):return None
    url=safe_image(web.get("url"))
    if not url:return None
    high=images.get("print") or {}
    full=safe_image(high.get("url")) if isinstance(high,dict) else ""
    title=clean(item.get("title"))
    if not title:return None
    creators=item.get("creators") or []
    names=[clean(x.get("description") or x.get("name")) for x in creators if isinstance(x,dict)]
    author="; ".join(x for x in names[:3] if x)
    accession=clean(item.get("accession_number"),70)
    if not re.fullmatch(r"[0-9A-Za-z][0-9A-Za-z.-]{0,65}",accession):accession=""
    page="https://www.clevelandart.org/art/"+accession if accession else API+str(ident)
    return {
        "provider":"cleveland","native_id":str(ident),
        "museum":"The Cleveland Museum of Art",
        "title":title,"artist":author,
        "date":clean(item.get("creation_date"),95),
        "medium":clean(item.get("technique"),140),
        "object_type":"Painting",
        "source_url":page,"source_api_url":API+str(ident),
        "image_preview_candidate":url,"image_print_candidate":full,
        "source_share_license_status":"CC0",
        "rights_evidence_url":POLICY,
        "publication_status":"HOLD",
        "rights_status":"IMAGE_REVIEW",
        "flags":["UNDERLYING_WORK_COPYRIGHT_REVIEW_PENDING","IMAGE_SOURCE_DELIVERY_NOT_VERIFIED"],
    }

def existing_ids(root):
    ids=set()
    for path in SOURCES:
        for item in json.loads((root/path).read_text(encoding="utf8")):
            if item.get("museum_source")=="cleveland":
                ids.add(str(item.get("museum_native_id") or item.get("id")))
    return ids

def discover(root,max_works=100,limit=60,requests_per_term=2,timeout=14):
    if not 1<=max_works<=100 or not 10<=limit<=100 or requests_per_term not in (1,2):
        raise ValueError("Unbounded source discovery")
    existing=existing_ids(root)
    found={}
    scanned=0
    blocked=CounterLike()
    errors=[]
    requests=0
    for term in TERMS:
        for page in range(requests_per_term):
            if len(found)>=max_works:break
            query=urlencode({"q":term,"skip":page*limit,"limit":limit,"has_image":1,"type":"Painting"})
            uri=API+"?cc0&"+query
            requests+=1
            try:
                req=Request(uri,headers={"Accept":"application/json","User-Agent":"ArtDrift-OpenAccessResearch/1.0"})
                with urlopen(req,timeout=timeout) as response:
                    payload=response.read(4_000_001)
                    if len(payload)>4_000_000:raise ValueError("Unbounded response")
                doc=json.loads(payload)
                if not isinstance(doc,dict) or not isinstance(doc.get("data"),list):
                    raise ValueError("Missing source data array")
                items=doc["data"]
            except Exception as e:
                errors.append({"term":term,"page":page,"error_type":type(e).__name__})
                continue
            for item in items:
                scanned+=1
                obj=candidate(item)
                if obj is None:
                    blocked.add("source_rights_type_or_url")
                    continue
                if obj["native_id"] in existing:
                    blocked.add("already_in_5085")
                    continue
                found.setdefault(obj["native_id"],obj)
                if len(found)>=max_works:break
            time.sleep(0.6)
        if len(found)>=max_works:break
    result=list(found.values())
    result.sort(key=lambda row:int(row["native_id"]))
    status="NEW_HOLD_CANDIDATES" if result else "NO_CANDIDATES_OR_SOURCE_UNAVAILABLE"
    report={
        "source":API,"policy":POLICY,"checked_utc":datetime.now(timezone.utc).isoformat(),
        "status":status,"requests":requests,"records_scanned":scanned,
        "new_unique_candidates":len(result),
        "existing_catalog_native_ids_excluded":len(existing),
        "source_rejections":blocked.as_dict(),"errors":errors,
        "auto_approved":0,"auto_published":0,"d1_writes":0,
        "images_downloaded":0,"canvas_works_enabled":0,
        "candidate_licensing":"source_share_license_status=CC0, underlying artwork and delivery still REVIEW",
    }
    return report,result

class CounterLike:
    def __init__(self):self.data={}
    def add(self,key):self.data[key]=self.data.get(key,0)+1
    def as_dict(self):return dict(sorted(self.data.items()))

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1])
    p.add_argument("--out",type=Path,default=Path("build/artdrift-new-waves"))
    p.add_argument("--max-works",type=int,default=100)
    a=p.parse_args()
    report,items=discover(a.root,max_works=a.max_works)
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"report.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    (a.out/"cleveland-new-HOLD.json").write_text(json.dumps(items,indent=2,ensure_ascii=False)+"\n")
    print("CLEVELAND_NEW_SOURCE_RESEARCH",report["status"],len(items),"REQUESTS",report["requests"])
    if not items:raise SystemExit("No verified candidates from live source; review API/network errors")

if __name__=="__main__":main()
