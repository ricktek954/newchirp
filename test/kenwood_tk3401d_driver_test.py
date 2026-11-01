"""Offline tests for the experimental Kenwood TK-3401D driver."""

import importlib.util
from pathlib import Path
import struct
import sys
import unittest


from chirp_test_source import chirp_source


ROOT = Path(__file__).resolve().parent.parent
SOURCE = chirp_source()
PYTHON_VENDOR = ROOT / "assets/python/pyserial-3.5-py2.py3-none-any.whl"
MODEL_ID = b"PTK 3401"


def _load_bridge():
    spec = importlib.util.spec_from_file_location(
        "newchirp_chirp_bridge_tk3401d",
        ROOT / "scripts/chirp_bridge.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load chirp_bridge.py")
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


def _identity():
    identity = bytearray(b"\xFF" * 48)
    identity[:8] = MODEL_ID
    identity[0x20:0x2C] = bytes(range(0x20, 0x2C))
    return bytes(identity)


class FakeKpg171Serial:
    def __init__(self, image):
        self.image = bytes(image)
        self.timeout = 1
        self.baudrate = 9600
        self.stopbits = 1
        self._rx = bytearray()
        self._checksum_seen = False
        self.writes = []
        self.block_addresses = []

    def write(self, data):
        data = bytes(data)
        self.writes.append(data)
        if data == b"PROGRAM":
            self._rx.extend(b"\x16\x06")
        elif data == b"\x02":
            self._rx.extend(_identity())
        elif len(data) == 1 and data != b"\x06":
            self._checksum_seen = True
        elif data == b"\x06":
            self._rx.extend(b"\x06")
        elif data == b"E":
            self._rx.extend(b"\x06")
        elif len(data) == 4 and data[0] == 0x52:
            address = struct.unpack(">H", data[1:3])[0]
            size = data[3]
            self.block_addresses.append(address)
            chunk = self.image[address:address + size]
            chunk = chunk.ljust(size, b"\xFF")
            self._rx.extend(b"W")
            self._rx.extend(struct.pack(">HB", address, size))
            self._rx.extend(chunk)
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


def _synthetic_image():
    image = bytearray(b"\xFF" * 0x10000)
    for index in range(32):
        offset = 0x2000 + index * 64
        frequency = 446_006_250
        image[offset:offset + 4] = (frequency // 10).to_bytes(4, "little")
        name = ("PMR %02i" % (index + 1)).encode("ascii")
        image[offset + 16:offset + 16 + len(name)] = name
    return bytes(image)


class KenwoodTK3401DDriverTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = _load_bridge().load_chirp(
            str(SOURCE),
            str(PYTHON_VENDOR),
            str(ROOT / "drivers"),
        )
        cls.radio_class = cls.directory.get_radio("Kenwood_TK-3401D")

    def test_catalog_and_read_only_policy(self):
        self.assertEqual(self.radio_class.__name__, "KenwoodTK3401DRadio")
        prompts = self.radio_class.get_prompts()
        self.assertIn("experimental", prompts.experimental.lower())
        self.assertIn("read-only", prompts.experimental.lower())

        radio = self.radio_class(FakeKpg171Serial(b"\xFF" * 0x10000))
        with self.assertRaisesRegex(Exception, "read-only"):
            radio.sync_out()
        with self.assertRaisesRegex(Exception, "disabled"):
            radio.set_memory(None)

    def test_download_reads_addressed_128_byte_blocks(self):
        image = _synthetic_image()
        serial = FakeKpg171Serial(image)
        radio = self.radio_class(serial)
        radio.process_mmap = lambda: None
        radio.status_fn = None

        radio.sync_in()

        self.assertEqual(radio.get_mmap().get_packed(), image)
        self.assertEqual(serial.block_addresses[0], 0)
        self.assertEqual(serial.block_addresses[1], 0x80)
        self.assertEqual(serial.block_addresses[-1], 0xFF80)
        self.assertTrue(any(b"PROGRAM" == write for write in serial.writes))
        self.assertTrue(any(write == b"E" for write in serial.writes))

    def test_provisional_scan_exposes_pmr446_channels(self):
        from chirp import memmap

        radio = self.radio_class(FakeKpg171Serial(b"\xFF" * 0x10000))
        radio._mmap = memmap.MemoryMapBytes(_synthetic_image())
        radio.process_mmap()

        memory = radio.get_memory(1)
        self.assertEqual(memory.freq, 446_006_250)
        self.assertEqual(memory.name, "PMR 01")
        self.assertEqual(memory.mode, "FM")
        self.assertEqual(radio.get_features().memory_bounds, (1, 32))


if __name__ == "__main__":
    unittest.main()
