#!/usr/bin/env python3
"""Count official Städel major-work OAI IDs without downloading any image.

This is a low-bandwidth preflight, not a catalog import or rights clearance.
Metadata are CC0; linked image rights require separate per-object review.
"""
from __future__ import annotations

import argparse
import json
import time
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

from artdrift_eu_new_museums_batch import fetch

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"research/museums/20261126/lanes/staedel_identifier_inventory.json"
BASE="https://sammlung.staedelmuseum.de/api/oai?"
NS={"oai":"http://www.openarchives.org/OAI/2.0/"}


def parse(payload):
    root=ET.fromstring(payload)
    errors=[{"code":e.attrib.get("code"),"message":(e.text or "")[:130]}
            for e in root.findall(".//oai:error",NS)]
    identifiers=[]
    deleted=0
    for header in root.findall(".//oai:ListIdentifiers/oai:header",NS):
        ident=header.findtext("./oai:identifier",default="",namespaces=NS)
        if not ident.startswith("oai:DE-MUS-048017:"):
            continue
        if header.attrib.get("status")=="deleted":
            deleted+=1
        else:
            identifiers.append(ident)
    token=root.find(".//oai:resumptionToken",NS)
    cursor=(token.text or "").strip() if token is not None else ""
    return identifiers,deleted,cursor,errors


def harvest(max_pages=15,previous=None,request=None):
    if request is None:
        request=lambda url:fetch(url,limit=3_000_000,timeout=30)
    previous=previous or {}
    known=set(previous.get("active_identifiers") or [])
    deleted=int(previous.get("deleted_headers_seen",0))
    token=previous.get("next_resumption_token") or ""
    seen_tokens=set()
    if previous.get("catalog_iteration_completed") is True:
        return previous
    pages=0
    faults=[]
    finished=False
    for _ in range(max_pages):
        query=({"verb":"ListIdentifiers","resumptionToken":token}
               if token else
               {"verb":"ListIdentifiers","metadataPrefix":"lido",
                "set":"scope:major"})
        url=BASE+urllib.parse.urlencode(query)
        try:
            found,old_deleted,nxt,errors=parse(request(url))
        except Exception as e:
            faults.append(str(e)[:190])
            break
        if errors:
            faults.extend(errors[:3])
            break
        pages+=1
        known.update(found)
        deleted+=old_deleted
        if not nxt:
            finished=True
            token=""
            break
        if nxt in seen_tokens:
            faults.append("REPEATED_OAI_RESUMPTION_TOKEN")
            break
        seen_tokens.add(nxt)
        token=nxt
        time.sleep(0.35)
    return {
        "schema_version":1,
        "as_of_utc":datetime.now(timezone.utc).isoformat(),
        "provider":"staedel",
        "source_url":"https://sammlung.staedelmuseum.de/en/oai/guide",
        "set":"scope:major",
        "metadata_prefix":"lido",
        "pages_retrieved_this_run":pages,
        "distinct_active_identifier_count":len(known),
        "active_identifiers":sorted(known),
        "deleted_headers_seen":deleted,
        "next_resumption_token":token or None,
        "catalog_iteration_completed":finished,
        "errors":faults,
        "source_is_not_exhaustively_searched":not finished,
        "source_zero_artworks_proven":False,
        "metadata_license":"CC0 1.0",
        "image_rights":"NOT_EVALUATED__OAI_LINKS_CC_BY_SA_REQUIRE_REVIEW",
        "runtime_imported":0,
        "commercially_approved":0,
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--max-pages",type=int,default=15)
    a=parser.parse_args()
    if not 1<=a.max_pages<=30:
        parser.error("--max-pages must be 1..30")
    old=json.loads(OUT.read_text(encoding="utf-8")) if OUT.is_file() else {}
    result=harvest(a.max_pages,old)
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k not in
                      ("active_identifiers","next_resumption_token")},
                     ensure_ascii=False),flush=True)


if __name__=="__main__":
    main()
