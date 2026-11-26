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


    def test_commons_continuation_is_reused_and_host_429_stops_requests(self):
        from unittest.mock import patch
        from urllib.error import HTTPError
        from urllib.parse import parse_qs,urlsplit
        seen=[]
        def mock_get(url):
            q=parse_qs(urlsplit(url).query)
            seen.append(q)
            if len(seen)==1:
                return {"query":{"pages":[{"pageid":101,"title":"File:Garden.jpg"}]},
                        "continue":{"continue":"-||","gcmcontinue":"page-B"}}
            raise HTTPError(url,429,"Too Many Requests",{},None)
        with patch.object(m,"COMMONS_THROTTLED",False):
            with patch.object(m,"jget",side_effect=mock_get),patch.object(m.time,"sleep"):
                rows,pages,errs,cursor,done=m.get_image_pages(
                    {"generator":"categorymembers","gcmtitle":"Category:Painting",
                     "gcmtype":"file","gcmlimit":50},3)
                self.assertEqual(len(rows),1)
                self.assertFalse(done)
                self.assertEqual(pages,1)
                self.assertEqual(cursor["gcmcontinue"],"page-B")
                self.assertTrue(any("429" in x or "THROTTLED" in x for x in errs))
                rows2,pages2,errs2,_,done2=m.get_image_pages(
                    {"generator":"search","gsrsearch":"museum","gsrlimit":50},3)
                self.assertEqual((len(rows2),pages2,done2),(0,0,False))
                self.assertEqual(len(seen),2)
                self.assertTrue(errs2)
        with patch.object(m,"COMMONS_THROTTLED",False):
            seen.clear()
            def resume_only(url):
                q=parse_qs(urlsplit(url).query)
                self.assertEqual(q["gcmcontinue"],["page-B"])
                return {"query":{"pages":[{"pageid":102,"title":"File:Sunshine.jpg"}]}}
            with patch.object(m,"jget",side_effect=resume_only):
                rows,pages,errs,cursor,done=m.get_image_pages(
                    {"generator":"categorymembers","gcmtitle":"Category:Painting",
                     "gcmtype":"file","gcmlimit":50},3,
                    resume={"continue":"-||","gcmcontinue":"page-B"})
                self.assertTrue(done)
                self.assertIsNone(cursor)
                self.assertEqual(rows[0]["pageid"],102)

if __name__=="__main__":
    unittest.main()
