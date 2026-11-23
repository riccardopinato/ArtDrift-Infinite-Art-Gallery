#!/usr/bin/env python3
"""Offline MediaWiki Commons license, author, source and import contract."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

FILE=Path(__file__).parent/"import_modern_commons.py"
spec=importlib.util.spec_from_file_location("artdrift_commons",FILE)
commons=importlib.util.module_from_spec(spec)
spec.loader.exec_module(commons)


def file_page(**updates):
    m={x:{"value":v} for x,v in {
      "LicenseShortName":"CC BY-SA 4.0",
      "LicenseUrl":"https://creativecommons.org/licenses/by-sa/4.0",
      "Artist":"Artwork Creator",
      "Credit":"Own work",
      "ObjectName":"Color Field",
    }.items()}
    base={"pageid":1234,"title":"File:Color Field.jpg","imageinfo":[{
      "mime":"image/jpeg","thumburl":"https://upload.wikimedia.org/wikipedia/commons/thumb/a/a1/image.jpg/700px-image.jpg",
      "descriptionurl":"https://commons.wikimedia.org/wiki/File:Color_Field.jpg",
      "user":"Artwork_Creator","extmetadata":m,
    }]}
    base.update(updates)
    return base


class CommonsModernTests(unittest.TestCase):
    def test_self_authored_and_cc_license(self):
        row=commons.parse(file_page(),2023)
        self.assertEqual(row["museum_source"],"commons")
        self.assertEqual(row["is_public_domain"],False)
        self.assertEqual(row["creation_year_verified"],2023)
        self.assertEqual(row["rights_license"],"CC BY-SA 4.0")
        self.assertTrue(row["remote_preview_url"].startswith("https://upload.wikimedia.org/"))
        self.assertIsNone(commons.parse(file_page(),1949))

    def test_reject_rights_and_identity_risks(self):
        base=file_page()
        info=base["imageinfo"][0]
        original=info["extmetadata"]
        for name, value in (("Artist","Other copyrighted artist"),
                            ("Credit","Museum photograph"),
                            ("LicenseShortName","CC BY-NC 4.0"),
                            ("LicenseUrl","https://evil.example/terms")):
            candidate=file_page()
            candidate["imageinfo"][0]["extmetadata"]={
                **original, name:{"value":value},
            }
            self.assertIsNone(commons.parse(candidate,2023),name)
        bad=file_page()
        bad["imageinfo"][0]["thumburl"]="https://upload.wikimedia.org.attacker.test/p.jpg"
        self.assertIsNone(commons.parse(bad,2023))

    def test_deterministic_offline_generation(self):
        def fake_fetch(year):
            if year==2023:
                return year,[commons.parse(file_page(),year)],1
            return year,[],0
        with tempfile.TemporaryDirectory() as temp:
            report=commons.generate(fake_fetch,Path(temp))
            rows=json.loads((Path(temp)/"catalog_modern_1950.json").read_text())
            self.assertEqual(report["admitted_records"],1)
            self.assertEqual(report["years"],77)
            self.assertEqual(rows[0]["id"],10_000_001_234)
            self.assertFalse(rows[0]["is_public_domain"])
            self.assertEqual(report["production_release"],"NOT_AUTHORIZED")


if __name__=="__main__":
    unittest.main()
