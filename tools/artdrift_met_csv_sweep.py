#!/usr/bin/env python3
"""Broad one-pass official Met Open Access CSV candidate mining.

No image verification or runtime publication is claimed for the CSV queue.
The Met LFS CSV is downloaded once, streamed, safety-bounded and filtered by
scene/title, CC0 metadata, painter/date and existing ArtDrift catalog keys.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,re
from collections import Counter
from pathlib import Path
from urllib.request import Request,urlopen
from artdrift_bright_mass import ROOT,main_keys,scene_ok,cleaned,dates
URL="https://media.githubusercontent.com/media/metmuseum/openaccess/master/MetObjects.csv"
OUT=ROOT/"research/mass_bright/20261126"
MAX_DOWNLOAD=500_000_000
csv.field_size_limit(25_000_000)

def stream_met():
    req=Request(URL,headers={"User-Agent":"ArtDrift-PD-Research/1.0",
                             "Accept":"text/csv"})
    response=urlopen(req,timeout=75)
    if response.url.split("/",3)[2] not in ("media.githubusercontent.com","github.com"):
        response.close();raise RuntimeError("Met CSV redirected off official media Github")
    # Streaming with bounded content length, reject LFS pointers and HTML errors.
    length=int(response.headers.get("Content-Length") or "0")
    if length>MAX_DOWNLOAD:
        response.close();raise RuntimeError("Met CSV too large for research stream")
    text=io.TextIOWrapper(response,encoding="utf-8-sig",newline="")
    reader=csv.DictReader(text)
    if not reader.fieldnames or "Object ID" not in reader.fieldnames:
        text.close();raise RuntimeError("Met CSV is not expanded dataset")
    return text,reader

def run(cap,selection=3000):
    keys,names=main_keys()
    stats=Counter();seen={};samples={}
    stream,reader=stream_met()
    try:
        for r in reader:
            stats["rows_scanned"]+=1
            ident=str(r.get("Object ID") or "").strip()
            if not ident.isdecimal():continue
            if str(r.get("Is Public Domain") or "").strip().lower() not in ("true","1"):continue
            stats["pd_rows"]+=1
            klass=cleaned(r.get("Classification") or "")
            obj=cleaned(r.get("Object Name") or "")
            if "painting" not in klass and "painting" not in obj:continue
            stats["pd_painting_rows"]+=1
            year=dates(r.get("Object Date"),int(r.get("Object Begin Date") or 0) if
                       str(r.get("Object Begin Date") or "").lstrip("-").isdigit() else None)
            if year is None or not 1850<=year<=1960:continue
            title=str(r.get("Title") or "").strip()
            artist=str(r.get("Artist Display Name") or "").strip()
            if not artist or not scene_ok(title,artist):continue
            # Museum has no image url in CSV. Await object-level API image check.
            if ("met",ident) in keys or (cleaned(title),cleaned(artist)) in names:
                stats["duplicate_in_main"]+=1;continue
            statartist=str(r.get("Artist End Date") or "").strip()
            death_candidates=[int(x) for x in re.findall(r"(?<!\d)(?:18|19)\d{2}(?!\d)",statartist)]
            death=max(death_candidates) if death_candidates else None
            if death is not None and death>1955:
                stats["recent_author_risk_excluded"]+=1;continue
            # Keep PD flag from institution but mark territorial clearance HOLD.
            rec={"source":"met","museum_native_id":ident,
                "title":title,"artist":artist,
                "year":year,"date":str(r.get("Object Date") or ""),
                "artist_death_year_if_available":death,
                "medium":str(r.get("Medium") or "")[:160],
                "artist_nationality":str(r.get("Artist Nationality") or "")[:100],
                "is_public_domain_institution":True,
                "rights_evidence_url":"https://www.metmuseum.org/hubs/open-access",
                "museum_url":f"https://www.metmuseum.org/art/collection/search/{ident}",
                "image_verified":False,
                "image_hash_verified":False,
                "publication_status":"HOLD_OBJECT_IMAGE_AND_VISUAL_AND_TERRITORIAL_QA",
                "runtime_visible":False}
            seen[ident]=rec
            stats["eligible_metadata_rows"]+=1
    finally:
        stream.close()
    values=list(seen.values())
    # Prioritize canonical scenic/flowers; spread across artists and years,
    # otherwise hundreds may be nearly identical sky studies.
    artistseen=Counter()
    def priority(w):
        t=cleaned(w["title"])
        scene=any(x in t for x in ("landscape","garden","seascape","coast","flower",
                "orchard","field","village","river","beach","tree","rose","blossom"))
        return (-int(scene),-int(w["year"]>=1880),w["artist"].lower(),int(w["museum_native_id"]))
    values.sort(key=priority)
    shortlist=[]
    for w in values:
        key=w["artist"].lower()
        if artistseen[key]>=130:continue
        artistseen[key]+=1
        shortlist.append(w)
        if len(shortlist)>=cap:break
    OUT.mkdir(parents=True,exist_ok=True)
    report={"schema_version":1,"source":"Met OA CSV",
            "as_of":"2026-11-26","source_url":URL,
            "csv_rows_scanned":stats["rows_scanned"],
            "official_pd_rows":stats["pd_rows"],
            "official_pd_painting_rows":stats["pd_painting_rows"],
            "eligible_novel_scenic_metadata":len(values),
            "queue_staged_count":len(shortlist),
            "image_verified_count":0,"runtime_imported":0,
            "worldwide_rights_approved":0,
            "important":"Metadata queue only; no image URL or color assertion yet.",
            "stats":dict(stats),"works":shortlist}
    dest=OUT/"met_full_csv_scenic_queue.json"
    dest.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k not in ("works","stats")},
                     ensure_ascii=False,sort_keys=True))
    if len(shortlist)<50:raise SystemExit("TOO_FEW_OFFICIAL_MET_SCENIC_METADATA_CANDIDATES")
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--max-candidates",type=int,default=3000)
    a=p.parse_args()
    if not 100<=a.max_candidates<=6000:p.error("bounded")
    run(a.max_candidates)
