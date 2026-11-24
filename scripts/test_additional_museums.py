#!/usr/bin/env python3
"""Offline contract tests: Smithsonian museum provenance, CC0 media, IDs."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

FILE=Path(__file__).parent/"import_additional_museums.py"
spec=importlib.util.spec_from_file_location("artdrift_additional_museums",FILE)
museum=importlib.util.module_from_spec(spec)
spec.loader.exec_module(museum)


def sample(unit="chndm",native="123",kind="Textile",date="1967",
           rights="CC0",image_rights="CC0",image_host="ids.si.edu"):
    obj={
        "id":unit+"_"+native,
        "title":"Open Museum Work",
        "content":{
            "descriptiveNonRepeating":{
                "title":{"content":"Open Museum Work"},
                "record_ID":unit+"_"+native,
                "record_link":"https://www.si.edu/object/"+unit+"_"+native,
                "metadata_usage":{"access":rights},
                "online_media":{"media":[
                    {"usage":{"access":image_rights},
                     "thumbnail":"https://"+image_host+"/ids/deliveryService?id=X&max=1000"}
                ]},
            },
            "freetext":{
                "objectType":[{"content":kind}],
                "date":[{"content":date}],
                "name":[{"content":"Museum Creator"}],
                "physicalDescription":[{"content":"Material, original provenance"}],
            },
        },
    }
    return obj


class MuseumSourceGate(unittest.TestCase):
    def test_distinct_real_institutions_and_stable_native_ids(self):
        self.assertGreaterEqual(len(museum.UNITS),3)
        for unit,name in museum.UNITS.items():
            record=museum.parse(unit,sample(unit,native="101"))
            self.assertIsNotNone(record,unit)
            self.assertEqual(record["museum_name"],name)
            self.assertEqual(record["museum_source"],"smithsonian")
            self.assertEqual(record["museum_native_id"],unit+":"+unit+"_101")
            self.assertEqual(record["rights_license"],"CC0")
            self.assertTrue(record["remote_preview_url"].startswith("https://ids.si.edu/"))
        self.assertNotEqual(museum.stable_id("chndm","chndm_101"),
                            museum.stable_id("hmsg","hmsg_101"))

    def test_no_rights_invention_or_untrusted_hosts(self):
        self.assertIsNone(museum.parse("chndm",sample(rights="Restricted")))
        self.assertIsNone(museum.parse("chndm",sample(image_rights="Restricted")))
        self.assertIsNone(museum.parse("chndm",sample(image_host="evil.test")))
        self.assertIsNone(museum.parse("chndm",sample(kind="Bookbinding press release")))
        self.assertIsNone(museum.parse("unknown",sample()))
        self.assertEqual(museum.parse("chndm",sample(kind="Textile"))["artwork_type_title"],"Textile")
        self.assertEqual(museum.parse("hmsg",sample(kind="Oil Painting"))["artwork_type_title"],"Painting")

    def test_never_reinterpret_ambiguous_centuries_as_post1950(self):
        self.assertIsNone(museum.first_verified_year("mid-20th century"))
        self.assertEqual(museum.first_verified_year("1946 to 1968"),1946)
        self.assertEqual(museum.first_verified_year("1957"),1957)
        self.assertIsNone(museum.first_verified_year("2027"))

    def test_atomic_file_output_only_after_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            def get(unit,shard):
                if shard:
                    raise FileNotFoundError("Expected sampling gap")
                return (json.dumps(sample(unit,native="101"))+"\n").encode()
            report=museum.import_all(fetch=get,root=root,shards=2)
            self.assertEqual(report["museums_added"],len(museum.UNITS))
            self.assertEqual(report["record_count"],len(museum.UNITS))
            self.assertEqual(report["original_records_modified"],0)
            self.assertEqual(report["device_image_delivery"],"NOT_VERIFIED")
            rows=json.loads((root/"assets/museums/catalog_new_museums.json").read_text())
            self.assertEqual(len({row["id"] for row in rows}),len(museum.UNITS))
            self.assertEqual(set(row["museum_name"] for row in rows),set(museum.UNITS.values()))


if __name__=="__main__":
    unittest.main()
