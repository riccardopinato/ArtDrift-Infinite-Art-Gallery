import json
import tempfile
import unittest
from pathlib import Path
from artdrift_candidate_rights_triage import triage, write_report

def row(ident, source="smithsonian", kind="Painting", lic="CC0", status="HOLD"):
    return {
        "source_key": ident, "museum_source": source,
        "museum_native_id": "id-" + ident.split(":")[-1], "title": "Landscape",
        "artist": "Painter", "type": kind, "license": lic,
        "publication_status": status,
        "source_url": "https://www.si.edu/object/" + ident,
        "preview_url": "https://ids.si.edu/ids/deliveryService?id=x",
        "rights_evidence_url": "https://www.si.edu/openaccess",
    }

class CatalogRightsTests(unittest.TestCase):
    def test_per_source_identity_and_no_auto_release(self):
        s, records, p, other = triage([
            row("smithsonian:100"),
            row("commons:200", "commons", "Photograph", "CC BY-SA 4.0"),
        ], expected=2)
        self.assertEqual(s["paintings_to_prioritize_for_canvas_review"], 1)
        self.assertEqual(s["non_paintings_preserved_for_separate_archive_review"], 1)
        self.assertEqual(s["rights_media_item_specific_cleared"], 0)
        self.assertTrue(all(r["publication_status"] == "HOLD" for r in records))
        self.assertIn("SHARE_ALIKE_CONDITIONS_REVIEW", other[0]["flags"])
        self.assertFalse(p[0]["commercial_release_cleared"])

    def test_duplicate_and_unheld_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            triage([row("smithsonian:100"), row("smithsonian:100")], 2)
        with self.assertRaisesRegex(ValueError, "Unexpected candidate publication"):
            triage([row("smithsonian:100", status="APPROVED")], 1)

    def test_bad_object_url_and_dirty_titles_stay_hold(self):
        x = row("commons:10", "commons", "Painting", "CC BY 4.0")
        x.update({"source_url": "http://invalid.example", "preview_url": "https://bad.example@evil.example/a", "title": 'German: Landscape label QS:Lde,"Landscape" <i>v1</i>'})
        summary, records, _, _ = triage([x], 1)
        self.assertIn("TITLE_CONTAINS_QS_METADATA", records[0]["flags"])
        self.assertIn("TITLE_CONTAINS_HTML_MARKUP", records[0]["flags"])
        self.assertIn("OFFICIAL_OBJECT_DETAIL_MISSING", records[0]["flags"])
        self.assertEqual(summary["published_or_unheld"], 0)

    def test_real_catalog_covers_all_585_without_releasing_anything(self):
        from artdrift_inventory_wave import inspect
        root = Path(__file__).resolve().parents[1]
        inventory, source = inspect(root, 5085)
        report, records, paintings, archive = triage(source, 585)
        self.assertEqual((report["candidate_records"], report["catalog_waves"]), (585, 6))
        self.assertEqual(len(paintings) + len(archive), 585)
        self.assertEqual(len(paintings), 60)
        self.assertEqual(len(archive), 525)
        self.assertEqual(report["by_flag"]["OFFICIAL_OBJECT_DETAIL_MISSING"], 558)
        self.assertEqual(report["by_flag"]["CREATOR_MISSING"], 74)
        self.assertEqual(report["by_flag"]["TITLE_CONTAINS_QS_METADATA"], 2)
        self.assertEqual(report["by_flag"]["TITLE_CONTAINS_HTML_MARKUP"], 40)
        self.assertEqual(report["published_or_unheld"], 0)

if __name__ == "__main__":
    unittest.main()
