#!/usr/bin/env python3
"""Safely probe NEW European museum catalog sources only.

Research diagnostics, not a scraper: bounded GET requests, allowlisted hosts,
no credentials/cookies, no links guessed for images, no assets written to app.
"""
from __future__ import annotations
import argparse,json,urllib.error,urllib.parse,urllib.request,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/".artdrift_eu/probes"
SOURCES={
 "rijks":{"url":"https://data.rijksmuseum.nl/search/collection?type=painting&imageAvailable=true&title=landschap","host":"data.rijksmuseum.nl","kind":"linked_art_json"},
 "nationalmuseum_se":{"url":"https://commons.wikimedia.org/w/api.php?action=query&format=json&formatversion=2&generator=categorymembers&gcmtitle=Category%3AImages_from_the_Nationalmuseum_Stockholm&gcmtype=file&gcmlimit=20&prop=imageinfo&iiprop=extmetadata%7Curl%7Cmime&iiurlwidth=320","host":"commons.wikimedia.org","kind":"commons_json"},
 "belvedere":{"url":"https://sammlung.belvedere.at/opencontent/images","host":"sammlung.belvedere.at","kind":"open_content_html"},
 "staedel":{"url":"https://sammlung.staedelmuseum.de/api/oai?verb=Identify","host":"sammlung.staedelmuseum.de","kind":"oai_xml"},
 "paris_musees":{"url":"https://www.parismuseescollections.paris.fr/en","host":"www.parismuseescollections.paris.fr","kind":"portal_html"},
 "finnish_national_gallery":{"url":"https://kokoelma.kansallisgalleria.fi/","host":"kokoelma.kansallisgalleria.fi","kind":"collection_portal_html"},
 "birmingham":{"url":"https://dams.birminghammuseums.org.uk/","host":"dams.birminghammuseums.org.uk","kind":"image_portal_html"},
 "te_papa":{"url":"https://data.tepapa.govt.nz/collection/search?q=landscape","host":"data.tepapa.govt.nz","kind":"tepapa_json"}
}
def get(source,timeout=18):
    d=SOURCES[source];p=urllib.parse.urlsplit(d["url"])
    assert p.scheme=="https" and p.hostname==d["host"]
    req=urllib.request.Request(d["url"],headers={
        "Accept":"application/json,application/xml,text/html",
        "User-Agent":"ArtDrift-Research-Museum-Access/1.0 (no bulk scraping)"})
    try:
        with urllib.request.urlopen(req,timeout=timeout) as response:
            uri=urllib.parse.urlsplit(response.url)
            if uri.hostname!=d["host"] or uri.scheme!="https":
                raise ValueError("Redirected away from official museum host")
            body=response.read(250001)
            if len(body)>250000:raise ValueError("Oversize probe response")
            return {"status":"HTTP_"+str(response.status),"media_type":response.headers.get("Content-Type",""),
                    "bytes":len(body),"body":body}
    except urllib.error.HTTPError as err:
        return {"status":"HTTP_"+str(err.code),"error":str(err.reason)[:100],"body":b""}
    except Exception as err:
        return {"status":"ERROR","error":str(err)[:160],"body":b""}
def analyze(name):
    result=get(name)
    raw=result.pop("body")
    summary={"museum_key":name,"source_url":SOURCES[name]["url"],
             "source_host":SOURCES[name]["host"],"kind":SOURCES[name]["kind"],**result,
             "metadata_only":True,"runtime_imported":0,"licensed_artwork_images":0}
    if raw and "json" in SOURCES[name]["kind"]:
        try:
            j=json.loads(raw)
            summary["root_fields"]=sorted(j.keys())[:24]
            if name=="te_papa":
                summary["preview_fields"]=list(j.keys())[:25]
                summary["total_hits"]=j.get("total") or j.get("totalHits") or j.get("hits")
                summary["sample_json_types"]={k:type(v).__name__ for k,v in list(j.items())[:8]}
            elif name=="rijks":
                summary["totalItems"]=(j.get("partOf") or {}).get("totalItems")
                summary["returned_identifier_count"]=len(j.get("orderedItems") or [])
                summary["example_identifier"]=(j.get("orderedItems") or [{}])[0].get("id")
                summary["has_next"]=bool(j.get("next"))
            else:
                pages=(j.get("query") or {}).get("pages") or []
                summary["returned_file_pages"]=len(pages)
                summary["sample_pages"]=[{"pageid":x.get("pageid"),"title":str(x.get("title") or "")[:130],
                        "mime":((x.get("imageinfo") or [{}])[0].get("mime")),
                        "ext_metadata_keys":sorted((((x.get("imageinfo") or [{}])[0].get("extmetadata")) or {}).keys())[:12]}
                        for x in pages[:3]]
        except Exception as err:
            summary["parse_error"]=str(err)[:130]
    elif raw:
        decoded=raw.decode("utf-8",errors="replace")
        summary["has_open_content"]=bool(re.search("open content|Open Content|CC0|CC BY-SA|oai|OAI",decoded,re.I))
        summary["html_contains_object_links"]=bool(re.search(r"/(en/)?(object|works|artwork)/",decoded,re.I))
        summary["probe_sample"]=re.sub(r"<[^>]+>"," ",decoded[:500]).strip()[:190]
    return summary
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--museum",choices=SOURCES,required=True)
    a=p.parse_args()
    o=analyze(a.museum)
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/(a.museum+".json")).write_text(json.dumps(o,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(o,ensure_ascii=False,sort_keys=True))
    if o["status"]=="ERROR":raise SystemExit(2)
if __name__=="__main__":main()
