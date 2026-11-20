"""Offline tests for the read-only IC-F50V/F60V channel decode.

The image is synthetic. It copies only the structure seen in an owner's
capture (section directory, 0x22-byte channel records); no owner data is
included. Nothing here proves physical-radio behaviour.
"""

import importlib.util
from pathlib import Path
import struct
import sys
import unittest

from chirp_test_source import chirp_source


ROOT = Path(__file__).resolve().parent.parent
SOURCE = chirp_source()
PYTHON_VENDOR = ROOT / "assets/python/pyserial-3.5-py2.py3-none-any.whl"


def _load_bridge():
    spec = importlib.util.spec_from_file_location(
        "newchirp_chirp_bridge_f60v", ROOT / "scripts/chirp_bridge.py")
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


def _channel(name, rx, tx):
    return (name.ljust(8).encode("ascii") + struct.pack(">II", rx, tx)
            + b"\x80\x00\x80\x00" + b"\x83\x06\x30" + b"\x00" * 11)


def synthetic_image(channels, count=16):
    image = bytearray(0x180)
    image[0x100:0x108] = b"ICOM Inc"
    records = b"".join(_channel(*ch) for ch in channels)
    records += _channel("", 0, 0) * (count - len(channels))
    sections = [(2, 0x22, count, 0x180, records),
                (3, 0x90, 1, None, b"\x11" * 0x90),
                (4, 0x20, 1, None, b"\x22" * 0x20)]
    table = b""
    for ident, size, number, _, body in sections:
        table += struct.pack(">HHHHH", ident, size, number, len(image), 0)
        image += body
    return bytes(image + table)


class IcomF60VDriverTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = _load_bridge().load_chirp(
            str(SOURCE), str(PYTHON_VENDOR), str(ROOT / "drivers"))
        cls.radio_class = cls.directory.get_radio("Icom_IC-F50V_F60V")
        from chirp import memmap
        cls.memmap = memmap

    def _radio(self, image):
        return self.radio_class(self.memmap.MemoryMapBytes(image))

    def test_decodes_names_and_frequencies(self):
        radio = self._radio(synthetic_image([
            ("SIMPLEX", 460_500_000, 460_500_000),
            ("RPT", 462_675_000, 467_675_000),
            ("SPLIT", 155_000_000, 450_000_000),
        ]))
        self.assertEqual(radio.get_features().memory_bounds, (1, 16))
        first = radio.get_memory(1)
        self.assertEqual((first.name, first.freq, first.duplex, first.offset),
                         ("SIMPLEX", 460_500_000, "", 0))
        repeater = radio.get_memory(2)
        self.assertEqual((repeater.duplex, repeater.offset),
                         ("+", 5_000_000))
        split = radio.get_memory(3)
        self.assertEqual((split.duplex, split.offset),
                         ("split", 450_000_000))
        self.assertTrue(radio.get_memory(4).empty)
        self.assertIn("freq", first.immutable)

    def test_channel_count_comes_from_directory(self):
        radio = self._radio(synthetic_image([("A", 451_000_000, 451_000_000)], count=8))
        self.assertEqual(radio.get_features().memory_bounds, (1, 8))

    def test_image_without_directory_points_to_capture(self):
        with self.assertRaisesRegex(Exception, "Capture"):
            self._radio(b"\x00" * 0x400)

    def test_never_writes(self):
        radio = self._radio(synthetic_image([("A", 451_000_000, 451_000_000)]))
        self.assertTrue(self.radio_class.NEWCHIRP_WRITE_DISABLED)
        with self.assertRaisesRegex(Exception, "read-only"):
            radio.sync_out()
        with self.assertRaisesRegex(Exception, "read-only"):
            radio.set_memory(radio.get_memory(1))

    def test_match_model_needs_directory(self):
        image = synthetic_image([("A", 451_000_000, 451_000_000)])
        self.assertTrue(self.radio_class.match_model(image, "f60v.img"))
        self.assertFalse(self.radio_class.match_model(
            image[:0x200] + b"\x00" * 0x400, "f60v.img"))


if __name__ == "__main__":
    unittest.main()
