#!/usr/bin/env python3
"""Pixel-level integrity and source-identity certificate for Art Drift offline WebP.

A technical QA certificate, NEVER commercial image licensing or visual approval.
Checks image readability and source mapping for all manifest-listed WebP images.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
PACK = "web/museum_thumbs"
CATALOG = "assets/museums/catalog_global.json"
OUTPUT = "docs/generated/ARTDRIFT_4042_WEBP_PIXEL_QA.json"
Image.MAX_IMAGE_PIXELS = 16_000_000


def measure_webp(path: Path):
    original=path.read_bytes()
    if not (original[:4]==b"RIFF" and original[8:12]==b"WEBP"):
        raise ValueError(f"Invalid WebP signature {path}")
    with Image.open(path) as im:
        if im.format != "WEBP":
            raise ValueError(f"Invalid decoded WebP {path}")
        im.load()
        w,h=im.size
        if w<10 or h<10 or w>8000 or h>8000:
            raise ValueError(f"Unexpected image dimensions {path} {w}x{h}")
        tile=ImageOps.exif_transpose(im.convert("RGB"))
        tile.thumbnail((80,80),Image.Resampling.BILINEAR)
        pixels=list(tile.getdata())
    n=len(pixels)
    dark=sum(1 for r,g,b in pixels if max(r,g,b)<64)/n
    vivid=sum(1 for r,g,b in pixels
              if max(r,g,b)>105 and max(r,g,b)-min(r,g,b)>48)/n
    mean_luminance=sum((.2126*r+.7152*g+.0722*b)/255
                       for r,g,b in pixels)/n
    return {
        "width":w,"height":h,"bytes":len(original),
        "sha256":hashlib.sha256(original).hexdigest(),
        "dark_fraction":round(dark,4),
        "vivid_fraction":round(vivid,4),
        "luminance":round(mean_luminance,4),
    }


def audit(root:Path,expected: int | None=None):
    catalog=json.loads((root/CATALOG).read_text(encoding="utf-8"))
    manifest=json.loads((root/PACK/"manifest.json").read_text(encoding="utf-8"))
    if manifest.get("schema_version")!=1:
        raise ValueError("Unexpected manifest schema")
    keys=manifest.get("keys")
    if not isinstance(keys,list) or len(keys)!=len(set(keys)):
        raise ValueError("Invalid/duplicate manifest keys")
    if expected is not None and len(keys)!=expected:
        raise ValueError(f"Expected {expected} artworks, got {len(keys)}")
    indexed={}
    for row in catalog:
        if not isinstance(row,dict):continue
        source=row.get("museum_source")
        ident=row.get("id")
        if isinstance(source,str) and source.isalpha() and type(ident) is int:
            k=f"{source}:{ident}"
            if k in indexed:raise ValueError(f"Duplicate primary catalog identity: {k}")
            indexed[k]=row
    source_counts=Counter()
    colors=Counter()
    rights=Counter()
    sha_to_ids=defaultdict(list)
    corrupted=[]
    min_bytes=None
    sum_bytes=0
    luminance_values=[]
    examples=[]
    for key in keys:
        source,num=key.split(":",1)
        if key not in indexed:raise ValueError(f"Missing corresponding source artwork {key}")
        row=indexed[key]
        if row.get("is_public_domain") is not True:
            raise ValueError(f"Non-PD artwork in image pack: {key}")
        if str(row.get("artwork_type_title") or "").lower()!="painting":
            raise ValueError(f"Nonpainting artwork in image pack: {key}")
        license=str(row.get("rights_license") or "")
        if not any(x in license.casefold() for x in ("cc0","public domain")):
            raise ValueError(f"Missing source open-rights flag: {key}")
        url=str(row.get("rights_evidence_url") or "")
        if not url.startswith("https://"):
            raise ValueError(f"Missing provider evidence URL {key}")
        file=root/PACK/f"{source}_{num}.webp"
        if not file.is_file():
            raise ValueError(f"Missing WebP {key}")
        try:
            stats=measure_webp(file)
        except Exception as e:
            corrupted.append({"source_id":key,"error":str(e)[:140]})
            continue
        if stats["bytes"]<250 or stats["bytes"]>24000:
            corrupted.append({"source_id":key,"error":"OUTSIDE_PACK_SIZE_GATE"})
            continue
        source_counts[source]+=1
        rights[license.strip()]+=1
        sha_to_ids[stats["sha256"]].append(key)
        luminance_values.append(stats["luminance"])
        min_bytes=stats["bytes"] if min_bytes is None else min(min_bytes,stats["bytes"])
        sum_bytes+=stats["bytes"]
        if stats["dark_fraction"]<=.15 and stats["luminance"]>=.55:
            color="BRIGHT_IMAGE_TECHNICAL_CANDIDATE"
        elif stats["dark_fraction"]<=.20 and stats["vivid_fraction"]>=.20:
            color="SATURATED_NEAR_MISS_CANDIDATE"
        else:
            color="OTHER_IMAGE_REVIEW"
        colors[color]+=1
        if len(examples)<35 or color=="BRIGHT_IMAGE_TECHNICAL_CANDIDATE" and len(
                [x for x in examples if x["color_tier"]=="BRIGHT_IMAGE_TECHNICAL_CANDIDATE"])<15:
            # Preview list is samples only; no auto release decision.
            examples.append({"source_id":key,"color_tier":color,
                             "title":str(row.get("title") or "")[:130],
                             "sha256":stats["sha256"],"pixels":stats})
    expected_files={key.replace(":","_")+".webp" for key in keys}
    real_files={x.name for x in (root/PACK).glob("*.webp")}
    if expected_files!=real_files:
        raise ValueError("Pack contains orphan or missing WebPs")
    duplicates=[{"sha256":sha,"source_ids":ids}
                for sha,ids in sha_to_ids.items() if len(ids)>1]
    result={
        "schema_version":1,
        "as_of_utc":datetime.now(timezone.utc).isoformat(),
        "certificate":"TECHNICAL_PIXEL_INTEGRITY_ONLY_NOT_COMMERCIAL_IMAGE_RIGHTS",
        "manifest_count":len(keys),
        "decoded_valid_webp_count":sum(source_counts.values()),
        "invalid_decoded_images":corrupted[:80],
        "image_bytes_total":sum_bytes,
        "min_image_bytes":min_bytes,
        "mean_image_brightness":round(statistics.mean(luminance_values),4)
                                if luminance_values else None,
        "source_counts":dict(sorted(source_counts.items())),
        "source_license_claim_distribution":dict(sorted(rights.items())),
        "technical_color_tiers":dict(colors),
        "byte_identical_image_hash_groups":duplicates[:100],
        "byte_identical_image_hash_group_count":len(duplicates),
        "sample_images":examples[:70],
        "commercially_approved":0,
        "runtime_imported_by_audit":0,
        "physical_device_qa":"PENDING",
        "source_image_rights_final":"PENDING_ITEM_AND_TERRITORY",
        "all_images_work_copyright_confirmed":False,
    }
    if corrupted:
        raise ValueError(f"{len(corrupted)} invalid media; report cannot pass")
    return result


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--root",type=Path,default=ROOT)
    parser.add_argument("--expected",type=int,default=4042)
    parser.add_argument("--out",type=Path,default=ROOT/OUTPUT)
    args=parser.parse_args()
    result=audit(args.root,args.expected)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+"\n",
                        encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k not in (
        "sample_images","byte_identical_image_hash_groups")},
        ensure_ascii=False),flush=True)


if __name__=="__main__":
    main()
