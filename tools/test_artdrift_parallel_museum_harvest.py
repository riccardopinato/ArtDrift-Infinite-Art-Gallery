"""Offline guards for independent metadata-first museum research lanes."""
from __future__ import annotations
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
import artdrift_parallel_museum_harvest as m

class MuseumLaneTests(unittest.TestCase):
    def test_all_nine_sources_independent(self):
        self.assertEqual(len(m.LANES),9)
        self.assertEqual(len(set(m.LANES)),9)
    def test_scenic_but_not_figure_centred(self):
        self.assertTrue(m.is_scenic("Sunlit landscape with gardens"))
        self.assertTrue(m.is_scenic("Summer meadow by a river"))
        self.assertFalse(m.is_scenic("Japanese Dolls with Apples"))
        self.assertFalse(m.is_scenic("Portrait of Woman in a Garden"))
    def test_no_runtime_import_path(self):
        self.assertIn("research/museums",str(m.OUT))
        self.assertNotIn("/assets/",str(m.OUT))
    def test_unknown_rights_never_approved(self):
        from unittest.mock import patch
        row={"pageid":12345,"title":"File:Sunlit Garden - Ateneum.jpg",
             "imageinfo":[{"mime":"image/jpeg","thumburl":"https://thumb.wikimedia.org/x.jpg",
                          "extmetadata":{}}]}
        with patch.object(m,"common_license",return_value=(False,{})):
            item=m.from_commons(row,"finnish_national_gallery","test",False)
        self.assertFalse(item["commercially_approved"])
        self.assertFalse(item["runtime_visible"])
        self.assertFalse(item["image_license_checked"])
    def test_no_false_catalog_zero(self):
        self.assertTrue(all(c.get("museum") for c in m.LANES.values()))
        self.assertTrue(m.OUT.name=="results")

if __name__=="__main__":
    unittest.main()
