import importlib.util
import sys
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
spec=importlib.util.spec_from_file_location("artdrift_smk_megabatch",ROOT/"tools/artdrift_smk_megabatch.py")
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
class SMKPolicies(unittest.TestCase):
    def test_languages_landscape(self):
        for title in ("Landskab ved kysten","Blomster i have","Sommerlandskab",
                      "Landscape at the Sea","Forår i skoven","Gule roser"):
            self.assertTrue(m.title_valid(title),title)
    def test_no_portrait(self):
        for title in ("Portræt af kvinde","Pige ved stranden","Woman in a Garden",
                      "Figure near trees","Mørk skov","Night Landscape"):
            self.assertFalse(m.title_valid(title),title)
    def test_year(self):
        self.assertEqual(m.date_year("1906-1909"),1906)
        self.assertIsNone(m.date_year("1775"))
        self.assertIsNone(m.date_year("circa 20th century"))
    def test_pd_image_classification(self):
        item={"public_domain":True,"has_image":True,
              "rights":"https://creativecommons.org/publicdomain/mark/1.0/",
              "object_names":[{"name":"Maleri"}],
              "image_iiif_id":"https://iip.smk.dk/iiif/jp2/a_KMS27.jp2",
              "object_number":"KMS27",
              "titles":[{"title":"Sommerlandskab ved havet"}],
              "artist":["Paul Test"],"production_date":[{"period":"1888"}]}
        self.assertIsNotNone(m.compatible(item))
        item["public_domain"]=False
        self.assertIsNone(m.compatible(item))
    def test_dedup_against_pending_pr(self):
        ids=m.prior_ids()
        self.assertGreater(len(ids),70)
        self.assertIn("kmsr189",ids)
        self.assertIn("dep717",ids)
if __name__=="__main__":unittest.main()
