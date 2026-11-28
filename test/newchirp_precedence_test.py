"""NewChirp-maintained drivers win over upstream CHIRP drivers for the
same radio on every CHIRP pin (upstream review 2026-11-28)."""

import importlib.util
from pathlib import Path
import sys
import unittest

from chirp_test_source import chirp_source


ROOT = Path(__file__).resolve().parent.parent
SOURCE = chirp_source()
PYTHON_VENDOR = ROOT / "assets/python/pyserial-3.5-py2.py3-none-any.whl"


def _load_bridge():
    spec = importlib.util.spec_from_file_location(
        "newchirp_chirp_bridge_precedence", ROOT / "scripts/chirp_bridge.py")
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


class NewChirpPrecedenceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = _load_bridge().load_chirp(
            str(SOURCE), str(PYTHON_VENDOR), str(ROOT / "drivers"))

    def _module(self, ident):
        return self.directory.get_radio(ident).__module__

    def test_newchirp_owns_the_ftx1(self):
        self.assertIn("newchirp_yaesu_ftx1", self._module("Yaesu_FTX-1"))

    def test_newchirp_owns_the_ftm150_models(self):
        for ident in ("Yaesu_FTM-150R", "Yaesu_FTM-150E"):
            self.assertIn("newchirp_ftm150", self._module(ident), ident)

    def test_ftx1_file_open_explains_live_cat(self):
        from chirp import errors

        radio_class = self.directory.get_radio("Yaesu_FTX-1")
        with self.assertRaisesRegex(errors.RadioError, "live over its CAT"):
            radio_class(None)


if __name__ == "__main__":
    unittest.main()
