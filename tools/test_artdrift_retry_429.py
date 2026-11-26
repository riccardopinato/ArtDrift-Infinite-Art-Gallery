"""Offline regression tests for rate-limited per-image follow-up."""
import csv
import io
import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).parent))
import artdrift_retry_429 as m


class RetryTests(unittest.TestCase):
    def generate(self):
        return [
            {"source_identity": "commons:" + str(i),
             "result": "HOLD_TECHNICAL" if i < 39 else "PIXELS_OK_RIGHTS_AND_VISUAL_HOLD",
             "error": "HTTP_429" if i < 39 else ""}
            for i in range(486)
        ]

    def test_only_39_failed_are_selected(self):
        rows = self.generate()
        result = m.pending_ids(rows)
        self.assertEqual(len(result),39)
        self.assertEqual(sum(m.gate.shard_of(x,m.WORKERS)==0 for x in result)
                         + sum(m.gate.shard_of(x,m.WORKERS)==1 for x in result),39)
        self.assertNotIn("commons:40",result)

    def test_unexpected_error_is_rejected(self):
        rows = self.generate()
        rows[0]["error"] = "UNEXPECTED_FAILURE"
        with self.assertRaises(ValueError):
            m.pending_ids(rows)

    def test_truncated_first_pass_is_rejected(self):
        rows=self.generate()[:5]
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"report.csv"
            with p.open("w",encoding="utf-8",newline="") as f:
                w=csv.DictWriter(f, fieldnames=["source_identity","result","error"])
                w.writeheader()
                w.writerows(rows)
            with self.assertRaises(ValueError):
                m.read_initial(p)

    def test_no_automatic_release_even_after_recovered_pixels(self):
        source=[
            {"source_identity": "commons:" + str(i), "artist_id":"harald_sohlberg",
             "title":str(i),
             "preview_url": "https://upload.wikimedia.org/wikipedia/commons/a/a.png",
             "commercially_approved":False,"runtime_visible":False}
            for i in range(486)
        ]
        rows=self.generate()
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)
            for w in range(m.WORKERS):
                m.run_worker(source,rows,w,out,do_download=False)
            summary=m.merge(rows,source,out,out/"aggregate")
            self.assertEqual(summary["original_total"],486)
            self.assertEqual(summary["combined_technical_ok"],447)
            self.assertEqual(summary["combined_technical_hold"],39)
            self.assertEqual(summary["commercially_approved"],0)


if __name__=="__main__":
    unittest.main()
