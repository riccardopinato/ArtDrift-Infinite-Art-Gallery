"""Art Drift 486-image final publication gate: fail-closed tests."""
import json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import artdrift_486_final_release_qa as q
class Tests(unittest.TestCase):
 def test_original_file_source_is_not_approval(self):
  r=q.review_wiki({"source_identity":"commons:3","source_file_page":"https://commons.wikimedia.org/wiki/File:A"},
     {"ns":6,"revisions":[{"revid":55,"slots":{"main":{"content":"{{Information\n|source=Old museum scan\n|author=Claude Monet\n}}"}}}]})
  self.assertTrue(r["wiki_checked"])
  self.assertEqual(r["source_field"],"Old museum scan")
  self.assertFalse(r["original_primary_source_authenticated"])
  self.assertFalse(r["commercially_approved"])
 def test_technical_issue_does_not_authorize(self):
  x=q.review_wiki({"source_identity":"commons:3"},error="HTTP_429")
  self.assertFalse(x["wiki_checked"])
  self.assertFalse(x["commercially_approved"])
 def test_stadel_conflict_persisted(self):
  x=q.review_wiki({"source_identity":"staedel:DE-MUS-048017/lido/1350"})
  self.assertIn("MUSEUM_PD_VS_UPSTREAM_CC_BY_SA_TO_RECONCILE",x["issues"])
 def test_potential_same_work_not_proof(self):
  a={"artist_id":"claude_monet","title":"Claude Monet - Water Lilies 1905.jpg","source_identity":"commons:1"}
  b={"artist_id":"claude_monet","title":"Claude Monet - Water Lilies 1905.JPG","source_identity":"commons:2"}
  links,pairs=q.potential_pairs([a,b])
  self.assertEqual(len(pairs),1)
  self.assertFalse(pairs[0]["identity_verified"])
  self.assertEqual(links[a["source_identity"]],["commons:2"])
 def test_blank_wiki_fields_never_capture_next_key(self):
  fields=q.parse_fields("{{Artwork\n|source= \n|author= \n|title= Boats on a river\n|description= River scenery\n}}")
  self.assertFalse(fields.get("source"))
  self.assertFalse(fields.get("author"))
  self.assertEqual(fields.get("description"),"River scenery")
  fields2=q.parse_fields("{{Artwork\n|source= \n|author=Claude Monet\n}}")
  self.assertFalse(fields2.get("source"))
  self.assertEqual(fields2.get("author"),"Claude Monet")
 def test_two_layer_pd_painting_and_cc_photo_is_not_implicit_permission(self):
  wiki="{{Licensed-PD-Art|PD-old-70|CC-BY-4.0}}"
  hints=q.layered_license_hints(wiki)
  self.assertTrue(hints["potential_layered_pd_plus_cc"])
  self.assertTrue(hints["cc_digital_file_license_detected"])
  r=q.review_wiki({"source_identity":"commons:3"},{
    "ns":6,"revisions":[{"slots":{"main":{"content":wiki}}}]})
  self.assertFalse(r["commercially_approved"])
  self.assertIn("PD_PAINTING_AND_CC_DIGITAL_REPRODUCTION_REQUIRE_SEPARATE_CREDIT_CHECK",r["issues"])
 def test_no_truncated_collection(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"q";p.mkdir()
   (p/"rights_486_summary.json").write_text(json.dumps({"source_revision":q.PIN,"images_checked":486}))
   (p/"rights_486_per_item.json").write_text("[]")
   with self.assertRaises(ValueError):q.pinned_reports(p,p)
if __name__=="__main__":unittest.main()
