"""Replay tests for the read-only IC-F50V/F60V capture profile.

CHIRP's Icom clone simulator plays a radio whose model ID and image size the
profile does not know in advance. Nothing here proves physical behaviour.
"""

import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

from chirp_test_source import chirp_source


ROOT = Path(__file__).resolve().parent.parent
SOURCE = chirp_source()
PYTHON_VENDOR = ROOT / "assets/python/pyserial-3.5-py2.py3-none-any.whl"


def _load_bridge():
    spec = importlib.util.spec_from_file_location(
        "newchirp_chirp_bridge_f50v_capture", ROOT / "scripts/chirp_bridge.py")
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


class _SimulatedF50V:
    MODEL_ID = b"\x25\x31\x01\x00"

    def __init__(self, size):
        self.size = size

    def get_model(self):
        return self.MODEL_ID

    def get_memsize(self):
        return self.size


class IcomF50VCaptureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bridge = _load_bridge()
        cls.directory = cls.bridge.load_chirp(
            str(SOURCE), str(PYTHON_VENDOR), str(ROOT / "drivers"))
        sys.path.insert(0, str(SOURCE / "tests"))
        import icom_clone_simulator
        cls.simulator = icom_clone_simulator

    def setUp(self):
        self.radio_class = self.directory.get_radio("Icom_IC-F50V_F60V_Capture")
        self.radio_class._model = "\x00\x00\x00\x00"

    def _capture(self, size=0x2000):
        memory = bytes((index * 7) & 0xFF for index in range(size))
        fake = self.simulator.FakeIcomRadio(_SimulatedF50V(size))
        fake._memory = memory
        radio = self.radio_class(fake)
        radio.status_fn = lambda _status: None
        radio.sync_in()
        return radio, memory

    def test_capture_reads_unknown_model_and_size(self):
        radio, memory = self._capture()
        self.assertEqual(radio._mmap.get_packed(), memory)
        self.assertEqual(radio._metadata["icom_capture_model_id"],
                         "25 31 01 00")
        self.assertEqual(radio._metadata["icom_capture_size"], 0x2000)
        self.assertIn("25 31 01 00", self.bridge.radio_firmware(radio))

    def test_saved_capture_reopens_with_its_model_id(self):
        radio, memory = self._capture()
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "f50v.img"
            radio.save_mmap(str(path))
            reopened = self.directory.get_radio_by_image(str(path))
        self.assertIsInstance(reopened, self.radio_class)
        self.assertEqual(reopened._mmap.get_packed(), memory)
        self.assertIn("25 31 01 00", self.bridge.radio_firmware(reopened))

    def test_profile_never_writes(self):
        radio, _memory = self._capture()
        self.assertTrue(self.radio_class.NEWCHIRP_WRITE_DISABLED)
        with self.assertRaisesRegex(Exception, "read-only"):
            radio.sync_out()
        self.assertTrue(radio.get_memory(1).empty)


if __name__ == "__main__":
    unittest.main()
