"""Offline checks for NewChirp's strict IC-9700 CI-V connection setup."""

from pathlib import Path
import importlib.util
import sys
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "build_support/chirp-20261023"
PYTHON_VENDOR = ROOT / "assets/python/pyserial-3.5-py2.py3-none-any.whl"


def _load_bridge():
    spec = importlib.util.spec_from_file_location(
        "newchirp_chirp_bridge_icom9700",
        ROOT / "scripts/chirp_bridge.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load chirp_bridge.py")
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


class _IC9700Serial:
    def __init__(self, working_baud=115200):
        self.baudrate = 19200
        self.timeout = 0.25
        self.working_baud = working_baud
        self.writes = []
        self.response = b""

    def reset_input_buffer(self):
        self.response = b""

    def write(self, data):
        data = bytes(data)
        self.writes.append(data)
        if data == b"\xfe\xfe\xe0\xe0\xfa\xfd":
            return len(data)
        if data[:5] != b"\xfe\xfe\xa2\xe0\x1a":
            return len(data)
        if self.baudrate == self.working_baud:
            self.response = (
                b"\xfe\xfe\xe0\xa2\x1a\x00\x01\x64\x00"
                + b"\xff"
                + b"\xfd"
            )
        elif self.baudrate == 19200:
            # A short line ending in FD makes the stock probe raise
            # struct.error instead of trying the remaining baud rates.
            self.response = b"\x00\xfd"
        return len(data)

    def read(self, size=1):
        result = self.response[:size]
        self.response = self.response[size:]
        return result

    def close(self):
        pass


class Icom9700DriverTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        bridge = _load_bridge()
        cls.bridge = bridge
        cls.directory = bridge.load_chirp(
            str(SOURCE),
            str(PYTHON_VENDOR),
            str(ROOT / "drivers"),
        )
        cls.radio_class = cls.directory.get_radio("Icom_IC-9700")

    def test_newchirp_driver_replaces_bundled_ic9700(self):
        self.assertEqual(self.radio_class.__name__, "Icom9700Radio")
        self.assertEqual(
            self.radio_class.__module__,
            "newchirp.drivers.newchirp_icom9700",
        )
        prompts = self.radio_class.get_prompts()
        self.assertIn("Unlink from [REMOTE]", prompts.info)
        self.assertIn("CI-V Transceive is off", prompts.pre_download)

    def test_garbled_reply_does_not_stop_baud_detection(self):
        serial = _IC9700Serial(working_baud=115200)
        radio = self.radio_class(serial)

        radio._detect_baudrate()

        self.assertEqual(serial.baudrate, 115200)
        self.assertTrue(radio._baud_detected)

    def test_band_views_reuse_the_validated_parent_connection(self):
        serial = _IC9700Serial(working_baud=115200)
        radio = self.radio_class(serial)
        radio._detect_baudrate()
        serial.writes.clear()

        band = radio.get_sub_devices()[0]
        band._detect_baudrate()

        self.assertEqual(serial.baudrate, 115200)
        self.assertTrue(band._baud_detected)
        self.assertEqual(serial.writes, [])

    def test_live_adapter_exposes_band_and_satellite_zones(self):
        serial = _IC9700Serial(working_baud=115200)
        with mock.patch.object(
            self.bridge,
            "open_serial",
            return_value=serial,
        ):
            radio = self.bridge.radio_for(
                self.directory,
                "Icom_IC-9700",
                "COM13",
                detect_serial=False,
                channel_zone=0,
            )

        channel_radio, zones, selected_zone = self.bridge.channel_context(radio)

        self.assertIs(channel_radio, radio._live_radio)
        self.assertEqual(selected_zone, 0)
        self.assertEqual(
            [zone["name"] for zone in zones],
            ["144 band", "430 band", "1240 band", "Satellite"],
        )
        self.assertEqual([zone["channelCount"] for zone in zones], [99] * 4)

    def test_empty_2m_read_completes_over_validated_connection(self):
        serial = _IC9700Serial(working_baud=115200)
        with mock.patch.object(
            self.bridge,
            "open_serial",
            return_value=serial,
        ):
            radio = self.bridge.radio_for(
                self.directory,
                "Icom_IC-9700",
                "COM13",
                detect_serial=False,
                channel_zone=0,
            )

        radio.status_fn = None
        radio.sync_in()

        self.assertEqual(serial.baudrate, 115200)
        self.assertEqual(radio._live_radio.VARIANT, "144 band")
        self.assertGreater(len(serial.writes), 6)

    def test_trace_identifies_civ_command_without_recording_payload(self):
        trace = self.bridge.RadioCommunicationTrace()

        trace.begin(b"\xfe\xfe\xa2\xe0\x1a\x00\x01\x64\x00\xfd")
        report = trace.format()

        self.assertIn("CI-V a2->e0 cmd=1a/00 (10 bytes)", report)
        self.assertNotIn("016400", report)

    def test_no_valid_reply_gives_actionable_civ_settings(self):
        serial = _IC9700Serial(working_baud=None)
        radio = self.radio_class(serial)

        with self.assertRaisesRegex(
            Exception,
            r"SET > Connectors > CI-V.*Unlink from \[REMOTE\].*"
            r"CI-V Transceive off",
        ):
            radio._detect_baudrate()

        self.assertEqual(serial.baudrate, radio.BAUD_RATE)


if __name__ == "__main__":
    unittest.main()
