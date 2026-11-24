import json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from artdrift_inventory_wave import inspect
from make_museum_d1_import import SOURCES

class InventoryTests(unittest.TestCase):
    def test_real_catalog_hold(self):
        info,rows=inspect(Path(__file__).resolve().parents[1],5085)
        self.assertEqual(info["candidate_records"],585)
        self.assertEqual(info["candidate_waves"],6)
        self.assertEqual(info["auto_approved"],0)
        self.assertTrue(all(x["publication_status"]=="HOLD" for x in rows))
        self.assertEqual(info["per_file"]["assets/museums/catalog_new_museums.json"],558)
        self.assertEqual(info["per_file"]["assets/museums/catalog_modern_1950.json"],27)
    def test_duplicate_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            for name in SOURCES:
                target=root/name;target.parent.mkdir(parents=True,exist_ok=True)
                target.write_bytes((Path(__file__).resolve().parents[1]/name).read_bytes())
            path=root/SOURCES[0];data=json.loads(path.read_text());data.append(data[0])
            path.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError,"Duplicate"):
                inspect(root,None)
if __name__=="__main__":unittest.main()
