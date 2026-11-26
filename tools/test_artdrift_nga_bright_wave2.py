import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("artdrift_nga_bright_wave2",ROOT/"tools/artdrift_nga_bright_wave2.py")
import sys
sys.path.insert(0,str(ROOT/"tools"))
w=importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)

class Wave2PolicyTest(unittest.TestCase):
    def test_dark_even_if_vivid(self):
        self.assertFalse(w.strict_pass({"luminance":.70,"dark_fraction":.22,
                                       "vivid_fraction":.90,"saturation":.80}))
    def test_pale_or_gray_does_not_pass(self):
        self.assertFalse(w.strict_pass({"luminance":.85,"dark_fraction":0,
                                       "vivid_fraction":.08,"saturation":.15}))
    def test_tight_pass(self):
        self.assertTrue(w.strict_pass({"luminance":.65,"dark_fraction":.04,
                                       "vivid_fraction":.52,"saturation":.38}))
    def test_no_portrait_or_night(self):
        for title in ("Woman in a Garden","Portrait of the Artist","Girl at the Beach",
                      "Clouds at Dusk","A Country Landscape at Night",
                      "Fishermen on Boats", "Young Child with Flowers",
                      "Washerwomen on the Beach", "Dancing Couple in the Snow",
                      "A Plow Horse in a Field"):
            self.assertEqual(w.scenery_score(title,"Claude Monet",1890),0,title)
    def test_new_titles(self):
        self.assertGreater(w.scenery_score("Haystacks","Claude Monet",1890),0)
        self.assertGreater(w.scenery_score("Cypress Grove","Vincent van Gogh",1890),0)
        self.assertGreater(w.scenery_score("Houses under Summer Sky","Georgia O Keeffe",1930),0)
    def test_no_lifespan_fallback(self):
        self.assertIsNone(w.new_year({"displaydate":"20th century","beginyear":"1880"}))
        self.assertEqual(w.new_year({"displaydate":"1897–1902"}),1897)
        self.assertIsNone(w.new_year({"displaydate":"1973"}))
    def test_prior_wave_dedup(self):
        ids=w.previous()
        self.assertEqual(len(ids),22)
        self.assertIn("52178",ids)

if __name__=="__main__":
    unittest.main()
