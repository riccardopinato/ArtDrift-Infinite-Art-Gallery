#!/usr/bin/env python3
"""Schema probes: museum-owned primary data only, no images downloaded."""
import json, urllib.request,urllib.parse
def get(url,limit=60000):
 try:
  req=urllib.request.Request(url,headers={"User-Agent":"ArtDrift-source-audit/1.0","Accept":"application/json,*/*"})
  with urllib.request.urlopen(req,timeout=20) as r:
   payload=r.read(limit)
   print("\nURL",url,"ct",r.headers.get("Content-Type"),"size",r.headers.get("Content-Length"),"bytes",len(payload),flush=True)
  try:
   ob=json.loads(payload)
   if isinstance(ob,dict):
    print("TOP KEYS",list(ob)[:40],flush=True)
    for k in ("items","data","records","hits","object","response","artworks","facets","total","pagination"):
     v=ob.get(k)
     if isinstance(v,dict):
      print("FIELD",k,"KEYS",list(v)[:20],flush=True)
      for sk in ("hits","results"):
       if isinstance(v.get(sk),list):print("SAMPLE",k+"."+sk,json.dumps(v[sk][0] if v[sk] else {},ensure_ascii=False)[:3500],flush=True)
     elif isinstance(v,list):print("SAMPLE",k,json.dumps(v[0] if v else {},ensure_ascii=False)[:3900],flush=True)
     elif v is not None:print("FIELD",k,str(v)[:250],flush=True)
   else:print("TYPE",type(ob).__name__,"SAMPLE",str(ob[:1])[:1300],flush=True)
  except Exception:print("PREFIX",repr(payload[:350]),flush=True)
 except Exception as ex:print("ERROR",url,type(ex).__name__,str(ex)[:160],flush=True)

get("https://api.smk.dk/api/v1/art/search/?"+urllib.parse.urlencode({"keys":"*","filters":"[public_domain:true],[has_image:true]","offset":"0","rows":"2"}),limit=120000)
get("https://api.smk.dk/api/v1/art/search/?"+urllib.parse.urlencode({"keys":"painting","offset":"0","rows":"2"}),limit=100000)
get("https://smithsonian-open-access.s3-us-west-2.amazonaws.com/metadata/edan/index.txt",limit=5500)
for unit in ("npg","fsg","nmafa"):
 get(f"https://smithsonian-open-access.s3-us-west-2.amazonaws.com/metadata/edan/{unit}/00.txt",limit=13000)
get("https://api.artsmia.org/objects/1",limit=3000)
get("https://api.artsmia.org/images/1/small.jpg",limit=1000)
get("https://data.rijksmuseum.nl/search/collection?type=painting&imageAvailable=true",limit=30000)
get("https://api.artic.edu/api/v1/artworks/search?"+urllib.parse.urlencode({
 "q":"painting","limit":"3","fields":"id,title,image_id,is_public_domain,artwork_type_title,artist_title,date_display,medium_display,place_of_origin,credit_line"}),limit=17000)
get("https://openaccess-api.clevelandart.org/api/artworks/?"+urllib.parse.urlencode({
 "q":"painting","cc0":"1","has_image":"1","limit":"2","skip":"0"}),limit=18000)

# 2026-11-21 official-source probe version 2.
