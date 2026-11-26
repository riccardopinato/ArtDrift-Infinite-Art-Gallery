#!/usr/bin/env python3
"""Target exact user-named paintings and Monet subthemes on Wikimedia Commons.

Not an institution scraper. No excluded US museum API calls. Search results
require artist corroboration; conservatively retain only research/HOLD.
"""
from __future__ import annotations

import argparse
import json
import re
import time
import urllib.error
from datetime import datetime, timezone

from artdrift_user_artist_pipeline import BASE, REMOTE, SOURCE, artist_id, commons_get, \
    parse_commons, target_id

DIRECT_FILE = ("ludvig_karsten",
    "File:Ludvig Karsten - The Blue Kitchen - NG.M.01507 - National Museum of Art, Architecture and Design.jpg")
SEARCH_TERMS = (
    ("gustave_caillebotte",'Caillebotte Yerres'),
    ("gustave_caillebotte",'Périssoires sur l Yerres'),
    ("alfred_sisley",'Sisley Villeneuve-la-Garenne bridge'),
    ("alfred_sisley",'Alfred Sisley pont Villeneuve'),
    ("claude_monet",'Monet Water Lilies'),
    ("claude_monet",'Claude Monet Giverny garden'),
    ("claude_monet",'Monet nympheas water'),
    ("claude_monet",'Claude Monet river landscape'),
)
SOURCE_ORIGIN = "COMMONS_WORK_AND_ARTIST_SEARCH_NEEDS_VALIDATION"


def verify_artist(row, seed, expected):
    label=artist_id(row,seed)
    if label==expected:
        return True
    # Some Commons title variants omit author in metadata; do not treat them
    # as a confirmed artist even if the category search included the name.
    return False


def search(seed, existing, max_queries, getter=commons_get, pause=time.sleep):
    records=dict(existing.get("records_by_commons_pageid") or {})
    progress=dict(existing.get("targeted_search_progress") or {})
    errors=[]
    network_queries=0
    additions=0
    throttled=False

    tasks=[("exact_karsten", DIRECT_FILE[0],DIRECT_FILE[1],True)]
    tasks.extend((f"search_{i}",p,q,False) for i,(p,q) in enumerate(SEARCH_TERMS))
    for key,expected,query,exact in tasks:
        if network_queries>=max_queries or throttled:
            break
        if progress.get(key,{}).get("completed"):
            continue
        if exact:
            params={"action":"query","format":"json","formatversion":2,
                    "titles":query,"prop":"imageinfo",
                    "iiprop":"url|mime|extmetadata|sha1","iiurlwidth":340}
        else:
            params={"action":"query","format":"json","formatversion":2,
                    "generator":"search","gsrsearch":query,
                    "gsrnamespace":6,"gsrlimit":50,"prop":"imageinfo",
                    "iiprop":"url|mime|extmetadata|sha1","iiurlwidth":340}
            if progress.get(key,{}).get("continuation"):
                params.update(progress[key]["continuation"])
        try:
            payload=getter(params)
        except Exception as err:
            msg=str(err)
            if (getattr(err,"code",None) in (429,503) or
                    re.search(r"\b(?:429|503)\b",msg)):
                throttled=True
            errors.append({"key":key,"error":msg[:150]})
            continue
        if payload.get("error"):
            err=payload["error"]
            code=str(err.get("code","")).lower() if isinstance(err,dict) else ""
            if code in ("ratelimited","maxlag"):
                throttled=True
            errors.append({"key":key,"error":str(err)[:160]})
            continue
        network_queries+=1
        found=0
        for item in (payload.get("query") or {}).get("pages") or []:
            if "missing" in item:
                continue
            r=parse_commons(item,expected,"EXPLICIT_FILE" if exact else SOURCE_ORIGIN)
            if not r:
                continue
            if not verify_artist(r,seed,expected):
                # Exact source title is already preverified independently,
                # but category/search snippets are NOT artist evidence.
                if not exact:
                    continue
                r["artist_attribution_status"]="HOLD_EXACT_FILE_AUTHOR_METADATA_MISSING"
            else:
                r["artist_attribution_status"]="SOURCE_ARTIST_TEXT_MATCH__HOLD_ORIGINAL_SOURCE"
            r["search_evidence"]={"query":query,"exact_title_lookup":exact}
            t=target_id(r,seed,expected)
            if t:
                r["explicit_work_target"]=t
            if r["museum_native_id"] not in records:
                records[r["museum_native_id"]]=r
                additions+=1
            else:
                prev=records[r["museum_native_id"]]
                if exact:
                    prev["explicit_work_target"]=t
                    prev["exact_direct_file_source"]=True
                else:
                    prev["also_seen_in_search"]=sorted(set(prev.get(
                        "also_seen_in_search",[])+[query]))
            found+=1
        cursor=(payload.get("continue") or None) if not exact else None
        progress[key]={"completed":not bool(cursor),
                       "continuation":cursor,
                       "last_results_eligible":found,
                       "query":query,
                       "expected_artist":expected}
        pause(.75)
    result=dict(existing)
    result.update({
        "records_by_commons_pageid":records,
        "total_distinct_commons_files":len(records),
        "targeted_search_progress":progress,
        "targeted_queries_executed_this_run":network_queries,
        "targeted_new_files_this_run":additions,
        "targeted_source_host_throttled":throttled,
        "targeted_errors":errors,
        "targeted_as_of_utc":datetime.now(timezone.utc).isoformat(),
        "commercially_approved":0,"runtime_imported":0,
        "source_evidence_is_not_artwork_ownership":True,
    })
    return result


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--max-queries",type=int,default=9)
    a=parser.parse_args()
    if not 1<=a.max_queries<=12:
        parser.error("--max-queries 1..12")
    seed=json.loads(SOURCE.read_text(encoding="utf-8"))
    old=json.loads(REMOTE.read_text(encoding="utf-8")) if REMOTE.is_file() else {}
    result=search(seed,old,a.max_queries)
    REMOTE.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",
                      encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k not in (
        "records_by_commons_pageid","query_progress","targeted_search_progress")},
        ensure_ascii=False),flush=True)


if __name__=="__main__":
    main()
