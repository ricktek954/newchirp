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


class _NoResponseSerial:
    def write(self, data):
        return len(data)

    def read(self, size):
        return b""


class _IdSerial:
    def __init__(self):
        self.response = b"ID TM-D700;"

    def write(self, data):
        return len(data)

    def read(self, size):
        result = self.response[:size]
        self.response = self.response[size:]
        return result


class _NoSettingsRadio:
    class Features:
        has_settings = False

    def get_features(self):
        return self.Features()

    def get_settings(self):
        raise AssertionError("get_settings must not run without settings")


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

    def test_write_timeout_names_the_failed_memory_command(self):
        radio = self.radio_class.__new__(self.radio_class)
        radio.LAST_DELIMITER = (";", "")
        radio.WRITE_COMMAND_TIMEOUT = 0.0
        radio.READ_COMMAND_TIMEOUT = 0.0

        with self.assertRaisesRegex(
            Exception,
            r"did not answer MW memory 001 within 0\.0 seconds",
        ):
            radio._command(_NoResponseSerial(), "MW000100146520000")

    def test_ts2000_reports_no_global_settings(self):
        radio = self.radio_class(None)

        self.assertFalse(radio.get_features().has_settings)

    def test_no_settings_radios_return_an_empty_payload(self):
        bridge = _load_bridge()

        self.assertFalse(bridge.has_global_settings(_NoSettingsRadio()))
        self.assertEqual(
            bridge.settings_payload(_NoSettingsRadio()),
            {"hasSettings": False, "settings": []},
        )

    def test_serial_trace_identifies_the_failed_memory_command(self):
        bridge = _load_bridge()
        trace = bridge.RadioCommunicationTrace()
        serial = bridge.TracedSerial(_NoResponseSerial(), trace)

        serial.write(b"MW000100146520000;")
        serial.read(8)
        report = trace.format()

        self.assertIn("MW memory=001", report)
        self.assertIn("no response", report)
        self.assertNotIn("146520000", report)

    def test_serial_trace_records_the_detected_radio_identifier(self):
        bridge = _load_bridge()
        trace = bridge.RadioCommunicationTrace()
        serial = bridge.TracedSerial(_IdSerial(), trace)

        serial.write(b"ID;")
        serial.read(32)

        self.assertIn("ID | radio id=TM-D700", trace.format())


if __name__ == "__main__":
    unittest.main()
