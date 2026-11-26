"""Safety and functional unit tests of ArtDrift non-US museum collectors."""
import importlib.util,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
sp=importlib.util.spec_from_file_location("eu",ROOT/"tools/artdrift_eu_new_museums_batch.py")
eu=importlib.util.module_from_spec(sp)
sp.loader.exec_module(eu)
class EuropeanMuseumSourceTests(unittest.TestCase):
    def test_research_hosts_exclude_us_museums(self):
        for domain in ("api.artic.edu","openaccess-api.clevelandart.org",
                       "collectionapi.metmuseum.org","api.nga.gov",
                       "iip.smk.dk","evil.example"):
            self.assertFalse(eu.allow("https://"+domain+"/api/objects"))
        self.assertTrue(eu.allow("https://data.rijksmuseum.nl/search/collection"))
        self.assertTrue(eu.allow("https://thumb.wikimedia.org/wikipedia/commons/thumb/a/a/img.jpg"))
        self.assertFalse(eu.allow("http://data.rijksmuseum.nl/a"))
        self.assertFalse(eu.allow("https://data.rijksmuseum.nl.evil.example/a"))

    def test_scenic_multilingual_titles(self):
        for title in ("Landschap aan de kust","Sommarlandskap","Garden at Giverny",
                      "Blumen im Garten","Bomen langs de rivier",
                      "Sommardag vid havet","Zomerlandschap"):
            self.assertTrue(eu.scene_title(title),title)
        for title in ("Portrait of Woman in Garden","A Nocturne Beach","Portrait",
                      "Woman at the Sea","Landscape in Black Night","Sketch of a Meadow"):
            self.assertFalse(eu.scene_title(title),title)

    def test_painting_year_never_from_artist_lifespan(self):
        self.assertEqual(eu.date_year("1899-01-01T00:00:00Z"),1899)
        self.assertIsNone(eu.date_year("1765"))
        self.assertIsNone(eu.date_year("1922–1970"))
        self.assertIsNone(eu.date_year("mid-20th century"))
        self.assertEqual(eu.author_year_from_doc("1903, Nationalmuseum"),1903)
        self.assertIsNone(eu.author_year_from_doc("unknown"))

    def test_linked_art_parse(self):
        obj={"identified_by":[{"type":"Identifier",
             "classified_as":[{"id":"https://id.rijksmuseum.nl/22015218"}],
             "content":"SK-A-11"},
             {"type":"Name","content":"Landschap bij de rivier",
             "language":[{"id":"http://vocab.getty.edu/aat/300388277"}]}],
             "produced_by":{"part":[{"timespan":{"begin_of_the_begin":"1907-01-01T00:00:00Z"},
              "carried_out_by":[{"notation":[{"@language":"en","@value":"Artist Example"}]}]}]}}
        self.assertEqual(eu.rijks_year(obj),1907)
        self.assertEqual(eu.rijks_ident(obj),"SK-A-11")
        self.assertEqual(eu.rijks_artist(obj),"Artist Example")
        self.assertTrue(eu.scene_title(eu.display_name(obj["identified_by"])))

    def test_high_chroma_near_miss_preserved_for_visual_qa(self):
        # Actual Rijksmuseum SK-A-2288, Landscape on the Oise.
        vivid={"luminance":.4935,"dark_fraction":.1906,
               "saturation":.5389,"vivid_fraction":.5614}
        self.assertTrue(eu.visual_review_exception(vivid))
        from artdrift_dark_threshold_ab import color_tier
        self.assertTrue(color_tier(vivid).startswith("HOLD"))
        # A predominantly dark low-chroma image is still rejected.
        self.assertFalse(eu.visual_review_exception(
            {"luminance":.29,"dark_fraction":.65,"saturation":.52,"vivid_fraction":.55}))
        self.assertFalse(eu.visual_review_exception(
            {"luminance":.59,"dark_fraction":.08,"saturation":.13,"vivid_fraction":.12}))

    def test_sweden_requires_public_domain_and_actual_creation_date(self):
        obj={"pageid":52109999,"title":"File:Summer Landscape (Test Artist) - Nationalmuseum - 9999.tif",
             "imageinfo":[{"mime":"image/tiff","thumburl":
                "https://thumb.wikimedia.org/wikipedia/commons/thumb/a/ab/test.tif/330px-test.tif.jpg",
                "extmetadata":{"LicenseShortName":{"value":"Public domain"},
                               "Copyrighted":{"value":"False"},
                               "Artist":{"value":"Test Artist"},
                               "DateTimeOriginal":{"value":"1891"}},
                "sha1":"abc"}]}
        self.assertIsNotNone(eu.sweden_object(obj))
        obj["imageinfo"][0]["extmetadata"]["LicenseShortName"]["value"]="CC BY-NC"
        self.assertIsNone(eu.sweden_object(obj))
        obj["imageinfo"][0]["extmetadata"]["LicenseShortName"]["value"]="Public domain"
        obj["imageinfo"][0]["extmetadata"]["DateTimeOriginal"]["value"]="Unknown"
        self.assertIsNone(eu.sweden_object(obj))
if __name__=="__main__":unittest.main()
