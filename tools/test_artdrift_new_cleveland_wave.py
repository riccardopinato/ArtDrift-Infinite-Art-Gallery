import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from artdrift_new_cleveland_wave import candidate
def fixture():
    return {"id":12345,"type":"Painting","share_license_status":"CC0",
        "title":"Landscape","creation_date":"1880",
        "accession_number":"1980.1","creators":[{"description":"Alice"}],
        "images":{"web":{"url":"https://openaccess-cdn.clevelandart.org/a.jpg"},
                  "print":{"url":"https://openaccess-cdn.clevelandart.org/print.jpg"}}}
class ClevelandTests(unittest.TestCase):
    def test_only_explicit_cc0_painting_with_approved_image_host(self):
        obj=candidate(fixture())
        self.assertEqual(obj["publication_status"],"HOLD")
        self.assertEqual(obj["rights_status"],"IMAGE_REVIEW")
        self.assertEqual(obj["image_print_candidate"],"https://openaccess-cdn.clevelandart.org/print.jpg")
        self.assertIsNone(candidate({...} if False else dict(fixture(),share_license_status="Copyrighted")))
        self.assertIsNone(candidate(dict(fixture(),type="Sculpture")))
        changed=fixture();changed["images"]["web"]["url"]="https://openaccess-cdn.clevelandart.org.evil/a"
        self.assertIsNone(candidate(changed))
if __name__=="__main__":unittest.main()
