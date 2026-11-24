import importlib.util
import json
import unittest
from pathlib import Path
from unittest.mock import patch

FILE=Path(__file__).parent/"import_museum_remote.py"
spec=importlib.util.spec_from_file_location("remote_d1", FILE)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class D1RemoteGates(unittest.TestCase):
    def test_exact_database_identity(self):
        self.assertTrue(mod.check_config())
        self.assertEqual(mod.DATABASE_ID,"4e7cb3bf-bf3c-480d-9789-93072e70274c")

    def test_wranger_json_count_safely_unwraps(self):
        good=json.dumps([{"results":[{"n":0}],"success":True}])
        self.assertEqual(mod.safe_count(good,"n"),0)
        self.assertEqual(mod.safe_count(json.dumps({"result":[{"results":[{"n":5084}]}]}),"n"),5084)
        with self.assertRaises(RuntimeError):
            mod.safe_count("not JSON","n")
        with self.assertRaises(RuntimeError):
            mod.safe_count(json.dumps({"results":[{"n":"5084"}]}),"n")
        with self.assertRaises(RuntimeError):
            mod.safe_count(json.dumps({"results":[{"n":0},{"n":5}]}),"n")

    def test_wrong_confirmation_id_never_contacts_provider(self):
        with patch("sys.argv",[str(FILE),"--apply","--confirm-id","wrong"]):
            with patch.object(mod,"wrangler") as cloud:
                with self.assertRaisesRegex(RuntimeError,"requires --confirm-id"):
                    mod.main()
                cloud.assert_not_called()

    def test_remote_count_accepts_only_fixed_tables(self):
        with patch.object(mod,"wrangler") as cloud:
            with self.assertRaises(ValueError):
                mod.remote_count("works;DROP TABLE museum_works;")
            cloud.assert_not_called()

    def test_remote_inventory_guard(self):
        payload=[{"uuid":mod.DATABASE_ID,"name":mod.DATABASE_NAME}]
        with patch.object(mod,"wrangler",return_value=json.dumps(payload)):
            self.assertTrue(mod.cloud_inventory())
        payload[0]["name"]="other-database"
        with patch.object(mod,"wrangler",return_value=json.dumps(payload)):
            with self.assertRaisesRegex(RuntimeError,"name mismatch"):
                mod.cloud_inventory()

if __name__=="__main__":
    unittest.main()
