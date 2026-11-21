#!/usr/bin/env python3
"""Smoke-test real museum preview delivery by official host, no bulk images.

Sampling only: successful metadata import does NOT prove all 3,915 remote
image URLs work on a physical Android device. Outputs bounded evidence.
"""
import json,random,urllib.request,urllib.parse,time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
from collections import defaultdict

path=Path("assets/museums/catalog_global.json")
rows=json.loads(path.read_text(encoding="utf-8"))
groups=defaultdict(list)
for obj in rows:groups[obj["museum_name"]].append(obj)
samples=[]
for name,art in sorted(groups.items()):
    rng=random.Random(name+"-artdrift-2026-11-21")
    sample=rng.sample(art,min(len(art),7))
    samples.extend(sample)
def probe(row):
    url=row["remote_preview_url"]
    req=urllib.request.Request(url,headers={
        "User-Agent":"ArtDrift/0.4 museum preview smoke check",
        "Accept":"image/jpeg,image/webp,image/*;q=0.8",
    })
    try:
        with urllib.request.urlopen(req,timeout=17) as resp:
            mime=resp.headers.get("Content-Type","")
            head=resp.read(600)
            good=resp.status==200 and mime.startswith("image/") and len(head)>=50
            return {"source":row["museum_name"],"id":row["id"],"status":resp.status,
               "mime":mime,"pass":good,"bytes_checked":len(head)}
    except Exception as e:
        return {"source":row["museum_name"],"id":row["id"],"pass":False,
            "error":type(e).__name__+": "+str(e)[:120]}
results=[]
with ThreadPoolExecutor(max_workers=5) as pool:
    futures=[pool.submit(probe,x) for x in samples]
    for f in as_completed(futures):
        out=f.result()
        results.append(out)
        print("IMAGE_PROBE",json.dumps(out,ensure_ascii=False),flush=True)
totals={}
for r in results:
    p=totals.setdefault(r["source"],{"pass":0,"fail":0})
    p["pass" if r["pass"] else "fail"]+=1
report={"samples":len(results),"passed":sum(x["pass"] for x in results),
    "failed":sum(not x["pass"] for x in results),"institutions":totals,
    "caveat":"Sample only, source runner network differs from Android; 3915 individual HTTP checks NOT performed"}
Path("global_image_preview_probe.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
print("IMAGE_PROBE_REPORT",json.dumps(report,ensure_ascii=False),flush=True)
