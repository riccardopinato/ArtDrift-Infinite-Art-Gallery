import importlib.util,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
sp=importlib.util.spec_from_file_location("met_full_verify",ROOT/"tools/artdrift_met_csv_verify.py")
m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
class TestVerifiedContract(unittest.TestCase):
    def test_official_api(self):
        self.assertEqual(m.API,"https://collectionapi.metmuseum.org/public/collection/v1/objects/")
        self.assertTrue(m.host_ok("https://images.metmuseum.org/a.jpg","images.metmuseum.org"))
        self.assertFalse(m.host_ok("https://images.metmuseum.org.evil.tld/a.jpg","images.metmuseum.org"))
    def test_source_metadata_ready(self):
        p=m.QUEUE
        if not p.exists():self.skipTest("Official CSV discovery not yet complete")
        import json
        data=json.loads(p.read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(data["works"]),50)
        self.assertEqual(data["runtime_imported"],0)
        self.assertFalse(data["works"][0]["image_verified"])
    def test_no_duplicate_renders(self):
        self.assertNotEqual(m.cleaned("Field of Flowers"),m.cleaned("River by Night"))
if __name__=="__main__":unittest.main()
