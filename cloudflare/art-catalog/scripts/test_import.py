import csv, sqlite3, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from make_d1_import import convert

class TestMoMA(unittest.TestCase):
    def test_metadata_only_and_escaping(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            source=root/"Artworks.csv"
            with source.open("w",encoding="utf-8",newline="") as output:
                writer=csv.DictWriter(output,fieldnames=[
                    "ObjectID","Title","Artist","Date","Medium","ThumbnailURL"])
                writer.writeheader()
                writer.writerow({"ObjectID":"12","Title":"O'Clock","Artist":"Van Gogh",
                    "Date":"1889","Medium":"Oil","ThumbnailURL":"https://fake/img.jpg"})
                writer.writerow({"ObjectID":"13","Title":"Garden","Artist":"Other",
                    "Date":"1900","Medium":"Watercolor"})
            with self.assertRaisesRegex(ValueError,"APPROVED_P1_ALLOWLIST_REQUIRED"):
                convert(source,root/"blocked",chunk=1,verify=False)
            m=convert(source,root/"shards",chunk=1,verify=False,
                allowlist={"12","13"},expected_count=2)
            self.assertEqual(m["artworks"],2)
            db=sqlite3.connect(":memory:")
            db.executescript((Path(__file__).resolve().parents[1]/"schema.sql").read_text())
            for sql_file in sorted((root/"shards").glob("import-*.sql")):
                sql=sql_file.read_text()
                self.assertNotIn("fake",sql)
                db.executescript(sql)
            self.assertEqual(db.execute("SELECT count(*) FROM works").fetchone()[0],2)
            self.assertEqual(db.execute("SELECT title FROM works WHERE id=12").fetchone()[0],"O'Clock")
            self.assertEqual(db.execute("SELECT count(*) FROM works_fts WHERE works_fts MATCH 'artist:Van*'").fetchone()[0],1)
            self.assertEqual(db.execute("SELECT count(*) FROM works WHERE image_key IS NOT NULL").fetchone()[0],0)

    def test_allowlist_missing_source_id_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            source=root/"Artworks.csv"
            with source.open("w",encoding="utf-8",newline="") as output:
                writer=csv.DictWriter(output,fieldnames=["ObjectID","Title","Artist","Date","Medium"])
                writer.writeheader()
                writer.writerow({"ObjectID":"12","Title":"Art","Artist":"A","Date":"1900","Medium":"Oil"})
            with self.assertRaisesRegex(ValueError,"missing/unverified"):
                convert(source,root/"blocked",chunk=1,verify=False,
                        allowlist={"12","13"},expected_count=2)
            self.assertEqual(list((root/"blocked").glob("import-*.sql")),[])
