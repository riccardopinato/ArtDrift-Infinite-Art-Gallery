"""Offline guards for exact-source visual reasoning without auto publication."""
from __future__ import annotations
import unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
import artdrift_artist_visual_triage as m


def inputs():
    source={
       "records":[{"identity":"commons:1","status":"PIXELS_CHECKED_HOLD",
            "artist_id":"alfred_sisley","title":"Bridge",
            "record_url":"https://commons.wikimedia.org/?curid=1",
            "pixel_sha256":"a"*64,"source_license_claim":"CC0",
            "color_metrics":{"bright_pass":True,"dark_fraction":.01,
                             "luminance":.7}}],
    }
    decision={"works":[{"identity":"commons:1",
            "decision":"PRIORITY_MAIN_LUMINOUS","rationale":"Source verified"}],
            "commercially_approved":0,"runtime_imported":0}
    return decision,source


class VisualTriageTests(unittest.TestCase):
    def test_exact_pixel_source_validated(self):
        d,p=inputs()
        result=m.verify(d,p)
        self.assertEqual(result["reviewed_raster_samples"],1)
        self.assertEqual(result["priority_candidate_count"],1)
        self.assertEqual(result["technical_color_pass_count"],1)
        self.assertEqual(result["commercially_approved"],0)
        self.assertFalse(result["individual_decisions"][0]["human_user_acceptance"])
    def test_no_decision_without_measured_raster(self):
        d,p=inputs()
        d["works"][0]["identity"]="commons:wrong"
        with self.assertRaises(ValueError):
            m.verify(d,p)
    def test_no_fake_bright_acceptance(self):
        d,p=inputs()
        p["records"][0]["color_metrics"]["bright_pass"]=False
        with self.assertRaises(ValueError):
            m.verify(d,p)
    def test_no_global_app_approval(self):
        d,p=inputs()
        d["commercially_approved"]=1
        with self.assertRaises(ValueError):
            m.verify(d,p)
    def test_accent_exception_requires_specific_user_painting(self):
        d,p=inputs()
        d["works"][0]["decision"]="PRIORITY_ACCENT_INTERIOR_USER_CHOICE"
        with self.assertRaises(ValueError):
            m.verify(d,p)
    def test_near_miss_bounded(self):
        d,p=inputs()
        d["works"][0]["decision"]="PRIORITY_MAIN_NEAR_MISS"
        p["records"][0]["color_metrics"].update(dark_fraction=.06,luminance=.52,
                                                 bright_pass=False)
        self.assertEqual(m.verify(d,p)["priority_candidate_count"],1)
        p["records"][0]["color_metrics"]["dark_fraction"]=.25
        with self.assertRaises(ValueError):
            m.verify(d,p)


if __name__=="__main__":
    unittest.main()
