"""Offline test suite for user-artist source discovery and shortlist."""
from __future__ import annotations
import unittest
from unittest.mock import patch
from pathlib import Path
import sys
import urllib.error
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
import artdrift_user_artist_pipeline as m


def fake_seed():
    return {
        "artists":[
            {"id":"serhii_vasylkivskyi","aliases":["Serhii Vasylkivskyi","Sergey Vasilkovsky"],"commons_categories":["Category:Paintings by Serhii Vasylkivskyi"]},
            {"id":"ludvig_karsten","aliases":["Ludvig Karsten"],"commons_categories":["Category:Paintings by Ludvig Karsten"]},
            {"id":"alfred_sisley","aliases":["Alfred Sisley"],"commons_categories":["Category:Paintings by Alfred Sisley"]},
        ],
        "explicit_works":[
            {"id":"karsten_blue_kitchen","artist_id":"ludvig_karsten","title_aliases":["Det blå kjøkken","The Blue Kitchen"],"work_reference_ids":["NG.M.01507"]},
            {"id":"sisley_villeneuve_bridge","artist_id":"alfred_sisley","title_aliases":["The Bridge at Villeneuve-la-Garenne"],"work_reference_ids":["64.287"]},
        ]
    }


def row(source,number,title,artist="",color=None):
    v={"source":source,"museum_native_id":str(number),"title":title,"artist":artist,
       "museum_url":"https://commons.wikimedia.org/w/index.php?curid="+str(number),
       "remote_preview_url":"https://upload.wikimedia.org/a.jpg",
       "image_license_per_item":"Public domain",
       "runtime_visible":False,"commercially_approved":False}
    if color:v["color_tier"]=color
    return v


def museum_reports():
    return {p:{"provider":p,"review_candidates":[],"runtime_imported":0,
                "commercially_approved":0} for p in m.PROVIDERS}


class ArtistPipelineTests(unittest.TestCase):
    def test_normalization_and_variant_matching(self):
        seed=fake_seed()
        self.assertEqual(m.norm("Det blå kjøkken"),"det bla kjokken")
        self.assertEqual(m.artist_id(row("staedel",3,"Landscape","Sergey Vasilkovsky"),seed),"serhii_vasylkivskyi")
        self.assertEqual(m.artist_id(row("staedel",4,"Det blå kjøkken","Ludvig Karsten"),seed),"ludvig_karsten")
        self.assertEqual(m.target_id(row("staedel",4,"Det blå kjøkken","Ludvig Karsten"),
                                     seed,"ludvig_karsten"),"karsten_blue_kitchen")
        self.assertEqual(m.target_id(row("staedel",4,"The Blue Kitchen - NG.M.01507",
                                        "Ludvig Karsten"),seed,"ludvig_karsten"),"karsten_blue_kitchen")
    def test_public_license_is_not_commercial_approval(self):
        p={"pageid":145,"title":"File:Ludvig Karsten - The Blue Kitchen.jpg",
           "imageinfo":[{"mime":"image/jpeg","thumburl":"https://upload.wikimedia.org/thumb/x.jpg",
                         "extmetadata":{"LicenseShortName":{"value":"Public domain"},
                                        "Artist":{"value":"Ludvig Karsten"}}}]}
        r=m.parse_commons(p,"ludvig_karsten","Category:Paintings by Ludvig Karsten")
        self.assertEqual(r["image_license_per_item"],"Public domain")
        self.assertTrue(r["public_domain_statement_present"])
        self.assertFalse(r["commercially_approved"])
        self.assertFalse(r["runtime_visible"])
        self.assertFalse(r["institutional_origin_confirmed"])
        p["imageinfo"][0]["mime"]="application/pdf"
        self.assertIsNone(m.parse_commons(p,"ludvig_karsten","x"))
    def test_resume_cursor_on_429_and_dont_erase_rows(self):
        seed={"artists":[{"id":"ludvig_karsten","commons_categories":["Category:Paintings by Ludvig Karsten"]}]}
        calls=[]
        def fetch(query):
            calls.append(query)
            if len(calls)==1:
                return {"query":{"pages":[{"pageid":145,"title":"File:Kitchen.jpg",
                         "imageinfo":[{"mime":"image/jpeg","url":"https://upload.wikimedia.org/a.jpg"}]}]},
                         "continue":{"continue":"-||","gcmcontinue":"segment2"}}
            raise urllib.error.HTTPError("https://commons.wikimedia.org",429,"Too Many Requests",{},None)
        r=m.discover(seed,{},max_pages=8,caller=fetch,pause=lambda x:None)
        self.assertTrue(r["source_host_throttled"])
        self.assertEqual(r["total_distinct_commons_files"],1)
        self.assertEqual(r["pages_retrieved_this_run"],1)
        progress=r["query_progress"]["ludvig_karsten|Category:Paintings by Ludvig Karsten"]
        self.assertEqual(progress["continuation"]["gcmcontinue"],"segment2")
        def fetch2(query):
            self.assertEqual(query["gcmcontinue"],"segment2")
            return {"query":{"pages":[{"pageid":146,"title":"File:Garden.jpg",
                   "imageinfo":[{"mime":"image/jpeg","url":"https://upload.wikimedia.org/a.jpg"}]}]}}
        nxt=m.discover(seed,r,8,caller=fetch2,pause=lambda x:None)
        self.assertEqual(nxt["total_distinct_commons_files"],2)
        self.assertTrue(nxt["query_progress"]["ludvig_karsten|Category:Paintings by Ludvig Karsten"]["exhausted"])
        replay=m.discover(seed,nxt,8,caller=lambda _:self.fail("Should not request completed category"),pause=lambda x:None)
        self.assertEqual(replay["total_distinct_commons_files"],2)
    def test_cross_provider_file_id_dedup_and_exact_work(self):
        reports=museum_reports()
        reports["nasjonalmuseet"]["review_candidates"].append(row("nasjonalmuseet",145,
                                           "Ludvig Karsten - The Blue Kitchen - NG.M.01507","Ludvig Karsten"))
        reports["finnish_national_gallery"]["review_candidates"].append(row("finnish_national_gallery",145,
                                          "Ludvig Karsten - The Blue Kitchen - NG.M.01507","Ludvig Karsten"))
        reports["staedel"]["review_candidates"].append(row("staedel",3,
                                          "Sergey Vasilkovsky - Landscape","Sergey Vasilkovsky"))
        sourced={"total_distinct_commons_files":1,
                 "records_by_commons_pageid":{"145":{**row("wikimedia_artist_category",145,
                                          "Ludvig Karsten - The Blue Kitchen - NG.M.01507"),
                                         "artist_id":"ludvig_karsten"}}}
        result=m.build(fake_seed(),reports,sourced)
        self.assertEqual(result["artist_matched_distinct_files"],2)
        self.assertEqual(result["exact_work_family_matches"]["karsten_blue_kitchen"],1)
        self.assertEqual(result["matches_by_artist"]["ludvig_karsten"],1)
        self.assertEqual(result["commercially_approved"],0)
        self.assertTrue(all(not w["commercially_approved"] and not w["runtime_visible"]
                            for w in result["priority_shortlist"]))
    def test_reject_incomplete_nine_reports(self):
        with self.assertRaises(ValueError):
            m.build(fake_seed(),{},{})


if __name__=="__main__":
    unittest.main()
