import importlib.util
import sqlite3
import unittest
from pathlib import Path

import sys
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from artdrift_museum_ingest import record, sql_upsert

spec = importlib.util.spec_from_file_location(
    "artdrift_cleveland_print_repair", HERE / "artdrift_cleveland_print_repair.py"
)
fix = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fix)


def make_fixture():
    staged, works = [], []
    for i in range(49):
        ident = str(10000 + i)
        web = f"https://openaccess-cdn.clevelandart.org/1900.{i}/1900.{i}_web.jpg"
        full = f"https://openaccess-cdn.clevelandart.org/1900.{i}/1900.{i}_print.jpg"
        base = record(
            provider="cleveland", native_id=ident, museum="Cleveland Museum of Art",
            title=f"Painting number {i}", artist="Claude Monet (French, 1840–1926)",
            year="1900", medium="Oil on canvas",
            metadata_url=f"https://clevelandart.org/art/1900.{i}",
            image_url=web, full_image_url=web if i < 28 else full,
            rights_license="CC0 1.0",
            rights_evidence_url="https://www.clevelandart.org/open-access",
            rights_status="IMAGE_RIGHTS_VERIFIED")
        staged.append(base)
        works.append({
            "source_key": base["source_key"],
            "source_check": "SOURCE_MATCH_PREVIEW_FALLBACK" if i < 28
                else "PRIMARY_SOURCE_MATCH",
            "review_flags": ["preview_used_as_full_image"] if i < 28
                else ["editorial_and_legal_review_pending"],
            "fingerprint": base["fingerprint"],
            "source_api": f"https://openaccess-api.clevelandart.org/api/artworks/{ident}",
            "current_share_license_status": "CC0",
            "current_official_print_url": full,
        })
    return staged, {
        "total": 49, "all_publication_status": "HOLD",
        "editorial_approved": 0, "published": 0, "works": works,
    }


class PrintRepairTests(unittest.TestCase):
    def test_28_fingerprint_guarded_repairs_and_sqlite_hold(self):
        rows, audit = make_fixture()
        changes, sql = fix.prepare(audit, rows)
        self.assertEqual(len(changes), 28)
        self.assertEqual(sql.count("UPDATE artdrift_museum_ingest"), 28)
        self.assertNotIn("publication_status='APPROVED'", sql)
        conn = sqlite3.connect(":memory:")
        migration = (HERE.parent / "cloudflare/d1/migrations/0001_museum_ingest.sql")
        conn.executescript(migration.read_text(encoding="utf-8"))
        conn.executescript("\n".join(sql_upsert(row) for row in rows))
        before = conn.total_changes
        conn.executescript(sql)
        self.assertEqual(conn.total_changes - before, 28)
        self.assertEqual(conn.execute(
            "SELECT COUNT(*) FROM artdrift_museum_ingest WHERE publication_status='HOLD'"
        ).fetchone()[0], 49)
        self.assertEqual(conn.execute(
            "SELECT COUNT(*) FROM artdrift_publishable_modern_art"
        ).fetchone()[0], 0)
        second = conn.total_changes
        conn.executescript(sql)
        self.assertEqual(conn.total_changes, second)  # fingerprint prevents duplicate updates
        conn.close()

    def test_untrusted_or_stale_audit_never_generates_sql(self):
        rows, audit = make_fixture()
        audit["works"][0]["current_share_license_status"] = "Copyrighted"
        with self.assertRaises(ValueError):
            fix.prepare(audit, rows)
        audit["works"][0]["current_share_license_status"] = "CC0"
        audit["works"][0]["fingerprint"] = "f" * 64
        with self.assertRaises(ValueError):
            fix.prepare(audit, rows)
        audit["works"][0]["fingerprint"] = rows[0]["fingerprint"]
        audit["works"][0]["current_official_print_url"] = "https://evil.example/img.jpg"
        with self.assertRaises(ValueError):
            fix.prepare(audit, rows)

    def test_no_editorial_approvals_allowed(self):
        rows, audit = make_fixture()
        audit["editorial_approved"] = 1
        with self.assertRaises(ValueError):
            fix.prepare(audit, rows)


if __name__ == "__main__":
    unittest.main()
