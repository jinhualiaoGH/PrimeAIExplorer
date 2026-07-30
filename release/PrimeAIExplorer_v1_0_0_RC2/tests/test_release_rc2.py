from pathlib import Path
import json,tempfile,unittest
from primeaiexplorer.release import *
class T(unittest.TestCase):
 def test_result(self): self.assertEqual(CheckResult("x",True,"ok").to_dict()["name"],"x")
 def test_optional(self): self.assertTrue(all_required_pass([CheckResult("x",False,"m",False)]))
 def test_required(self): self.assertFalse(all_required_pass([CheckResult("x",False,"m")]))
 def test_doctor(self): self.assertIn("Import primeaiexplorer.observatories",{x.name for x in doctor_checks(Path.cwd())})
 def test_unique(self): self.assertEqual(len(required_release_paths()),len(set(required_release_paths())))
 def test_missing(self):
  with tempfile.TemporaryDirectory() as d: self.assertFalse(all_required_pass(release_checks(Path(d))))
 def test_current(self): self.assertTrue(all_required_pass(release_checks(Path(__file__).resolve().parents[1])))
 def test_report(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"r.json"; write_check_report(p,[CheckResult("x",True,"ok")],kind="test"); self.assertTrue(json.loads(p.read_text())["passed"])
