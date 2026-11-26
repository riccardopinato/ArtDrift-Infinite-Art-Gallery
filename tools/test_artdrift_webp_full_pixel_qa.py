"""Synthetic fixtures guard full WebP QA mapping without legal certification."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from PIL import Image

from artdrift_webp_full_pixel_qa import audit, measure_webp


def setup(root,license="CC0",count=2):
    pack=root/"web/museum_thumbs"
    catalog=root/"assets/museums"
    pack.mkdir(parents=True)
    catalog.mkdir(parents=True)
    keys=[]
    items=[]
    for i in range(1,count+1):
        key=f"met:{i}"
        keys.append(key)
        items.append({"id":i,"museum_source":"met",
                      "title":f"Painting {i}",
                      "artwork_type_title":"Painting",
                      "is_public_domain":True,"rights_license":license,
                      "rights_evidence_url":"https://www.metmuseum.org/about-the-met/policies-and-documents/open-access"})
        painting=Image.new("RGB",(300,200))
        painting.putdata([((x*3+y*2+i*11)%256,
                           (x*2+y*5+i*19)%256,
                           (x*7+y*3+i*23)%256)
                          for y in range(200) for x in range(300)])
        painting.save(pack/f"met_{i}.webp","WEBP",quality=65)
    (pack/"manifest.json").write_text(json.dumps({"schema_version":1,"keys":keys}))
    (catalog/"catalog_global.json").write_text(json.dumps(items))


class WebpTechnicalCertificateTests(unittest.TestCase):
    def test_decoded_and_mapped_images_not_commercially_approved(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            setup(root)
            cert=audit(root,expected=2)
            self.assertEqual(cert["manifest_count"],2)
            self.assertEqual(cert["decoded_valid_webp_count"],2)
            self.assertEqual(cert["commercially_approved"],0)
            self.assertFalse(cert["all_images_work_copyright_confirmed"])
            self.assertEqual(sum(cert["technical_color_tiers"].values()),2)
    def test_reject_broken_webp(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            setup(root)
            (root/"web/museum_thumbs/met_1.webp").write_bytes(b"WRONG")
            with self.assertRaises(ValueError):
                audit(root,expected=2)
    def test_reject_unlicensed_source(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            setup(root,license="No known rights")
            with self.assertRaises(ValueError):
                audit(root,expected=2)
    def test_reject_orphan_webp(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            setup(root)
            Image.new("RGB",(30,30)).save(root/"web/museum_thumbs/met_999.webp","WEBP")
            with self.assertRaises(ValueError):
                audit(root,expected=2)
    def test_reject_duplicate_source_ids(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            setup(root)
            manifest=root/"web/museum_thumbs/manifest.json"
            manifest.write_text(json.dumps({"schema_version":1,"keys":["met:1","met:1"]}))
            with self.assertRaises(ValueError):
                audit(root,expected=None)


if __name__=="__main__":
    unittest.main()
