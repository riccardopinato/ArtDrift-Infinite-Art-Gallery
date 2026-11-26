"""Offline guards for fair artist sample, preview-source safety and HOLD pixels."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))

from PIL import Image
import artdrift_user_artist_visual_pixels as m


def item(artist,seq,exact=None,license="Public domain",title="Lake landscape"):
    return {"artist_id":artist,"identity":artist+":"+str(seq),
            "title":title,"preview_url":"https://upload.wikimedia.org/x.jpg",
            "record_url":"https://commons.wikimedia.org/wiki/X",
            "source_license_claim":license,
            "curatorial_score":40+seq,"explicit_work_target":exact,
            "source":"wikimedia_artist_category"}


class PixelEvidenceTests(unittest.TestCase):
    def test_strict_host_allowlist(self):
        self.assertTrue(m.safe_preview("https://upload.wikimedia.org/wikipedia/commons/thumb/x.jpg"))
        self.assertTrue(m.safe_preview("https://thumb.wikimedia.org/x.jpg"))
        self.assertFalse(m.safe_preview("https://example.com/image.jpg"))
        self.assertFalse(m.safe_preview("http://upload.wikimedia.org/img.jpg"))
        self.assertFalse(m.safe_preview("https://upload.wikimedia.org.evil.tld/x"))
    def test_fair_painter_sampling_and_exact_target_priority(self):
        rows=[item("artistA",i) for i in range(10)]
        rows.append(item("artistB",12,exact="karsten_blue_kitchen",
                         title="The Blue Kitchen"))
        rows.extend(item("artistB",j) for j in range(2))
        rows.extend(item("artistC",j) for j in range(3))
        sample=m.select({"priority_shortlist":rows},per_artist=2,max_total=6)
        self.assertEqual(len(sample),6)
        self.assertEqual({x["artist_id"] for x in sample},
                         {"artistA","artistB","artistC"})
        self.assertEqual(next(x for x in sample
                              if x["artist_id"]=="artistB")["explicit_work_target"],
                         "karsten_blue_kitchen")
    def test_reject_nonpainting_pdf_and_restricted_claim(self):
        rows=[item("A",1,title="Portrait of Somebody"),
              item("B",2,license="CC BY-NC"),
              item("C",3,title="Summer landscape")]
        sample=m.select({"priority_shortlist":rows})
        self.assertEqual(len(sample),1)
        self.assertEqual(sample[0]["artist_id"],"C")
    def test_actual_raster_evidence_never_approved(self):
        rows=[item("A",1,exact="caillebotte_yerres_skiffs"),
              item("B",2,exact="karsten_blue_kitchen")]
        def receiver(url):
            return {"dark_fraction":.06,"luminance":.7,
                    "saturation":.3,"vivid_fraction":.31,
                    "bright_pass":True},"123abc",Image.new("RGB",(80,60))
        with patch.object(m,"render_sheet"),patch.object(m,"render_html"), \
             patch.object(m,"color_tier",return_value="PASS_PREFERRED"):
            result=m.run({"priority_shortlist":rows},max_images=2,
                         receiver=receiver,pause=lambda _:None)
        self.assertEqual(result["decoded_images"],2)
        self.assertEqual(result["technical_color_pass"],2)
        self.assertEqual(result["commercially_approved"],0)
        self.assertEqual(result["visually_curated_and_approved"],0)
        self.assertTrue(all(x["runtime_visible"] is False for x in result["records"]))
    def test_throttle_stops_followups(self):
        import urllib.error
        rows=[item("A",1),item("B",2)]
        counter=[0]
        def receiver(url):
            counter[0]+=1
            raise urllib.error.HTTPError(url,429,"Too Many Requests",{},None)
        with patch.object(m,"render_sheet"),patch.object(m,"render_html"):
            result=m.run({"priority_shortlist":rows},max_images=2,
                         receiver=receiver,pause=lambda _:None)
        self.assertTrue(result["host_throttled"])
        self.assertEqual(counter[0],1)


if __name__=="__main__":
    unittest.main()
