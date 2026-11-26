"""Offline research inventory coverage, rights HOLD, and runtime collision tests."""
from __future__ import annotations
import unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
import artdrift_artist_bulk_triage as m


def inputs():
    seed={"artists":[
        {"id":"alfred_sisley","aliases":["Alfred Sisley"]},
        {"id":"ludvig_karsten","aliases":["Ludvig Karsten"]}]}
    row1={"identity":"commons:1","artist_id":"alfred_sisley",
          "title":"The Bridge at Villeneuve-la-Garenne","source":"wikimedia_artist_category",
          "record_url":"https://commons.wikimedia.org/?curid=1",
          "preview_url":"https://upload.wikimedia.org/1.jpg",
          "explicit_work_target":"sisley_villeneuve_bridge",
          "source_license_claim":"CC0","image_sha256":"a"*64,
          "commercially_approved":False,"runtime_visible":False}
    row2={"identity":"commons:2","artist_id":"ludvig_karsten",
          "title":"Trichromogravure catalogue of paintings",
          "source":"wikimedia_artist_category",
          "record_url":"https://commons.wikimedia.org/?curid=2",
          "preview_url":"https://upload.wikimedia.org/2.jpg",
          "commercially_approved":False,"runtime_visible":False}
    raw={"artist_matched_distinct_files":2,"priority_shortlist":[row1,row2]}
    pixels={"records":[{"identity":"commons:1","status":"PIXELS_CHECKED_HOLD",
            "pixel_sha256":"a"*64,"color_tier":"PREFERRED_AT_MOST_15_PERCENT_DARK"}]}
    decisions={"individual_decisions":[{"identity":"commons:1",
           "decision":"PRIORITY_MAIN_LUMINOUS"}]}
    return seed,raw,pixels,decisions


class ArtistBulkTriageTests(unittest.TestCase):
    def test_lossless_all_rows_and_user_priorities(self):
        seed,raw,px,dec=inputs()
        r=m.build(raw,px,dec,seed=seed)
        self.assertEqual(r["all_candidate_records_retained"],2)
        self.assertEqual(r["pixel_qa_records_available"],1)
        self.assertEqual(r["exact_user_work_records"],1)
        self.assertEqual(r["commercially_approved"],0)
        self.assertEqual(r["runtime_imported"],0)
        self.assertEqual(len(r["complete_queue"]),2)
        self.assertEqual(r["complete_queue"][0]["review_lane"],
                         "USER_PALETTE_PRIORITY_VISUAL_RIGHTS_REVIEW")
        self.assertEqual(r["complete_queue"][1]["review_lane"],
                         "SOURCE_REFERENCE_NOT_PRIORITY")
        self.assertTrue(all(not w["commercially_approved"] and
                            not w["runtime_visible"] for w in r["complete_queue"]))
    def test_reject_duplicate_source_and_unapproved(self):
        seed,raw,px,dec=inputs()
        raw["priority_shortlist"].append(dict(raw["priority_shortlist"][0]))
        with self.assertRaises(ValueError):
            m.build(raw,px,dec,seed=seed)
        raw["priority_shortlist"].pop()
        raw["priority_shortlist"][0]["commercially_approved"]=True
        with self.assertRaises(ValueError):
            m.build(raw,px,dec,seed=seed)
    def test_exact_runtime_title_and_artist_only_flag(self):
        seed,raw,px,dec=inputs()
        runtime={"the bridge at villeneuve la garenne":[
            {"catalog":"assets/gallery/catalog.json","runtime_id":2,
             "museum_source":"gallery","runtime_title":"The Bridge at Villeneuve-la-Garenne",
             "runtime_artist":"Alfred Sisley","normalized_artist":"alfred sisley"}]}
        r=m.build(raw,px,dec,runtime_index=runtime,seed=seed)
        self.assertEqual(r["possible_runtime_collision_candidates"],1)
        self.assertTrue(any("POSSIBLE_RUNTIME_DUPLICATE_EXACT_TITLE_ARTIST"
                        in x["risk_codes"] for x in r["complete_queue"]))
    def test_no_inferred_identity_from_artist_only(self):
        seed,raw,px,dec=inputs()
        r=m.build(raw,px,dec,seed=seed)
        self.assertTrue(r["not_proven_unique_paintings"])
        self.assertTrue(all(x["work_and_image_licenses"]=="HOLD_PER_ITEM_TERRITORY"
                            for x in r["complete_queue"]))
    def test_data_source_catalog_rows_must_be_list(self):
        import tempfile,json
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            name=root/m.RUNTIME_FILES[0]
            name.parent.mkdir(parents=True,exist_ok=True)
            name.write_text(json.dumps({"invalid":"not a list"}))
            with self.assertRaises(ValueError):
                m.runtime_catalog_index(root)


if __name__=="__main__":
    unittest.main()
