"""Offline nicFW950 protocol, image preservation and bridge integration tests."""

import importlib.util
import io
import json
import struct
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
PIN = dict(
    line.split()
    for line in (ROOT / "scripts/chirp-source.pin").read_text().splitlines()
    if line and not line.startswith("#")
)
SOURCE = ROOT / "build_support" / ("chirp-" + PIN["commit"])
if not SOURCE.is_dir():
    SOURCE = ROOT / "build_support/chirp-20261023"
VENDOR = ROOT / "assets/python/pyserial-3.5-py2.py3-none-any.whl"
MODEL = "Radtel_RT-950_nicFW950"


def _load_bridge():
    spec = importlib.util.spec_from_file_location(
        "newchirp_chirp_bridge_nicfw950", ROOT / "scripts/chirp_bridge.py"
    )
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


def _image():
    # Deliberately nonzero reserved bytes, padding, calibration and power bands.
    image = bytearray((index * 37 + 19) & 0xFF for index in range(0xFB00))
    image[248 : 248 + 62] = struct.pack(
        "<IIIHHh8B6B30s",
        14_652_000,
        14_592_000,
        0x1A030201,
        1000,
        0xC04C,
        -123,
        3,
        2,
        1,
        4,
        0,
        0x85,
        0x50,
        0xC9,
        7,
        12,
        1,
        0xA5,
        0x5A,
        0x54,
        b"LOCAL\x00preserved-padding",
    )
    # The exact magic offset is 24, with the unused bytes 30..31 preserved.
    image[248 + 24 : 248 + 26] = b"\x50\xc9"
    # Remaining channels are empty according to magic, regardless of padding.
    for index in range(1, 999):
        offset = 248 + index * 62
        image[offset + 24 : offset + 26] = b"\x00\x00"
    driver = next(
        module
        for name, module in sys.modules.copy().items()
        if name.endswith(".newchirp_nicfw950")
    )
    for _category, kind, _label, offset, *args in driver.SETTING_DEFINITIONS:
        if kind == "number":
            low, high, places, default, width = args
            encoded = int(round(default * 10**places)).to_bytes(
                width, "little", signed=low < 0
            )
        elif kind == "options":
            encoded = args[0].to_bytes(2, "little")
        elif kind == "bool":
            encoded = int(args[0]).to_bytes(2, "little")
        else:
            default, width = args
            encoded = default.encode("ascii").ljust(width, b"\x00")
        image[0xF400 + offset : 0xF400 + offset + len(encoded)] = encoded
    return image


def _setting(settings, name):
    from chirp.settings import RadioSetting

    for element in settings:
        if isinstance(element, RadioSetting):
            if element.get_name() == name:
                return element
        else:
            result = _setting(element, name)
            if result is not None:
                return result
    return None


class FakeNicFW950Serial:
    """Fragmented protocol peer, with flash writes staged until command 0x48."""

    def __init__(self, memory):
        self.memory = bytearray(memory)
        self.pending = {}
        self.responses = bytearray()
        self.writes = []
        self.baudrate = 38400
        self.timeout = 1.5
        self.corrupt_read = None
        self.reject_command = None
        self.negotiate_timeouts = 0
        self.closed = False

    def reset_input_buffer(self):
        self.responses.clear()

    def flush(self):
        pass

    def close(self):
        self.closed = True

    def write(self, packet):
        packet = bytes(packet)
        self.writes.append(packet)
        command = packet[1]
        if command == self.reject_command:
            self.responses.extend(b"\xaa\xff")
            return len(packet)
        if command == 0x70:
            assert packet == b"\xaa\x70\x00\x08\x07\x00\x55"
            assert self.baudrate == 38400
            if self.negotiate_timeouts:
                self.negotiate_timeouts -= 1
                return len(packet)
            self.responses.extend(b"\xaa\x70\xaa\x70")
        elif command == 0x30:
            assert len(packet) == 7 and packet[-1] == 0x55
            address = struct.unpack_from("<I", packet, 2)[0]
            offset = address - 0x50200
            payload = packet[2:6] + self.memory[offset : offset + 128]
            response = bytearray(
                b"\xaa\x30" + payload + bytes((sum(payload) & 255,))
            )
            if self.corrupt_read == "header":
                response[1] = 0x31
            elif self.corrupt_read == "address":
                response[2] ^= 1
            elif self.corrupt_read == "checksum":
                response[-1] ^= 1
            self.responses.extend(response)
        elif command == 0x40:
            assert len(packet) == 136 and packet[-1] == 0x55
            assert sum(packet[2:134]) & 255 == packet[134]
            offset = struct.unpack_from("<I", packet, 2)[0] - 0x50200
            self.pending[offset] = packet[6:134]
            self.responses.extend(b"\xaa\x40")
        elif command == 0x48:
            assert packet == b"\xaa\x48\x55"
            for offset, block in self.pending.items():
                self.memory[offset : offset + 128] = block
            self.pending.clear()
            self.responses.extend(b"\xaa\x48")
        elif command == 0x50:
            assert packet == b"\xaa\x50"  # No terminator or expected ACK.
        else:
            raise AssertionError("Unexpected command %r" % packet)
        return len(packet)

    def read(self, count):
        result = bytes(self.responses[: min(count, 7)])
        del self.responses[: len(result)]
        return result


class NicFW950DriverTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bridge = _load_bridge()
        cls.directory = cls.bridge.load_chirp(
            str(SOURCE), str(VENDOR), str(ROOT / "drivers")
        )
        cls.radio_class = cls.directory.get_radio(MODEL)
        cls.driver = sys.modules[cls.radio_class.__module__]

    def radio(self, image=None):
        from chirp import memmap

        return self.radio_class(
            memmap.MemoryMapBytes(bytes(_image() if image is None else image))
        )

    def test_catalog_keeps_stock_and_nicfw_models_separate(self):
        for name in (
            MODEL,
            "Radtel_RT-950_Pro_nicFW950",
            "Bajeton_BJ-9000_nicFW950",
        ):
            self.assertEqual(
                self.directory.get_radio(name).__module__,
                self.radio_class.__module__,
            )
        self.assertNotEqual(
            self.directory.get_radio("Radtel_RT-950"), self.radio_class
        )
        features = self.radio().get_features()
        self.assertEqual(features.memory_bounds, (1, 999))
        self.assertEqual(features.valid_name_length, 30)
        self.assertTrue(features.has_settings)
        self.assertTrue(features.has_comment)
        self.assertIn("nicFW950", self.radio_class.get_prompts().experimental)

    def test_decode_layout_groups_and_octal_dcs(self):
        memory = self.radio().get_memory(1)
        self.assertEqual(
            (memory.freq, memory.duplex, memory.offset),
            (146_520_000, "-", 600_000),
        )
        self.assertEqual(memory.name, "LOCAL")
        self.assertEqual(memory.comment, "ABCZ")
        self.assertEqual(memory.cross_mode, "DTCS->Tone")
        self.assertEqual(memory.dtcs, 114)
        self.assertEqual(memory.dtcs_polarity[0], "R")
        self.assertEqual(memory.ctone, 100.0)
        self.assertEqual(str(memory.power), "Medium")
        self.assertEqual(
            str(_setting(memory.extra, "modulation").value), "Automatic"
        )
        self.assertTrue(self.radio().get_memory(999).empty)

    def test_unchanged_channel_is_byte_identical(self):
        radio = self.radio()
        before = radio.get_mmap().get_packed()
        radio.set_memory(radio.get_memory(1))
        self.assertEqual(radio.get_mmap().get_packed(), before)

    def test_standard_mode_edit_is_not_overridden_by_unchanged_extras(self):
        radio = self.radio()
        memory = radio.get_memory(1)
        memory.mode = "NFM"
        radio.set_memory(memory)
        self.assertEqual(radio.get_memory(1).mode, "NFM")
        self.assertEqual(int(radio._memobj.channels[0].modulation), 0)
        self.assertEqual(int(radio._memobj.channels[0].bandwidth), 1)

    def test_explicit_dsb_and_bandwidth_extra_are_preserved(self):
        radio = self.radio()
        memory = radio.get_memory(1)
        _setting(memory.extra, "modulation").value = "DSB"
        _setting(memory.extra, "bandwidth").value = "Narrow"
        radio.set_memory(memory)
        self.assertEqual(int(radio._memobj.channels[0].modulation), 2)
        self.assertEqual(radio.get_memory(1).mode, "AM")
        before = radio.get_mmap().get_packed()
        radio.set_memory(radio.get_memory(1))
        self.assertEqual(radio.get_mmap().get_packed(), before)

    def test_create_last_channel_and_delete_only_magic(self):
        from chirp import chirp_common

        radio = self.radio()
        memory = chirp_common.Memory(999)
        memory.freq = 446_006_250
        memory.name = "LAST"
        memory.duplex = "off"
        memory.comment = "bz"
        memory.tmode = "DTCS"
        memory.dtcs = 114
        memory.dtcs_polarity = "RN"
        radio.set_memory(memory)
        result = radio.get_memory(999)
        self.assertEqual(
            (result.name, result.comment, result.duplex), ("LAST", "BZ", "off")
        )
        self.assertEqual(result.dtcs, 114)
        offset = 248 + 998 * 62
        before = bytearray(radio.get_mmap().get_packed())
        result.empty = True
        radio.set_memory(result)
        before[offset + 24 : offset + 26] = b"\x00\x00"
        self.assertEqual(radio.get_mmap().get_packed(), before)

    def test_invalid_edit_does_not_partially_modify_the_image(self):
        from chirp import errors

        for field, value in (
            ("freq", 146_520_001),
            ("comment", "ABCDE"),
            ("comment", "A1"),
            ("name", "x" * 31),
            ("name", "ñ"),
        ):
            with self.subTest(field=field, value=value):
                radio = self.radio()
                before = radio.get_mmap().get_packed()
                memory = radio.get_memory(1)
                setattr(memory, field, value)
                with self.assertRaises((errors.RadioError, UnicodeError)):
                    radio.set_memory(memory)
                self.assertEqual(radio.get_mmap().get_packed(), before)
                self.assertTrue(radio.validate_memory(memory))

    def test_settings_defaults_do_not_overwrite_unrelated_bytes(self):
        radio = self.radio()
        before = radio.get_mmap().get_packed()
        radio.set_settings(radio.get_settings())
        self.assertEqual(radio.get_mmap().get_packed(), before)

    def test_invalid_settings_display_defaults_without_rewriting_them(self):
        image = _image()
        image[0xF404:0xF406] = b"\xff\xff"  # Squelch outside 0..9.
        image[0xF428:0xF42A] = b"\xff\xff"  # Invalid tail-elimination option.
        image[0xF400 + 441] = 0x80  # Non-ASCII callsign.
        radio = self.radio(image)
        with self.assertLogs(self.driver.LOG, level="WARNING"):
            settings = radio.get_settings()
        radio.set_settings(settings)
        self.assertEqual(radio.get_mmap().get_packed(), bytes(image))

    def test_settings_numeric_string_boolean_and_group_name_edits(self):
        radio = self.radio()
        before = bytearray(radio.get_mmap().get_packed())
        settings = radio.get_settings()
        for index, spec in enumerate(self.driver.SETTING_DEFINITIONS):
            value = {
                "Squelch Level": 5,
                "Squelch Tail (s)": 0.7,
                "Time Zone": -3,
                "Callsign": "LU1ABC",
                "GPS Enabled": False,
            }.get(spec[2])
            if value is not None:
                _setting(settings, "setting_%d" % index).value = value
                if spec[1] == "number":
                    stored = int(round(value * 10 ** spec[6]))
                    encoded = stored.to_bytes(
                        spec[8], "little", signed=spec[4] < 0
                    )
                elif spec[1] == "bool":
                    encoded = int(value).to_bytes(2, "little")
                else:
                    encoded = value.encode("ascii")
                before[0xF400 + spec[3] : 0xF400 + spec[3] + len(encoded)] = (
                    encoded
                )
        _setting(settings, "group_name_1").value = "Local"
        before[0xF900 + 13 : 0xF900 + 26] = b"\xaaLocal       "
        radio.set_settings(settings)
        self.assertEqual(radio.get_mmap().get_packed(), before)
        self.assertEqual(
            str(_setting(radio.get_settings(), "group_name_1").value), "Local"
        )
        self.assertEqual(radio._original, bytes(_image()))

    def test_download_negotiates_speed_and_validates_every_block(self):
        serial = FakeNicFW950Serial(_image())
        radio = self.radio_class(serial)
        radio.status_fn = lambda _status: None
        radio.sync_in()
        reads = [packet for packet in serial.writes if packet[1] == 0x30]
        self.assertEqual(len(reads), 502)
        self.assertEqual(struct.unpack_from("<I", reads[0], 2)[0], 0x50200)
        self.assertEqual(struct.unpack_from("<I", reads[-1], 2)[0], 0x5FC80)
        self.assertEqual(radio.get_mmap().get_packed(), bytes(_image()))
        self.assertEqual(serial.baudrate, 38400)

    def test_download_rejects_header_address_checksum_and_timeout(self):
        from chirp import errors

        for corruption in ("header", "address", "checksum", "timeout"):
            with self.subTest(corruption=corruption):
                serial = FakeNicFW950Serial(_image())
                serial.corrupt_read = corruption
                radio = self.radio_class(serial)
                if corruption == "timeout":
                    serial.read = lambda _count: b""
                with (
                    mock.patch.object(self.driver.time, "sleep"),
                    self.assertRaises(errors.RadioError),
                ):
                    radio.sync_in()
                self.assertEqual(serial.baudrate, 38400)

    def test_baud_handshake_retries_once_after_a_quiet_idle_interval(self):
        serial = FakeNicFW950Serial(_image())
        serial.negotiate_timeouts = 1
        with mock.patch.object(self.driver.time, "sleep") as sleep:
            self.driver._negotiate(serial)
        sleep.assert_called_once_with(3.0)
        self.assertEqual(len(serial.writes), 2)
        self.assertTrue(all(packet[1] == 0x70 for packet in serial.writes))
        self.assertEqual(serial.baudrate, 460800)

    def test_baud_handshake_rejects_bad_ack_without_retrying(self):
        from chirp import errors

        serial = FakeNicFW950Serial(_image())
        serial.reject_command = 0x70
        with (
            mock.patch.object(self.driver.time, "sleep") as sleep,
            self.assertRaisesRegex(errors.RadioError, "Unexpected ACK"),
        ):
            self.driver._negotiate(serial)
        sleep.assert_not_called()
        self.assertEqual(len(serial.writes), 1)

    def test_saved_image_upload_in_fresh_process_writes_only_changed_blocks(
        self,
    ):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "nicfw950.img"
            self.radio().save_mmap(str(path))
            radio = self.directory.get_radio_by_image(str(path))
            radio.load_mmap(str(path))  # The bridge loads the image again.
            memory = radio.get_memory(1)
            memory.name = "EDITED"
            radio.set_memory(memory)
            target = radio.get_mmap().get_packed()
            serial = FakeNicFW950Serial(_image())
            radio.pipe = serial
            radio.status_fn = lambda _status: None
            radio.sync_out()
            writes = [p for p in serial.writes if p[1] == 0x40]
            self.assertEqual(len(writes), 1)
            self.assertEqual(
                struct.unpack_from("<I", writes[0], 2)[0], 0x50300
            )
            self.assertEqual(serial.memory, target)
            self.assertEqual(
                serial.writes[-2:], [b"\xaa\x48\x55", b"\xaa\x50"]
            )
            self.assertEqual(serial.baudrate, 38400)
            self.assertEqual(radio._original, target)
            serial.writes.clear()
            radio.sync_out()
            self.assertEqual(serial.writes, [])

    def test_upload_rejects_stale_adjacent_bytes_before_any_write(self):
        from chirp import errors

        radio = self.radio()
        memory = radio.get_memory(1)
        memory.name = "EDITED"
        radio.set_memory(memory)
        serial = FakeNicFW950Serial(_image())
        serial.memory[0x170] ^= 1  # Same block, outside the edited name.
        radio.pipe = serial
        with self.assertRaisesRegex(errors.RadioError, "fresh image"):
            radio.sync_out()
        self.assertFalse(
            [p for p in serial.writes if p[1] in (0x40, 0x48, 0x50)]
        )
        self.assertEqual(serial.baudrate, 38400)

    def test_upload_rejects_protected_region_edits_without_serial_traffic(
        self,
    ):
        from chirp import errors

        for offset in (0, 247, 0xF300, 0xF800, 0xF900, 0xFAFF):
            with self.subTest(offset=offset):
                radio = self.radio()
                radio._mmap[offset] = bytes((radio._original[offset] ^ 1,))
                radio.pipe = FakeNicFW950Serial(_image())
                with self.assertRaisesRegex(errors.RadioError, "protected"):
                    radio.sync_out()
                self.assertEqual(radio.pipe.writes, [])

    def test_upload_failure_does_not_commit_reboot_or_advance_baseline(self):
        from chirp import errors

        for rejected in (0x40, 0x48):
            with self.subTest(rejected=rejected):
                radio = self.radio()
                before = radio._original
                memory = radio.get_memory(1)
                memory.name = "EDITED"
                radio.set_memory(memory)
                serial = FakeNicFW950Serial(_image())
                serial.reject_command = rejected
                radio.pipe = serial
                radio.status_fn = lambda _status: None
                with self.assertRaises(errors.RadioError):
                    radio.sync_out()
                self.assertNotIn(b"\xaa\x50", serial.writes)
                self.assertEqual(radio._original, before)
                self.assertEqual(serial.baudrate, 38400)
                self.assertEqual(serial.timeout, 2.0)

    def test_invalid_image_and_upload_without_image_are_rejected(self):
        from chirp import errors

        with self.assertRaisesRegex(errors.RadioError, "image size"):
            self.radio(b"\xff" * 100)
        serial = FakeNicFW950Serial(_image())
        with self.assertRaisesRegex(errors.RadioError, "Download"):
            self.radio_class(serial).sync_out()
        self.assertEqual(serial.writes, [])

    def test_bridge_json_edit_and_settings_write_survive_image_reload(self):
        radio = self.radio()
        item = self.bridge.memory_json(radio.get_memory(1))
        item.update(name="BRIDGE", mode="NFM", comment="AZ")
        with tempfile.TemporaryDirectory() as temp:
            image = Path(temp) / "radio.img"
            channels = Path(temp) / "channels.json"
            radio.save_mmap(str(image))
            channels.write_text(json.dumps([item]), encoding="utf-8")
            serial = FakeNicFW950Serial(_image())
            arguments = [
                "chirp_bridge.py",
                "--source",
                str(SOURCE),
                "--vendor",
                str(VENDOR),
                "--newchirp-driver-dir",
                str(ROOT / "drivers"),
                "upload",
                "--model",
                MODEL,
                "--port",
                "COM_TEST",
                "--image",
                str(image),
                "--channels",
                str(channels),
            ]
            with (
                mock.patch.object(sys, "argv", arguments),
                mock.patch.object(
                    self.bridge, "open_serial", return_value=serial
                ),
                redirect_stdout(io.StringIO()) as output,
            ):
                self.bridge.main()
            self.assertTrue(json.loads(output.getvalue())["ok"])
            self.assertTrue(serial.closed)
            reopened = self.directory.get_radio_by_image(str(image))
            memory = reopened.get_memory(1)
            self.assertEqual(
                (memory.name, memory.mode, memory.comment),
                ("BRIDGE", "NFM", "AZ"),
            )
            self.assertEqual(
                reopened.get_mmap().get_packed(), bytes(serial.memory)
            )
            settings = self.bridge.settings_payload(reopened)
            changes = [
                {"id": node["id"], "value": value}
                for group in settings["settings"]
                for node in group["children"]
                for name, value in (
                    ("group_name_26", "Last group"),
                    ("setting_0", 5),
                )
                if node["name"] == name
            ]
            self.assertEqual(len(changes), 2)
            payload = Path(temp) / "settings.json"
            payload.write_text(
                json.dumps({"changes": changes}), encoding="utf-8"
            )
            before = bytes(serial.memory)
            serial.closed = False
            serial.writes.clear()
            arguments = arguments[: arguments.index("upload")] + [
                "write-settings",
                "--model",
                MODEL,
                "--port",
                "COM_TEST",
                "--image",
                str(image),
                "--settings",
                str(payload),
            ]
            with (
                mock.patch.object(sys, "argv", arguments),
                mock.patch.object(
                    self.bridge, "open_serial", return_value=serial
                ),
                redirect_stdout(io.StringIO()) as output,
            ):
                self.bridge.main()
            self.assertEqual(json.loads(output.getvalue())["changed"], 2)
            reopened = self.directory.get_radio_by_image(str(image))
            self.assertEqual(
                reopened.get_mmap().get_packed(), bytes(serial.memory)
            )
            self.assertEqual(bytes(serial.memory[:0xF400]), before[:0xF400])
            self.assertEqual(
                bytes(serial.memory[0xF800:0xF900]), before[0xF800:0xF900]
            )
            self.assertEqual(serial.memory[0xFA52:0xFA5F], b"\xaaLast group  ")


if __name__ == "__main__":
    unittest.main()
