#!/usr/bin/env python3
"""Bounded Smithsonian Open Access SAAM/NPG/FSG CC0 modern paintings probe."""
import gzip
import json
import re
from urllib.request import urlopen, Request
from collections import Counter
from urllib.parse import urlparse

BASE="https://smithsonian-open-access.s3-us-west-2.amazonaws.com/metadata/edan/"
P=re.compile(r"(?<!\d)(?:1[0-9]{3}|20[0-9]{2})(?!\d)")
def extracts(freetext, field):
    return [str(x.get("content","")) for x in (freetext.get(field) or []) if isinstance(x,dict)]
def year(date):
    matches=[int(x) for x in P.findall(date)]
    if not matches:return None
    return min(matches) if min(matches)>=1950 and max(matches)<=2026 else None
for museum in ("saam","npg","fsg"):
    for shard in (0,1):
        url=f"{BASE}{museum}/{shard:02x}.txt"
        try:
            req=Request(url,headers={"User-Agent":"ArtDrift-CC0-Modern-Catalog/1.0"})
            with urlopen(req,timeout=25) as response:
                data=response.read(9_000_000)
            rights=cc0=years=modern=0
            kinds=Counter()
            examples=[]
            for line in data.splitlines():
                try: x=json.loads(line)
                except Exception:continue
                c=x.get("content") or {}
                det=c.get("descriptiveNonRepeating") or {}
                ft=c.get("freetext") or {}
                rights+=(det.get("metadata_usage") or {}).get("access")=="CC0"
                usable=False
                for item in (det.get("online_media") or {}).get("media") or []:
                    if not isinstance(item,dict) or (item.get("usage") or {}).get("access")!="CC0":continue
                    uri=str(item.get("thumbnail") or item.get("content") or "")
                    if urlparse(uri).hostname=="ids.si.edu":
                        usable=True
                        break
                if not usable:continue
                cc0+=1
                dates=extracts(ft,"date")
                values=[year(d) for d in dates]
                valid=[v for v in values if v is not None]
                if not valid:continue
                years+=1
                types=extracts(ft,"objectType")
                kind=" | ".join(types[:2])
                kinds[kind[:75]]+=1
                if any(term in kind.lower() for term in ("paint","draw","print","photo","sculpt","ceramic","textile","poster","design","collage","mixed media","assemblage","graphic","installation")):
                    modern+=1
                    if len(examples)<5:
                        examples.append({"year":min(valid),"type":kind[:65],"cc0":True})
            print("SMITHSONIAN_PROBE",museum,shard,json.dumps({"records":len(data.splitlines()),"metadata_cc0":rights,"media_cc0":cc0,"dated_1950":years,"eligible_modern":modern,"types":dict(kinds.most_common(8)),"examples":examples}),flush=True)
        except Exception as e:
            print("SMITHSONIAN_PROBE_ERROR",museum,shard,type(e).__name__,str(e)[:150],flush=True)
