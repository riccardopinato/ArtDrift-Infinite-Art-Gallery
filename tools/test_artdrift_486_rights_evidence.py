import json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import artdrift_486_rights_evidence as m
def example(lic="Public domain"):
 return {"ns":6,"title":"File:Example.jpg","imageinfo":[{"sha1":"abc",
 "descriptionurl":"https://commons.wikimedia.org/wiki/File:Example.jpg",
 "extmetadata":{"LicenseShortName":{"value":lic},"Artist":{"value":"Harald Sohlberg"},
 "Source":{"value":"Nasjonalmuseet"},"Credit":{"value":"National Museum"}}}]}
def cand(lic="Public domain"):
 return {"source_identity":"commons:1","artist_id":"harald_sohlberg","title":"Example",
 "image_license_claim":lic,"record_url":"https://commons.wikimedia.org/?curid=1",
 "commercially_approved":False,"runtime_visible":False}
def source():return {"image_file_sha1":"abc"}
class RightsAuditTests(unittest.TestCase):
 def test_classification(self):
  self.assertEqual(m.cl("CC BY-NC-SA 4.0"),"NO_COMMERCIAL")
  self.assertEqual(m.cl("CC BY-SA 4.0"),"CC_BY_SA")
  self.assertEqual(m.cl("CC BY 4.0"),"CC_BY")
  self.assertEqual(m.cl("CC0 1.0"),"CC0")
  self.assertEqual(m.cl("Public domain"),"PUBLIC_DOMAIN")
 def test_pd_metadata_does_not_authorize(self):
  x=m.inspect(cand(),source(),example())
  self.assertTrue(x["live_checked"])
  self.assertEqual(x["evidence_tier"],"LIVE_PD_CC0_CLAIM_TO_REVIEW")
  self.assertFalse(x["commercially_approved"])
 def test_nc_disallows(self):
  x=m.inspect(cand(),source(),example("CC BY-NC 4.0"))
  self.assertEqual(x["evidence_tier"],"COMMERCIAL_USE_DISALLOWED_BY_LICENSE")
  self.assertTrue(x["licence_mismatch"])
 def test_attribution_terms(self):
  x=m.inspect(cand("CC BY-SA 4.0"),source(),example("CC BY-SA 4.0"))
  self.assertIn("SHAREALIKE_WHEN_APPLICABLE",x["reuse_requirements"])
  self.assertFalse(x["commercially_approved"])
 def test_file_change(self):
  p=example();p["imageinfo"][0]["sha1"]="changed"
  self.assertIn("FILE_SHA1_CHANGED_SINCE_DISCOVERY",m.inspect(cand(),source(),p)["license_issues"])
 def test_no_live_data(self):
  x=m.inspect(cand(),source(),error="HTTP_429")
  self.assertFalse(x["live_checked"]);self.assertEqual(x["evidence_tier"],"LIVE_QUERY_FAILED")
 def test_official_museum_discrepancy(self):
  x=m.inspect({"source_identity":m.SPECIAL,"artist_id":"alfred_sisley",
     "image_license_claim":"CC BY-SA 4.0"},source())
  self.assertTrue(x["licence_mismatch"])
  self.assertFalse(x["commercially_approved"])
 def test_all_486_coverage(self):
  rows=[dict(cand(),source_identity="commons:"+str(i)) for i in range(1,486)]
  rows.append({"source_identity":m.SPECIAL,"artist_id":"alfred_sisley",
    "image_license_claim":"CC BY-SA 4.0","commercially_approved":False,"runtime_visible":False})
  raw=[dict(source(),identity=x["source_identity"]) for x in rows]
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"q.json";s=Path(d)/"s.json"
   p.write_text(json.dumps({"complete_queue":rows}),encoding="utf-8")
   s.write_text(json.dumps({"priority_shortlist":raw}),encoding="utf-8")
   self.assertEqual(len(m.inputs(p,s)[0]),486)
if __name__=="__main__":unittest.main()
