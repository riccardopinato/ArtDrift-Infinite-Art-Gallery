import importlib.util
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("artdrift_museum_ingest.py")
spec = importlib.util.spec_from_file_location("artdrift_museum_ingest", MODULE_PATH)
ing = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ing)
merge_spec = importlib.util.spec_from_file_location("artdrift_merge_staging",
    Path(__file__).with_name("artdrift_merge_staging.py"))
merge = importlib.util.module_from_spec(merge_spec)
merge_spec.loader.exec_module(merge)


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

    def test_moma_modern_master_metadata_only(self):
        row = {
            "ObjectID": "1234", "Title": "Composizione moderna",
            "Artist": "Henri Matisse", "Medium": "Oil on canvas",
            "Classification": "Painting", "Date": "1912",
            "URL": "https://www.moma.org/collection/works/1234",
            "ThumbnailURL": "https://www.moma.org/forbidden-image.jpg",
        }
        r = ing.moma_row(row)
        self.assertEqual(r["source_key"], "moma:1234")
        self.assertEqual(r["rights_status"], "METADATA_ONLY")
        self.assertEqual(r["image_url"], "")
        self.assertEqual(r["rights_license"], "")
        self.assertEqual(r["metadata_url"], row["URL"])
        self.assertIsNone(ing.moma_row({**row, "Classification": "Sculpture"}))
        self.assertIsNone(ing.moma_row({**row, "Artist": "Not famous"}))
        self.assertIsNone(ing.moma_row({**row, "ObjectID": "AB123"}))

    def test_d1_idempotence_and_approval_revocation(self):
        conn = sqlite3.connect(":memory:")
        migration = (Path(__file__).resolve().parents[1] /
                     "cloudflare/d1/migrations/0001_museum_ingest.sql")
        conn.executescript(migration.read_text(encoding="utf-8"))
        base = dict(provider="wikidata", native_id="Q2026", museum="Barnes",
                    title="Landscape", artist="Renoir", year="1901",
                    medium="Oil", metadata_url="https://www.wikidata.org/wiki/Q2026",
                    image_url="https://upload.wikimedia.org/p.jpg",
                    full_image_url="https://upload.wikimedia.org/p.jpg",
                    rights_license="CC0 1.0",
                    rights_evidence_url="https://commons.wikimedia.org/wiki/File:P.jpg",
                    rights_status="IMAGE_RIGHTS_VERIFIED")
        first = ing.record(**base)
        conn.executescript(ing.sql_upsert(first))
        self.assertEqual(conn.execute(
            "SELECT count(*) FROM artdrift_publishable_modern_art").fetchone()[0], 0)
        conn.execute("UPDATE artdrift_museum_ingest SET publication_status = 'APPROVED'")
        conn.executescript(ing.sql_upsert(first))
        self.assertEqual(conn.execute(
            "SELECT count(*) FROM artdrift_publishable_modern_art").fetchone()[0], 1)
        updated = ing.record(**{**base, "title": "Updated landscape"})
        conn.executescript(ing.sql_upsert(updated))
        self.assertEqual(conn.execute(
            "SELECT publication_status FROM artdrift_museum_ingest").fetchone()[0], "HOLD")
        self.assertEqual(conn.execute(
            "SELECT count(*) FROM artdrift_publishable_modern_art").fetchone()[0], 0)
        self.assertEqual(conn.execute(
            "SELECT count(*) FROM artdrift_museum_ingest").fetchone()[0], 1)
        conn.close()

    def test_existing_catalog_rights_checked_images(self):
        row = {
            "museum_source": "cleveland",
            "museum_native_id": "12345",
            "museum_name": "Cleveland Museum of Art",
            "title": "The painting",
            "artist_title": "Vincent van Gogh (Dutch, 1853–1890)",
            "date_display": "1889",
            "artwork_type_title": "Painting",
            "is_public_domain": True,
            "rights_license": "CC0",
            "rights_evidence_url": "https://www.clevelandart.org/open-access",
            "remote_preview_url": "https://openaccess-cdn.clevelandart.org/1889/preview.jpg",
            "remote_full_url": "https://openaccess-cdn.clevelandart.org/1889/full.jpg",
            "remote_museum_url": "https://clevelandart.org/art/12345",
            "medium_display": "Oil on canvas",
        }
        r = ing.existing_catalog_row(row)
        self.assertIsNotNone(r)
        self.assertEqual(r["rights_status"], "IMAGE_RIGHTS_VERIFIED")
        self.assertIn("cleveland", r["source_key"])
        self.assertTrue(ing.confirmed_eu_public_domain_artist(row["artist_title"]))
        self.assertFalse(ing.confirmed_eu_public_domain_artist("Pablo Picasso (Spanish, 1881–1973)"))
        self.assertFalse(ing.confirmed_eu_public_domain_artist("Vincent van Gogh"))
        self.assertIsNone(ing.existing_catalog_row({**row, "artist_title": "Pablo Picasso (Spanish, 1881–1973)"}))
        self.assertIsNone(ing.existing_catalog_row({**row, "artist_title": "Vincent van Gogh"}))
        self.assertIsNone(ing.existing_catalog_row({**row, "rights_license": "CC BY 4.0"}))
        self.assertIsNone(ing.existing_catalog_row({**row, "rights_license": "Public Domain"}))
        self.assertIsNone(ing.existing_catalog_row({**row, "artist_title": "Unknown"}))
        self.assertIsNone(ing.existing_catalog_row({**row, "remote_preview_url": "https://evil.example/p.jpg"}))
        self.assertIsNone(ing.existing_catalog_row({**row, "rights_evidence_url": "https://evil.example/cc0"}))
        self.assertIsNone(ing.existing_catalog_row({**row, "artwork_type_title": "Sculpture"}))
        self.assertIsNone(ing.existing_catalog_row({**row, "is_public_domain": False}))

    def test_bulk_stage_merger_rechecks_policy_dedup_and_conflicts(self):
        first = ing.record(provider="tate", native_id="2026", museum="Tate",
                           title="First painting", artist="Paul Cezanne", year="1907",
                           medium="Oil", metadata_url=ing.TATE_GUIDELINES)
        second = ing.record(provider="moma", native_id="900", museum="MoMA",
                            title="Second painting", artist="Henri Matisse", year="1914",
                            medium="Oil", metadata_url=ing.MOMA_REPO)
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            a, b = root / "first.jsonl", root / "second.jsonl"
            a.write_text(json.dumps(first) + "\n", encoding="utf-8")
            b.write_text(json.dumps(second) + "\n" + json.dumps(first) + "\n", encoding="utf-8")
            records, meta = merge.combine([a, b])
            self.assertEqual(len(records), 2)
            self.assertEqual(meta["identical_duplicates_dropped"], 1)
            self.assertEqual(meta["providers"], {"moma": 1, "tate": 1})
            out = root / "all.sql"
            summary = ing.export(records, root / "all.jsonl", out)
            self.assertEqual(summary["total"], 2)
            db = sqlite3.connect(":memory:")
            migration = Path(__file__).resolve().parents[1] / "cloudflare/d1/migrations/0001_museum_ingest.sql"
            db.executescript(migration.read_text())
            db.executescript(out.read_text())
            self.assertEqual(db.execute("SELECT count(*) FROM artdrift_museum_ingest").fetchone()[0], 2)
            self.assertEqual(db.execute("SELECT count(*) FROM artdrift_publishable_modern_art").fetchone()[0], 0)
            db.close()
            b.write_text(json.dumps({**second, "rights_status": "IMAGE_RIGHTS_VERIFIED"}) + "\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                merge.combine([a, b])
            tampered = ing.record(provider="tate", native_id="2026", museum="Tate",
                                  title="Changed painting", artist="Paul Cezanne",
                                  year="1907", medium="Oil", metadata_url=ing.TATE_GUIDELINES)
            b.write_text(json.dumps(tampered) + "\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                merge.combine([a, b])

    def test_https_policy(self):
        self.assertFalse(ing.safe_https("https://upload.wikimedia.org.evil.com/x", {"upload.wikimedia.org"}))
        self.assertFalse(ing.safe_https("https://user@upload.wikimedia.org/x", {"upload.wikimedia.org"}))
        self.assertFalse(ing.safe_https("https://upload.wikimedia.org:444/x", {"upload.wikimedia.org"}))
        self.assertTrue(ing.safe_https("https://upload.wikimedia.org/a", {"upload.wikimedia.org"}))


if __name__ == "__main__":
    unittest.main()
