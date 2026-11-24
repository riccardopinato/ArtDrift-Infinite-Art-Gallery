import importlib.util
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "artdrift_cleveland_rights_audit", HERE / "artdrift_cleveland_rights_audit.py"
)
import sys
sys.path.insert(0, str(HERE))
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class ClevelandRightsSourceTests(unittest.TestCase):
    def setUp(self):
        self.staged = {
            "provider": "cleveland", "native_id": "95272",
            "title": "Gardener's House at Antibes",
            "artist": "Claude Monet (French, 1840–1926)",
            "metadata_url": "https://clevelandart.org/art/1916.1044",
            "image_url": "https://openaccess-cdn.clevelandart.org/1916.1044/1916.1044_web.jpg",
            "full_image_url": "https://openaccess-cdn.clevelandart.org/1916.1044/1916.1044_print.jpg",
        }
        self.primary = {"data": {
            "id": 95272, "title": "Gardener's House at Antibes",
            "type": "Painting", "share_license_status": "CC0",
            "url": self.staged["metadata_url"],
            "images": {"web": {"url": self.staged["image_url"]},
                       "print": {"url": self.staged["full_image_url"]}},
            "creators": [{"description": "Claude Monet (French, 1840–1926)"}]
        }}

    def test_match_is_not_an_editorial_approval(self):
        status, notes = audit.assess(self.staged, self.primary)
        self.assertEqual(status, "PRIMARY_SOURCE_MATCH")
        self.assertIn("editorial_and_legal_review_pending", notes)

    def test_fail_closed_on_changed_rights(self):
        data = {"data": {**self.primary["data"], "share_license_status": "Copyrighted"}}
        status, flags = audit.assess(self.staged, data)
        self.assertEqual(status, "NEEDS_REVIEW")
        self.assertIn("not_current_cc0", flags)

    def test_fail_closed_on_image_identity_and_title(self):
        tests = [
            {"id": 1},
            {"title": "Other Painting"},
            {"images": {"web": {"url": "https://bad.example/abc.jpg"},
                        "print": {"url": self.staged["full_image_url"]}}},
            {"type": "Sculpture"},
            {"creators": [{"description": "Pablo Picasso (Spanish, 1881–1973)"}]},
            {"creators": []},
        ]
        for altered in tests:
            with self.subTest(altered=altered):
                status, _ = audit.assess(self.staged, {"data": {**self.primary["data"], **altered}})
                self.assertEqual(status, "NEEDS_REVIEW")

    def test_invalid_source_fails_closed(self):
        self.assertEqual(audit.assess(self.staged, {"data": []})[0], "SOURCE_REVIEW")
        self.assertEqual(audit.assess({**self.staged, "provider": "tate"}, self.primary)[0],
                         "SOURCE_REVIEW")


if __name__ == "__main__":
    unittest.main()
