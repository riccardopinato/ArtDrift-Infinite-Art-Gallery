#!/usr/bin/env python3
"""Read-only diagnostic of false-negative paths in Art Drift new-museum research."""
import json,re,sys,collections,xml.etree.ElementTree as ET
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from artdrift_eu_new_museums_batch import (fetch,NS,staedel_records,staedel_parse,scene_title,
  jget,sweden_object,commons_search,search_rijks,RIJKS_QUERIES,NAT_QUERIES,ROOT)
from artdrift_eu_source_probe import SOURCES
OUT=ROOT/"research/museums/20261126/false_negative_diagnostics.json"
def staedel():
    data={"inspected_record_count":0,"lido_nodes_found":0,"recid_looks_like":[],"lido_first_record_child_tags":[],"field_count":{}}
    counts=collections.Counter();links=collections.Counter();types=collections.Counter();names=[]
    try:record=staedel_records()
    except Exception as e:return {"error":str(e)[:250]}
    data["inspected_record_count"]=len(record)
    for r in record:
        e=r.find(".//lido:lido",NS)
        if e is None:continue
        data["lido_nodes_found"]+=1
        if not data["lido_first_record_child_tags"]:
            data["lido_first_record_child_tags"]=[x.tag for x in e[:20]]
            data["example_top_32_xml_leaf_paths"]=[
                {"tag":x.tag,"text":str(x.text or "")[:110],"attrs":dict(x.attrib)}
                for x in e.iter() if x.text and x.text.strip()][:32]
        ids=[x.text for x in e.findall(".//lido:lidoRecID",NS) if x.text]
        if ids and len(data["recid_looks_like"])<5:data["recid_looks_like"].append(ids[0])
        for x in e.iter():
            if not isinstance(x.tag,str):continue
            local=x.tag.rsplit("}",1)[-1];counts[local]+=1
            if local=="linkResource" and x.text:
                try:
                    from urllib.parse import urlsplit
                    links[urlsplit(x.text.strip()).hostname or "none"]+=1
                except:pass
            if local=="titleSet":
                v=" ".join(t.text.strip() for t in x.iter()
                           if isinstance(t.tag,str) and t.tag.endswith("appellationValue") and t.text)
                if v and len(names)<20:names.append(v[:90])
    data["element_local_name_counts"]=dict(counts.most_common(30))
    data["image_resource_host_counts"]=dict(links)
    data["example_titles"]=names[:20]
    data["current_st_idx_parsed"]=sum(bool(staedel_parse(x)) for x in record)
    return data

def sweden():
    data={"raw_searches":{},"sample_first_200_rejection_reasons":collections.Counter(),
          "examples":[ ]}
    for term in ("landscape","summer","blom","sea"):
        try:rows=commons_search(term)
        except Exception as e:data["raw_searches"][term]={"error":str(e)[:170]};continue
        data["raw_searches"][term]={"pages":len(rows)}
        for w in rows[:8]:
            title=w.get("title","")
            part=title.split(" (",1)[0]
            reasons=[]
            if "Nationalmuseum" not in title:reasons.append("wrong_institution")
            if not scene_title(part):reasons.append("title_mismatch")
            ii=(w.get("imageinfo") or [{}])[0]
            e=ii.get("extmetadata") or {}
            from artdrift_eu_new_museums_batch import common_license, author_year_from_doc
            if not common_license(e)[0]:reasons.append("license")
            if not author_year_from_doc((e.get("DateTimeOriginal") or {}).get("value")):reasons.append("no_original_creation_year")
            if len(data["examples"])<15:data["examples"].append({
                "title":title[:140],"part":part[:100],"reasons":reasons,
                "year_raw":str((e.get("DateTimeOriginal") or {}).get("value"))[:130],
                "license":str((e.get("LicenseShortName") or {}).get("value"))[:60],
                "mime":str(ii.get("mime"))})
            for reason in reasons:data["sample_first_200_rejection_reasons"][reason]+=1
    data["sample_first_200_rejection_reasons"]=dict(data["sample_first_200_rejection_reasons"])
    return data

def rijks():
    j={"groups":[]}
    for terms in RIJKS_QUERIES:
        n=0;tot=0
        for term in terms:
            try:ids,t=search_rijks(term)
            except Exception as e:j["groups"].append({"term":term,"error":str(e)[:90]});continue
            n+=len(ids);tot+=t
            j["groups"].append({"term":term,"listed_page_1":len(ids),"catalog_total":t,
                                "unread_matches_due_to_pagination":max(t-len(ids),0)})
    return j
def main():
    report={"schema_version":1,"as_of":"2026-11-26","audit_kind":"FALSE_NEGATIVE_ROOT_CAUSE",
            "source":"actual official Rijks/Sweden/Städel API endpoints",
            "rijks":rijks(),"nationalmuseum_se":sweden(),"staedel":staedel(),
            "runtime_imported":0}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({"rijks":report["rijks"],"sweden":report["nationalmuseum_se"],
      "staedel":report["staedel"]},ensure_ascii=False)[:22000])
if __name__=="__main__":main()
