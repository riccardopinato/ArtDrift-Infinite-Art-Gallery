import importlib.util
from pathlib import Path
import sys
import unittest
from PIL import Image

root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("artdrift_bright_mass",root/"tools/artdrift_bright_mass.py")
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class BatchResearchTests(unittest.TestCase):
    def test_filter_scenic_portraits(self):
        for t in ("Portrait of a Woman","Woman in a Garden","Figures at the Beach",
                  "Man by the Sea","Spring Landscape at Night",
                  "Nocturne Seascape","Dusk over the Harbor"):
            self.assertFalse(m.scene_ok(t,"Claude Monet"),t)
        for t in ("Garden in Giverny","Sunlit Coast","Blue and Orange Bouquet",
                  "Still Life with Oranges","Woodland Spring"):
            self.assertTrue(m.scene_ok(t,"Vincent van Gogh"),t)

    def test_date(self):
        self.assertEqual(m.dates("ca. 1891"),1891)
        self.assertEqual(m.dates("1880-1892"),1880)
        self.assertIsNone(m.dates("1600"))
        self.assertIsNone(m.dates("1970"))
        self.assertIsNone(m.dates("20th century"))
        self.assertEqual(m.dates("",start=1901),1901)

    def test_color_intense_pale_passes(self):
        c=m.color_metric(Image.new("RGB",(100,100),(255,155,15)))
        self.assertTrue(c["bright_pass"],c)

    def test_color_dark_rejected(self):
        c=m.color_metric(Image.new("RGB",(100,100),(20,30,80)))
        self.assertFalse(c["bright_pass"])
        self.assertGreater(c["dark_fraction"],.9)

    def test_neutral_white_rejected(self):
        c=m.color_metric(Image.new("RGB",(100,100),(245,245,245)))
        self.assertFalse(c["bright_pass"])
        self.assertLess(c["vivid_fraction"],.01)

    def test_partly_dark_rejected(self):
        pic=Image.new("RGB",(100,100),(255,155,15))
        for x in range(25):
            for y in range(100):pic.putpixel((x,y),(9,9,9))
        c=m.color_metric(pic)
        self.assertFalse(c["bright_pass"],c)
        self.assertGreater(c["dark_fraction"],.10)

    def test_source_hosts_strict(self):
        self.assertTrue(m.host_ok("https://www.artic.edu/iiif/2/id/full/256,/0/default.jpg","www.artic.edu"))
        self.assertFalse(m.host_ok("https://www.artic.edu.attacker.test/foo","www.artic.edu"))
        self.assertFalse(m.host_ok("http://www.artic.edu/foo","www.artic.edu"))
        self.assertFalse(m.host_ok("https://u:p@www.artic.edu/foo","www.artic.edu"))

    def test_live_dedup_loaded(self):
        keys,names=m.main_keys()
        self.assertGreater(len(keys),600)
        self.assertGreater(len(names),400)

if __name__=="__main__":unittest.main()
