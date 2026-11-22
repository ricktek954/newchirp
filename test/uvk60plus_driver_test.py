"""Offline replay tests for the CPS-derived KSUN UV-K60 Plus driver."""

from collections import deque
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
IMAGE_SIZE = 0x2A00
CHANNEL_START = 0x10
NAME_START = 0x2000


def _load_bridge():
    spec = importlib.util.spec_from_file_location(
        "newchirp_chirp_bridge_uvk60plus",
        ROOT / "scripts/chirp_bridge.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load chirp_bridge.py")
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


bridge = _load_bridge()
directory = bridge.load_chirp(
    str(SOURCE),
    str(PYTHON_VENDOR),
    str(ROOT / "drivers"),
)
driver = sys.modules["newchirp.drivers.newchirp_uvk60plus"]
driver.time.sleep = lambda *_args, **_kwargs: None


def _bcd_frequency(frequency):
    digits = f"{frequency // 10:08d}"
    return bytes.fromhex(digits)[::-1]


def _bcd_tone(frequency):
    digits = f"{round(frequency * 10):04d}"
    return bytes.fromhex(digits)[::-1]


def _channel(rx, tx, rx_tone=None, tx_tone=None):
    record = bytearray(b"\xff" * 16)
    record[0:4] = _bcd_frequency(rx)
    record[4:8] = (
        b"\xff" * 4 if tx is None else _bcd_frequency(tx)
    )
    record[8:10] = (
        b"\xff\xff" if rx_tone is None else _bcd_tone(rx_tone)
    )
    record[10:12] = (
        b"\xff\xff" if tx_tone is None else _bcd_tone(tx_tone)
    )
    record[12:14] = b"\x00\x00"
    return bytes(record)


def _synthetic_image():
    image = bytearray(b"\xff" * IMAGE_SIZE)
    image[CHANNEL_START:CHANNEL_START + 16] = _channel(
        438_387_500,
        430_787_500,
        tx_tone=118.8,
    )
    image[CHANNEL_START + 16:CHANNEL_START + 32] = _channel(
        121_175_000,
        None,
    )
    image[NAME_START:NAME_START + 16] = (
        b"\xc6\xb5\xb5\xc0" + b"GB3DI       "
    )
    image[NAME_START + 16:NAME_START + 32] = (
        b"\xc6\xb5\xb5\xc0" + b"FFG1        "
    )
    return bytes(image)


class FakeUVK60PlusSerial:
    def __init__(self, image=None, chunk_size=37, bad_at=None):
        self.image = image if image is not None else _synthetic_image()
        self.chunk_size = chunk_size
        self.bad_at = bad_at
        self.timeout = 0.25
        self.baudrate = 9600
        self.bytesize = 8
        self.parity = "N"
        self.stopbits = 1
        self._rx = bytearray()
        self.writes = []
        self.addresses = []

    def _queue(self, data):
        self._rx.extend(data)

    def write(self, data):
        data = bytes(data)
        self.writes.append(data)
        if data == b"P{OJI}E":
            self._queue(b"\x06")
        elif data == b"\x02":
            self._queue(b"P31183\xff\xff")
        elif data == b"\x06":
            self._queue(b"\x06")
        elif len(data) == 4 and data[:1] == b"R":
            address = struct.unpack(">H", data[1:3])[0]
            length = data[3]
            self.addresses.append(address)
            payload = self.image[address:address + length]
            checksum = sum(payload) & 0xFF
            if address == self.bad_at:
                checksum ^= 0xFF
            self._queue(
                b"W"
                + data[1:4]
                + payload
                + bytes((checksum,))
            )
        elif data != b"E":
            raise AssertionError(
                "Unexpected UV-K60 Plus command: %s" % data.hex()
            )
        return len(data)

    def read(self, size=1):
        count = min(size, self.chunk_size, len(self._rx))
        data = bytes(self._rx[:count])
        del self._rx[:count]
        return data

    def reset_input_buffer(self):
        self._rx.clear()

    def close(self):
        pass


class UVK60PlusDriverTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.radio_class = directory.get_radio("KSUN_UV-K60-Plus")

    def _radio(self, serial):
        radio = self.radio_class(serial)
        radio.status_fn = lambda _status: None
        return radio

    def test_registration_and_read_only_policy(self):
        self.assertEqual(self.radio_class.__name__, "KSUNUVK60Plus")
        self.assertEqual(
            self.radio_class.__module__,
            "newchirp.drivers.newchirp_uvk60plus",
        )
        prompts = self.radio_class.get_prompts()
        self.assertIn("read-only", prompts.experimental.lower())
        radio = self._radio(FakeUVK60PlusSerial())
        with self.assertRaisesRegex(Exception, "not validated"):
            radio.sync_out()
        with self.assertRaisesRegex(Exception, "not validated"):
            radio.set_memory(None)

    def test_full_sparse_image_read_and_reassembly(self):
        image = _synthetic_image()
        serial = FakeUVK60PlusSerial(image, chunk_size=3)
        radio = self._radio(serial)

        radio.sync_in()

        self.assertEqual(radio.get_mmap().get_packed(), image)
        self.assertEqual(serial.writes[0], b"P{OJI}E")
        self.assertEqual(serial.writes[1], b"\x02")
        self.assertEqual(serial.addresses[0], 0x0000)
        self.assertNotIn(0x1F40, serial.addresses)
        self.assertIn(0x2000, serial.addresses)
        self.assertEqual(serial.addresses[-1], 0x29E0)
        self.assertEqual(serial.writes[-1], b"E")

    def test_channel_frequency_tone_offset_and_name_decode(self):
        image = _synthetic_image()
        radio = self._radio(FakeUVK60PlusSerial(image))
        radio._mmap = driver.memmap.MemoryMapBytes(image)
        radio.process_mmap()

        repeater = radio.get_memory(1)
        self.assertEqual(repeater.freq, 438_387_500)
        self.assertEqual(repeater.duplex, "-")
        self.assertEqual(repeater.offset, 7_600_000)
        self.assertEqual(repeater.tmode, "Tone")
        self.assertEqual(repeater.rtone, 118.8)
        self.assertEqual(repeater.name, "GB3DI")

        receive_only = radio.get_memory(2)
        self.assertEqual(receive_only.freq, 121_175_000)
        self.assertEqual(receive_only.duplex, "off")
        self.assertEqual(receive_only.name, "FFG1")
        self.assertTrue(radio.get_memory(3).empty)

    def test_unmapped_records_are_deleted_channels(self):
        # 2026-11-21 owner read: records 1-97 present, both channel maps at
        # 0x1A00/0x1A20 = ff x10 07 (83 channels); MH-580 showed 83 and
        # blank records 84-97. NewChirp showed 97, with factory names.
        image = bytearray(b"\xff" * IMAGE_SIZE)
        for number in range(1, 98):
            start = CHANNEL_START + (number - 1) * 16
            image[start:start + 16] = _channel(145_500_000, 145_500_000)
        for base in (0x1A00, 0x1A20):
            image[base:base + 16] = b"\xff" * 10 + b"\x07" + b"\x00" * 5
        radio = self._radio(FakeUVK60PlusSerial(bytes(image)))
        radio._mmap = driver.memmap.MemoryMapBytes(bytes(image))
        radio.process_mmap()

        shown = [n for n in range(1, 129) if not radio.get_memory(n).empty]
        self.assertEqual(shown, list(range(1, 84)))

        # Either map marks a channel in use (which one is the scan list is
        # unproven).
        image[0x1A00 + 10] = 0x03          # clear channel 83 in one map
        radio._mmap = driver.memmap.MemoryMapBytes(bytes(image))
        radio.process_mmap()
        self.assertFalse(radio.get_memory(83).empty)
        image[0x1A20 + 10] = 0x03          # and in the other
        radio._mmap = driver.memmap.MemoryMapBytes(bytes(image))
        radio.process_mmap()
        self.assertTrue(radio.get_memory(83).empty)

    def test_bad_checksum_retries_same_page_then_fails(self):
        serial = FakeUVK60PlusSerial(bad_at=0x0060)
        radio = self._radio(serial)

        with self.assertRaisesRegex(Exception, "did not return block"):
            radio.sync_in()

        self.assertEqual(serial.addresses.count(0x0060), 3)


if __name__ == "__main__":
    unittest.main()
