import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from artdrift_prepare_new_cleveland_d1 import prepare
def historical():
    museum=[{"museum_source":"cleveland","museum_native_id":str(i)} for i in range(5085)]
    stage=[{"provider":"moma","native_id":str(i),"publication_status":"HOLD"} for i in range(535)]
    candidates=[{"provider":"cleveland","native_id":str(i+70000),
      "publication_status":"HOLD","rights_status":"IMAGE_REVIEW",
      "source_share_license_status":"CC0","museum":"Cleveland Museum",
      "title":"Landscape","artist":"An artist","date":"1900",
      "medium":"Oil on canvas","source_url":"https://www.clevelandart.org/art/1900.1"} for i in range(100)]
    return candidates,museum,stage
class NewD1HoldTests(unittest.TestCase):
    def test_produces_only_100_metadata_only_holds(self):
        c,m,s=historical()
        rows=prepare(c,m,s)
        self.assertEqual(len(rows),100)
        self.assertTrue(all(x["rights_status"]=="METADATA_ONLY" and x["image_url"]=="" and x["rights_license"]=="" for x in rows))
    def test_existing_native_collision_rejected(self):
        c,m,s=historical()
        c[0]["native_id"]="1"
        with self.assertRaisesRegex(ValueError,"Duplicate"):
            prepare(c,m,s)
    def test_source_copyright_review_must_not_claim_approval(self):
        c,m,s=historical()
        c[0]["publication_status"]="APPROVED"
        with self.assertRaisesRegex(ValueError,"Source identity"):
            prepare(c,m,s)
    def test_stage_cannot_be_modified_if_any_already_approved(self):
        c,m,s=historical()
        s[0]["publication_status"]="APPROVED"
        with self.assertRaisesRegex(ValueError,"approved"):
            prepare(c,m,s)
if __name__=="__main__":unittest.main()
