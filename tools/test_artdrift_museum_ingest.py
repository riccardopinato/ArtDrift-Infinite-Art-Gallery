import importlib.util
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("artdrift_museum_ingest.py")
spec = importlib.util.spec_from_file_location("artdrift_museum_ingest", MODULE_PATH)
ing = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ing)


class ImportTests(unittest.TestCase):
    def test_tate_painting_metadata_only(self):
        row = {"id": "101", "title": "Modern Landscape", "artist": "Claude Monet",
               "medium": "Oil paint on canvas", "year": "1902", "accession_number": "T00444"}
        r = ing.tate_row(row)
        self.assertEqual(r["source_key"], "tate:101")
        self.assertEqual(r["rights_status"], "METADATA_ONLY")
        self.assertEqual(r["image_url"], "")
        self.assertIsNone(ing.tate_row({**row, "artist": "Unlisted artist"}))
        self.assertIsNone(ing.tate_row({**row, "medium": "Lithograph"}))

    def test_guggenheim_does_not_grant_image_rights_by_museum(self):
        row = {"work": {"value": "http://www.wikidata.org/entity/Q777"},
               "museum": {"value": "http://www.wikidata.org/entity/Q201469"},
               "workLabel": {"value": "Abstract composition"},
               "creatorLabel": {"value": "Wassily Kandinsky"},
               "death": {"value": "1944-12-13T00:00:00Z"},
               "image": {"value": "https://commons.wikimedia.org/wiki/Special:FilePath/x.jpg"}}
        original = ing.commons_image
        try:
            ing.commons_image = lambda _url: None
            r = ing.wd_row(row)
            self.assertEqual(r["rights_status"], "METADATA_ONLY")
            self.assertEqual(r["image_url"], "")
            ing.commons_image = lambda _url: ("https://upload.wikimedia.org/a.jpg",
                                             "https://upload.wikimedia.org/a.jpg",
                                             "CC0 1.0",
                                             "https://commons.wikimedia.org/wiki/File:X.jpg")
            r = ing.wd_row(row)
            self.assertEqual(r["rights_status"], "IMAGE_RIGHTS_VERIFIED")
            r2 = ing.wd_row({**row, "death": {"value": "1980-01-01T00:00:00Z"}})
            self.assertEqual(r2["rights_status"], "METADATA_ONLY")
        finally:
            ing.commons_image = original

    def test_no_unsafe_image_hosts_or_rights(self):
        base = dict(provider="wikidata", native_id="Q99", museum="Guggenheim",
                    title="Example", artist="Van Gogh", year="", medium="Painting",
                    metadata_url="https://www.wikidata.org/wiki/Q99")
        for host in ("https://evil.example/a.jpg", "http://upload.wikimedia.org/a.jpg"):
            with self.assertRaises(ValueError):
                ing.record(**base, image_url=host,
                           full_image_url="https://upload.wikimedia.org/a.jpg",
                           rights_license="CC0 1.0",
                           rights_evidence_url="https://commons.wikimedia.org/wiki/File:A.jpg",
                           rights_status="IMAGE_RIGHTS_VERIFIED")

    def test_sql_escaping_versioning_and_no_auto_publication(self):
        r = ing.record(provider="tate", native_id="99", museum="Tate",
                       title="Painter's best", artist="Paul Cézanne", year="1901",
                       medium="oil", metadata_url="https://github.com/tategallery/collection")
        statement = ing.sql_upsert(r)
        self.assertIn("Painter''s best", statement)
        self.assertIn("ELSE 'HOLD'", statement)
        with tempfile.TemporaryDirectory() as tmp:
            jsonl, sql = Path(tmp) / "records.jsonl", Path(tmp) / "records.sql"
            report = ing.export([r], jsonl, sql)
            self.assertEqual(report["published_by_import"], 0)
            self.assertIn("INSERT INTO artdrift_museum_ingest", sql.read_text())
            self.assertNotIn("BEGIN TRANSACTION", sql.read_text())
            self.assertIn('"fingerprint"', jsonl.read_text())
            with self.assertRaises(ValueError):
                ing.export([r, r], jsonl, sql)
            with self.assertRaises(ValueError):
                ing.sql_upsert({**r, "title": "tampered"})

    def test_new_museum_wikidata_membership_and_fail_closed(self):
        expected = {
            "Q808462": "Barnes Foundation",
            "Q303139": "Belvedere",
            "Q1568434": "Yale University",
            "Q754507": "Ateneum",
            "Q857276": "Musee d'Art Moderne",
            "Q1132918": "Nasjonalmuseet",
        }
        for qid, name in expected.items():
            self.assertIn(name, ing.MUSEUMS[qid])
            query = ing.wd_query(100, (qid,))
            self.assertIn("wdt:P195 ?museum", query)
            self.assertIn("wd:" + qid, query)
            self.assertIn("wdt:P31 wd:Q3305213", query)
        with self.assertRaises(ValueError):
            ing.wd_query(100, ("Q999999999",))
        self.assertTrue(ing.famous("Helene Schjerfbeck"))
        self.assertTrue(ing.famous("Akseli Gallen-Kallela"))

    def test_https_policy(self):
        self.assertFalse(ing.safe_https("https://upload.wikimedia.org.evil.com/x", {"upload.wikimedia.org"}))
        self.assertFalse(ing.safe_https("https://user@upload.wikimedia.org/x", {"upload.wikimedia.org"}))
        self.assertFalse(ing.safe_https("https://upload.wikimedia.org:444/x", {"upload.wikimedia.org"}))
        self.assertTrue(ing.safe_https("https://upload.wikimedia.org/a", {"upload.wikimedia.org"}))


if __name__ == "__main__":
    unittest.main()
