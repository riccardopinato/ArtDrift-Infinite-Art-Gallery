"""Second-stage Städel sampling is deterministic, bounded and HOLD-only."""
from __future__ import annotations
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
import artdrift_staedel_detail_sample as m


class DetailSampleTests(unittest.TestCase):
    def test_stratified_selection_excludes_older_records(self):
        all_ids=[f"oai:DE-MUS-048017:{i}" for i in range(500)]
        a=m.select_ids(all_ids,{"oai:DE-MUS-048017:4"},30)
        b=m.select_ids(reversed(all_ids),{"oai:DE-MUS-048017:4"},30)
        self.assertEqual(a,b)
        self.assertEqual(len(a),30)
        self.assertNotIn("oai:DE-MUS-048017:4",a)
    def test_getrecord_parsing_rejects_source_errors(self):
        def fake(url,**kwargs):
            self.assertIn("GetRecord",url)
            return b'<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/"><error code="idDoesNotExist">Missing</error></OAI-PMH>'
        with self.assertRaises(ValueError):
            m.fetch_record("oai:DE-MUS-048017:1",read=fake)
    def test_getrecord_returns_non_deleted_record(self):
        xml=b'<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/"><GetRecord><record><header><identifier>oai:DE-MUS-048017:1</identifier></header><metadata/></record></GetRecord></OAI-PMH>'
        r=m.fetch_record("oai:DE-MUS-048017:1",read=lambda u,**kw:xml)
        self.assertIsNotNone(r)
    def test_no_unknown_record_ids(self):
        a=m.select_ids(["invalid","oai:DE-MUS-048017:2"],[],10)
        self.assertEqual(a,["oai:DE-MUS-048017:2"])


if __name__=="__main__":
    unittest.main()
