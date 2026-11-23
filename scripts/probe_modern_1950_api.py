#!/usr/bin/env python3
"""Read-only, bounded probe of Cleveland Open Access filter semantics."""
from collections import Counter
import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen
BASE="https://openaccess-api.clevelandart.org/api/artworks/"
queries=[
    ("cc0_only",{"cc0":"1","has_image":"1"}),
    ("cc0_after_1949",{"cc0":"1","has_image":"1","created_after":"1949"}),
    ("cc0_after_1950",{"cc0":"1","has_image":"1","created_after":"1950"}),
    ("cc0_date_iso",{"cc0":"1","has_image":"1","created_after":"1950-01-01"}),
    ("cc0_keyword_1950",{"cc0":"1","has_image":"1","q":"1950"}),
    ("all_modern",{"has_image":"1","created_after":"1949"}),
    ("cc0_type_painting",{"cc0":"1","has_image":"1","type":"Painting"}),
    ("cc0_keyword_modern",{"cc0":"1","has_image":"1","q":"modern"}),
]
for label,opts in queries:
    uri=BASE+"?"+urlencode({**opts,"limit":"10","skip":"0"})
    try:
        req=Request(uri,headers={"User-Agent":"ArtDrift-CC0-Modern-Catalog/1.0", "Accept":"application/json"})
        with urlopen(req,timeout=15) as response:
            obj=json.load(response)
        rows=obj.get("data") or []
        types=Counter(str(q.get("type","")) for q in rows)
        samples=[{
          "year":str(q.get("creation_date",""))[:35],
          "type":str(q.get("type",""))[:60],
          "rights":str(q.get("share_license_status",""))[:30],
          "has_web_image":bool(((q.get("images") or {}).get("web") or {}).get("url")),
        } for q in rows[:5]]
        print("FILTER_PROBE",label,json.dumps({
          "total":(obj.get("info") or {}).get("total"),
          "returned":len(rows),"types":dict(types),
          "samples":samples,
        },ensure_ascii=False),flush=True)
    except Exception as exc:
        print("FILTER_PROBE_ERROR",label,type(exc).__name__,str(exc)[:80],flush=True)
