#!/usr/bin/env python3
"""Sample genuine European museum object metadata structures before bulk import."""
from __future__ import annotations
import json,re,urllib.error,urllib.parse,urllib.request,xml.etree.ElementTree as ET
from pathlib import Path
from tools.artdrift_eu_source_probe import SOURCES
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"research/museums/20261126/eu_sample_object_schemas.json"
def fetch(url,allowed,maxsize=700000):
    u=urllib.parse.urlsplit(url)
    if u.scheme!="https" or u.hostname not in allowed:raise ValueError("untrusted URL")
    req=urllib.request.Request(url,headers={"User-Agent":"ArtDrift-EU-Source-Schema/1.0","Accept":"application/json,application/xml"})
    with urllib.request.urlopen(req,timeout=25) as res:
        u=urllib.parse.urlsplit(res.url)
        if u.scheme!="https" or u.hostname not in allowed:raise ValueError("redirect off provider")
        d=res.read(maxsize+1)
        if len(d)>maxsize:raise ValueError("schema response over max bytes")
        return d
def sample_rijks():
    out={"source":"rijks"}
    try:
        raw=fetch(SOURCES["rijks"]["url"],{"data.rijksmuseum.nl"})
        j=json.loads(raw)
        ids=[x["id"] for x in j.get("orderedItems") or [] if re.fullmatch(r"https://id.rijksmuseum.nl/\d+",str(x.get("id") or ""))]
        out["list_total"]=j.get("partOf",{}).get("totalItems")
        for ident in ids[:2]:
            base=ident.replace("id.rijksmuseum.nl","data.rijksmuseum.nl")
            rec=json.loads(fetch(base+"?_profile=la-framed",{"data.rijksmuseum.nl"}))
            out.setdefault("object_samples",[]).append({"url":base,"root_keys":list(rec.keys()),
                "identified_by":rec.get("identified_by",[])[:5],
                "produced_by":rec.get("produced_by"),
                "shows":rec.get("shows",[])[:2],
                "classified_as":rec.get("classified_as",[])[:3],
                "rights_keys":[k for k in rec if "right" in k or "license" in k],
                "referred_to_by":rec.get("referred_to_by",[])[:2]})
            vis=(rec.get("shows") or [])
            if vis and vis[0].get("id"):
                u=vis[0]["id"].replace("id.rijksmuseum.nl","data.rijksmuseum.nl")+"?_profile=la-framed"
                v=json.loads(fetch(u,{"data.rijksmuseum.nl"}))
                out.setdefault("visual_samples",[]).append({"root_keys":list(v),"digitally_shown_by":v.get("digitally_shown_by",[])[:2]})
                digital=(v.get("digitally_shown_by") or [])
                if digital and digital[0].get("id"):
                    u=digital[0]["id"].replace("id.rijksmuseum.nl","data.rijksmuseum.nl")+"?_profile=la-framed"
                    d=json.loads(fetch(u,{"data.rijksmuseum.nl"}))
                    out.setdefault("digital_samples",[]).append({"root_keys":list(d),"access_point":d.get("access_point",[])[:2],"rights":d.get("rights"),"referred_to_by":d.get("referred_to_by",[])[:2]})
    except Exception as e:out["error"]=str(e)[:180]
    return out
def sample_sweden():
    out={"source":"nationalmuseum_se"}
    try:
        q=SOURCES["nationalmuseum_se"]["url"]
        j=json.loads(fetch(q,{"commons.wikimedia.org"}))
        for x in (j.get("query") or {}).get("pages",[])[:4]:
            info=(x.get("imageinfo") or [{}])[0]
            ext=info.get("extmetadata") or {}
            out.setdefault("samples",[]).append({"id":x.get("pageid"),"title":x.get("title"),"mime":info.get("mime"),
                "thumburl":str(info.get("thumburl"))[:290],"url":str(info.get("url"))[:140],
                "right_fields":{k:str(ext.get(k,{}).get("value",""))[:170] for k in ("LicenseShortName","LicenseUrl","Copyrighted","AttributionRequired","DateTimeOriginal","Artist","ObjectName")}})
    except Exception as e:out["error"]=str(e)[:180]
    return out
def sample_staedel():
    out={"source":"staedel"}
    for metadata in ("oai_dc","lido"):
        try:
            url="https://sammlung.staedelmuseum.de/api/oai?verb=ListRecords&metadataPrefix="+metadata
            raw=fetch(url,{"sammlung.staedelmuseum.de"},maxsize=1100000)
            root=ET.fromstring(raw)
            out[metadata]={"root_tag":root.tag,
                           "error_tags":[e.attrib for e in root.iter() if e.tag.endswith("error")][:3],
                           "record_count_in_response":len([e for e in root.iter() if e.tag.endswith("record")]),
                           "title_examples":[(e.text or "")[:115] for e in root.iter() if e.tag.endswith("title")][:7],
                           "license_links":[(e.text or "")[:200] for e in root.iter() if e.tag.endswith("linkResource")][:5],
                           "resumption_tokens":[(e.text or "")[:80] for e in root.iter() if e.tag.endswith("resumptionToken")][:2]}
        except Exception as e:out[metadata]={"error":str(e)[:180]}
    return out
def main():
    data={"schema_version":1,"as_of":"2026-11-26",
          "source_schema_probe_only":True,"runtime_imported":0,"sample_results":{}}
    for name,fun in (("rijks",sample_rijks),("nationalmuseum_se",sample_sweden),("staedel",sample_staedel)):
        data["sample_results"][name]=fun()
        print(name,json.dumps(data["sample_results"][name],ensure_ascii=False)[:1600],flush=True)
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
if __name__=="__main__":main()
