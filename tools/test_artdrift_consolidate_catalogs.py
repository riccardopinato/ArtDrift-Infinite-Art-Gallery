import unittest
import sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from artdrift_consolidate_catalogs import reconcile
from artdrift_museum_ingest import record

def stage(provider="cleveland", native_id="95272", title="Gardener's House at Antibes"):
    return record(provider=provider,native_id=native_id,museum="Museum",
      title=title,artist="Claude Monet (French, 1840–1926)",year="1890",
      medium="Painting",
      metadata_url="https://clevelandart.org/art/1916.1044" if provider=="cleveland"
                   else "https://www.tate.org.uk/art/artworks/T00001")

def existing(native="95272",internal="20095272",title="Gardener's House at Antibes"):
    return {"source_key":"cleveland:"+internal,"museum_source":"cleveland",
        "museum_native_id":native,"title":title}

class ConsolidationIdentityTests(unittest.TestCase):
    def test_different_internal_keys_same_native_id_collapse(self):
        report=reconcile([existing()],[stage()])
        self.assertEqual(report["already_present"],1)
        self.assertEqual(report["new_stage_distinct_records"],0)
        self.assertEqual(report["hypothetical_distinct_records"],1)
        self.assertEqual(report["overlap"][0]["existing_source_key"],"cleveland:20095272")
        self.assertEqual(report["overlap"][0]["staged_source_key"],"cleveland:95272")
        self.assertEqual(report["all_stage_publication_status"],"HOLD")
        self.assertEqual(report["automatic_approvals"],0)

    def test_different_provider_is_a_distinct_identity(self):
        report=reconcile([existing()],[stage(provider="tate",native_id="95272")])
        self.assertEqual(report["already_present"],0)
        self.assertEqual(report["new_stage_distinct_records"],1)

    def test_conflicting_same_native_id_is_not_silently_merged(self):
        with self.assertRaisesRegex(ValueError,"Conflicting primary-source title"):
            reconcile([existing(title="Completely different work")],[stage()])

    def test_duplicate_stage_or_museum_identity_is_rejected(self):
        with self.assertRaisesRegex(ValueError,"Duplicate museum identity"):
            reconcile([existing(),existing(internal="50095272")],[stage()])
        with self.assertRaisesRegex(ValueError,"Duplicate staged identity"):
            reconcile([existing()],[stage(),stage()])

if __name__=="__main__":
    unittest.main()
