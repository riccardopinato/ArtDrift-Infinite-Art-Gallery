import importlib.util
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("modern",ROOT/"tools/artdrift_modern_masters.py")
modern=importlib.util.module_from_spec(spec)
spec.loader.exec_module(modern)

class ModernArtAdmission(unittest.TestCase):
    def test_complete_source_inventory(self):
        works=modern.inventory()
        self.assertEqual(len(works),53)
        self.assertEqual(sum(x["rights_inventory_status"] in modern.BLOCKED for x in works),5)
        self.assertEqual(len(json.loads(modern.ARTISTS.read_text())["artists"]),109)
        self.assertTrue(all(w["publication_status"]=="HOLD" and not w["runtime_visible"]
                            for w in works))

    def sample(self):
        return {"object_number":"KMSr189","public_domain":True,"has_image":True,
                "rights":"https://creativecommons.org/publicdomain/mark/1.0/",
                "object_names":[{"name":"Collage"}], "artist":["Henri Matisse"],
                "titles":[{"title":"Zulma"}],
                "image_iiif_id":"https://iip.smk.dk/iiif/jp2/test"}

    def test_valid_collage_remains_territory_hold(self):
        row=modern.validate_smk(self.sample(),modern.inventory()[0],
                                 image_probe=lambda url:"f00d")
        self.assertEqual(row["title"],"Zulma")
        self.assertEqual(row["artwork_type_title"],"Collage")
        self.assertEqual(row["id"],modern.validate_smk(
            self.sample(),modern.inventory()[0],image_probe=lambda _: "f00d")["id"])
        self.assertFalse(row["worldwide_commercial_clearance"])
        self.assertFalse(row["runtime_visible"])
        self.assertEqual(row["publication_status"],"HOLD_TERRITORY_AND_CURATORIAL")

    def test_museum_object_mismatch_rejected(self):
        obj=self.sample()
        obj["object_number"]="KMSr174"
        with self.assertRaisesRegex(ValueError,"NATIVE_ID_MISMATCH"):
            modern.validate_smk(obj,modern.inventory()[0],image_probe=lambda _: "a")

    def test_copyright_or_missing_license_rejected(self):
        obj=self.sample();obj["public_domain"]=False
        with self.assertRaisesRegex(ValueError,"UNDERLYING_PUBLIC_DOMAIN_UNPROVEN"):
            modern.validate_smk(obj,modern.inventory()[0],image_probe=lambda _: "a")
        obj=self.sample();obj["rights"]="https://creativecommons.org/licenses/by-nc/4.0/"
        with self.assertRaisesRegex(ValueError,"IMAGE_RIGHTS_UNPROVEN"):
            modern.validate_smk(obj,modern.inventory()[0],image_probe=lambda _: "a")

    def test_no_untrusted_media_host_or_artist(self):
        obj=self.sample();obj["image_iiif_id"]="https://iip.smk.dk.evil.com/a"
        with self.assertRaisesRegex(ValueError,"NOT_OFFICIAL_IIIF"):
            modern.validate_smk(obj,modern.inventory()[0],image_probe=lambda _: "a")
        obj=self.sample();obj["artist"]=["Unknown Artist"]
        with self.assertRaisesRegex(ValueError,"ARTIST_MISMATCH"):
            modern.validate_smk(obj,modern.inventory()[0],image_probe=lambda _: "a")
        self.assertFalse(modern.safe("http://iip.smk.dk/a",modern.IMG_HOSTS))
        self.assertFalse(modern.safe("https://user@iip.smk.dk/a",modern.IMG_HOSTS))

    def test_painting_classification_does_not_auto_publish(self):
        obj=self.sample();obj["object_names"]=[{"name":"Painting"}]
        row=modern.validate_smk(obj,modern.inventory()[0],image_probe=lambda _: "a")
        self.assertEqual(row["artwork_type_title"],"Painting")
        self.assertFalse(row["runtime_visible"])

if __name__=="__main__":
    unittest.main()
