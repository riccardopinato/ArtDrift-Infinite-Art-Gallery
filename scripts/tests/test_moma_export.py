import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from export_moma_collection import artist_ids

class TestMoMAExporter(unittest.TestCase):
    def test_multi_artist(self):
        self.assertEqual(artist_ids("[17, 42, 17]"),["17","42"])
    def test_empty(self):
        self.assertEqual(artist_ids(None),[])
        self.assertEqual(artist_ids(""),[])
    def test_numeric(self):
        self.assertEqual(artist_ids("345"),["345"])

if __name__=="__main__": unittest.main()
