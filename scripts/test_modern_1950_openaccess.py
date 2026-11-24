#!/usr/bin/env python3
"""Deterministic rights/date/import tests without querying any museum API."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

PATH = Path(__file__).resolve().parent / "import_modern_1950_openaccess.py"
spec = importlib.util.spec_from_file_location("artdrift_modern", PATH)
modern = importlib.util.module_from_spec(spec)
spec.loader.exec_module(modern)


def artwork(**extra):
    row = {
        "id": 123,
        "title": "Museum CC0 work",
        "type": "Painting",
        "creation_date": "1964",
        "share_license_status": "CC0",
        "images": {"web": {"url": "https://openaccess-cdn.clevelandart.org/museum/123.jpg"}},
        "creators": [{"description": "Artist (museum record)"}],
        "url": "https://www.clevelandart.org/art/1964.123",
    }
    row.update(extra)
    return row


class ModernCatalogTests(unittest.TestCase):
    def test_strict_license_image_and_date(self):
        self.assertEqual(modern.normalize(artwork())["creation_year_verified"], 1964)
        self.assertIsNone(modern.normalize(artwork(share_license_status="Copyright")))
        self.assertIsNone(modern.normalize(artwork(creation_date="1940-1956")))
        self.assertIsNone(modern.normalize(artwork(creation_date="late 20th century")))
        self.assertIsNone(modern.normalize(artwork(creation_date="2027")))
        self.assertIsNone(modern.normalize(artwork(type="Natural History Specimen")))
        self.assertIsNone(modern.normalize(artwork(images={"web": {"url": "https://bad.example/a.jpg"}})))
        self.assertIsNone(modern.normalize(artwork(images={"web": {"url": "http://openaccess-cdn.clevelandart.org/a.jpg"}})))
        self.assertIsNone(modern.normalize(artwork(images={"web": {"url": "https://openaccess-cdn.clevelandart.org.evil.test/a.jpg"}})))

    def test_modern_media_are_truthful_not_relabeled_as_paintings(self):
        for kind in ("Painting", "Drawing", "Print", "Photograph",
                     "Sculpture", "Mixed Media", "Ceramics"):
            self.assertEqual(modern.normalize(artwork(type=kind))["artwork_type_title"], kind)
        self.assertEqual(modern.creation_year("circa 1950-1956"), 1950)
        self.assertEqual(modern.creation_year("1980s"), 1980)

    def test_import_deduplicates_and_preserves_existing(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / "assets/museums").mkdir(parents=True)
            (base / "assets/gallery").mkdir(parents=True)
            (base / "assets/gallery/catalog.json").write_text("[]")
            (base / "assets/museums/catalog.json").write_text("[]")
            (base / "assets/museums/catalog_global.json").write_text(json.dumps([{
                "museum_source": "cleveland", "museum_native_id": "123",
                "id": 20000123
            }]))
            examples = [
                artwork(id=123), artwork(id=124), artwork(id=124),
                artwork(id=125, share_license_status="Copyright"),
                artwork(id=126, creation_date="1940"),
            ]
            def fetch(skip):
                self.assertEqual(skip, 0)
                return {"data": examples, "info": {"total": 5}}
            report = modern.import_catalog(fetch, base)
            rows = json.loads((base / "assets/museums/catalog_modern_1950.json").read_text())
            self.assertEqual(report["new_unique_records"], 1)
            self.assertEqual(rows[0]["museum_native_id"], "124")
            self.assertEqual(rows[0]["creation_year_verified"], 1964)
            self.assertEqual(rows[0]["artwork_type_title"], "Painting")
            self.assertTrue(rows[0]["remote_preview_url"].startswith("https://openaccess-cdn.clevelandart.org/"))


if __name__ == "__main__":
    unittest.main()
