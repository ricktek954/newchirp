"""Offline tests for the experimental TYT MD-UV380 DFU driver."""

import importlib.util
from pathlib import Path
import sys
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "build_support/chirp-20261023"
PYTHON_VENDOR = ROOT / "assets/python/pyserial-3.5-py2.py3-none-any.whl"
sys.path.insert(0, str(ROOT / "scripts"))

SEGMENT0 = 0x3E000
SEGMENT1 = 0x90000


def _load_bridge():
    spec = importlib.util.spec_from_file_location(
        "newchirp_chirp_bridge_uv380",
        ROOT / "scripts/chirp_bridge.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load chirp_bridge.py")
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


def _bcd_le(number):
    value = 0
    for index in range(8):
        value |= (number % 10) << (index * 4)
        number //= 10
    return value.to_bytes(4, "little")


def _ctcss(value):
    scaled = int(round(value * 10))
    return (
        ((scaled // 1000) & 0x03) << 12
        | ((scaled // 100) % 10) << 8
        | ((scaled // 10) % 10) << 4
        | scaled % 10
    ).to_bytes(2, "little")


def _channel(frequency, tx_frequency, name, digital):
    record = bytearray(0x40)
    record[0] = 2 if digital else 0x09
    record[0x01] = 0x19 if digital else 0x01
    record[0x06:0x08] = (5).to_bytes(2, "little")
    record[0x0C] = 2
    record[0x10:0x14] = _bcd_le(frequency // 10)
    record[0x14:0x18] = _bcd_le(tx_frequency // 10)
    record[0x18:0x1A] = _ctcss(123.0)
    record[0x1A:0x1C] = _ctcss(123.0)
    record[0x1E] = 0xC0
    record[0x20:0x40] = name.encode("utf-16le").ljust(0x20, b"\x00")
    return bytes(record)


class FakeDfuTransport:
    def __init__(self):
        self.segment0 = bytearray(b"\xff" * SEGMENT0)
        self.segment1 = bytearray(b"\xff" * SEGMENT1)
        self.erased = []
        self.closed = False
        self.segment1[0:0x40] = _channel(
            439_200_000,
            439_200_000,
            "DMR ONE",
            True,
        )
        self.segment1[0x40:0x80] = _channel(
            146_940_000,
            147_540_000,
            "146.94 RPT",
            False,
        )

        zone = bytearray(0x40)
        zone[0:0x20] = "Local".encode("utf-16le").ljust(0x20, b"\x00")
        zone[0x20:0x22] = (1).to_bytes(2, "little")
        zone[0x22:0x24] = (2).to_bytes(2, "little")
        zones_offset = 0x0149E0 - 0x002000
        self.segment0[zones_offset:zones_offset + 0x40] = zone

    def program_mode(self):
        return b"MD-UV380".ljust(64, b"\x00")

    def read(self, address, length):
        if address >= 0x110000:
            offset = address - 0x110000
            return bytes(self.segment1[offset:offset + length])
        offset = address - 0x002000
        return bytes(self.segment0[offset:offset + length])

    def erase(self, address, size):
        self.erased.append((address, size))

    def write(self, address, data):
        if address >= 0x110000:
            offset = address - 0x110000
            self.segment1[offset:offset + len(data)] = data
        else:
            offset = address - 0x002000
            self.segment0[offset:offset + len(data)] = data

    def close(self, reboot=True):
        self.closed = True


class TYTMDUV380Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bridge = _load_bridge()
        cls.directory = cls.bridge.load_chirp(
            str(SOURCE),
            str(PYTHON_VENDOR),
            str(ROOT / "drivers"),
        )
        cls.radio_class = cls.directory.get_radio("TYT_MD-UV380")

    def test_catalog_and_features(self):
        transport = FakeDfuTransport()
        radio = self.radio_class(transport)
        radio.status_fn = None
        radio.sync_in()
        features = radio.get_features()
        self.assertEqual(features.memory_bounds, (1, 3000))
        self.assertTrue(features.has_bank)
        self.assertIn("DMR", features.valid_modes)
        self.assertIn(
            "experimental",
            self.radio_class.get_prompts().experimental.lower(),
        )

    def test_bridge_selects_usb_dfu_transport(self):
        transport = FakeDfuTransport()
        with mock.patch(
            "newchirp_usb_dfu.DfuTransport",
            return_value=transport,
        ) as factory:
            radio = self.bridge.radio_for(
                self.directory,
                "TYT_MD-UV380",
                "usb-dfu:1:2",
            )
        factory.assert_called_once_with("usb-dfu:1:2")
        radio.status_fn = lambda _status: None
        radio.sync_in()
        self.assertEqual(radio.get_memory(1).name, "DMR ONE")

    def test_reads_channel_fields_and_zone(self):
        radio = self.radio_class(FakeDfuTransport())
        radio.status_fn = None
        radio.sync_in()

        first = radio.get_memory(1)
        self.assertEqual(first.freq, 439_200_000)
        self.assertEqual(first.name, "DMR ONE")
        self.assertEqual(first.mode, "DMR")
        self.assertEqual(first.extra["color_code"].value, 1)
        self.assertEqual(first.extra["time_slot"].value, "2")

        second = radio.get_memory(2)
        self.assertEqual(second.freq, 146_940_000)
        self.assertEqual(second.duplex, "+")
        self.assertEqual(second.offset, 600_000)
        self.assertEqual(second.mode, "FM")
        self.assertEqual(second.tmode, "TSQL")
        self.assertEqual(second.rtone, 123.0)

        mapping = radio.get_bank_model().get_mappings()[0]
        self.assertEqual(mapping.get_name(), "Local")
        self.assertEqual(
            [memory.number for memory in
             radio.get_bank_model().get_mapping_memories(mapping)],
            [1, 2],
        )

    def test_edits_and_round_trips_channel(self):
        transport = FakeDfuTransport()
        radio = self.radio_class(transport)
        radio.status_fn = None
        radio.sync_in()
        memory = radio.get_memory(1)
        memory.freq = 440_000_000
        memory.name = "NEW DMR"
        memory.extra["color_code"].value = 7
        memory.extra["time_slot"].value = "1"
        radio.set_memory(memory)
        radio.sync_out()

        self.assertEqual(
            transport.erased,
            [
                (0x002000, SEGMENT0),
                (0x110000, SEGMENT1),
            ],
        )
        second = self.radio_class(transport)
        second.status_fn = None
        second.sync_in()
        readback = second.get_memory(1)
        self.assertEqual(readback.freq, 440_000_000)
        self.assertEqual(readback.name, "NEW DMR")
        self.assertEqual(readback.extra["color_code"].value, 7)
        self.assertEqual(readback.extra["time_slot"].value, "1")

    def test_saved_newchirp_image_reopens(self):
        from chirp import memmap

        radio = self.radio_class(FakeDfuTransport())
        radio.status_fn = None
        radio.sync_in()
        image = radio.get_mmap().get_packed()
        reopened = self.radio_class(FakeDfuTransport())
        reopened._mmap = memmap.MemoryMapBytes(image)
        reopened.process_mmap()
        self.assertEqual(reopened.get_memory(1).name, "DMR ONE")
        self.assertEqual(reopened.get_memory(2).name, "146.94 RPT")


if __name__ == "__main__":
    unittest.main()
