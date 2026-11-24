import tempfile,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from artdrift_visual_review import inspect
class VisualReviewTests(unittest.TestCase):
    def test_all_real_local_images_decode_and_board_is_reproducible(self):
        with tempfile.TemporaryDirectory() as temp:
            report=inspect(Path(__file__).resolve().parents[1],Path(temp),board_size=20,remote_sample=0)
            self.assertEqual(report["baseline_real_thumbnails_decoded"],457)
            self.assertEqual(report["candidate_metadata_without_packaged_image"],585)
            self.assertEqual(report["displayed_contact_cards"],20)
            self.assertEqual(report["remote_source_comparison_attempts"],0)
            self.assertEqual(report["actual_user_visual_review"],"PENDING")
            self.assertTrue((Path(temp)/"review-board.html").is_file())
if __name__=="__main__":unittest.main()
