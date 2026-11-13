"""Offline tests for the experimental Kenwood TK-863G driver."""

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

MEM_SIZE = 0x8000
CHANNEL_OFFSET = 0x02F0
IDENTITY_OFFSET = 0x58D0
MODEL = "Kenwood_TK-863G"


def _load_bridge():
    spec = importlib.util.spec_from_file_location(
        "newchirp_chirp_bridge_tk863g",
        ROOT / "scripts/chirp_bridge.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load chirp_bridge.py")
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


def _lbcd(value):
    digits = "%08i" % value
    return bytes(
        int(digits[index:index + 2], 16)
        for index in range(6, -1, -2)
    )


def _channel_record(number, rx, tx, name, tone=1738, wide=True):
    record = bytearray(b"\xFF" * 0x20)
    record[0] = number
    record[1:5] = _lbcd(rx // 10)
    record[5:9] = _lbcd(tx // 10)
    record[9:11] = bytes((0x35, 0x32))
    record[11:13] = struct.pack("<H", tone)
    record[13:15] = struct.pack("<H", tone)
    record[15:23] = name.encode("ascii").ljust(8, b" ")[:8]
    record[26] = 0xFE if wide else 0xF6
    record[27] = 0xFB if rx != tx else 0xDB
    return bytes(record)


def _synthetic_image():
    image = bytearray(b"\xFF" * MEM_SIZE)
    image[IDENTITY_OFFSET:IDENTITY_OFFSET + 7] = b"TK-863G"
    image[CHANNEL_OFFSET:CHANNEL_OFFSET + 0x20] = _channel_record(
        1,
        451_787_500,
        456_787_500,
        "REPEATER",
    )
    image[CHANNEL_OFFSET + 0x20:CHANNEL_OFFSET + 0x40] = _channel_record(
        2,
        451_787_500,
        451_787_500,
        "DIRECT",
    )
    return bytes(image)


def _dat_image():
    header = bytearray(b"\xFF" * 0x70)
    header[:6] = b"KPG76D"
    header[12:17] = b"M0863"
    return bytes(header) + _synthetic_image()


class FakeKpg76Serial:
    def __init__(self, image, chunk_size=1024, corrupt_first=False):
        self.image = bytearray(image)
        self.chunk_size = chunk_size
        self.corrupt_first = corrupt_first
        self.timeout = 1
        self.baudrate = 9600
        self.bytesize = 8
        self.parity = "E"
        self.stopbits = 2
        self.rtscts = False
        self.xonxoff = False
        self._rx = bytearray()
        self.writes = []
        self.addresses = []
        self._first_block = True

    @staticmethod
    def _tuning_record():
        payload = bytes(range(32))
        return b"N" + payload + bytes((sum(payload) & 0xFF,))

    def write(self, data):
        data = bytes(data)
        self.writes.append(data)
        if data == b"PROGRAM":
            self._rx.extend(b"\x06")
        elif data == b"\x02":
            self._rx.extend(b"M0863\x06\xff\xf2")
        elif data == b"NRK":
            self._rx.extend(self._tuning_record())
        elif data == b"\x7c":
            self._rx.extend(b"\x12\x34")
        elif data == b"\x15":
            self._rx.extend(b"\x06")
        elif data == b"\x06":
            self._rx.extend(b"\x06")
        elif data == b"E":
            self._rx.extend(b"\x06")
        elif len(data) == 3 and data[:1] == b"R":
            address = struct.unpack(">H", data[1:])[0]
            self.addresses.append(address)
            payload = self.image[address:address + 0x100].ljust(
                0x100, b"\xFF"
            )
            checksum = sum(payload) & 0xFF
            if self.corrupt_first and self._first_block:
                checksum ^= 0xFF
                self._first_block = False
            self._rx.extend(b"W")
            self._rx.extend(payload)
            self._rx.extend(bytes((checksum,)))
        return len(data)

    def read(self, size=1):
        count = min(size, self.chunk_size, len(self._rx))
        data = bytes(self._rx[:count])
        del self._rx[:count]
        return data

    def flush(self):
        pass

    def reset_input_buffer(self):
        self._rx.clear()

    def close(self):
        pass


class KenwoodTK863GDriverTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = _load_bridge().load_chirp(
            str(SOURCE),
            str(PYTHON_VENDOR),
            str(ROOT / "drivers"),
        )
        cls.radio_class = cls.directory.get_radio(MODEL)
        from chirp import memmap

        cls.memmap = memmap

    def _radio_from_image(self, image):
        radio = self.radio_class(FakeKpg76Serial(image))
        radio._mmap = self.memmap.MemoryMapBytes(bytes(image))
        radio.process_mmap()
        return radio

    def test_catalog_and_read_only_policy(self):
        self.assertEqual(
            self.radio_class.__name__, "KenwoodTK863GRadio"
        )
        prompts = self.radio_class.get_prompts()
        self.assertIn("experimental", prompts.experimental.lower())
        self.assertIn("read-only", prompts.experimental.lower())
        self.assertIn("KPG-76D", prompts.info)

        radio = self.radio_class(FakeKpg76Serial(_synthetic_image()))
        with self.assertRaisesRegex(Exception, "read-only"):
            radio.sync_out()
        with self.assertRaisesRegex(Exception, "disabled"):
            radio.set_memory(None)

    def test_oem_dat_is_unwrapped_and_channels_decode(self):
        self.assertTrue(self.radio_class.match_model(_dat_image(), "test.dat"))
        radio = self.radio_class(FakeKpg76Serial(_dat_image()))
        radio._mmap = self.memmap.MemoryMapBytes(_dat_image())
        radio.process_mmap()

        self.assertEqual(len(radio.get_mmap().get_packed()), MEM_SIZE)
        repeater = radio.get_memory(1)
        self.assertEqual(repeater.freq, 451_787_500)
        self.assertEqual(repeater.offset, 5_000_000)
        self.assertEqual(repeater.duplex, "+")
        self.assertEqual(repeater.name, "REPEATER")
        self.assertEqual(repeater.mode, "FM")
        self.assertEqual(repeater.tmode, "TSQL")
        self.assertEqual(repeater.ctone, 173.8)

        direct = radio.get_memory(2)
        self.assertEqual(direct.freq, 451_787_500)
        self.assertEqual(direct.offset, 0)
        self.assertEqual(direct.duplex, "")
        self.assertEqual(direct.name, "DIRECT")
        self.assertTrue(radio.get_memory(3).empty)

    def test_wrong_radio_identity_is_rejected(self):
        image = bytearray(_synthetic_image())
        image[IDENTITY_OFFSET:IDENTITY_OFFSET + 7] = b"TK-373G"
        radio = self.radio_class(FakeKpg76Serial(image))
        radio._mmap = self.memmap.MemoryMapBytes(bytes(image))
        with self.assertRaisesRegex(Exception, "TK-863G"):
            radio.process_mmap()

    def test_fragmented_read_uses_all_256_byte_blocks(self):
        image = _synthetic_image()
        serial = FakeKpg76Serial(image, chunk_size=3)
        radio = self.radio_class(serial)
        radio.status_fn = lambda _status: None

        with mock.patch("time.sleep", return_value=None):
            radio.sync_in()

        self.assertEqual(radio.get_mmap().get_packed(), image)
        self.assertEqual(len(serial.addresses), 128)
        self.assertEqual(serial.addresses[0], 0)
        self.assertEqual(serial.addresses[1], 0x100)
        self.assertEqual(serial.addresses[-1], 0x7F00)
        self.assertEqual(serial.writes[0], b"PROGRAM")
        self.assertEqual(serial.writes[-1], b"E")

    def test_bad_block_checksum_is_retried(self):
        image = _synthetic_image()
        serial = FakeKpg76Serial(
            image, chunk_size=17, corrupt_first=True
        )
        radio = self.radio_class(serial)
        radio.status_fn = lambda _status: None

        with mock.patch("time.sleep", return_value=None):
            radio.sync_in()

        self.assertEqual(radio.get_mmap().get_packed(), image)
        self.assertIn(b"\x15", serial.writes)
        self.assertEqual(serial.addresses.count(0), 2)


if __name__ == "__main__":
    unittest.main()
