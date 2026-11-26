"""Fail-closed tests for the 486 independent artist review lanes."""
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parents[0]))
import artdrift_486_parallel_gate as m


class ParallelArtistGateTests(unittest.TestCase):
    def row(self, identity):
        return {
            "source_identity": identity,
            "artist_id": "harald_sohlberg",
            "title": "Example painting",
            "preview_url": "https://upload.wikimedia.org/wikipedia/commons/a/a0/Example.jpg",
            "image_license_claim": "Public domain",
            "artist_attribution": "HOLD_SOURCE_VS_CATEGORY_CLAIM",
            "commercially_approved": False,
            "runtime_visible": False,
        }

    def test_partition_covers_every_identity_exactly_once(self):
        identities = ["commons:" + str(i) for i in range(486)]
        partitioned = [x for shard in range(m.SHARDS)
                       for x in identities if m.shard_of(x, m.SHARDS) == shard]
        self.assertEqual(len(partitioned), 486)
        self.assertEqual(len(set(partitioned)), 486)

    def test_unsafe_urls_rejected(self):
        self.assertFalse(m.url_safe("http://upload.wikimedia.org/file.jpg"))
        self.assertFalse(m.url_safe("https://evil.example/"))
        self.assertFalse(m.url_safe("file:///etc/passwd"))
        self.assertTrue(m.url_safe("https://thumb.wikimedia.org/wikipedia/commons/thumb/a.jpg"))
        self.assertTrue(m.url_safe("https://cdn.staedelmuseum.de/images/20/88/1350/thumb-lg.jpg"))

    def test_pixel_evidence_does_not_clear_rights(self):
        im = Image.new("RGB", (120, 80), "white")
        output = io.BytesIO()
        im.save(output, format="PNG")
        row = self.row("commons:42")
        result, _ = m.assess(row, download=lambda u: output.getvalue())
        self.assertEqual(result["result"], "PIXELS_OK_RIGHTS_AND_VISUAL_HOLD")
        self.assertFalse(result["commercially_approved"])
        self.assertFalse(result["runtime_visible"])
        self.assertEqual(result["image_rights_gate"], "HOLD_PER_ITEM_TERRITORY")
        self.assertEqual(result["technical_color_class"], "LUMINOUS_VISUAL_REVIEW")

    def test_network_failure_stays_visible_as_hold(self):
        row = self.row("commons:43")
        def fail(_):
            raise RuntimeError("HTTP_429")
        result, image = m.assess(row, download=fail)
        self.assertIsNone(image)
        self.assertEqual(result["technical_error"], "HTTP_429")
        self.assertEqual(result["result"], "HOLD_TECHNICAL")

    def test_source_data_cannot_supply_approvals(self):
        rows = [self.row("commons:" + str(i)) for i in range(486)]
        rows[0]["source_identity"] = "staedel:DE-MUS-048017/lido/1350"
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "inventory.json"
            p.write_text(json.dumps({"all_candidate_records_retained": 486,
                                     "complete_queue": rows}), encoding="utf-8")
            self.assertEqual(len(m.read_queue(p)), 486)
            rows[0]["commercially_approved"] = True
            p.write_text(json.dumps({"all_candidate_records_retained": 486,
                                     "complete_queue": rows}), encoding="utf-8")
            with self.assertRaises(ValueError):
                m.read_queue(p)

    def test_full_offline_sharding_and_aggregation(self):
        rows = [self.row("commons:" + str(i)) for i in range(486)]
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            for shard in range(m.SHARDS):
                m.run_shard(rows, shard, m.SHARDS, directory, offline=True)
            result = m.aggregate(rows, directory, directory / "aggregate")
            self.assertEqual(result["independent_evidence_rows"], 486)
            self.assertEqual(result["commercially_approved"], 0)
            self.assertEqual(result["statuses"]["HOLD_TECHNICAL"], 486)
            self.assertTrue((directory / "aggregate" / "review_queue.csv").exists())


if __name__ == "__main__":
    unittest.main()
