#!/usr/bin/env python3
"""Produce a truthful Art Drift visual audit board and optional bounded source comparison.

Only existing bundled thumbnails are displayed. New 585 candidate images remain
unloaded/unapproved. Remote comparisons are sampled from historical CC0/PD art,
subject to museum host allowlists. Network/visual failures are recorded, never faked.
"""
import argparse
import hashlib
import html
import io
import json
import shutil
import sys
from collections import Counter
from pathlib import Path
from urllib.request import Request,urlopen
from PIL import Image,ImageStat,ImageOps

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"cloudflare/art-catalog/scripts"))
from make_museum_d1_import import PREVIEW_HOSTS,official
Image.MAX_IMAGE_PIXELS=24_000_000

def files(root):
    result=[]
    for filename in ("assets/gallery/catalog.json","assets/museums/catalog.json"):
        data=json.loads((root/filename).read_text(encoding="utf8"))
        for item in data:
            path=item.get("bootstrap_asset")
            if not path:raise ValueError("Missing baseline artwork thumbnail")
            result.append((item,root/path))
    return result

def load_image(path):
    if not path.is_file():raise ValueError("Missing real image: "+str(path))
    with Image.open(path) as src:
        src.load()
        if src.width*src.height>24_000_000:raise ValueError("Oversized image")
        size=(src.width,src.height)
        thumb=src.convert("RGB")
    lum=ImageStat.Stat(thumb.convert("L"))
    return size,round(lum.mean[0],1)

def remote_compare(item,root_out,index):
    source=item.get("museum_source") or "aic"
    url=item.get("remote_preview_url") or ""
    if (not item.get("is_public_domain") is True or
        not official(url,PREVIEW_HOSTS.get(source,set()))):
        return {"status":"NO_SAFE_OFFICIAL_PREVIEW_URL"}
    try:
        req=Request(url,headers={"User-Agent":"ArtDrift-VisualQA/1.0","Accept":"image/*"})
        with urlopen(req,timeout=10) as response:
            content_type=response.headers.get("Content-Type","").split(";")[0].lower()
            if content_type not in ("image/jpeg","image/png","image/webp"):
                raise ValueError("Unexpected MIME "+content_type)
            payload=response.read(3_000_001)
            if len(payload)>3_000_000:raise ValueError("Remote image too large")
        with Image.open(io.BytesIO(payload)) as src:
            src.load()
            if src.width*src.height>24_000_000:raise ValueError("Remote pixel cap")
            image=src.convert("RGB")
            image.thumbnail((600,600))
            target=root_out/("remote-%03d.jpg"%index)
            image.save(target,format="JPEG",quality=85)
        return {"status":"REMOTE_IMAGE_DECODED_FOR_SIDE_BY_SIDE_REVIEW",
                "file":target.name,"bytes":len(payload)}
    except Exception as exc:
        return {"status":"REMOTE_UNAVAILABLE_NOT_VISUALLY_VERIFIED",
                "error":type(exc).__name__}

def inspect(root,out,board_size=100,remote_sample=0):
    out.mkdir(parents=True,exist_ok=True)
    image_out=out/"images";image_out.mkdir(exist_ok=True)
    entries=files(root)
    if len(entries)!=457:raise ValueError("Unexpected 457 baseline preview count")
    examined=[]
    seen_hashes={}
    duplicate_bytes=[]
    by_provider=Counter()
    for item,path in entries:
        dims,brightness=load_image(path)
        sha=hashlib.sha256(path.read_bytes()).hexdigest()
        source=item.get("museum_source") or "aic"
        by_provider[source]+=1
        if sha in seen_hashes:
            duplicate_bytes.append([seen_hashes[sha],item.get("id")])
        seen_hashes[sha]=item.get("id")
        original=item.get("thumbnail") or {}
        ow,oh=original.get("width"),original.get("height")
        mismatch=None
        if isinstance(ow,(int,float)) and isinstance(oh,(int,float)) and ow>0 and oh>0:
            ratio=(dims[0]/dims[1])/(ow/oh)
            if ratio <0.85 or ratio > 1.15:mismatch=round(ratio,3)
        examined.append({"source_key":source+":"+str(item["id"]),
            "title":item.get("title",""),
            "artist":item.get("artist_title") or item.get("artist_display") or "",
            "museum":item.get("museum_name") or source,
            "path":str(path.relative_to(root)),
            "dimensions":list(dims),"brightness":brightness,
            "sha256":sha,"image_vs_museum_reported_aspect_ratio":mismatch,
            "visual_approval":"NOT_REVIEWED"})
    # Representative deterministic spread; include all institutions before repeats.
    by_source={}
    for obj in examined:by_source.setdefault(obj["museum"],[]).append(obj)
    board=[]
    while len(board)<min(board_size,len(examined)) and any(by_source.values()):
        for k in sorted(by_source):
            if by_source[k] and len(board)<board_size:
                board.append(by_source[k].pop(len(by_source[k])//2))
    old={x["source_key"]:x for x in entries for _ in [0]}
    # old above intentionally replaced by direct stable lookup below.
    original={(item.get("museum_source") or "aic")+":"+str(item["id"]):item for item,_ in entries}
    cells=[]
    remote_attempted=0
    remote_decoded=0
    remote_status=Counter()
    for j,row in enumerate(board):
        img_path=root/row["path"]
        dest=image_out/("local-%03d.webp"%j)
        shutil.copy2(img_path,dest)
        r=None
        if remote_attempted<remote_sample:
            source=original[row["source_key"]]
            url=source.get("remote_preview_url") or ""
            provider=source.get("museum_source") or "aic"
            if official(url,PREVIEW_HOSTS.get(provider,set())) and source.get("is_public_domain") is True:
                remote_attempted+=1
                r=remote_compare(source,image_out,j)
                remote_status[r["status"]]+=1
                if r["status"]=="REMOTE_IMAGE_DECODED_FOR_SIDE_BY_SIDE_REVIEW":remote_decoded+=1
        local_link="images/"+dest.name
        remote_tag=('<img loading="lazy" src="images/'+r["file"]+'" alt="source preview">' if r and r.get("file")
                    else '<div class="missing">Original source: not compared</div>')
        title=html.escape(row["title"],quote=True)
        caption=html.escape(row["artist"],quote=True)
        museum=html.escape(row["museum"],quote=True)
        cells.append('<article><h3>'+title+'</h3><small>'+caption+' · '+museum+
            '</small><div class="pair"><figure><img loading="lazy" src="'+local_link+
            '" alt="bundled preview"><figcaption>Bundled preview</figcaption></figure><figure>'+
            remote_tag+'<figcaption>Official source (only if safely retrieved)</figcaption></figure></div>'+
            '<p>Dimensions: '+str(row["dimensions"])+
            ' · Aspect discrepancy: '+str(row["image_vs_museum_reported_aspect_ratio"])+
            ' · NOT VISUALLY APPROVED</p></article>')
    candidate_count=sum(len(json.loads((root/name).read_text(encoding="utf8"))) for name in
        ("assets/museums/catalog_new_museums.json","assets/museums/catalog_modern_1950.json"))
    summary={"baseline_real_thumbnails_decoded":len(examined),
        "candidate_metadata_without_packaged_image":candidate_count,
        "displayed_contact_cards":len(board),
        "remote_source_comparison_attempts":remote_attempted,
        "remote_source_comparisons_downloaded":remote_decoded,
        "remote_results":dict(remote_status),
        "byte_identical_preview_pairs":duplicate_bytes,
        "aspect_ratio_review_flags":sum(x["image_vs_museum_reported_aspect_ratio"] is not None for x in examined),
        "sources":dict(by_provider),
        "actual_user_visual_review":"PENDING",
        "app_flutter_screenshot_comparison":"NOT_EXECUTED",
        "new_candidate_rights_approval":"NOT_EXECUTED"}
    (out/"metrics.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n")
    (out/"work-image-audit.json").write_text(json.dumps(examined,ensure_ascii=False,indent=2)+"\n")
    style="body{background:#101117;color:#ead8b8;font:14px system-ui;margin:24px}h1{font-family:Georgia}p,small{color:#bcb2a5}section{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:16px}article{border:1px solid #786747;padding:12px;border-radius:9px}h3{margin:0 0 5px}.pair{display:grid;grid-template-columns:1fr 1fr;gap:8px}figure{margin:0}figure img{width:100%;height:180px;object-fit:contain;background:#222}figcaption{font-size:11px;color:#c5b390}.missing{height:180px;display:grid;place-items:center;color:#999;border:1px dashed #665}"
    markup='<!doctype html><html lang="en"><meta charset="utf-8"><title>Art Drift Visual QA</title><style>'+style+'</style><h1>Art Drift: sourced image comparison</h1><p>Local previews are real. New 585 candidates remain HOLD. Screenshots are not approval.</p><section>'+"".join(cells)+"</section></html>"
    (out/"review-board.html").write_text(markup,encoding="utf8")
    print("ARTDRIFT_VISUAL_SOURCE_AUDIT_PASS",len(examined),candidate_count,len(board),remote_attempted,remote_decoded)
    return summary

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=ROOT)
    p.add_argument("--out",type=Path,default=Path("build/artdrift-visual"))
    p.add_argument("--board-size",type=int,default=100)
    p.add_argument("--remote-sample",type=int,default=0)
    a=p.parse_args()
    if not 1<=a.board_size<=200 or not 0<=a.remote_sample<=20:raise ValueError("Unsafe QA size")
    inspect(a.root,a.out,a.board_size,a.remote_sample)
