"""NewChirp-maintained drivers win over upstream CHIRP drivers for the
same radio on every CHIRP pin (upstream review 2026-11-28)."""

import importlib.util
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import types
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


class PreferNewChirpDriversTest(unittest.TestCase):
    def test_newchirp_class_wins_regardless_of_import_order(self):
        bridge = _load_bridge()
        upstream = type("Upstream", (), {"__module__": "chirp.drivers.ftx1"})
        ours = type("Ours", (), {
            "__module__": "chirp.drivers.newchirp_yaesu_ftx1"})
        other = type("Other", (), {"__module__": "chirp.drivers.uv5r"})
        directory = types.SimpleNamespace(
            RADIO_TO_DRV={ours: "Yaesu_FTX-1", upstream: "Yaesu_FTX-1",
                          other: "Baofeng_UV-5R"},
            DRV_TO_RADIO={"Yaesu_FTX-1": upstream, "Baofeng_UV-5R": other},
        )
        bridge._prefer_newchirp_drivers(directory)
        self.assertIs(directory.DRV_TO_RADIO["Yaesu_FTX-1"], ours)
        self.assertIs(directory.DRV_TO_RADIO["Baofeng_UV-5R"], other)


PACKAGED_CHECK = """
import importlib.util, sys
spec = importlib.util.spec_from_file_location("bridge", sys.argv[1])
bridge = importlib.util.module_from_spec(spec)
sys.modules["bridge"] = bridge
spec.loader.exec_module(bridge)
directory = bridge.load_chirp(sys.argv[2], sys.argv[3], None)
for ident in ("Yaesu_FTX-1", "Yaesu_FTM-150E", "Retevis_RA89"):
    print(ident, directory.get_radio(ident).__module__)
"""


class PackagedLayoutTest(unittest.TestCase):
    def test_packaged_layout_keeps_newchirp_drivers(self):
        with tempfile.TemporaryDirectory() as scratch:
            source = Path(scratch) / "source"
            shutil.copytree(SOURCE / "chirp", source / "chirp",
                            ignore=shutil.ignore_patterns("__pycache__"))
            for driver in (ROOT / "drivers").glob("*.py"):
                shutil.copy2(driver, source / "chirp/drivers" / driver.name)
            result = subprocess.run(
                [sys.executable, "-B", "-c", PACKAGED_CHECK,
                 str(ROOT / "scripts/chirp_bridge.py"), str(source),
                 str(PYTHON_VENDOR)],
                capture_output=True, text=True, timeout=600)
            self.assertEqual(result.returncode, 0, result.stderr[-2000:])
            owners = dict(line.split() for line in result.stdout.splitlines()
                          if line.count(" ") == 1)
            for ident in ("Yaesu_FTX-1", "Yaesu_FTM-150E", "Retevis_RA89"):
                self.assertIn(".newchirp_", owners.get(ident, ""), ident)


if __name__ == "__main__":
    unittest.main()
