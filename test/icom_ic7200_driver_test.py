"""Offline tests for the corrected Icom IC-7200 memory frame."""

import sys
from pathlib import Path
import unittest

from chirp_test_source import chirp_source


ROOT = Path(__file__).resolve().parent.parent
PYTHON_VENDOR = ROOT / "assets/python/pyserial-3.5-py2.py3-none-any.whl"


def _load_bridge():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "newchirp_chirp_bridge_icom_ic7200",
        ROOT / "scripts/chirp_bridge.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load chirp_bridge.py")
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


class Icom7200MemoryFrameTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = _load_bridge().load_chirp(
            str(chirp_source()),
            str(PYTHON_VENDOR),
            str(ROOT / "drivers"),
        )
        cls.radio_class = cls.directory.get_radio("Icom_IC-7200")

    def test_override_replaces_the_broken_upstream_memory_grammar(self):
        self.assertEqual(
            self.radio_class.__name__,
            "NewChirpIcom7200Radio",
        )

        radio = self.radio_class(None)
        frame = radio._classes["mem"]()
        data = bytearray(11)
        data[2] = 1 << 4
        frame._data = bytes(data)

        parsed = frame.get_obj()

        self.assertEqual(parsed.split, 1)
        self.assertEqual(parsed.size() // 8, 11)


if __name__ == "__main__":
    unittest.main()
