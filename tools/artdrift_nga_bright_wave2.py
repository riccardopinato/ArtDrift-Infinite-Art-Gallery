#!/usr/bin/env python3
"""Art Drift NGA bright scenery WAVE 2: broaden subjects, tighten dark rejection.

Never modify canvas/runtime or original wave1. Verify official NGA Open Access
primary images, decode actual pixels, dedup main+wave1, keep HOLD status.
"""
from __future__ import annotations
import argparse
import csv
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import artdrift_nga_color_research as base

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/".artdrift_research/nga_bright_wave2"
WAVE1=ROOT/"research/nga/20261125/nga_bright_review.json"
SCENIC=(
 "seascape","countryside","cottage","haystack","haystacks",
 "village","villages","river","bay","coast","coastal","beach","island",
 "harbour","harbor","port","seashore","shore","boats","sails","boat",
 "ocean","lakes","lake","streams","brook","creek","waterfall",
 "estuary","canal","pond","pools","water lilies","waterlilies",
 "cypress","pines","pine trees","palms","oak trees","forest",
 "woods","woodland","glade","trees","tree","grove",
 "mountain","hills","hill","cliffs","valley","snow","sunshine",
 "meadow","pasture","prairie","wheat","cornfield","field",
 "garden","flowering","flowers","blossoms","blossom","roses",
 "dahlias","sunflowers","poppies","irises","lilacs","tulips","violets",
 "spring","summer","autumn","landscape","countryside","fence",
 "orchard","vineyard","road","path","avenue","park","bridge",
 "terrace","view","houses","rooftops","rooftop","town","village",
 "villas","villa","farm","farmhouse","windmill","mill","street",
 "boulevard","square","promenade","canal","fountain",
 "sky","clouds","morning","afternoon","sunlit",
 "provence","brittany","riviera","normandy","arles","giverny",
 "auvers","montmartre","venice","etretat","argenteuil","vétheuil",
 "vtheuil","estaque","collioure","nice","marseille","italy","france",
 "california","maine","cape ann","capri","saint tropez","cannes"
)
# Exclude when human beings likely are the main focus, or low-light artwork.
AVOID=(
 "portrait","self-portrait","woman","women","man","men","boy","boys",
 "girl","girls","person","people","child","children","figures",
 "family","mother","father","daughter","lady","peasant","bather",
 "nude","seated","standing","head","face","profile","dancers",
 "sleeping","in bed","costume","worker","workers","fishermen",
 "fisherwoman","horseman","saints","madonna","crucifix",
 "nocturne","night","at dusk","twilight","dusk","moonlit",
 "moonlight","evening","dark","black","storm","rainstorm",
 "study of a","sketch of","study for","copy after","after ",
 "imitator","school of","follower of","attributed to","unknown"
)
POS_RE=re.compile(r"\b(?:"+"|".join(re.escape(s) for s in sorted(set(SCENIC),key=len,reverse=True))+r")\b")
AVOID_RE=re.compile(r"\b(?:"+"|".join(re.escape(s) for s in sorted(set(AVOID),key=len,reverse=True))+r")\b")

# Tight enough to exclude large dark areas even if the subject looks colorful.
MIN_LUMINANCE=.595
MAX_DARK_FRAC=.095
MIN_VIVID_FRAC=.255
MIN_SATURATION=.235
MIN_YEAR=1850
MAX_YEAR=1965

def new_year(row):
    # Do not silently invent dates from lifespans.
    d=str(row.get("displaydate") or "")
    y=[int(v) for v in re.findall(r"(?<!\d)(?:18|19)\d{2}(?!\d)",d)]
    if not y or min(y)<MIN_YEAR or max(y)>MAX_YEAR:return None
    return min(y)

def scenery_score(title,artist,year):
    t=base.ascii_text(title)
    a=base.ascii_text(artist)
    if AVOID_RE.search(t) or any(v in a for v in
       ("imitator","after ","school of","follower of","unknown","anonymous")):
        return 0
    terms=POS_RE.findall(t)
    if not terms:return 0
    # Keep scenic titles, not generic still-lifes or figures. Focus on land/sea.
    score=5+sum(min(6,len(word)//3) for word in set(terms))
    if any(x in a for x in base.ARTISTS):score+=5
    if 1870<=year<=1940:score+=3
    if any(s in t for s in ("flower","garden","sea","landscape","coast","beach",
                             "orchard","village","harbor","meadow")):score+=4
    return score

def previous():
    if not WAVE1.is_file():raise FileNotFoundError("wave1 catalog missing: cannot dedup")
    j=json.loads(WAVE1.read_text(encoding="utf-8"))
    if j.get("selected_bright_landscape_works")!=22:
        raise ValueError("wave1 count not certified")
    return {str(w["museum_native_id"]) for w in j["works"]}

def candidate_objects(exclude):
    found=base.catalog_keys()
    found|=exclude
    found|=set(base.VISUAL_QA_EXCLUSIONS)
    stream,rows=base.stream_csv("objects.csv")
    all_count=0;scenic={}
    try:
        for row in rows:
            all_count+=1
            if "paint" not in base.ascii_text(row.get("classification")):continue
            ident=str(row.get("objectid") or "").strip()
            if not ident.isdecimal() or ident in found:continue
            yr=new_year(row)
            if yr is None:continue
            artist=str(row.get("attribution") or "")
            title=str(row.get("title") or "").strip()
            s=scenery_score(title,artist,yr)
            if s<9:continue
            scenic[ident]={"native_id":ident,"title":title,"artist":artist,
                           "year":yr,"date":row.get("displaydate") or "",
                           "classification":row.get("classification") or "",
                           "medium":row.get("medium") or "",
                           "metadata_score":s,
                           "nga_url":f"https://www.nga.gov/artworks/{ident}"}
    finally:stream.close()
    return all_count,len(found),scenic

def find_images(objs):
    return base.join_open_access(objs)

def strict_pass(c):
    return (c["luminance"]>=MIN_LUMINANCE and
            c["dark_fraction"]<=MAX_DARK_FRAC and
            c["vivid_fraction"]>=MIN_VIVID_FRAC and
            c["saturation"]>=MIN_SATURATION)

def run(max_probe,workers,max_selected):
    existing=previous()
    objects_count,excluded_count,scenes=candidate_objects(existing)
    images_count,flags,images=find_images(scenes)
    pool=[v for k,v in scenes.items() if k in images]
    pool.sort(key=lambda a:(-a["metadata_score"],a["artist"].lower(),int(a["native_id"])))
    kept=[];holds=[];thumbs={}
    selection=pool[:max_probe]
    with ThreadPoolExecutor(max_workers=workers) as executor:
        tasks={executor.submit(base.probe,w,images):w for w in selection}
        for f in as_completed(tasks):
            w=tasks[f]
            try:
                color,sha,thumb=f.result()
                if not strict_pass(color):
                    holds.append({"native_id":w["native_id"],
                                  "title":w["title"],
                                  "reason":"NOT_BRIGHT_ENOUGH",
                                  "color_metrics":color})
                    continue
                ident=w["native_id"]
                rec={**w,"id":4_000_000_000+int(ident),
                     "museum_source":"nga","museum_native_id":ident,
                     "museum_name":"National Gallery of Art, Washington",
                     "rights_license":"Public Domain / NGA Open Access",
                     "rights_evidence_url":base.RIGHTS,
                     "source_dataset_sha":base.NGA_SHA,
                     "source_image_uuid":images[ident]["image_uuid"],
                     "remote_preview_url":images[ident]["preview"],
                     "remote_full_url":images[ident]["full"],
                     "image_sha256":sha,
                     "color_metrics":{**color,"wave2_strict_bright_pass":True},
                     "portrait_subject_candidate":False,
                     "public_domain_image_flag":True,
                     "publication_status":"HOLD_FINAL_RIGHTS_AND_VISUAL_QA",
                     "runtime_visible":False}
                rec["curation_score"]=round(
                    color["luminance"]*.34+color["saturation"]*.25+
                    color["vivid_fraction"]*.42-color["dark_fraction"]*.77+
                    min(.12,w["metadata_score"]/210),4)
                kept.append(rec);thumbs[ident]=thumb
            except Exception as e:
                holds.append({"native_id":w["native_id"],"title":w["title"],
                              "reason":str(e)[:160]})
    kept.sort(key=lambda x:(-x["curation_score"],int(x["native_id"])))
    chosen=kept[:max_selected]
    result={
        "schema_version":2,"as_of":"2026-11-26",
        "source":"National Gallery of Art official open data",
        "dataset_commit":base.NGA_SHA,
        "wave1_original_preserved":len(existing),
        "existing_or_explicitly_blocked":excluded_count,
        "objects_scanned":objects_count,
        "modern_scenic_candidates":len(scenes),
        "scenic_with_primary_openaccess_image":len(pool),
        "images_probed":len(selection),
        "strict_bright_image_pass":len(kept),
        "wave2_selected_count":len(chosen),
        "color_or_image_holds":len(holds),
        "unprobed_remaining":max(0,len(pool)-len(selection)),
        "rights_counts":dict(flags),
        "thresholds":{"luminance_min":MIN_LUMINANCE,
                      "dark_fraction_max":MAX_DARK_FRAC,
                      "vivid_fraction_min":MIN_VIVID_FRAC,
                      "saturation_min":MIN_SATURATION,
                      "year_min":MIN_YEAR,"year_max":MAX_YEAR},
        "portrait_count":0,"runtime_imported":0,
        "territorial_and_final_curation_approved":0,
        "works":chosen,
        "hold_samples":sorted(holds,key=lambda x:int(x["native_id"]))[:200],
    }
    return result,thumbs

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--max-probe",type=int,default=230)
    a.add_argument("--max-selected",type=int,default=150)
    a.add_argument("--workers",type=int,default=4)
    args=a.parse_args()
    if not 1<=args.max_probe<=320 or not 1<=args.max_selected<=200 or not 1<=args.workers<=4:
        a.error("Bounded probe/selection/workers values required")
    result,thumbs=run(args.max_probe,args.workers,args.max_selected)
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"nga_bright_wave2_review.json").write_text(
        json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    base.contact_sheet(result["works"],thumbs,OUT/"nga_bright_wave2_contact_sheet.jpg")
    print(json.dumps({k:v for k,v in result.items() if k not in ("works","hold_samples")},
                     ensure_ascii=False,sort_keys=True))
    if result["wave2_selected_count"]<5:
        raise SystemExit("TOO_FEW_NEW_BRIGHT_SCENIC_PAINTINGS")

if __name__=="__main__":
    main()
