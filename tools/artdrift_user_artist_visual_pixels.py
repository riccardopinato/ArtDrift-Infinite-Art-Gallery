#!/usr/bin/env python3
"""Pixel-level contact-sheet QA of named-artist candidates, never publication.

Samples fairly across artists, records actual raster metrics and immutable
bytes SHA-256, preserves source ownership/licensing HOLD. Wikimedia-only
thumbnail downloads; image assets remain as temporary GitHub Actions artifacts.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import io
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

from artdrift_bright_mass import color_metric
from artdrift_dark_threshold_ab import color_tier
from artdrift_user_artist_pipeline import BASE, SHORTLIST, safe_url

OUTPUT = BASE / "artist_pixel_visual_evidence.json"
SHEET = BASE / "artist_contact_sheet_research.jpg"
HTML = BASE / "artist_contact_sheet_research.html"
MAX_BYTES = 1_800_000
Image.MAX_IMAGE_PIXELS = 24_000_000
EXCLUDE_SUBJECTS = re.compile(
    r"\b(?:portrait|self.portrait|nude|catalogue|catalog|postcard|document|"
    r"statue|sculpture|battle|drawing|etching|engraving)\b",re.I)


def safe_preview(url):
    try:
        p=urllib.parse.urlsplit(str(url or ""))
    except ValueError:
        return False
    return (safe_url(url) and p.hostname in
            {"upload.wikimedia.org","thumb.wikimedia.org"} and
            p.port in (None,443))


def select(report, per_artist=5, max_total=35):
    buckets=defaultdict(list)
    for r in report.get("priority_shortlist") or []:
        if not safe_preview(r.get("preview_url")):
            continue
        if not str(r.get("source_license_claim") or "").lower().strip() in (
                "public domain","public domain mark 1.0","cc0","cc0 1.0",
                "pdm","pd-art","pd-old"):
            # Research may retain additional licenses, but raster QA is
            # limited to likely-open Commons thumbnails.
            continue
        title=str(r.get("title") or "")
        if EXCLUDE_SUBJECTS.search(title) and not r.get("explicit_work_target"):
            continue
        if str(r.get("image_mime") or "image/jpeg") not in (
                "image/jpeg","image/png","image/webp","image/tiff"):
            continue
        aid=r.get("artist_id")
        if aid:
            buckets[aid].append(r)
    for rows in buckets.values():
        rows.sort(key=lambda r:(not bool(r.get("explicit_work_target")),
                                -r.get("curatorial_score",0),
                                str(r.get("identity") or "")))
    out=[]
    artists=sorted(buckets)
    for i in range(per_artist):
        for artist in artists:
            if len(out)>=max_total:break
            if len(buckets[artist])>i:
                out.append(buckets[artist][i])
    # Prioritize the exact user works independently of painter distribution,
    # including multiple distinguishable Sisley reproductions.
    known={r.get("identity") for r in out}
    for rows in buckets.values():
        for r in rows:
            if (len(out)>=max_total or r.get("identity") in known or
                    not r.get("explicit_work_target")):
                continue
            out.append(r)
            known.add(r["identity"])
    return out


def download(url):
    if not safe_preview(url):
        raise ValueError("unapproved media preview host")
    req=urllib.request.Request(url,headers={
        "User-Agent":"ArtDrift-VisualResearch/1.0 (research QA; GitHub riccardopinato)",
        "Accept":"image/jpeg,image/png,image/webp"})
    with urllib.request.urlopen(req,timeout=22) as resp:
        if not safe_preview(resp.url):
            raise ValueError("unsafe media redirect")
        raw=resp.read(MAX_BYTES+1)
        if len(raw)>MAX_BYTES:
            raise ValueError("image exceeds bound")
        if len(raw)<200:
            raise ValueError("image too small")
    with Image.open(io.BytesIO(raw)) as im:
        if im.format not in {"JPEG","PNG","WEBP"}:
            raise ValueError("unsupported raster image")
        metrics=color_metric(im)
        thumb=ImageOps.exif_transpose(im.convert("RGB"))
        thumb.thumbnail((180,140),Image.Resampling.LANCZOS)
        thumbnail=thumb.copy()
    return metrics, hashlib.sha256(raw).hexdigest(),thumbnail


def render_sheet(records):
    if not records:
        return
    width,height,cols=218,190,5
    canvas=Image.new("RGB",(cols*width,
        ((len(records)+cols-1)//cols)*height),(246,247,246))
    painter=ImageDraw.Draw(canvas)
    for i,(work,thumb) in enumerate(records):
        x=(i%cols)*width
        y=(i//cols)*height
        canvas.paste(thumb,(x+(width-thumb.width)//2,y+5))
        artist=str(work.get("artist_id") or "")
        title=str(work.get("title") or "")
        # Pillow's default font may not support all diacritics; avoid a
        # rendering exception while keeping original UTF-8 in the JSON.
        artist=artist.encode("ascii","replace").decode()
        title=title.encode("ascii","replace").decode()
        painter.text((x+4,y+147),artist[:27],fill=(25,32,38))
        painter.text((x+4,y+162),title[:30],fill=(50,53,60))
        painter.text((x+4,y+176),"HOLD - visual review",fill=(90,52,45))
    SHEET.parent.mkdir(parents=True,exist_ok=True)
    canvas.save(SHEET,quality=85,optimize=True)


def render_html(rows):
    items=[]
    for r in rows:
        title=html.escape(str(r.get("title") or ""))
        url=r.get("preview_url") or ""
        if not safe_preview(url):
            continue
        artist=html.escape(str(r.get("artist_id") or ""))
        link=html.escape(str(r.get("record_url") or ""))
        status=html.escape(str(r.get("status") or ""))
        target=html.escape(str(r.get("explicit_work_target") or ""))
        items.append(f'<article><a href="{link}" rel="noreferrer"><img loading="lazy" src="{html.escape(url)}" alt="{title}"></a><p><b>{artist}</b> {title}</p><small>{target} / {status} / HOLD RIGHTS</small></article>')
    content=("\u003c!doctype html><html lang=\"it\"><meta charset=\"utf-8\">"
       "<title>Art Drift — Artist visual research (HOLD)</title>"
       "<style>body{background:#121822;color:#f6f7fa;font:14px system-ui;margin:2rem}"
       "main{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:16px}"
       "article{background:#242d3b;padding:12px;border-radius:12px}"
       "img{width:100%;height:220px;object-fit:contain;background:#121822}"
       "p{min-height:42px}small{color:#d6c6af}</style>"
       "<h1>Art Drift — ricerca visiva: solo HOLD, non utilizzabili nell'app</h1><main>"
       +"".join(items)+"</main></html>")
    HTML.write_text(content,encoding="utf-8")


def run(report, max_images=35, pause=time.sleep, receiver=download):
    selected=select(report,max_total=max_images)
    images=[]
    result=[]
    fail=Counter()
    blocked=False
    for work in selected:
        outcome={k:work.get(k) for k in (
            "artist_id","title","identity","record_url","preview_url",
            "explicit_work_target","source","source_license_claim")}
        outcome["commercially_approved"]=False
        outcome["runtime_visible"]=False
        outcome["license_territory_status"]="HOLD"
        outcome["human_visual_approval"]="PENDING"
        if blocked:
            outcome["status"]="NOT_TRIED_AFTER_REMOTE_THROTTLE"
        else:
            try:
                measures,sha,thumb=receiver(work["preview_url"])
                outcome.update(status="PIXELS_CHECKED_HOLD",
                    color_metrics=measures,pixel_sha256=sha,
                    color_tier=color_tier(measures))
                images.append((work,thumb))
            except Exception as e:
                msg=str(e)
                if (getattr(e,"code",None) in (429,503) or
                        re.search(r"\b(?:429|503)\b",msg)):
                    blocked=True
                outcome["status"]="HOLD_IMAGE_ERROR"
                outcome["error"]=msg[:160]
                fail["image_errors"]+=1
            pause(.4)
        result.append(outcome)
    render_sheet(images)
    render_html(result)
    return {
        "schema_version":1,
        "as_of_utc":datetime.now(timezone.utc).isoformat(),
        "selection_policy":"USER_ARTISTS_ROUND_ROBIN_WITH_EXACT_WORK_PRIORITY",
        "sample_size":len(selected),
        "decoded_images":len(images),
        "image_errors":fail["image_errors"],
        "host_throttled":blocked,
        "technical_color_pass":sum(1 for x in result if x.get(
            "color_tier") and not str(x["color_tier"]).startswith("HOLD")),
        "painter_image_counts":dict(Counter(x["artist_id"] for x in result
                                           if x["status"]=="PIXELS_CHECKED_HOLD")),
        "records":result,
        "visually_curated_and_approved":0,
        "commercially_approved":0,
        "runtime_imported":0,
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--max-images",type=int,default=35)
    a=parser.parse_args()
    if not 1<=a.max_images<=40:
        parser.error("--max-images 1..40")
    report=json.loads(SHORTLIST.read_text(encoding="utf-8"))
    data=run(report,max_images=a.max_images)
    OUTPUT.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",
                      encoding="utf-8")
    print(json.dumps({k:v for k,v in data.items() if k!="records"},
                     ensure_ascii=False),flush=True)


if __name__=="__main__":
    main()
