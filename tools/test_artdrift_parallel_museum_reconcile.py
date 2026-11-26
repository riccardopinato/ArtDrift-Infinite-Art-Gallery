"""Regression tests: partial retries must never delete museum research evidence."""
from __future__ import annotations
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
import artdrift_parallel_museum_reconcile as m


def item(key, **extras):
    return {"source":"birmingham","museum_native_id":key,
            "title":"Flower Garden at Sunrise","artist":"Painter",
            "remote_preview_url":"https://thumb.wikimedia.org/p.jpg",
            "institutional_origin_confirmed":True,
            "image_license_checked":True,
            "supported_image_format":True,"scenic_title_indicator":True,
            "runtime_visible":False,"commercially_approved":False, **extras}


def report(date, rows, errors=None):
    return {"provider":"birmingham","date_utc":date,"review_candidates":rows,
            "candidates_in_report":len(rows),
            "metadata_identifiers_discovered_or_scanned":len(rows),
            "source_identifier_sample":[x["museum_native_id"] for x in rows],
            "errors":errors or [],
            "stats":{"pixel_checked":len(rows)},
            "commercially_approved":0,"runtime_imported":0}


class ReconcileTests(unittest.TestCase):
    def test_partial_429_never_deletes_prior_records_or_color_measurements(self):
        older=report("a",[item("100", image_sha256="hash", color_tier="PASS",
                                 color_metrics={"dark_fraction":.06}),
                          item("200")])
        latest=report("b",[item("100")],[{"error":"HTTP Error 429"}])
        combined=m.reconcile(latest,older,None)
        self.assertEqual(combined["candidates_in_report"],2)
        self.assertEqual(combined["latest_run_candidates_in_report"],1)
        self.assertEqual(combined["cumulative_technical_color_pass_records"],1)
        self.assertEqual(combined["review_candidates"][0]["image_sha256"],"hash")
        self.assertEqual(len(combined["run_history"]),1)
        self.assertEqual(combined["commercially_approved"],0)
    def test_idempotent_if_same_report_loaded_again(self):
        original=report("a",[item("100"),item("200")])
        result=m.reconcile(original,None,None)
        replay=m.reconcile(original,result,None)
        self.assertEqual(replay["candidates_in_report"],2)
        self.assertEqual(len(replay["run_history"]),1)
        self.assertEqual(replay["cumulative_retained_source_identifiers"],2)
    def test_snapshot_and_latest_are_union_not_addition(self):
        snap=report("a",[item("100"),item("200")])
        prior=report("b",[item("200"),item("300")])
        latest=report("c",[item("300"),item("400")])
        combined=m.reconcile(latest,prior,snap)
        self.assertEqual([x["museum_native_id"] for x in
                          combined["review_candidates"]],["100","200","300","400"])
    def test_reject_cross_source_or_false_commercial_release(self):
        a=report("a",[item("100")])
        a["review_candidates"][0]["source"]="rijks"
        with self.assertRaises(ValueError):
            m.reconcile(a,None,None)
        bad=report("a",[])
        bad["commercially_approved"]=1
        with self.assertRaises(ValueError):
            m.reconcile(bad,None,None)
    def test_conflicted_license_never_auto_approves(self):
        old=report("a",[item("100",image_license_per_item="CC0")])
        new=report("b",[item("100",image_license_per_item="CC BY-SA 4.0")])
        result=m.reconcile(new,old,None)
        w=result["review_candidates"][0]
        self.assertEqual(len(w["license_claims_to_reconcile"]),2)
        self.assertFalse(w["commercially_approved"])
        self.assertEqual(w["review_status"],"HOLD_CONFLICTING_LICENSE_EVIDENCE")
    def test_queue_excludes_pdf_unconfirmed_portrait_and_out_of_period(self):
        old=report("a",[item("100",color_tier="PASS"),
                        {**item("200",color_tier="PASS"),"supported_image_format":False},
                        {**item("300",color_tier="PASS"),"title":"Portrait of Queen"},
                        {**item("400",color_tier="PASS"),"year":1742},
                        {**item("500",color_tier="PASS"),
                         "institutional_origin_confirmed":False}])
        r=m.queue(m.reconcile(old,None,None))
        self.assertEqual(len(r["items_for_review"]),1)
        self.assertEqual(r["items_for_review"][0]["museum_native_id"],"100")
        self.assertEqual(r["ready_to_import"],0)


if __name__=="__main__":
    unittest.main()
