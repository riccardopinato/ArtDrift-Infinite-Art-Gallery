import json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from artdrift_d1_reconcile import reconcile,unwrap
def item(provider,native,id):
    return dict(museum_source=provider,museum_native_id=native,source_key=f"{provider}:{id}")
def staged(provider,native,status="HOLD"):
    return dict(provider=provider,native_id=native,publication_status=status)
class D1ReconcileTests(unittest.TestCase):
    def data(self):
        old=[item("cleveland",str(i),i+100000) for i in range(49)]
        old+=[item("smithsonian",str(i),i+200000) for i in range(5035)]
        new=item("smithsonian","npg:npg_NPG.2007.11",60000001)
        stage=[staged("cleveland",str(i)) for i in range(49)]
        stage+=[staged("moma",str(i)) for i in range(253)]
        stage+=[staged("tate",str(i)) for i in range(233)]
        return old+[new],old,stage
    def test_one_missing_and_no_auto_approval(self):
        local,remote,stage=self.data()
        r=reconcile(local,remote,stage)
        self.assertEqual(r["missing_remote_native_ids"],1)
        self.assertEqual(r["distinct_native_identities"],5571)
        self.assertEqual(r["approved_staged_rows"],0)
    def test_stage_approval_fails_closed(self):
        local,remote,stage=self.data()
        stage[0]["publication_status"]="APPROVED"
        with self.assertRaisesRegex(ValueError,"Unexpected published"):
            reconcile(local,remote,stage)
    def test_reject_bad_remote_identity(self):
        local,remote,stage=self.data()
        remote[0]["museum_native_id"]="malicious"
        with self.assertRaisesRegex(ValueError,"Unexpected remote"):
            reconcile(local,remote,stage)
    def test_wrangler_json_contract(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/"wrangler.json"
            p.write_text(json.dumps([{"results":[{"source_key":"x"}],"success":True}]))
            self.assertEqual(unwrap(p),[{"source_key":"x"}])
if __name__=="__main__":unittest.main()
