"""Tests for Art Drift's 10/15/20 dark-fraction A/B policy."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location(
    "ab",ROOT/"tools/artdrift_dark_threshold_ab.py")
ab=importlib.util.module_from_spec(spec)
spec.loader.exec_module(ab)

def colors(dark=.05,luminance=.66,saturation=.38,vivid=.52):
    return {"dark_fraction":dark,"luminance":luminance,
            "saturation":saturation,"vivid_fraction":vivid}

class DarknessPolicyTests(unittest.TestCase):
    def test_10_15_20_recovery(self):
        c=colors(dark=.12)
        self.assertFalse(ab.pixel_eligible(c,.10))
        self.assertTrue(ab.pixel_eligible(c,.15))
        c=colors(dark=.18)
        self.assertFalse(ab.pixel_eligible(c,.15))
        self.assertTrue(ab.pixel_eligible(c,.20))
        self.assertFalse(ab.pixel_eligible(colors(dark=.21),.20))

    def test_no_dark_image_without_brightness(self):
        self.assertFalse(ab.pixel_eligible(colors(dark=.12,luminance=.45),.20))
        self.assertFalse(ab.pixel_eligible(colors(dark=.12,vivid=.08),.20))
        self.assertFalse(ab.pixel_eligible(colors(dark=.12,saturation=.09),.20))

    def test_intermediate_dark_requires_high_chroma(self):
        self.assertEqual(ab.color_tier(colors(dark=.14)),
                         "PREFERRED_AT_MOST_15_PERCENT_DARK")
        self.assertEqual(ab.color_tier(colors(dark=.17)),
                         "CONDITIONAL_15_TO_20_PERCENT__HIGH_CHROMA")
        self.assertEqual(ab.color_tier(colors(dark=.17,saturation=.20,vivid=.22)),
                         "HOLD_15_TO_20_PERCENT__NOT_VIVID_ENOUGH")
        self.assertEqual(ab.color_tier(colors(dark=.21)),
                         "HOLD_DARK_OR_MUTED")

    def test_no_double_count_shards_and_missing_metric_not_pass(self):
        with tempfile.TemporaryDirectory() as d:
            base=Path(d)/"commons"
            for i in (1,2):
                p=base/str(i)/f"batch_{i:02d}"
                p.mkdir(parents=True)
                payload={"images_probed":3,"works":[
                    {"file_pageid":20,"color_metrics":colors(dark=.02)}],
                    "holds":[{"id":21,"reason":"DARK_OR_MUTED",
                              "color_metrics":colors(dark=.18)},
                             {"id":22,"reason":"HTTP_403"}]}
                (p/"review.json").write_text(json.dumps(payload))
            prior=ab.EVIDENCE
            ab.EVIDENCE=Path(d)
            try:
                rec,shards=ab.observations(base)
            finally:
                ab.EVIDENCE=prior
            self.assertEqual(len(rec),2)
            self.assertEqual(ab.eligible_count(rec,.10),1)
            self.assertEqual(ab.eligible_count(rec,.15),1)
            self.assertEqual(ab.eligible_count(rec,.20),2)
            self.assertEqual(len(shards),2)

    def test_nga_historical_dark_restore(self):
        data=ab.nga_reinstate()
        self.assertEqual(data["reinstated_at_15"],2)
        self.assertEqual(data["reinstated_at_20"],2)

if __name__=="__main__":unittest.main()
