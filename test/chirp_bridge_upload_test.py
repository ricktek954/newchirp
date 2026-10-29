"""Protocol regression tests for CHIRP bridge uploads."""

from __future__ import annotations

import importlib.util
import struct
import sys
import tempfile
import unittest
from collections import deque
from pathlib import Path
from types import SimpleNamespace
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

    def test_bridge_error_does_not_require_a_model_argument(self):
        message = bridge.bridge_error_message(
            RuntimeError("catalog failed"),
            command="list-models",
            model=None,
        )

        self.assertEqual(message, "catalog failed")

    def test_common_extra_fields_include_documentation(self):
        image = SOURCE / "tests/images/Baofeng_UV-5R_Mini.img"
        radio = self.directory.get_radio_by_image(str(image))
        start, end = radio.get_features().memory_bounds
        channel = next(
            mem
            for number in range(start, end + 1)
            if not (mem := radio.get_memory(number)).empty
        )
        fields = {
            field["name"]: field["documentation"]
            for field in bridge.extra_fields_json(channel)
        }

        self.assertIn("Busy Channel Lockout", fields["bcl"])
        self.assertIn("PTT ID", fields["pttid"])
        self.assertIn("S-CODE", fields["scode"])

    def test_metadata_backed_channel_comments_round_trip(self):
        image = SOURCE / "tests/images/Yaesu_FT-60.img"
        radio = self.directory.get_radio_by_image(str(image))
        memory = radio.get_memory(1)
        self.assertFalse(memory.empty)
        memory.comment = "Spirit Mountain - Peak Radio Association"

        bridge.set_memory_with_extras(radio, memory)
        with tempfile.TemporaryDirectory() as directory:
            saved = Path(directory) / "ft60-comments.img"
            radio.save_mmap(str(saved))
            reopened = self.directory.get_radio_by_image(str(saved))

            restored = bridge.memory_with_extras(reopened, 1)
            self.assertEqual(restored.comment, memory.comment)

            bridge.erase_memory_with_extras(reopened, 1)
            self.assertTrue(reopened.get_memory(1).empty)
            self.assertNotIn(
                "0001_comment",
                reopened.metadata.get("mem_extra", {}),
            )

    def test_channel_subdevice_comments_use_parent_metadata(self):
        image = SOURCE / "tests/images/Kenwood_TK-880.img"
        radio = self.directory.get_radio_by_image(str(image))
        channel_radio, _zones, _selected_zone = bridge.channel_context(radio)
        radio.metadata = {
            "mem_extra": {
                "0001_comment": "Zone A repeater",
            }
        }

        restored = bridge.memory_with_extras(channel_radio, 1)

        self.assertEqual(restored.comment, "Zone A repeater")

    def test_live_radio_gets_headless_sync_interface(self):
        from chirp import chirp_common

        class FakeLiveRadio(chirp_common.LiveRadio):
            VENDOR = "Kenwood"
            MODEL = "TS-2000"

            def __init__(self, pipe):
                super().__init__(pipe)
                self.pipe = pipe

            def get_features(self):
                features = chirp_common.RadioFeatures()
                features.memory_bounds = (0, 2)
                return features

        serial = FakeTDH3Serial()
        with (
            mock.patch.object(
                bridge,
                "open_serial",
                lambda _radio_class, _port: serial,
            ),
            mock.patch.object(
                self.directory,
                "get_radio",
                return_value=FakeLiveRadio,
            ),
        ):
            radio = bridge.radio_for(
                self.directory,
                "Kenwood_TS-2000",
                "fake",
                detect_serial=False,
            )

        self.assertEqual(radio.MODEL, "TS-2000")
        self.assertTrue(hasattr(radio, "sync_in"))
        self.assertTrue(hasattr(radio, "sync_out"))
        self.assertIsInstance(radio._live_radio.pipe, bridge.TracedSerial)
        self.assertIs(radio._live_radio.pipe._serial_port, serial)
        self.assertTrue(
            issubclass(
                self.directory.get_radio("Kenwood_TS-2000"),
                chirp_common.LiveRadio,
            )
        )

    def test_repeaterbook_result_converts_to_channel(self):
        channel = bridge.repeaterbook_item_to_channel({
            "Frequency": "146.865000",
            "Input Freq": "146.265000",
            "PL": "151.4",
            "TSQ": "",
            "Callsign": "WB2ECR",
            "Landmark": "Buffalo",
            "Nearest City": "Buffalo",
            "County": "Erie",
            "State": "New York",
            "Use": "OPEN",
            "Operational Status": "On-air",
            "FM Analog": "Yes",
            "DMR": "No",
            "D-Star": "No",
            "System Fusion": "No",
        }, 1)

        self.assertEqual(channel["frequency"], 146.865)
        self.assertEqual(channel["duplex"], "-")
        self.assertEqual(channel["offset"], 0.6)
        self.assertEqual(channel["tone"], "Tone")
        self.assertEqual(channel["txTone"], 151.4)
        self.assertIn("RepeaterBook: WB2ECR", channel["comment"])

    def test_repeaterbook_search_filters_closed_results(self):
        items = [
            {
                "Frequency": "146.865000",
                "Input Freq": "146.265000",
                "PL": "",
                "TSQ": "",
                "Callsign": "OPEN1",
                "Landmark": "Open repeater",
                "Nearest City": "Buffalo",
                "County": "Erie",
                "State": "New York",
                "Use": "OPEN",
                "Operational Status": "On-air",
                "FM Analog": "Yes",
                "DMR": "No",
                "D-Star": "No",
                "System Fusion": "No",
            },
            {
                "Frequency": "147.000000",
                "Input Freq": "147.600000",
                "PL": "",
                "TSQ": "",
                "Callsign": "CLOSED1",
                "Landmark": "Closed repeater",
                "Nearest City": "Buffalo",
                "County": "Erie",
                "State": "New York",
                "Use": "CLOSED",
                "Operational Status": "On-air",
                "FM Analog": "Yes",
                "DMR": "No",
                "D-Star": "No",
                "System Fusion": "No",
            },
        ]
        with mock.patch.object(
            bridge,
            "fetch_repeaterbook_data",
            return_value={"results": items},
        ):
            results = bridge.search_repeaterbook(
                "United States",
                "New York",
                query="Buffalo",
                open_only=True,
                fm_only=True,
            )

        self.assertEqual(results["totalMatches"], 1)
        self.assertEqual(results["results"][0]["callsign"], "OPEN1")

    def test_repeaterbook_radius_excludes_missing_coordinates(self):
        item = {
            "Frequency": "146.865000",
            "Input Freq": "146.265000",
            "PL": "",
            "TSQ": "",
            "Callsign": "NOCOORD",
            "Landmark": "No coordinates",
            "County": "Erie",
            "State": "New York",
            "Use": "OPEN",
            "Operational Status": "On-air",
            "FM Analog": "Yes",
            "DMR": "No",
            "D-Star": "No",
            "System Fusion": "No",
        }
        with mock.patch.object(
            bridge,
            "fetch_repeaterbook_data",
            return_value={"results": [item]},
        ):
            results = bridge.search_repeaterbook(
                "United States",
                "New York",
                latitude=42.8864,
                longitude=-78.8784,
                distance=50,
            )

        self.assertEqual(results["totalMatches"], 0)

    def test_repeaterbook_query_normalizes_county_suffix(self):
        self.assertEqual(
            bridge.normalize_repeaterbook_query("Broward County"),
            "broward",
        )
        self.assertEqual(
            bridge.normalize_repeaterbook_query("East Baton Rouge Parish"),
            "east baton rouge",
        )

    def test_repeaterbook_all_services_combines_results(self):
        def item(callsign, frequency, latitude, longitude):
            return {
                "Frequency": frequency,
                "Input Freq": "0",
                "PL": "",
                "TSQ": "",
                "Callsign": callsign,
                "Landmark": callsign,
                "County": "Broward",
                "State": "Florida",
                "Use": "OPEN",
                "Operational Status": "On-air",
                "FM Analog": "Yes",
                "DMR": "No",
                "D-Star": "No",
                "System Fusion": "No",
                "Lat": latitude,
                "Long": longitude,
            }

        def fetch(service, country, state):
            if service == "gmrs":
                return {
                    "results": [
                        item("GMRS1", "462.550000", "26.1224", "-80.1373")
                    ]
                }
            return {
                "results": [
                    item("HAM1", "146.865000", "42.8864", "-78.8784")
                ]
            }

        with mock.patch.object(
            bridge,
            "fetch_repeaterbook_data",
            side_effect=fetch,
        ):
            results = bridge.search_repeaterbook(
                "United States",
                "Florida",
                service="all",
                query="Broward County",
            )

        self.assertEqual(results["totalMatches"], 2)
        self.assertEqual(
            {result["service"] for result in results["results"]},
            {"Amateur", "GMRS"},
        )
        coordinates = {
            result["callsign"]: (result["latitude"], result["longitude"])
            for result in results["results"]
        }
        self.assertEqual(coordinates["HAM1"], (42.8864, -78.8784))
        self.assertEqual(coordinates["GMRS1"], (26.1224, -80.1373))


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

    def test_unsupported_frequency_error_names_nearest_programmable_value(self):
        message = bridge.channel_validation_message(
            SimpleNamespace(freq=462124500),
            ["Unable to find a supported tuning step for 462.124500"],
            [2.5, 5.0, 6.25, 10.0, 12.5, 25.0],
        )

        self.assertIn("Nearest frequency", message)
        self.assertIn("462.125000 MHz", message)


if __name__ == "__main__":
    unittest.main()
