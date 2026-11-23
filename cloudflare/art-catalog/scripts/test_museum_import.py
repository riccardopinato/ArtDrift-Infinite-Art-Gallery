import importlib.util
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

FILE=Path(__file__).parent/"make_museum_d1_import.py"
spec=importlib.util.spec_from_file_location("museum_d1",FILE)
museum=importlib.util.module_from_spec(spec)
spec.loader.exec_module(museum)


def fixtures(root,rows):
    for p in museum.SOURCES:
        file=root/p
        file.parent.mkdir(parents=True,exist_ok=True)
        file.write_text(json.dumps(rows if p==museum.SOURCES[0] else []),
                        encoding="utf-8")


def classic():
    return {"id":72,"title":"Historic sample","artist_title":"Artist",
      "date_display":"1900","is_public_domain":True,
      "artwork_type_title":"Painting","image_id":"abcdefab-cdef-abcd-1234-abcd1234abcd"}


def modern():
    return {"id":10000012,"museum_source":"commons","museum_native_id":"12",
      "museum_name":"Wikimedia Commons","title":"Modern self-authored",
      "artist_title":"Painter","date_display":"2020","artwork_type_title":"Painting",
      "is_public_domain":False,"rights_license":"CC BY-SA 4.0",
      "rights_license_url":"https://creativecommons.org/licenses/by-sa/4.0/",
      "rights_evidence_url":"https://commons.wikimedia.org/wiki/File:Modern.jpg",
      "credit_line":"Painter / CC BY-SA 4.0",
      "remote_preview_url":"https://upload.wikimedia.org/a.jpg",
      "remote_museum_url":"https://commons.wikimedia.org/wiki/File:Modern.jpg"}


class MuseumD1Tests(unittest.TestCase):
    def test_prepare_and_sqlite_fts_without_cloud(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            fixtures(root,[classic(),modern()])
            report=museum.export(root,root/"out",expected=2,chunk=25)
            self.assertEqual(report["records"],2)
            self.assertEqual(report["images_bundled"],0)
            self.assertEqual(report["d1_remote_import"],"REQUIRES_EXPLICIT_APPROVAL")
            db=sqlite3.connect(":memory:")
            db.executescript((FILE.parent.parent/"museum_schema.sql").read_text())
            for shard in sorted((root/"out").glob("museum-*.sql")):
                db.executescript(shard.read_text())
                db.executescript(shard.read_text())  # repeatable imports
            self.assertEqual(db.execute("SELECT COUNT(*) FROM museum_works").fetchone()[0],2)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM museum_works_fts WHERE museum_works_fts MATCH 'Modern'").fetchone()[0],1)
            self.assertEqual(db.execute("SELECT rights_license FROM museum_works WHERE source_key='commons:10000012'").fetchone()[0],"CC BY-SA 4.0")
            self.assertEqual(db.execute("SELECT image_url FROM museum_works WHERE source_key='aic:72'").fetchone()[0],"")

    def test_no_fake_rights_or_image_hosts(self):
        self.assertIsNone(museum.normalize({**modern(),"rights_license":"CC BY-NC 4.0"}))
        self.assertIsNone(museum.normalize({**modern(),"is_public_domain":True}))
        self.assertIsNone(museum.normalize({**modern(),"rights_evidence_url":"https://evil.test/lic"}))
        unsafe=museum.normalize({**modern(),"remote_preview_url":"https://upload.wikimedia.org.evil.test/z"})
        self.assertEqual(unsafe["image_url"],"")

    def test_duplicates_and_count_mismatch_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            fixtures(root,[classic(),classic()])
            with self.assertRaisesRegex(ValueError,"Duplicate identity"):
                museum.export(root,root/"out",expected=2,chunk=25)
            fixtures(root,[classic()])
            with self.assertRaisesRegex(ValueError,"count mismatch"):
                museum.export(root,root/"out",expected=5084,chunk=25)


if __name__=="__main__":
    unittest.main()
