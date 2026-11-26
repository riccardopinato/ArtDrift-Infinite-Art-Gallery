"""Cross-museum duplicate detection tests, all offline."""
from __future__ import annotations
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
import artdrift_cross_museum_dedupe as d


def row(p, num, commons=None, sha=None,artist="A",title="Lush landscape",year=1880):
    return {"source":p,"museum_native_id":str(num),
            "museum_url":f"https://commons.wikimedia.org/w/index.php?curid={commons}" if commons else "",
            "image_sha256":sha or "","artist":artist,"title":title,"year":year,
            "commercially_approved":False,"runtime_visible":False}


def samples():
    return {p:{"provider":p,"runtime_imported":0,"commercially_approved":0,
               "review_candidates":[]} for p in d.PROVIDERS}


class CrossMuseumTests(unittest.TestCase):
    def test_exact_commons_page_across_two_museums_is_one_file(self):
        a=samples()
        a["nasjonalmuseet"]["review_candidates"].append(row("nasjonalmuseet",2,commons=999))
        a["finnish_national_gallery"]["review_candidates"].append(row("finnish_national_gallery",2,commons=999))
        r=d.build(a)
        self.assertEqual(r["records_retained_across_museums"],2)
        self.assertEqual(r["cross_museum_exact_file_clusters"],1)
        self.assertFalse(r["unique_paintings_proven"])
        self.assertEqual(r["commercially_approved"],0)
    def test_same_semantic_but_different_image_is_only_possible_match(self):
        a=samples()
        a["rijks"]["review_candidates"].append(row("rijks","r1"))
        a["staedel"]["review_candidates"].append(row("staedel","s1"))
        r=d.build(a)
        self.assertEqual(r["cross_museum_exact_file_clusters"],0)
        self.assertEqual(r["semantic_match_evidence_count"],1)
    def test_exact_pixel_sha_across_museum_even_without_commons(self):
        a=samples()
        sha="a"*64
        a["rijks"]["review_candidates"].append(row("rijks","r1",sha=sha))
        a["staedel"]["review_candidates"].append(row("staedel","s1",sha=sha))
        r=d.build(a)
        self.assertEqual(r["cross_museum_exact_file_clusters"],1)
    def test_no_missing_source_or_release(self):
        a=samples()
        a.pop("staedel")
        with self.assertRaises(ValueError):
            d.build(a)
        a=samples()
        a["staedel"]["review_candidates"].append(row("staedel","s1"))
        a["staedel"]["review_candidates"][0]["runtime_visible"]=True
        with self.assertRaises(ValueError):
            d.build(a)


if __name__=="__main__":
    unittest.main()
