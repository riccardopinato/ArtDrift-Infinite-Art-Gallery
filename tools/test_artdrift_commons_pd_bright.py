import importlib.util
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
s=importlib.util.spec_from_file_location("commons",ROOT/"tools/artdrift_commons_pd_bright.py")
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class CommonsColorTests(unittest.TestCase):
    def test_artist_roster_rights_year(self):
        self.assertEqual(len(m.ARTISTS),8)
        self.assertTrue(all(y<=1955 for group in m.ARTISTS for name,y in group))
    def test_file_licence(self):
        ok={"LicenseShortName":{"value":"Public domain"},"Copyrighted":{"value":"False"}}
        self.assertTrue(m.licenses(ok)[0])
        self.assertTrue(m.licenses({"LicenseShortName":{"value":"CC0"}})[0])
        self.assertFalse(m.licenses({"LicenseShortName":{"value":"CC BY-NC"}})[0])
        self.assertFalse(m.licenses({"LicenseShortName":{"value":"Public domain"},"Copyrighted":{"value":"True"}})[0])
    def test_media_trusted_host(self):
        self.assertTrue(m.safe_thumb("https://upload.wikimedia.org/wikipedia/commons/thumb/1/a/test.jpg"))
        self.assertFalse(m.safe_thumb("https://upload.wikimedia.org.evil.test/wikipedia/commons/thumb/1/a.jpg"))
        self.assertFalse(m.safe_thumb("http://upload.wikimedia.org/wikipedia/commons/thumb/1/a.jpg"))
    def test_search_attribution(self):
        self.assertTrue(m.title_relevant("File:Claude Monet - Haystacks.jpg","Claude Monet"))
        self.assertFalse(m.title_relevant("File:Portrait of Woman Claude Monet.jpg","Claude Monet"))
        self.assertFalse(m.title_relevant("File:Unknown Portrait.jpg","Claude Monet"))
if __name__=="__main__":unittest.main()
