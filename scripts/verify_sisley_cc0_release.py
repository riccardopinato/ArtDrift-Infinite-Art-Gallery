#!/usr/bin/env python3
"""Fail-closed Sisley release preflight: main catalogs and CC0 evidence."""
import json,re,sys
from pathlib import Path
ROOT=Path(sys.argv[1] if len(sys.argv)>1 else ".")
FILE="assets/museums/catalog_curated_commons.json"
src=json.loads((ROOT/FILE).read_text(encoding="utf-8"))
assert isinstance(src,list) and len(src)==1, "Exactly one reviewed file is allowed"
r=src[0]
assert r["source_identity"]=="commons:57672559" and r["id"]==57672559
assert r["rights_license"]=="CC0 1.0"
assert r["museum_native_id"]=="57672559"
assert r["commercially_approved"] is True
assert r["source_provenance_verified"] is True
assert r["worldwide_distribution_reviewed"] is True
assert r["rights_review_reference"]=="docs/ARTDRIFT_FIRST_MET_CC0_SISLEY_REVIEW_20261127.md"
assert (ROOT/r["rights_review_reference"]).is_file()
assert r["remote_full_url"]=="https://upload.wikimedia.org/wikipedia/commons/4/45/The_Bridge_at_Villeneuve-la-Garenne_MET_DT1040.jpg"
assert r["remote_museum_url"]=="https://commons.wikimedia.org/wiki/File:The_Bridge_at_Villeneuve-la-Garenne_MET_DT1040.jpg"
assert "Gift of Mr. and Mrs. Henry Ittleson Jr., 1964" in r["credit_line"]
assert r["image_license_url"]=="https://creativecommons.org/publicdomain/zero/1.0/"
assert r["artwork_type_title"]=="Painting" and r["is_public_domain"] is True
assert r["thumbnail"]["width"]==3811 and r["thumbnail"]["height"]==2911
# Do not duplicate other museum-source IDs, even when titles differ.
files=["assets/gallery/catalog.json","assets/museums/catalog.json","assets/museums/catalog_global.json",
       "assets/museums/catalog_modern_1950.json","assets/museums/catalog_new_museums.json"]
seen_names=[]
ids=set()
for file in files:
    obj=json.loads((ROOT/file).read_text(encoding="utf8"))
    if not isinstance(obj,list):raise ValueError("Bad catalog")
    for x in obj:
        key=(str(x.get("museum_source","aic")),str(x.get("museum_native_id",x.get("id"))))
        ids.add(key)
        title=str(x.get("title","")).casefold()
        artist=str(x.get("artist_title",x.get("artist_display",""))).casefold()
        # Prevent a high-risk duplicate of same painting under a provider ID.
        if ("sisley" in artist and
                ("villeneuve" in title or "villeneuve-la-garenne" in title or
                 ("bridge" in title and "garenne" in title))):
            seen_names.append((file,key,x.get("title")))
if ("met","437680") in ids:raise ValueError("Met 437680 is already in runtime")
if ("commons","57672559") in ids:raise ValueError("Commons 57672559 is already in runtime")
if seen_names:raise ValueError("Potential duplicate artwork: "+str(seen_names))
print("SISLEY_MET_CC0_ONE_ARTWORK_RELEASE_CANDIDATE_PASS")
print("EXISTING_CATALOG_FILES",len(files),"SOURCE_IDENTITIES",len(ids))
