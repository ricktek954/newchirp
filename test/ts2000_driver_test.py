"""Offline checks for NewChirp's TS-2000 timing override."""

from pathlib import Path
import importlib.util
import sys
import unittest


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "build_support/chirp-20261023"
PYTHON_VENDOR = ROOT / "assets/python/pyserial-3.5-py2.py3-none-any.whl"


def _load_bridge():
    spec = importlib.util.spec_from_file_location(
        "newchirp_chirp_bridge_ts2000",
        ROOT / "scripts/chirp_bridge.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load chirp_bridge.py")
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


class _EchoSerial:
    def __init__(self):
        self.last_response = b""
        self.timeout = 0.25
        self.writes = []

    def write(self, data):
        self.writes.append(bytes(data))
        self.last_response = bytes(data)

    def read(self, size):
        result = self.last_response[:size]
        self.last_response = self.last_response[size:]
        return result


class TS2000DriverTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        bridge = _load_bridge()
        cls.directory = bridge.load_chirp(
            str(SOURCE),
            str(PYTHON_VENDOR),
            str(ROOT / "drivers"),
        )
        cls.radio_class = cls.directory.get_radio("Kenwood_TS-2000")

    def test_newchirp_driver_replaces_bundled_ts2000(self):
        self.assertEqual(self.radio_class.__name__, "TS2000Radio")
        self.assertEqual(
            self.radio_class.__module__,
            "newchirp.drivers.newchirp_ts2000",
        )
        self.assertEqual(self.radio_class.READ_COMMAND_TIMEOUT, 1.0)
        self.assertEqual(self.radio_class.WRITE_COMMAND_TIMEOUT, 5.0)

    def test_write_command_echo_is_accepted(self):
        radio = self.radio_class.__new__(self.radio_class)
        radio.LAST_DELIMITER = (";", "")
        serial = _EchoSerial()

        response = radio._command(serial, "MW", "000100000")

        self.assertEqual(response, "MW000100000")
        self.assertEqual(serial.writes[-1], b"MW000100000;")


if __name__ == "__main__":
    unittest.main()
