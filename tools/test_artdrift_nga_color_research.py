import importlib.util
from pathlib import Path
import unittest
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("nga",ROOT/"tools/artdrift_nga_color_research.py")
nga=importlib.util.module_from_spec(spec)
spec.loader.exec_module(nga)

class NgaResearchPolicy(unittest.TestCase):
    def test_no_portraits(self):
        self.assertEqual(nga.title_score("Portrait of a Lady","Claude Monet",1910),0)
        self.assertEqual(nga.title_score("Self-Portrait in a Garden","Vincent van Gogh",1887),0)
        self.assertEqual(nga.title_score("Woman with a Sunflower","Mary Cassatt",1905),0)
        self.assertEqual(nga.title_score("Girl in a Boat with Geese","Berthe Morisot",1889),0)
        self.assertEqual(nga.title_score("Young Peasant Girls Resting in the Fields","Camille Pissarro",1882),0)
        self.assertEqual(nga.title_score("Waterloo Bridge, London, at Dusk","Claude Monet",1904),0)
        self.assertGreater(nga.title_score("Garden at Vetheuil","Claude Monet",1880),0)

    def test_official_image_only(self):
        self.assertIsNone(nga.image_url("https://api.nga.gov.evil.example/iiif/x"))
        self.assertIsNone(nga.image_url("http://api.nga.gov/iiif/x"))
        self.assertEqual(nga.image_url("https://api.nga.gov/iiif/id/info.json"),
                         "https://api.nga.gov/iiif/id/full/256,/0/default.jpg")

    def test_date_not_artist_lifetime_fallback(self):
        self.assertEqual(nga.year({"displaydate":"c. 1897"}),1897)
        self.assertIsNone(nga.year({"displaydate":"20th century","beginyear":"1880"}))
        self.assertIsNone(nga.year({"displaydate":"1983"}))

    def test_light_vibrant_pass(self):
        im=Image.new("RGB",(100,100),(250,135,25))
        c=nga.color_measure(im)
        self.assertTrue(c["bright_color_pass"])
        self.assertEqual(c["dark_fraction"],0)

    def test_dark_image_rejected(self):
        dark=Image.new("RGB",(100,100),(18,40,51))
        c=nga.color_measure(dark)
        self.assertFalse(c["bright_color_pass"])
        self.assertGreater(c["dark_fraction"],0.9)

    def test_gray_image_rejected(self):
        im=Image.new("RGB",(100,100),(221,221,221))
        self.assertFalse(nga.color_measure(im)["bright_color_pass"])
        self.assertLess(nga.color_measure(im)["vivid_fraction"],.01)

if __name__=="__main__":
    unittest.main()
