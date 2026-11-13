"""Offline tests for the experimental Kenwood TK-350 and TK-359 drivers."""

import importlib.util
from pathlib import Path
import struct
import sys
import unittest
from unittest import mock

from chirp_test_source import chirp_source


ROOT = Path(__file__).resolve().parent.parent
SOURCE = chirp_source()
PYTHON_VENDOR = ROOT / "assets/python/pyserial-3.5-py2.py3-none-any.whl"

MEM_SIZE = 0x0E00
CHANNEL_SIZE = 16
RX_BASE = 0x4D18
TX_BASE = 0x6940


def _load_bridge():
    spec = importlib.util.spec_from_file_location(
        "newchirp_chirp_bridge_kpg23",
        ROOT / "scripts/chirp_bridge.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load chirp_bridge.py")
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


def _frequency_word(frequency, base):
    steps = (frequency - 450_000_000) // 6_250
    return (base + steps) & 0xFFFF


def _channel(rx, tx, name):
    record = bytearray(b"\xFF" * CHANNEL_SIZE)
    record[0:2] = struct.pack("<H", _frequency_word(rx, RX_BASE))
    record[2:4] = struct.pack("<H", _frequency_word(tx, TX_BASE))
    record[8:12] = name.encode("ascii").ljust(4, b" ")[:4]
    return bytes(record)


def _synthetic_image():
    image = bytearray(b"\xFF" * MEM_SIZE)
    image[0:CHANNEL_SIZE] = _channel(
        451_787_500, 456_787_500, "RPT"
    )
    image[CHANNEL_SIZE:CHANNEL_SIZE * 2] = _channel(
        451_006_250, 451_006_250, "SIMP"
    )
    return bytes(image)


class FakeKpgSerial:
    def __init__(self, image, chunk_size=128):
        self.image = bytes(image)
        self.chunk_size = chunk_size
        self.timeout = 1
        self.baudrate = 9600
        self.bytesize = 8
        self.parity = "N"
        self.stopbits = 1
        self.rtscts = False
        self.xonxoff = False
        self._rx = bytearray()
        self.writes = []
        self.addresses = []
        self.block_lengths = []

    def write(self, data):
        data = bytes(data)
        self.writes.append(data)
        if data == b"\x02":
            self._rx.extend(b"P350S\x00\xe2\x00")
        elif data == b"\x06":
            self._rx.extend(b"\x06")
        elif data == b"E":
            self._rx.extend(b"\x06")
        elif len(data) == 4 and data[:1] == b"R":
            address = struct.unpack(">H", data[1:3])[0]
            length = data[3]
            self.addresses.append(address)
            self.block_lengths.append(length)
            offset = address - 0xF000
            payload = self.image[offset:offset + length].ljust(
                length, b"\xff"
            )
            self._rx.extend(b"W\x00\x00")
            self._rx.extend(bytes((length,)))
            self._rx.extend(payload)
        return len(data)

    def read(self, size=1):
        count = min(size, self.chunk_size, len(self._rx))
        data = bytes(self._rx[:count])
        del self._rx[:count]
        return data

    def reset_input_buffer(self):
        self._rx.clear()

    def flush(self):
        pass

    def close(self):
        pass


class KenwoodKPG23DriverTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = _load_bridge().load_chirp(
            str(SOURCE),
            str(PYTHON_VENDOR),
            str(ROOT / "drivers"),
        )
        cls.tk350 = cls.directory.get_radio("Kenwood_TK-350")
        cls.tk359 = cls.directory.get_radio("Kenwood_TK-359")
        from chirp import memmap

        cls.memmap = memmap

    def _radio_from_image(self, radio_class, image):
        radio = radio_class(FakeKpgSerial(image))
        radio._mmap = self.memmap.MemoryMapBytes(bytes(image))
        radio.process_mmap()
        return radio

    def test_models_are_registered_and_read_only(self):
        for radio_class in (self.tk350, self.tk359):
            prompts = radio_class.get_prompts()
            self.assertIn("experimental", prompts.experimental.lower())
            self.assertIn("read-only", prompts.experimental.lower())
            radio = radio_class(FakeKpgSerial(_synthetic_image()))
            with self.assertRaisesRegex(Exception, "read-only"):
                radio.sync_out()
            with self.assertRaisesRegex(Exception, "disabled"):
                radio.set_memory(None)

    def test_tk350_channel_layout_and_frequency_decode(self):
        radio = self._radio_from_image(self.tk350, _synthetic_image())
        repeater = radio.get_memory(1)
        self.assertEqual(repeater.freq, 451_787_500)
        self.assertEqual(repeater.offset, 5_000_000)
        self.assertEqual(repeater.duplex, "+")
        self.assertEqual(repeater.name, "RPT")

        simplex = radio.get_memory(2)
        self.assertEqual(simplex.freq, 451_006_250)
        self.assertEqual(simplex.offset, 0)
        self.assertEqual(simplex.duplex, "")
        self.assertEqual(simplex.name, "SIMP")
        self.assertTrue(radio.get_memory(3).empty)

    def test_fragmented_reads_cover_full_image_and_preserve_bytes(self):
        image = _synthetic_image()
        serial = FakeKpgSerial(image, chunk_size=3)
        radio = self.tk350(serial)
        radio.status_fn = lambda _status: None

        with mock.patch("time.sleep", return_value=None):
            radio.sync_in()

        self.assertEqual(radio.get_mmap().get_packed(), image)
        self.assertEqual(serial.addresses[0], 0xF000)
        self.assertEqual(serial.addresses[1], 0xF080)
        self.assertEqual(serial.addresses[-1], 0xF000 + 0x0D80)
        self.assertEqual(serial.writes[0], b"\x02")
        self.assertEqual(serial.writes[-1], b"E")

    def test_short_block_is_retried_then_fails(self):
        class ShortSerial(FakeKpgSerial):
            def write(self, data):
                if len(data) == 4 and data[:1] == b"R":
                    self.writes.append(bytes(data))
                    self._rx.extend(b"W\x00\x00")
                    return len(data)
                return super().write(data)

        radio = self.tk350(ShortSerial(_synthetic_image()))
        radio.status_fn = lambda _status: None
        with mock.patch("time.sleep", return_value=None):
            with self.assertRaisesRegex(Exception, "0xF000"):
                radio.sync_in()


if __name__ == "__main__":
    unittest.main()
