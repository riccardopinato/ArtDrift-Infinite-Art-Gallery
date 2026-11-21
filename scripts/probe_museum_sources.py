#!/usr/bin/env python3
"""Read-only museum source schema probe; no artwork downloads or credentials."""
import urllib.request
import urllib.parse
import json

def read(url, extra=None):
    headers={"User-Agent":"ArtDrift-Museum-SchemaProbe/0.1","Accept":"application/ld+json, application/json, application/xml, */*"}
    if extra: headers.update(extra)
    try:
        with urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=14) as r:
            data=r.read(4000)
            print("URL",url,"STATUS",r.status,"CT",r.headers.get("Content-Type"),
                  "LENGTH",r.headers.get("Content-Length"),"PREFIX",repr(data[:220]),flush=True)
            try:
                obj=json.loads(data)
                print("JSON KEYS",list(obj)[:20],flush=True)
            except Exception:pass
    except Exception as e:print("ERROR",url,type(e).__name__,str(e)[:160],flush=True)

read("https://data.rijksmuseum.nl/200107928?_profile=la-framed")
read("https://data.rijksmuseum.nl/200107928?_profile=edm")
read("https://data.rijksmuseum.nl/202107928?_profile=la-framed")
read("https://data.rijksmuseum.nl/500711199912110510799100?_profile=la-framed")
read("https://data.rijksmuseum.nl/search/collection?type=painting&imageAvailable=true")
read("https://raw.githubusercontent.com/NationalGalleryOfArt/opendata/main/data/objects.csv")
read("https://raw.githubusercontent.com/NationalGalleryOfArt/opendata/main/data/published_images.csv")
read("https://data.getty.edu/museum/collection/object/c88b3df0-de91-4f5b-a9ef-7b2b9a6d8abb")
read("https://smithsonian-open-access.s3-us-west-2.amazonaws.com/metadata/edan/saam/00.txt")
