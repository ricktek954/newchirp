"""Offline tests for scripts/upstream_review.py helpers."""

import importlib.util
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parent.parent


def _load():
    spec = importlib.util.spec_from_file_location(
        "newchirp_upstream_review", ROOT / "scripts/upstream_review.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class UpstreamReviewTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.review = _load()

    def test_changed_files_and_line_delta(self):
        with tempfile.TemporaryDirectory() as scratch:
            old = Path(scratch) / "old"
            new = Path(scratch) / "new"
            for root in (old, new):
                (root / "chirp/drivers/__pycache__").mkdir(parents=True)
                (root / "chirp/drivers/same.py").write_text("a\n")
            (old / "chirp/drivers/uv5r.py").write_text("a\nb\n")
            (new / "chirp/drivers/uv5r.py").write_text("a\nc\nd\n")
            (new / "chirp/drivers/newradio.py").write_text("x\n")
            (old / "chirp/drivers/gone.py").write_text("y\n")
            (new / "chirp/drivers/__pycache__/x.pyc").write_bytes(b"\0")
            added, removed, modified = self.review.changed_files(old, new)
            self.assertEqual(added, ["chirp/drivers/newradio.py"])
            self.assertEqual(removed, ["chirp/drivers/gone.py"])
            self.assertEqual(modified, ["chirp/drivers/uv5r.py"])
            self.assertEqual(
                self.review.line_delta(old / modified[0], new / modified[0]),
                (2, 1))

    def test_module_users_match_imports_not_substrings(self):
        texts = {
            ROOT / "drivers/a.py": "from chirp.drivers import uv5r, icf\n",
            ROOT / "drivers/b.py": "import chirp.drivers.uv5rmini\n",
            ROOT / "drivers/c.py": "from chirp import bitwise, memmap\n",
        }
        self.assertEqual(self.review.module_users("uv5r", texts),
                         ["drivers/a.py"])
        self.assertEqual(self.review.module_users("memmap", texts),
                         ["drivers/c.py"])
        self.assertEqual(self.review.module_users("uv5rmini", texts),
                         ["drivers/b.py"])

    def test_pin_is_readable(self):
        commit, digest = self.review.pinned()
        self.assertRegex(commit, r"^[0-9a-f]{40}$")
        self.assertRegex(digest, r"^[0-9a-f]{64}$")


if __name__ == "__main__":
    unittest.main()
