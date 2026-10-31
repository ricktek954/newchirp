"""Offline tests for the experimental Icom IC-41S driver."""

import importlib.util
from pathlib import Path
import struct
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "build_support/chirp-20261023"
PYTHON_VENDOR = ROOT / "assets/python/pyserial-3.5-py2.py3-none-any.whl"
MODEL_ID = b"\x29\x28\x00\x00"
SETTINGS_SIGNATURE = bytes.fromhex(
    "500f0102464543100000000000000000"
)


def _load_bridge():
    spec = importlib.util.spec_from_file_location(
        "newchirp_chirp_bridge_icom_ic41s",
        ROOT / "scripts/chirp_bridge.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load chirp_bridge.py")
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


def _record(rx_hz, tx_hz, name, flags=0x58, tones=(0x8000, 0x8000)):
    return (
        struct.pack(">IIHH", rx_hz, tx_hz, tones[0], tones[1])
        + name.encode("ascii").ljust(8, b" ")
        + struct.pack("<H", flags)
    )


def _image(records, include_zones=True):
    image = bytearray(0x7D80)
    start = 0x240 if include_zones else 0x178
    cursor = start
    for record in records:
        image[cursor:cursor + len(record)] = record
        cursor += len(record)
    image[cursor:cursor + len(SETTINGS_SIGNATURE)] = SETTINGS_SIGNATURE
    return bytes(image)


def _frame(source, destination, command, payload=b""):
    return (
        b"\xfe\xfe"
        + bytes((source, destination, command))
        + payload
        + b"\xfd"
    )


def _model_payload():
    data = bytearray(49)
    data[:4] = MODEL_ID
    data[5] = 1
    data[6:22] = b"IC-41S TEST     "
    data[35:49] = b"00000000000000"
    return bytes(data)


def _legacy_data_payload(address, data):
    prefix = struct.pack(">HB", address, len(data))
    checksum = (-sum(prefix + data)) & 0xFF
    raw = prefix + data + bytes((checksum,))
    return raw.hex().upper().encode("ascii")


class FakeLegacyIcomSerial:
    def __init__(self, image):
        self.image = bytes(image)
        self.timeout = 1
        self.baudrate = 9600
        self._rx = bytearray()
        self.writes = []

    def write(self, data):
        data = bytes(data)
        self.writes.append(data)
        if len(data) < 5 or data[:2] != b"\xfe\xfe":
            return len(data)
        command = data[4]
        if command == 0xE0:
            self._rx.extend(_frame(0xEF, 0xEE, 0xE1, _model_payload()))
        elif command == 0xE2:
            for address in range(0, len(self.image), 16):
                chunk = self.image[address:address + 16]
                self._rx.extend(
                    _frame(
                        0xEF,
                        0xEE,
                        0xE4,
                        _legacy_data_payload(address, chunk),
                    )
                )
            self._rx.extend(_frame(0xEF, 0xEE, 0xE5, b"Icom Inc."))
        elif command == 0xE5:
            self._rx.extend(_frame(0xEF, 0xEE, 0xE6, b"\x00"))
        return len(data)

    def read(self, size=1):
        data = bytes(self._rx[:size])
        del self._rx[:size]
        return data

    def flush(self):
        pass

    def reset_input_buffer(self):
        self._rx.clear()

    def close(self):
        pass


class IcomIC41SDriverTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = _load_bridge().load_chirp(
            str(SOURCE),
            str(PYTHON_VENDOR),
            str(ROOT / "drivers"),
        )
        cls.radio_class = cls.directory.get_radio("Icom_IC-41S")

    def _radio(self, records, include_zones=True):
        from chirp import memmap

        radio = self.radio_class(None)
        radio._mmap = memmap.MemoryMapBytes(
            _image(records, include_zones=include_zones)
        )
        radio.process_mmap()
        return radio

    def test_driver_is_registered_as_experimental_read_write(self):
        self.assertEqual(self.radio_class.__name__, "IcomIC41SRadio")
        self.assertEqual(self.radio_class.get_model(), MODEL_ID)
        self.assertEqual(self.radio_class._ranges, [(0, 0x7D80, 16)])
        self.assertFalse(self.radio_class._can_hispeed)
        self.assertFalse(self.radio_class._raw_frames)
        prompts = self.radio_class.get_prompts()
        self.assertIn("experimental", prompts.experimental.lower())
        self.assertIn("Reading and writing are enabled", prompts.experimental)
        self.assertIn("backup", prompts.pre_upload.lower())

    def test_reads_cps_channel_records_and_split_frequencies(self):
        radio = self._radio(
            [
                _record(
                    476425000,
                    477175000,
                    "CB-R01",
                    flags=0x70,
                ),
                _record(476450000, 476450000, "CALL"),
            ]
        )

        first = radio.get_memory(1)
        self.assertFalse(first.empty)
        self.assertEqual(first.freq, 476425000)
        self.assertEqual(first.duplex, "split")
        self.assertEqual(first.offset, 477175000)
        self.assertEqual(first.name, "CB-R01")

        second = radio.get_memory(2)
        self.assertEqual(second.freq, 476450000)
        self.assertEqual(second.duplex, "")
        self.assertEqual(second.offset, 0)
        self.assertEqual(second.name, "CALL")
        self.assertEqual(radio.get_features().memory_bounds, (1, 2))

    def test_reads_image_without_zone_table(self):
        radio = self._radio(
            [_record(476500000, 476500000, "DIRECT")],
            include_zones=False,
        )
        self.assertEqual(radio._channel_start, 0x178)
        self.assertEqual(radio.get_memory(1).name, "DIRECT")

    def test_set_memory_updates_only_proven_channel_fields(self):
        from chirp import chirp_common

        radio = self._radio(
            [_record(476425000, 476425000, "OLD", tones=(0x8123, 0x8456))]
        )
        memory = chirp_common.Memory()
        memory.number = 1
        memory.freq = 476450000
        memory.duplex = "split"
        memory.offset = 477200000
        memory.mode = "FM"
        memory.name = "NEW"

        radio.set_memory(memory)

        restored = radio.get_memory(1)
        self.assertEqual(restored.freq, 476450000)
        self.assertEqual(restored.duplex, "split")
        self.assertEqual(restored.offset, 477200000)
        self.assertEqual(restored.name, "NEW")

        offset = radio._channel_start
        raw = radio._mmap[offset:offset + 22]
        self.assertEqual(raw[8:10], bytes.fromhex("8123"))
        self.assertEqual(raw[10:12], bytes.fromhex("8456"))
        self.assertEqual(struct.unpack("<H", raw[20:22])[0], 0x78)

    def test_empty_channel_preserves_count_and_disables_duplex(self):
        from chirp import chirp_common

        radio = self._radio(
            [_record(476425000, 477175000, "RPTR", flags=0xF0)]
        )
        memory = chirp_common.Memory()
        memory.number = 1
        memory.empty = True

        radio.set_memory(memory)

        self.assertTrue(radio.get_memory(1).empty)
        raw = radio._mmap[radio._channel_start:radio._channel_start + 22]
        self.assertEqual(struct.unpack(">I", raw[0:4])[0], 0)
        self.assertEqual(struct.unpack("<H", raw[20:22])[0], 0x90)

    def test_rejects_setting_out_of_band_frequency(self):
        from chirp import chirp_common, errors

        radio = self._radio([_record(476425000, 476425000, "TEST")])
        memory = chirp_common.Memory()
        memory.number = 1
        memory.freq = 146520000
        memory.mode = "FM"

        with self.assertRaises(errors.RadioError):
            radio.set_memory(memory)

    def test_icf_model_header_matches(self):
        self.assertTrue(
            self.radio_class.match_model(b"29280000\r\n", "radio.icf")
        )
        self.assertTrue(
            self.radio_class.match_model(b"29280000\r\n", "radio.ics")
        )
        self.assertFalse(
            self.radio_class.match_model(b"29290000\r\n", "radio.icf")
        )

    def test_icf_round_trip_preserves_channel_count_and_edit(self):
        radio = self._radio(
            [_record(476425000, 477175000, "BEFORE", flags=0x70)]
        )
        memory = radio.get_memory(1)
        memory.name = "AFTER"
        memory.offset = 477250000
        radio.set_memory(memory)

        with tempfile.NamedTemporaryFile(suffix=".icf") as output:
            radio.save_mmap(output.name)
            restored = self.radio_class(None)
            restored.load_mmap(output.name)

        restored_memory = restored.get_memory(1)
        self.assertEqual(restored.get_features().memory_bounds, (1, 1))
        self.assertEqual(restored_memory.name, "AFTER")
        self.assertEqual(restored_memory.duplex, "split")
        self.assertEqual(restored_memory.offset, 477250000)

    def test_initial_cps_extension_round_trips_as_icom_data(self):
        radio = self._radio(
            [_record(476425000, 476425000, "INITIAL")],
            include_zones=False,
        )

        with tempfile.NamedTemporaryFile(suffix=".ics") as output:
            radio.save_mmap(output.name)
            restored = self.radio_class(None)
            restored.load_mmap(output.name)

        self.assertEqual(restored.get_features().memory_bounds, (1, 1))
        self.assertEqual(restored.get_memory(1).name, "INITIAL")

    def test_clone_download_uses_legacy_icf_frames(self):
        image = _image([_record(476425000, 477175000, "CLONE", flags=0x70)])
        serial = FakeLegacyIcomSerial(image)
        radio = self.radio_class(serial)
        radio.status_fn = None

        radio.sync_in()

        memory = radio.get_memory(1)
        self.assertEqual(memory.freq, 476425000)
        self.assertEqual(memory.offset, 477175000)
        self.assertEqual(memory.name, "CLONE")
        commands = [frame[4] for frame in serial.writes if len(frame) > 4]
        self.assertEqual(commands[:2], [0xE0, 0xE2])

    def test_clone_upload_waits_for_legacy_clone_ok(self):
        from chirp import chirp_common

        image = _image([_record(476425000, 476425000, "CLONE")])
        serial = FakeLegacyIcomSerial(image)
        radio = self.radio_class(serial)
        radio.status_fn = None

        from chirp import memmap

        radio._mmap = memmap.MemoryMapBytes(image)
        radio.process_mmap()
        memory = chirp_common.Memory()
        memory.number = 1
        memory.freq = 476450000
        memory.mode = "FM"
        memory.name = "UPLOAD"
        radio.set_memory(memory)

        radio.sync_out()
        commands = [frame[4] for frame in serial.writes if len(frame) > 4]
        self.assertIn(0xE3, commands)
        self.assertIn(0xE4, commands)
        self.assertEqual(commands[-1], 0xE5)


if __name__ == "__main__":
    unittest.main()
