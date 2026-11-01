"""Offline tests for the experimental AnyTone D578UVIII Plus driver."""

import importlib.util
from pathlib import Path
import sys
import unittest


from chirp_test_source import chirp_source


ROOT = Path(__file__).resolve().parent.parent
SOURCE = chirp_source()
PYTHON_VENDOR = ROOT / "assets/python/pyserial-3.5-py2.py3-none-any.whl"

CHANNEL_BITMAP = 0x024C1500
CHANNEL_BANKS = 0x00800000
ZONE_BITMAP = 0x024C1300
ZONE_CHANNELS = 0x01000000
ZONE_NAMES = 0x02540000


def _load_bridge():
    spec = importlib.util.spec_from_file_location(
        "newchirp_chirp_bridge_d578",
        ROOT / "scripts/chirp_bridge.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load chirp_bridge.py")
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


def _bcd(value):
    return bytes.fromhex("%08i" % value)


def _channel(
    frequency,
    offset=0,
    *,
    digital=True,
    name="CHANNEL",
    color=1,
    slot=1,
):
    record = bytearray(0x40)
    record[0:4] = _bcd(frequency // 10)
    record[4:8] = _bcd(offset // 10)
    record[8] = (
        (1 if offset > 0 else 2 if offset < 0 else 0) << 6
        | (1 if digital else 0)
    )
    record[0x14:0x18] = (3).to_bytes(4, "little")
    record[0x1C] = 0xFF
    record[0x20] = color
    record[0x21] = 0 if slot == 1 else 1
    record[0x23:0x33] = name.encode().ljust(16, b"\x00")
    return bytes(record)


class FakeAnyToneSerial:
    def _put(self, address, data):
        data = bytes(data)
        for offset in range(0, len(data), 16):
            self.memory[address + offset] = data[offset:offset + 16]

    def __init__(self):
        self.timeout = 1
        self._rx = bytearray()
        self.memory = {}
        channel_bitmap = bytearray(0x200)
        channel_bitmap[0] = 0x03
        self.memory[CHANNEL_BITMAP] = bytes(channel_bitmap)
        self._put(
            CHANNEL_BANKS,
            _channel(438_800_000, name="Alabama", color=1, slot=2),
        )
        self._put(
            CHANNEL_BANKS + 0x40,
            _channel(
                146_520_000,
                600_000,
                digital=False,
                name="CALL 2M",
            ),
        )
        zone_bitmap = bytearray(0x20)
        zone_bitmap[0] = 0x01
        self.memory[ZONE_BITMAP] = bytes(zone_bitmap)
        zone_channels = bytearray(b"\xff" * 0x200)
        zone_channels[0:4] = (
            (0).to_bytes(2, "little") + (1).to_bytes(2, "little")
        )
        self._put(ZONE_CHANNELS, zone_channels)
        self._put(
            ZONE_NAMES, b"Mississippi".ljust(0x20, b"\x00")
        )

    def write(self, data):
        data = bytes(data)
        if data == b"PROGRAM":
            self._rx.extend(b"QX\x06")
        elif data == b"\x02":
            self._rx.extend(b"I" + b"D578UV2" + b"\x0e" +
                            b"V2.08\x00" + b"\x06")
        elif data == b"END":
            self._rx.extend(b"\x06")
        elif data[:1] == b"R" and len(data) == 6:
            address = int.from_bytes(data[1:5], "big")
            size = data[5]
            payload = self.memory.get(
                address, b"\xff" * size
            )[:size].ljust(size, b"\xff")
            body = address.to_bytes(4, "big") + bytes((size,)) + payload
            self._rx.extend(b"W" + body + bytes((sum(body) & 0xFF,)) + b"\x06")
        elif data[:1] == b"W" and len(data) == 24:
            address = int.from_bytes(data[1:5], "big")
            size = data[5]
            self.memory[address] = data[6:6 + size]
            self._rx.extend(b"\x06")
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


class AnyToneD578UVIIITest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = _load_bridge().load_chirp(
            str(SOURCE),
            str(PYTHON_VENDOR),
            str(ROOT / "drivers"),
        )
        cls.radio_class = cls.directory.get_radio(
            "AnyTone_AT-D578UVIII_Plus"
        )

    def _read_radio(self):
        serial = FakeAnyToneSerial()
        radio = self.radio_class(serial)
        radio.status_fn = None
        radio.sync_in()
        return radio, serial

    def test_catalog_and_features(self):
        radio, _serial = self._read_radio()
        features = radio.get_features()
        self.assertEqual(features.memory_bounds, (1, 4000))
        self.assertTrue(features.has_bank)
        self.assertIn("DMR", features.valid_modes)
        self.assertIn("experimental",
                      self.radio_class.get_prompts().experimental.lower())

    def test_reads_channels_and_zone(self):
        radio, _serial = self._read_radio()
        first = radio.get_memory(1)
        self.assertEqual(first.freq, 438_800_000)
        self.assertEqual(first.name, "Alabama")
        self.assertEqual(first.mode, "DMR")
        self.assertEqual(first.extra["color_code"].value, 1)
        self.assertEqual(first.extra["time_slot"].value, "2")

        second = radio.get_memory(2)
        self.assertEqual(second.freq, 146_520_000)
        self.assertEqual(second.duplex, "+")
        self.assertEqual(second.offset, 600_000)
        self.assertEqual(second.mode, "NFM")
        self.assertEqual(second.name, "CALL 2M")

        banks = radio.get_bank_model().get_mappings()
        self.assertEqual(banks[0].get_name(), "Mississippi")
        self.assertEqual(
            [memory.number for memory in
             radio.get_bank_model().get_mapping_memories(banks[0])],
            [1, 2],
        )

    def test_edits_and_round_trips_channel(self):
        radio, serial = self._read_radio()
        memory = radio.get_memory(1)
        memory.freq = 441_000_000
        memory.name = "NEW CH"
        memory.extra["color_code"].value = 7
        memory.extra["time_slot"].value = "1"
        radio.set_memory(memory)
        radio.sync_out()

        second = self.radio_class(serial)
        second.status_fn = None
        second.sync_in()
        self.assertEqual(second.get_memory(1).freq, 441_000_000)
        self.assertEqual(second.get_memory(1).name, "NEW CH")
        self.assertEqual(second.get_memory(1).extra["color_code"].value, 7)
        self.assertEqual(second.get_memory(1).extra["time_slot"].value, "1")

    def test_saved_newchirp_image_reopens(self):
        from chirp import memmap

        radio, _serial = self._read_radio()
        image = radio.get_mmap().get_packed()
        reopened = self.radio_class(FakeAnyToneSerial())
        reopened._mmap = memmap.MemoryMapBytes(image)
        reopened.process_mmap()
        self.assertEqual(reopened.get_memory(1).name, "Alabama")
        self.assertEqual(reopened.get_memory(2).name, "CALL 2M")


if __name__ == "__main__":
    unittest.main()
