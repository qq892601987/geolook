import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import geo
import geolib as G


class TestCliRouting(unittest.TestCase):
    def _run(self, argv):
        out = io.StringIO()
        with mock.patch.object(sys, "argv", argv), redirect_stdout(out):
            geo.main()
        return out.getvalue()

    def test_list_empty_project_root(self):
        with tempfile.TemporaryDirectory() as td, mock.patch.object(G, "WORK", Path(td)):
            self.assertIn("还没有任何项目", self._run(["geo.py", "list"]))

    def test_list_project_and_doctor_do_not_overlap(self):
        with tempfile.TemporaryDirectory() as td, mock.patch.object(G, "WORK", Path(td)):
            pdir = Path(td) / "demo"
            pdir.mkdir()
            G.write_json(pdir / "geo.json", {"brand": {"name": "Demo"}, "questions": []})
            (pdir / "reports").mkdir()
            self.assertIn("demo", self._run(["geo.py", "list"]))
            with mock.patch("sample.available", return_value=False):
                doctor = self._run(["geo.py", "doctor"])
            self.assertNotIn("demo", doctor)
            self.assertIn("可用 API 平台：无", doctor)

    def test_help_builds_all_subparsers(self):
        with mock.patch.object(sys, "argv", ["geo.py", "--help"]):
            with self.assertRaises(SystemExit) as raised:
                geo.main()
        self.assertEqual(raised.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
