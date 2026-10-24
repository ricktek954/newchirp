"""Protocol regression tests for CHIRP bridge uploads."""

from __future__ import annotations

import importlib.util
import struct
import sys
import unittest
from collections import deque
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parent.parent
SOURCE = (
    ROOT / "build_support/chirp-20261023"
    if (ROOT / "build_support/chirp-20261023").is_dir()
    else ROOT.parent / "chirp-20260626"
)
VENDOR = ROOT / "assets/python/pyserial-3.5-py2.py3-none-any.whl"
TD_H3_IMAGE = SOURCE / "tests/images/TIDRADIO_TD-H3.img"
A36PLUS_IMAGE = SOURCE / "tests/images/Talkpod_A36plus.img"

spec = importlib.util.spec_from_file_location(
    "newchirp_chirp_bridge", ROOT / "scripts/chirp_bridge.py"
)
if spec is None or spec.loader is None:
    raise RuntimeError("Could not load chirp_bridge.py")

bridge = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = bridge
spec.loader.exec_module(bridge)


class FakeTDH3Serial:
    def __init__(self):
        self.timeout = 0.25
        self.writes: list[bytes] = []
        self._responses: deque[bytes] = deque()
        self.ident_count = 0

    def write(self, data):
        self.writes.append(bytes(data))
        if data == b"PVOJH\x5c\x14":
            self.ident_count += 1
            if self.ident_count == 1:
                self._responses.append(b"\x06")
        elif data == b"\x02":
            self._responses.append(b"P31183\xff\xff")
        elif data == b"\x06":
            self._responses.append(b"\x06")
        elif data[:1] == b"R":
            command = bytes(data)
            self._responses.append(
                b"W" + command[1:] + b"\x00" * 0x20 + b"\x00"
            )
        elif data[:1] == b"W":
            self._responses.append(b"\x06")

    def read(self, size):
        result = bytearray()
        while self._responses and len(result) < size:
            chunk = self._responses[0]
            take = min(size - len(result), len(chunk))
            result.extend(chunk[:take])
            if take == len(chunk):
                self._responses.popleft()
            else:
                self._responses[0] = chunk[take:]
        return bytes(result)

    def close(self):
        pass


class UploadHandshakeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = bridge.load_chirp(str(SOURCE), str(VENDOR))
        from chirp import errors

        cls.errors = errors
        bridge.status_progress = lambda *_args, **_kwargs: None

    def test_td_h3_upload_handshakes_once_before_writing(self):
        serial = FakeTDH3Serial()
        bridge.open_serial = lambda _radio_class, _port: serial

        radio = bridge.radio_for(
            self.directory,
            "TIDRADIO_TD-H3",
            "fake",
            image=str(TD_H3_IMAGE),
            detect_serial=False,
        )
        self.assertEqual(serial.writes, [])

        radio.load_mmap(str(TD_H3_IMAGE))
        radio.sync_out()

        self.assertEqual(serial.ident_count, 1)
        write_blocks = [
            data for data in serial.writes if data[:1] == b"W"
        ]
        self.assertGreater(len(write_blocks), 0)
        self.assertEqual(serial.writes[-1], b"E")

    def test_probe_before_td_h3_upload_causes_second_handshake_failure(self):
        serial = FakeTDH3Serial()
        bridge.open_serial = lambda _radio_class, _port: serial

        radio = bridge.radio_for(
            self.directory,
            "TIDRADIO_TD-H3",
            "fake",
            image=str(TD_H3_IMAGE),
            detect_serial=True,
        )
        radio.load_mmap(str(TD_H3_IMAGE))

        with self.assertRaises(self.errors.RadioNoResponse):
            radio.sync_out()
        self.assertEqual(serial.ident_count, 2)

    def test_tk880_image_uses_populated_channel_subdevice(self):
        image = SOURCE / "tests/images/Kenwood_TK-880.img"
        radio = bridge.radio_from_image(
            self.directory,
            "Kenwood_TK-880",
            str(image),
        )

        channel_radio, zones, selected_zone = bridge.channel_context(radio)

        self.assertIsNot(channel_radio, radio)
        self.assertFalse(channel_radio.get_memory(1).empty)
        self.assertGreaterEqual(len(zones), 2)
        self.assertEqual(selected_zone, 0)
        self.assertEqual(zones[0]["name"], "1")
        self.assertEqual(zones[0]["channelCount"], 30)
        self.assertEqual(
            channel_radio.get_features().memory_bounds,
            (1, 250),
        )

    def test_ft60_read_ready_message_follows_serial_open(self):
        calls = []
        serial = FakeTDH3Serial()
        with (
            mock.patch.object(
                bridge,
                "open_serial",
                lambda _radio_class, _port: (
                    calls.append("open") or serial
                ),
            ),
            mock.patch.object(
                bridge,
                "emit_progress",
                lambda label, fraction=None: calls.append(
                    ("ready", label, fraction)
                ),
            ),
        ):
            radio = bridge.radio_for(
                self.directory,
                "Yaesu_FT-60",
                "fake",
                detect_serial=False,
            )
            bridge.emit_read_ready(radio)

        self.assertEqual(
            calls,
            [
                "open",
                (
                    "ready",
                    bridge.MANUAL_READ_READY_MESSAGE,
                    0.01,
                ),
            ],
        )

    def test_ft60_read_timeout_explains_when_to_press_ptt(self):
        error = self.errors.RadioNoResponse()

        message = bridge.bridge_error_message(
            error,
            command="download",
            model="Yaesu_FT-60",
        )

        self.assertIn("F8 CLONE", message)
        self.assertIn(bridge.MANUAL_READ_READY_MESSAGE, message)
        self.assertNotIn(
            "read again",
            bridge.bridge_error_message(
                error,
                command="upload",
                model="Yaesu_FT-60",
            ),
        )


class FrequencyPrecisionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = bridge.load_chirp(str(SOURCE), str(VENDOR))

    def test_a36plus_airband_frequency_rounds_to_whole_hertz(self):
        radio = bridge.radio_from_image(
            self.directory, "Talkpod_A36plus", str(A36PLUS_IMAGE)
        )
        memory = radio.get_memory(83)
        item = bridge.memory_json(memory)
        item.update({"frequency": 131.325, "step": 25.0})

        bridge.apply_json(radio, memory, item)

        self.assertEqual(memory.freq, 131325000)
        self.assertEqual(radio.validate_memory(memory), [])


if __name__ == "__main__":
    unittest.main()
