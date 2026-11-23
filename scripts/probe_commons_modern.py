#!/usr/bin/env python3
"""Read-only modern artwork availability/rights probe on Wikimedia Commons."""
import html
import json
import re
from urllib.parse import urlencode
from urllib.request import Request, urlopen
YEARS=(1950,1970,1990,2010,2020,2023,2025)
ENDPOINT="https://commons.wikimedia.org/w/api.php"
def clean(v):
    return re.sub('<[^>]+>',' ',html.unescape(str(v))).strip()[:100]
for yr in YEARS:
    params={
        "action":"query","format":"json","formatversion":"2",
        "generator":"categorymembers","gcmtitle":f"Category:{yr} paintings",
        "gcmtype":"file","gcmlimit":"25",
        "prop":"imageinfo","iiprop":"url|extmetadata|mime","iiurlwidth":"320"
    }
    try:
        req=Request(ENDPOINT+"?"+urlencode(params),headers={"User-Agent":"ArtDrift/0.3 (contact: independent openaccess research)", "Accept":"application/json"})
        with urlopen(req,timeout=25) as resp:
            data=json.load(resp)
        pages=data.get("query",{}).get("pages",[])
        out=[]
        for p in pages:
            imgs=p.get("imageinfo") or []
            if not imgs:continue
            v=imgs[0]
            meta=v.get("extmetadata") or {}
            def md(k):return clean((meta.get(k) or {}).get("value",""))
            out.append({"license":md("LicenseShortName"),"url":md("LicenseUrl"),"artist":md("Artist"),"credit":md("Credit"),"date":md("DateTimeOriginal"),"mime":v.get("mime"),"thumb":bool(v.get("thumburl"))})
        print("COMMONS_PROBE",yr,json.dumps({"returned":len(pages),"items":out[:12],"continued":bool(data.get("continue"))},ensure_ascii=False),flush=True)
    except Exception as e:
        print("COMMONS_PROBE_ERROR",yr,type(e).__name__,str(e)[:220],flush=True)
