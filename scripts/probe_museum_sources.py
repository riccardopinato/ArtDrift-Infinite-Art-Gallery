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

# Structured, read-only diagnostics on API responses with no secrets.
import xml.etree.ElementTree as ET
for profile in ("edm", "la-framed"):
    url="https://data.rijksmuseum.nl/200107928?_profile="+profile
    try:
        with urllib.request.urlopen(urllib.request.Request(url,headers={
           "User-Agent":"ArtDrift museum rights audit","Accept":"application/ld+json, application/rdf+xml, */*"}),timeout=15) as r:
            raw=r.read(250000)
        if profile=="edm":
            doc=ET.fromstring(raw)
            matches=[]
            for elt in doc.iter():
                if "rights" in elt.tag.lower() or "license" in elt.tag.lower():
                    matches.append((elt.tag,elt.text,elt.attrib))
            print("RIJKS_EDM_RIGHTS",repr(matches[:14]),flush=True)
        else:
            record=json.loads(raw)
            print("RIJKS_LA_KEYS",list(record.keys()),flush=True)
            print("RIJKS_LA_TITLE",repr(record.get("_label")),flush=True)
            print("RIJKS_LA_SHOWS",repr(record.get("shows",[])[:1]),flush=True)
            print("RIJKS_LA_PRODUCTION",repr(record.get("produced_by",{}))[:700],flush=True)
    except Exception as ex:
        print("RIJKS_AUDIT_ERROR",profile,type(ex).__name__,str(ex)[:180],flush=True)
try:
    data=urllib.request.urlopen("https://smithsonian-open-access.s3-us-west-2.amazonaws.com/metadata/edan/saam/00.txt",timeout=15).read(500000)
    rows=[json.loads(line) for line in data.splitlines() if line.strip()]
    print("SMITHSONIAN_ROWS",len(rows),flush=True)
    for record in rows[:2]:
        print("SI_KEYS",list(record.keys()),flush=True)
        print("SI_CONTENT_KEYS",list(record.get("content",{}).keys()),flush=True)
        print("SI_RIGHTS",repr(record.get("content",{}).get("descriptiveNonRepeating",{}))[:750],flush=True)
        print("SI_FREETEXT",repr(record.get("content",{}).get("freetext",{}))[:900],flush=True)
        print("SI_MEDIA",repr(record.get("content",{}).get("descriptiveNonRepeating",{}).get("online_media",{}))[:900],flush=True)
except Exception as ex:
    print("SI_AUDIT_ERROR",type(ex).__name__,str(ex)[:170],flush=True)
