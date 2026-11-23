#!/usr/bin/env python3
"""Reproducible pixel-based mood curation of already-packaged open-access previews.

No network, no new rights grant, no new artworks or image downloads.
Only existing, source-policy-eligible WebP pixels are analyzed.
"""
import argparse
import colorsys
import csv
import json
import math
import re
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit
from PIL import Image, ImageOps, ImageStat, ImageDraw
import cv2
import numpy as np
cv2.setNumThreads(1)
FACE_CASCADE=cv2.CascadeClassifier(cv2.data.haarcascades+"haarcascade_frontalface_default.xml")
if FACE_CASCADE.empty():
    raise RuntimeError("OpenCV frontal face classifier unavailable")

PORTRAIT_TITLE=re.compile(r"(?iu)\b(portrait|portret|portræt|porträtt|portratt|portraet|portr[aä]t|ritratto|retrato|bildnis|selvportr[aæ]t|zelfportret|autoportrait|autorretrato|auto[- ]?retrato|self[- ]?portrait|head of|head study|bust of|likeness of|face of)\b")
PERSON_TITLE=re.compile(r"(?iu)\b(lady|girl|woman|young man|young woman|young lady|boy|gentleman|mrs\.?|mr\.?|miss\b|mademoiselle|madame|queen|countess|duchess|princess|prince|herzog|frau|fr[äa]ulein|femme|jeune fille|junge frau|dame|hoved|kvinne|kvinde|dronning|pigen|pige|t[êe]te|head\b|bust\b|bishop\b|cardinal\b|duke\b|sitter|sitters|sitting man|seated man|seated woman|figure\b)\b")
SCENE_TITLE=re.compile(r"(?iu)\b(landscape|still life|landskab|fountain|park|garden|flower|fish|bird|cat|dog|horse|tree|winter|summer|sea|beach|house|forest|mountain|river|field|flowers|kitchen|christ|virgin|madonna|angel|battle|annunciation|crucifixion)\b")
NONPORTRAIT_SUBJECT=re.compile(r"(?iu)\b(landscape|landskab|paysage|paesaggio|landschaft|sea|mountain|sky|river|valley|forest|garden|flower|flowers|rose|still life|nature morte|stilleven|stilleben|abstract|composition|sunset|sunrise|waterlilies|water lilies|trees|bridge|bouquet|fruit)\b")

FAVORITES=("van gogh","matisse","monet","kandinsky","delaunay",
    "gauguin","renoir","chagall","bonnard","cezanne","pissarro",
    "degas","klee","cassat","derain","signac","kirchner","turner")
HOSTS={"cleveland":{"openaccess-cdn.clevelandart.org"},
    "met":{"images.metmuseum.org"},"nga":{"api.nga.gov","media.nga.gov"},
    "rijks":{"iiif.micr.io"},"smithsonian":{"ids.si.edu"},
    "smk":{"iip.smk.dk","iip-thumb.smk.dk"},"getty":{"media.getty.edu"}}

def safe_record(row):
    source=row.get("museum_source") or "aic"
    if row.get("is_public_domain") is not True:return False
    if source=="aic":return bool(re.fullmatch(r"[a-fA-F0-9-]{16,64}",
        row.get("image_id") or ""))
    rights=(row.get("rights_license") or "").lower()
    if not any(t in rights for t in ("cc0","public domain")):return False
    try:
        proof=urlsplit(row.get("rights_evidence_url") or "")
        url=urlsplit(row.get("remote_preview_url") or "")
        return (proof.scheme=="https" and bool(proof.hostname) and
            not proof.username and url.scheme=="https" and
            url.hostname in HOSTS.get(source,set()) and not url.username and
            url.port in (None,443))
    except ValueError:return False

def local_file(root,row):
    src=row.get("museum_source") or "aic"
    n=str(row["id"])
    paths=[root/"assets/gallery/thumbs"/(n+".webp")] if src=="aic" else [
        root/"assets/museums/thumbs"/(src+"_"+n+".webp"),
        root/"web/museum_thumbs"/(src+"_"+n+".webp")]
    return next((p for p in paths if p.is_file()),None)

def metrics(path):
    if not (1200 <= path.stat().st_size <= 25000):return None
    try:
        with Image.open(path) as opened:
            if opened.format!="WEBP" or min(opened.size)<120:return None
            im=ImageOps.exif_transpose(opened).convert("RGB").resize((48,48))
            if min(im.size)<40:return None
        hsv=[colorsys.rgb_to_hsv(*(v/255 for v in px)) for px in im.getdata()]
        n=len(hsv)
        vibrant=sum(s>.45 and .22<v<.95 for h,s,v in hsv)/n
        saturation=sum(s for h,s,v in hsv)/n
        white=sum(v>.96 and s<.10 for h,s,v in hsv)/n
        dark=sum(v<.13 for h,s,v in hsv)/n
        if white>.75 or dark>.75:return None
        hist=Counter(int(h*12)%12 for h,s,v in hsv if s>.22 and v>.2)
        entropy=0.
        if hist:
            count=sum(hist.values())
            entropy=-sum((k/count)*math.log2(k/count) for k in hist.values())/math.log2(12)
        contrast=min(1,ImageStat.Stat(im.convert("L")).stddev[0]/90)
        # A luminous chromatic area matters more than a few saturated pixels
        # against a nearly black or sepia painting. These are objective
        # image measures; they are not subjective beauty certifications.
        bright_color=sum(s>.30 and v>.50 for h,s,v in hsv)/n
        sepia=sum(.04<h<.16 and .17<s<.70 and .25<v<.73 for h,s,v in hsv)/n
        score=(.24*vibrant+.17*saturation+.16*entropy+
            .15*contrast+.28*bright_color)
        score*=max(.1,1-.65*(dark+white)-.28*sepia)
        return {"score":round(score,5),"saturation":round(saturation,4),
            "vibrant":round(vibrant,4),"bright_color":round(bright_color,4),
            "sepia":round(sepia,4),"entropy":round(entropy,4),
            "contrast":round(contrast,4),
            "hue":hist.most_common(1)[0][0] if hist else -1}
    except (OSError,ValueError):return None


def portrait_flag(title,image_path):
    """Conservative heuristic: title context + facial share of the small image.

    Measured category only; the Haar detector may miss side faces or see
    unrelated people, and title patterns may match historical narrative art.
    """
    title=title or ""
    if PORTRAIT_TITLE.search(title):return True
    if PERSON_TITLE.search(title) and not SCENE_TITLE.search(title):return True
    try:
        with Image.open(image_path) as im:
            im.thumbnail((120,120))
            gray=np.asarray(im.convert("L"))
        # Same parameters as the pre-merge 4,499-asset baseline audit.
        faces=FACE_CASCADE.detectMultiScale(
            gray,scaleFactor=1.25,minNeighbors=3,minSize=(17,17),
            flags=cv2.CASCADE_SCALE_IMAGE)
        height,width=gray.shape
        return any((w/width)*(h/height)>=.025 for x,y,w,h in faces)
    except (OSError,ValueError,cv2.error):
        return False

def reduce_portrait_share(chosen,all_results):
    original=[r for r in chosen if r["is_portrait"]]
    before=len(original)
    keep=(before*30)//100  # >=70% reduction, including odd baseline counts
    selected_keys={r["key"] for r in chosen}
    retained=[]
    seen_author=Counter()
    for row in sorted(original,key=lambda r:-r["score"]):
        if len(retained)>=keep:break
        if seen_author[row["author"]]>=7:continue
        retained.append(row["key"]);seen_author[row["author"]]+=1
    if len(retained)<keep:
        for row in sorted(original,key=lambda r:-r["score"]):
            if len(retained)>=keep:break
            if row["key"] not in retained:retained.append(row["key"])
    retained=set(retained)
    removed=[r for r in chosen if r["is_portrait"] and r["key"] not in retained]
    if not removed:return chosen,{"portrait_before":before,"portrait_after":before,
        "portraits_replaced":0,"reduction_pct":0.0}
    authors=Counter(r["author"] for r in chosen if not r["is_portrait"] or r["key"] in retained)
    titles={(r["author"],re.sub(r"\W+","",r["title"].lower())[:65])
        for r in chosen if not r["is_portrait"] or r["key"] in retained}
    pool=[r for r in all_results if r["key"] not in selected_keys and not r["is_portrait"]]
    pool.sort(key=lambda r:-(r["score"]+
        (.09 if r["role"]=="color" else 0)+
        (.05 if NONPORTRAIT_SUBJECT.search(r["title"]) else 0)+
        (.07 if r["priority_artist"] else 0)))
    picked=[];picked_keys=set()
    for cap in (18,26,99):
        for row in pool:
            if len(picked)>=len(removed):break
            title_key=(row["author"],re.sub(r"\W+","",row["title"].lower())[:65])
            if row["key"] in picked_keys or authors[row["author"]]>=cap or title_key in titles:
                continue
            picked.append(row);picked_keys.add(row["key"])
            authors[row["author"]]+=1;titles.add(title_key)
        if len(picked)>=len(removed):break
    if len(picked)!=len(removed):
        raise ValueError("Insufficient non-portrait licensed-source alternatives")
    replacements=iter(picked)
    final=[next(replacements) if r["is_portrait"] and r["key"] not in retained
        else r for r in chosen]
    after=sum(r["is_portrait"] for r in final)
    assert len(final)==len(chosen) and len({r["key"] for r in final})==len(final)
    assert after==keep and after*10<=before*3
    return final,{
        "portrait_before":before,"portrait_after":after,
        "portraits_replaced":len(removed),
        "reduction_pct":round((before-after)/before*100,2),
        "classification":"Title pattern or frontal face occupying at least 2.5% of thumbnail",
        "classification_limit":"Automatic heuristic; not full manual portrait certification",
        "original_work_ids_preserved":len(selected_keys & {r["key"] for r in final}),
        "new_image_files_added":0,
    }

def generate(root,out,count):
    files=["assets/gallery/catalog.json","assets/museums/catalog.json",
        "assets/museums/catalog_global.json"]
    rows={}
    for filename in files:
        for row in json.loads((root/filename).read_text()):
            key=(row.get("museum_source") or "aic")+":"+str(row.get("id"))
            rows.setdefault(key,row)
    results=[];excluded=Counter()
    for key,row in rows.items():
        if not safe_record(row):
            excluded["rights_or_source"]+=1;continue
        file=local_file(root,row)
        if not file:
            excluded["no_offline_webp"]+=1;continue
        stat=metrics(file)
        if stat is None:
            excluded["thin_or_unreadable"]+=1;continue
        flag=portrait_flag(row.get("title") or "",file)
        artist=(row.get("artist_title") or row.get("artist_display") or "").strip()
        al=artist.lower().split("(")[0].strip() or "unknown"
        priority=any(word in al for word in FAVORITES)
        role="color" if stat["vibrant"]>=.18 and stat["saturation"]>=.27 else "pause"
        results.append({"key":key,"artist":artist,"author":al,
            "title":row.get("title") or "Untitled","file":str(file.relative_to(root)),
            "source":row.get("museum_source") or "aic","role":role,
            "score":round(stat["score"]+(.16 if priority else 0),5),
            "color":stat,"priority_artist":priority,"is_portrait":flag})
    if len(results)<count:
        raise ValueError("Only "+str(len(results))+" assets found; expected at least "+str(count))
    results.sort(key=lambda x:(-x["score"],x["key"]))
    target_color=round(count*.78);target_pause=count-target_color
    count_roles=Counter(x["role"] for x in results)
    if count_roles["color"]<target_color:
        target_color=count_roles["color"];target_pause=count-target_color
    if count_roles["pause"]<target_pause:
        target_pause=count_roles["pause"];target_color=count-target_pause
    if target_color+target_pause<count:raise ValueError("Not enough mood coverage")
    remaining={x["key"]:x for x in results}
    authors=Counter();seen_titles=set();chosen=[];role_counts=Counter()
    for i in range(count):
        role="pause" if i%5==4 and role_counts["pause"]<target_pause else "color"
        if role_counts[role] >= (target_pause if role=="pause" else target_color):
            role="color" if role=="pause" else "pause"
        scored=[]
        for x in remaining.values():
            if x["role"]!=role:continue
            author=x["author"]
            title=(author,re.sub(r"\W+","",x["title"].lower())[:70])
            if authors[author]>=18 or title in seen_titles:continue
            if author in {y["author"] for y in chosen[-5:]}:continue
            matching=sum(y["color"]["hue"]==x["color"]["hue"] for y in chosen[-3:])
            s=x["score"]-.07*matching-.009*authors[author]
            scored.append((s,x["key"],title))
        if not scored:
            scored=[(x["score"],x["key"],(x["author"],x["key"]))
                for x in remaining.values() if x["role"]==role]
        if not scored:raise ValueError("Role distribution failed")
        _,key,title=max(scored)
        picked=remaining.pop(key)
        chosen.append(picked);seen_titles.add(title)
        authors[picked["author"]]+=1
        role_counts[role]+=1
    chosen,portrait_report=reduce_portrait_share(chosen,results)
    manifest={"schema_version":1,"selection":[x["key"] for x in chosen],
        "selected_count":len(chosen),"pool_count":len(results),
        "source_rights_policy_checked":True,"commercial_rights_certified":False,
        "actual_image_pixels_analyzed":True,"manual_visual_review_complete":False,
        "image_downloads":0,"reuses_existing_image_files":True,
        "portrait_policy":portrait_report}
    target=root/"assets/museums/canvas_visual_color_v1.json"
    target.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+"\n")
    out.mkdir(parents=True,exist_ok=True)
    with (out/"curation_audit.csv").open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f);w.writerow(["rank","key","artist","title","role",
            "score","saturation","vibrant","hue","image_path"])
        for i,x in enumerate(chosen,1):
            w.writerow([i,x["key"],x["artist"],x["title"],x["role"],x["score"],
                x["color"]["saturation"],x["color"]["vibrant"],x["color"]["hue"],x["file"]])
    sheet=Image.new("RGB",(12*130,10*144),(21,22,27))
    drawer=ImageDraw.Draw(sheet)
    for i,x in enumerate(chosen[:120]):
        xx=i%12*130;yy=i//12*144
        with Image.open(root/x["file"]) as pic:
            pic=ImageOps.contain(pic.convert("RGB"),(122,116))
            sheet.paste(pic,(xx+(122-pic.width)//2,yy+(116-pic.height)//2))
        drawer.text((xx+2,yy+119),x["artist"].split("(")[0][:19],fill=(240,240,240))
    sheet.save(out/"first_120_contact_sheet.jpg",quality=80)
    summary={"total_catalog":len(rows),"image_backed_candidates":len(results),
        "selected":len(chosen),"mood_counts":dict(role_counts),
        "unique_artists":len(authors),
        "van_gogh":sum("van gogh" in x["author"] for x in chosen),
        "matisse":sum("matisse" in x["author"] for x in chosen),
        "sample_first_10":[x["key"] for x in chosen[:10]],
        "portrait_policy":portrait_report,
        "excluded":dict(excluded),"sources":dict(Counter(x["source"] for x in chosen)),
        "reuses_existing_images":True,"commercial_release_gate_open":True}
    (out/"summary.json").write_text(json.dumps(summary,indent=2))
    print("CANVAS_VISUAL_CURATED",json.dumps(summary))
    return summary

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--repo",type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument("--out",type=Path,default=Path("build/visual-color"))
    parser.add_argument("--count",type=int,default=2400)
    args=parser.parse_args()
    generate(args.repo,args.out,args.count)
