"""Offline checks for Icom IC-746PRO CI-V addressing."""

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
        "newchirp_chirp_bridge_icom_ic746pro",
        ROOT / "scripts/chirp_bridge.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load chirp_bridge.py")
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


class _Serial:
    def __init__(self):
        self.writes = []

    def write(self, data):
        self.writes.append(bytes(data))
        return len(data)

    def read(self, size=1):
        return b""

    def reset_input_buffer(self):
        pass


class IcomIC746ProDriverTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        bridge = _load_bridge()
        cls.directory = bridge.load_chirp(
            str(SOURCE),
            str(PYTHON_VENDOR),
            str(ROOT / "drivers"),
        )
        cls.radio_class = cls.directory.get_radio("Icom_IC-746PRO")

    def test_exact_profile_uses_pro_civ_address(self):
        self.assertEqual(self.radio_class.MODEL, "IC-746PRO")
        self.assertEqual(self.radio_class._model, "\x66")
        self.assertEqual(self.radio_class.BAUD_RATE, 9600)
        self.assertEqual(self.radio_class._template, 102)

    def test_frames_are_addressed_to_ic746pro(self):
        from chirp.drivers import icomciv

        serial = _Serial()
        radio = self.radio_class.__new__(self.radio_class)
        radio.pipe = serial
        radio._willecho = False
        frame = icomciv.Frame()
        frame.set_command(0x19)
        radio._send_frame(frame)
        self.assertEqual(serial.writes[0][:4], b"\xFE\xFE\x66\xE0")

    def test_original_ic746_remains_a_separate_model(self):
        original = self.directory.get_radio("Icom_IC-746")
        self.assertEqual(original._model, "\x56")
        self.assertIsNot(original, self.radio_class)


if __name__ == "__main__":
    unittest.main()
