"""Verify Städel stage 2 is added losslessly without publishing images."""
from __future__ import annotations
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
import artdrift_staedel_integrate_details as m


class IntegrationTests(unittest.TestCase):
    def test_existing_and_staged_are_union(self):
        old={"provider":"staedel","date_utc":"a","review_candidates":[
            {"source":"staedel","museum_native_id":"sg1","title":"Garden",
             "runtime_visible":False,"commercially_approved":False}],
             "source_identifier_sample":["oai:DE-MUS-048017:1"],
             "candidates_in_report":1,"runtime_imported":0,"commercially_approved":0}
        detail={"provider":"staedel","as_of_utc":"b","review_candidates":[
            {"source":"staedel","museum_native_id":"sg2","title":"Landscape",
             "runtime_visible":False,"commercially_approved":False}],
             "processed_oai_identifiers":["oai:DE-MUS-048017:2"],
             "total_new_metadata_processed":1,"runtime_imported":0,
             "commercially_approved":0}
        res=m.merge(old,detail)
        self.assertEqual(res["candidates_in_report"],2)
        self.assertEqual(res["cumulative_retained_source_identifiers"],2)
        self.assertEqual(res["commercially_approved"],0)
        self.assertEqual(m.queue(res)["ready_to_import"],0)
    def test_reject_cross_museum_source(self):
        old={"provider":"staedel","review_candidates":[],
             "commercially_approved":0,"runtime_imported":0}
        with self.assertRaises(ValueError):
            m.merge(old,{"provider":"birmingham"})


if __name__=="__main__":
    unittest.main()
