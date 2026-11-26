"""Exact title lookup/artist identity and hold gates for supplied artworks."""
from __future__ import annotations
import unittest
from unittest.mock import patch
from pathlib import Path
import sys
import urllib.error
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
import artdrift_artist_exact_works as x


def seed():
    return {
     "artists":[
        {"id":"ludvig_karsten","aliases":["Ludvig Karsten"],"commons_categories":[]},
        {"id":"alfred_sisley","aliases":["Alfred Sisley"],"commons_categories":[]},
        {"id":"claude_monet","aliases":["Claude Monet"],"commons_categories":[]},
        {"id":"gustave_caillebotte","aliases":["Gustave Caillebotte"],"commons_categories":[]},
     ],
     "explicit_works":[
        {"id":"karsten_blue_kitchen","artist_id":"ludvig_karsten",
         "work_reference_ids":["NG.M.01507"],
         "title_aliases":["Det blå kjøkken","The Blue Kitchen"]},
        {"id":"caillebotte_yerres_skiffs","artist_id":"gustave_caillebotte",
         "work_reference_ids":[],"title_aliases":["Périssoires sur l'Yerres","Skiffs"]},
        {"id":"sisley_villeneuve_bridge","artist_id":"alfred_sisley",
         "work_reference_ids":["64.287"],
         "title_aliases":["The Bridge at Villeneuve-la-Garenne"]},
     ]}


def commons_page(i,title,artist):
    return {"pageid":i,"title":"File:"+title,"imageinfo":[{
       "mime":"image/jpeg","url":"https://upload.wikimedia.org/picture.jpg",
       "extmetadata":{"Artist":{"value":artist},"LicenseShortName":{"value":"Public domain"}}}]}


class ExactWorksTests(unittest.TestCase):
    def test_exact_karsten_direct_file_is_a_target_not_a_release(self):
        requests=[]
        def fetch(q):
            requests.append(q)
            return {"query":{"pages":[commons_page(151,
                "Ludvig Karsten - The Blue Kitchen - NG.M.01507 - National Museum of Art, Architecture and Design.jpg",
                "Ludvig Karsten")]}}
        result=x.search(seed(),{},1,getter=fetch,pause=lambda _:None)
        self.assertEqual(result["targeted_queries_executed_this_run"],1)
        self.assertEqual(result["targeted_new_files_this_run"],1)
        r=result["records_by_commons_pageid"]["151"]
        self.assertEqual(r["explicit_work_target"],"karsten_blue_kitchen")
        self.assertFalse(r["commercially_approved"])
        self.assertTrue(requests[0].get("titles","").startswith("File:Ludvig Karsten"))
    def test_generic_search_must_have_artist_evidence(self):
        def fetch(q):
            if "titles" in q:return {"query":{"pages":[]}}
            return {"query":{"pages":[commons_page(152,
                "The Yellow Garden.JPG","Another Artist"),
                commons_page(153,"Gustave Caillebotte - Périssoires sur l'Yerres.jpg",
                "Gustave Caillebotte")]}}
        r=x.search(seed(),{},2,getter=fetch,pause=lambda _:None)
        self.assertNotIn("152",r["records_by_commons_pageid"])
        self.assertEqual(r["records_by_commons_pageid"]["153"]["explicit_work_target"],
                         "caillebotte_yerres_skiffs")
    def test_throttle_stops_future_queries(self):
        calls=[]
        def blocked(q):
            calls.append(q)
            raise urllib.error.HTTPError("https://commons.wikimedia.org",429,"Too Many Requests",{},None)
        r=x.search(seed(),{},9,getter=blocked,pause=lambda _:None)
        self.assertTrue(r["targeted_source_host_throttled"])
        self.assertEqual(len(calls),1)
        self.assertEqual(r["targeted_queries_executed_this_run"],0)


if __name__=="__main__":
    unittest.main()
