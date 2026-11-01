"""Offline compatibility tests for the AnyTone 5888UV driver override."""

import importlib.util
from pathlib import Path
import sys
import unittest
import warnings


from chirp_test_source import chirp_source


ROOT = Path(__file__).resolve().parent.parent
SOURCE = chirp_source()
VENDOR = ROOT / "assets/python/pyserial-3.5-py2.py3-none-any.whl"


def _load_bridge():
    spec = importlib.util.spec_from_file_location(
        "newchirp_chirp_bridge_anytone",
        ROOT / "scripts/chirp_bridge.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load chirp_bridge.py")
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


class AnyTone5888UVCompatTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = _load_bridge().load_chirp(
            str(SOURCE),
            str(VENDOR),
            str(ROOT / "drivers"),
        )
        cls.radio_class = cls.directory.get_radio("AnyTone_5888UV")

    def test_unknown_sql_mode_does_not_abort_channel_read(self):
        from chirp import memmap

        radio = self.radio_class(memmap.MemoryMapBytes(b"\x00" * 0x8000))
        radio.process_mmap()
        radio._memobj.memory[0].sqlMode = 7

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            memory = radio.get_memory(1)

        self.assertEqual(memory.number, 1)
        self.assertFalse(memory.empty)
        self.assertFalse(
            any("RadioSettingValueList" in str(warning.message)
                for warning in caught)
        )


if __name__ == "__main__":
    unittest.main()
