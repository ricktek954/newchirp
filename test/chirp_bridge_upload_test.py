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
GMRS_V2_IMAGE = SOURCE / "tests/images/BTECH_GMRS-V2.img"
DM32UV_IMAGE = SOURCE / "tests/images/Baofeng_DM-32UV.img"

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


class FakeLineSerial:
    def __init__(self, response):
        self.response = response

    def write(self, data):
        return len(data)

    def readline(self, _size=-1):
        return self.response

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

    def test_dm32uv_mapping_payload_exposes_zone_memberships(self):
        radio = self.directory.get_radio_by_image(str(DM32UV_IMAGE))

        models = bridge.mapping_payload(radio)

        self.assertEqual(len(models), 1)
        self.assertEqual(models[0]["name"], "Zones")
        self.assertTrue(models[0]["editable"])
        self.assertTrue(models[0]["multiple"])
        self.assertEqual(
            [entry["name"] for entry in models[0]["mappings"]],
            ["Analog", "Digital", "New zone"],
        )
        self.assertEqual(
            models[0]["mappings"][0]["channelLocations"],
            list(range(1, 10)) + [13, 14],
        )

    def test_dm32uv_mapping_changes_create_rename_and_keep_multi_zone(self):
        radio = self.directory.get_radio_by_image(str(DM32UV_IMAGE))
        models = bridge.mapping_payload(radio)
        analytics = models[0]["mappings"][0]
        digital = models[0]["mappings"][1]
        new_zone = models[0]["mappings"][2]
        analytics["channelLocations"].append(10)
        new_zone["name"] = "Local"
        new_zone["channelLocations"] = [10]

        updated = bridge.apply_mapping_payload(
            radio,
            [models[0]],
            active_locations={
                *analytics["channelLocations"],
                *digital["channelLocations"],
                *new_zone["channelLocations"],
            },
        )

        self.assertEqual(
            updated[0]["mappings"][0]["channelLocations"][-1],
            10,
        )
        self.assertEqual(updated[0]["mappings"][2]["name"], "Local")
        self.assertEqual(
            updated[0]["mappings"][2]["channelLocations"],
            [10],
        )
        with tempfile.TemporaryDirectory() as directory:
            saved = Path(directory) / "dm32uv-zones.img"
            radio.save_mmap(str(saved))
            reopened = self.directory.get_radio_by_image(str(saved))
            reopened_models = bridge.mapping_payload(reopened)

        self.assertEqual(
            reopened_models[0]["mappings"][0]["channelLocations"][-1],
            10,
        )
        self.assertIn(
            10,
            reopened_models[0]["mappings"][1]["channelLocations"],
        )
        self.assertEqual(
            reopened_models[0]["mappings"][2]["name"],
            "Local",
        )

    def test_mapping_change_rejects_an_empty_channel(self):
        radio = self.directory.get_radio_by_image(str(DM32UV_IMAGE))
        models = bridge.mapping_payload(radio)
        models[0]["mappings"][2]["name"] = "Local"
        models[0]["mappings"][2]["channelLocations"] = [999]
        active_locations = {
            location
            for mapping in models[0]["mappings"]
            for location in mapping["channelLocations"]
        }

        with self.assertRaisesRegex(
            RuntimeError,
            "Channel 999 is empty",
        ):
            bridge.apply_mapping_payload(
                radio,
                [models[0]],
                active_locations,
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

    def test_ar8200_timeout_checks_rs232_lead_and_remote_id(self):
        message = bridge.bridge_error_message(
            self.errors.RadioNoResponse(),
            command="download",
            model="AOR_AR8200",
            port="COM4",
        )

        self.assertIn("CC8200-compatible", message)
        self.assertIn("RMT-ID to 00", message)
        self.assertIn("REMOTE BPS", message)
        self.assertIn("echoed back", message)
        self.assertIn("using COM4", message)
        self.assertNotIn("using COM6", message)

    def test_rt1_timeout_distinguishes_rt21(self):
        message = bridge.bridge_error_message(
            self.errors.RadioNoResponse(),
            command="download",
            model="Retevis_RT1",
        )

        self.assertIn("select Retevis RT21", message)
        self.assertIn("2400 baud", message)
        self.assertIn("9600 baud", message)
        self.assertIn("PRMZUNE", message)

    def test_f8hp_pro_timeout_checks_exact_model_and_firmware(self):
        message = bridge.bridge_error_message(
            self.errors.RadioNoResponse(),
            command="download",
            model="Baofeng_BF-F8HP-PRO",
        )

        self.assertIn("includes PRO", message)
        self.assertIn("separate Baofeng BF-F8HP entry", message)
        self.assertIn("firmware v0.52", message)

    def test_uv5r_mini_timeout_checks_for_the_usb_com_port(self):
        message = bridge.bridge_error_message(
            self.errors.RadioNoResponse(),
            command="download",
            model="Baofeng_UV-5R_Mini",
        )

        self.assertIn("not a built-in COM1 port", message)
        self.assertIn("newly appears", message)
        self.assertIn("Bluetooth serial port", message)

    def test_setting_error_names_the_rejected_setting_and_value(self):
        from chirp.settings import RadioSetting, RadioSettingValueList

        setting = RadioSetting(
            "squelch",
            "Squelch",
            RadioSettingValueList(["Off", "1", "2"], current_index=0),
        )

        with self.assertRaisesRegex(
            RuntimeError,
            r"Radio setting 'Squelch' rejected value '3'",
        ):
            bridge.apply_setting_changes(
                [setting],
                [{"id": [0], "value": "3"}],
            )

    def test_numeric_choice_restores_the_driver_option_type(self):
        from chirp.settings import RadioSetting, RadioSettingValueList

        setting = RadioSetting(
            "squelch",
            "Squelch",
            RadioSettingValueList(list(range(0, 9)), current_index=3),
        )

        bridge.apply_setting_changes(
            [setting],
            [{"id": [0], "value": "3"}],
        )

        self.assertEqual(setting.value.get_value(), 3)

    def test_trace_records_readline_data(self):
        trace = bridge.RadioCommunicationTrace()
        serial = bridge.TracedSerial(FakeLineSerial(b"\xff"), trace)

        serial.write(b"VR\r")
        self.assertEqual(serial.readline(), b"\xff")

        rendered = trace.format()
        self.assertIn("VR | incomplete response (1 bytes)", rendered)

    def test_bridge_error_does_not_require_a_model_argument(self):
        message = bridge.bridge_error_message(
            RuntimeError("catalog failed"),
            command="list-models",
            model=None,
        )

        self.assertEqual(message, "catalog failed")

    def test_serial_access_denied_explains_port_ownership(self):
        with mock.patch.object(bridge.sys, "platform", "win32"):
            message = bridge.bridge_error_message(
                RuntimeError(
                    "could not open port 'COM100': "
                    "PermissionError(13, 'Access is denied.', None, 5)"
                ),
                command="read-settings",
                model="Baofeng_DM-32UV",
            )

        self.assertIn("COM100", message)
        self.assertIn("another program or driver", message)
        self.assertIn("Close Baofeng CPS", message)
        self.assertIn("old saved port", message)

    def test_linux_serial_access_denied_names_linux(self):
        with mock.patch.object(bridge.sys, "platform", "linux"):
            message = bridge.bridge_error_message(
                RuntimeError(
                    "could not open port '/dev/ttyUSB0': "
                    "PermissionError(13, 'Permission denied', None, 13)"
                ),
                command="download",
                model="Quansheng_UV-K5",
            )

        self.assertIn("Linux could not open /dev/ttyUSB0", message)
        self.assertIn("dialout", message)
        self.assertNotIn("Windows", message)

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

    def test_driver_specific_live_modes_are_accepted_by_memory_map(self):
        from chirp import chirp_common

        for mode in ("DR", "R-CW"):
            memory = chirp_common.Memory()
            memory.mode = mode
            self.assertEqual(memory.mode, mode)

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

    def test_repeaterbook_prefers_fm_when_analog_is_available(self):
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
            "System Fusion": "Yes",
        }, 1)

        self.assertEqual(channel["mode"], "FM")

    def test_driver_frequency_bands_are_exported_in_mhz(self):
        image = SOURCE / "tests/images/Baofeng_5RM.img"
        radio = bridge.radio_from_image(
            self.directory,
            "Baofeng_5RM",
            str(image),
        )

        bands = bridge.features_json(radio)["validBands"]

        self.assertIn(
            {"startMhz": 400.0, "endMhz": 520.0},
            bands,
        )

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

    def test_legacy_wouxun_uses_extended_serial_timeout(self):
        self.assertEqual(
            bridge.serial_read_timeout(SimpleNamespace(MODEL="KG-UVD1P")),
            1.0,
        )
        self.assertEqual(
            bridge.serial_read_timeout(SimpleNamespace(MODEL="FT-60")),
            0.25,
        )

    def test_legacy_wouxun_timeout_is_applied_to_serial_port(self):
        radio_class = SimpleNamespace(
            MODEL="KG-UVD1P",
            BAUD_RATE=9600,
            HARDWARE_FLOW=False,
            WANTS_RTS=True,
            WANTS_DTR=True,
        )
        with mock.patch("serial.Serial") as serial_constructor:
            bridge.open_serial(radio_class, "COM6")

        serial_constructor.assert_called_once_with(
            baudrate=9600,
            rtscts=False,
            xonxoff=False,
            timeout=1.0,
        )

    def test_wouxun_block_failure_suggests_power_cycle(self):
        message = bridge.bridge_error_message(
            Exception(
                "Failed to communicate with radio: "
                "Failed to read full block (67!=68)"
            ),
            command="download",
            model="Wouxun_KG-UVD1P",
        )

        self.assertIn("KG-UV2D", message)
        self.assertIn("power the radio off and on", message)
        self.assertIn("Wouxun CPS", message)

    def test_ic2730_settings_timeout_suggests_leaving_clone_mode(self):
        message = bridge.bridge_error_message(
            Exception(
                "Data stream stopped before end-of-clone received"
            ),
            command="read-settings",
            model="Icom_IC-2730A",
        )

        self.assertIn("turn the radio off and back on", message)
        self.assertIn("Load from stored image", message)

    def test_empty_live_radio_snapshot_can_be_filled_for_upload(self):
        from chirp import chirp_common

        written = []
        erased = []
        stored = {}

        def blank_memory(number):
            memory = chirp_common.Memory()
            memory.number = number
            memory.empty = True
            return memory

        def set_live_memory(memory):
            written.append(memory.number)
            stored[memory.number] = memory.dupe()

        def erase_live_memory(number):
            erased.append(number)
            stored[number] = blank_memory(number)

        features = SimpleNamespace(memory_bounds=(1, 2))
        live_radio = SimpleNamespace(
            VENDOR="Icom",
            MODEL="IC-7100",
            VARIANT="",
            BAUD_RATE=19200,
            HARDWARE_FLOW=False,
            pipe=SimpleNamespace(),
            status_fn=None,
            get_features=lambda: features,
            get_memory=lambda number: stored.get(number, blank_memory(number)),
            set_memory=set_live_memory,
            erase_memory=erase_live_memory,
        )
        adapter = bridge.headless_live_adapter(live_radio)
        adapter.status_fn = None

        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".img",
            encoding="utf-8",
        ) as handle:
            handle.write(",".join(chirp_common.Memory.CSV_FORMAT) + "\n")
            handle.flush()
            adapter.load_mmap(handle.name)

        memory = chirp_common.Memory()
        memory.number = 1
        memory.freq = 146520000
        adapter.set_memory(memory)
        adapter.sync_out()

        self.assertEqual(written, [1])
        self.assertEqual(erased, [2])

    def test_live_write_verification_rejects_silent_changes(self):
        from chirp import chirp_common

        expected = chirp_common.Memory()
        expected.number = 1
        expected.freq = 146520000
        expected.duplex = ""
        expected.offset = 0
        expected.mode = "FM"
        expected.name = "CALL"

        stored = {}
        live_radio = SimpleNamespace(
            get_memory=lambda number: stored.get(
                number,
                SimpleNamespace(empty=True),
            )
        )

        with self.assertRaisesRegex(
            Exception,
            "did not retain the changes: channel 1",
        ):
            bridge.verify_live_write(live_radio, [expected], [])

        stored[1] = expected.dupe()
        bridge.verify_live_write(live_radio, [expected], [])

    def test_repeaterbook_country_resources_use_supported_region_rules(self):
        self.assertEqual(
            bridge.repeaterbook_resource_name(
                "amateur",
                "Canada",
                "Ontario",
            ),
            "rb-canada-ontario.json",
        )
        self.assertEqual(
            bridge.repeaterbook_resource_name(
                "gmrs",
                "Germany",
                "Bavaria",
            ),
            "rb-germany-all.json",
        )

    def test_non_us_repeaterbook_search_uses_amateur_service(self):
        calls = []

        def fetch(service, country, state):
            calls.append((service, country, state))
            return {"results": []}

        with mock.patch.object(
            bridge,
            "fetch_repeaterbook_data",
            side_effect=fetch,
        ):
            bridge.search_repeaterbook(
                "Canada",
                "Ontario",
                service="all",
            )

        self.assertEqual(calls, [("amateur", "Canada", "Ontario")])

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

    def test_custom_gmrs_v2_channel_is_written_as_receive_only(self):
        radio = bridge.radio_from_image(
            self.directory,
            "BTECH_GMRS-V2",
            str(GMRS_V2_IMAGE),
        )
        memory = radio.get_memory(31)
        item = bridge.memory_json(memory)
        item.update({
            "location": 31,
            "name": "CUSTOM",
            "frequency": 155.0,
            "duplex": "",
            "offset": 0,
        })

        locked_fields = bridge.apply_json(radio, memory, item)
        errors, warnings, fields, notes = bridge.normalize_upload_memory(
            radio,
            memory,
        )

        self.assertEqual(locked_fields, [])
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])
        self.assertEqual(fields, ["duplex", "offset"])
        self.assertIn("TX off", notes[0])
        self.assertEqual(memory.duplex, "off")
        self.assertEqual(memory.offset, 0)

        bridge.set_memory_with_extras(radio, memory)
        stored = radio.get_memory(31)
        self.assertEqual(stored.freq, 155000000)
        self.assertEqual(stored.duplex, "off")
        self.assertEqual(stored.offset, 0)

    def test_standard_gmrs_v2_simplex_channel_is_unchanged(self):
        radio = bridge.radio_from_image(
            self.directory,
            "BTECH_GMRS-V2",
            str(GMRS_V2_IMAGE),
        )
        memory = radio.get_memory(15)

        errors, warnings, fields, notes = bridge.normalize_upload_memory(
            radio,
            memory,
        )

        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])
        self.assertEqual(fields, [])
        self.assertEqual(notes, [])
        self.assertEqual(memory.duplex, "")
        self.assertEqual(memory.offset, 0)

    def test_gmrs_v2_normalization_does_not_hide_fatal_errors(self):
        radio = bridge.radio_from_image(
            self.directory,
            "BTECH_GMRS-V2",
            str(GMRS_V2_IMAGE),
        )
        memory = radio.get_memory(31)
        item = bridge.memory_json(memory)
        item.update({
            "location": 31,
            "name": "CUSTOM",
            "frequency": 155.0,
            "duplex": "",
            "offset": 0,
            "mode": "AM",
        })

        bridge.apply_json(radio, memory, item)
        errors, warnings, fields, notes = bridge.normalize_upload_memory(
            radio,
            memory,
        )

        self.assertTrue(errors)
        self.assertEqual(warnings, [])
        self.assertEqual(fields, ["duplex", "offset"])
        self.assertTrue(notes)
        self.assertIn("Mode AM not supported", str(errors[0]))


if __name__ == "__main__":
    unittest.main()
