"""Unset CTCSS tones must not stop a live Icom CI-V read (IC-910 report)."""

import importlib.util
from pathlib import Path
import sys
import unittest
from unittest import mock

from chirp_test_source import chirp_source


ROOT = Path(__file__).resolve().parent.parent
PYTHON_VENDOR = ROOT / "assets/python/pyserial-3.5-py2.py3-none-any.whl"


def _load_bridge():
    spec = importlib.util.spec_from_file_location(
        "newchirp_chirp_bridge_icomciv_tone", ROOT / "scripts/chirp_bridge.py"
    )
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


class IcomCIVToneCompatTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = _load_bridge().load_chirp(
            str(chirp_source()), str(PYTHON_VENDOR), str(ROOT / "drivers"))

    def _read_with_tones(self, model, rtone, ctone):
        radio_class = self.directory.get_radio(model)
        radio = radio_class(None)
        from chirp import bitwise
        from chirp.memmap import MemoryMapBytes

        frame = radio._classes["mem"]()
        size = bitwise.parse(
            frame.FORMAT, MemoryMapBytes(bytes(256))).size() // 8
        frame._data = bytes(size)
        obj = frame.get_obj()
        obj.freq = 145_500_000
        obj.rtone = rtone
        obj.ctone = ctone
        frame._data = frame._data.get_packed()

        with mock.patch.object(radio, "_detect_baudrate"), \
                mock.patch.object(radio, "_send_frame"), \
                mock.patch.object(radio, "_recv_frame", return_value=frame):
            return radio.get_memory(1)

    def test_ic910_channel_with_unset_tones_reads(self):
        mem = self._read_with_tones("Icom_IC-910", 0, 0)
        self.assertEqual(mem.freq, 145_500_000)
        self.assertEqual(mem.rtone, 88.5)
        self.assertEqual(mem.ctone, 88.5)

    def test_real_tones_are_unchanged(self):
        mem = self._read_with_tones("Icom_IC-910", 1000, 1318)
        self.assertEqual(mem.rtone, 100.0)
        self.assertEqual(mem.ctone, 131.8)

    def test_newchirp_frame_classes_are_covered(self):
        from chirp.drivers import icomciv

        for model in ("Icom_IC-7200", "Icom_IC-9700", "Icom_IC-910"):
            radio = self.directory.get_radio(model)(None)
            frame_class = radio._classes["mem"]
            self.assertTrue(issubclass(frame_class, icomciv.MemFrame))
            self.assertTrue(getattr(frame_class.get_obj,
                                    "newchirp_tone_safe", False), model)


if __name__ == "__main__":
    unittest.main()
