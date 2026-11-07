"""Offline replay tests for the CPS-derived Radioddity GA-510 V2 transport."""

from collections import deque
import importlib.util
from pathlib import Path
import struct
import sys
import unittest

from chirp_test_source import chirp_source


ROOT = Path(__file__).resolve().parent.parent
SOURCE = chirp_source()
PYTHON_VENDOR = ROOT / "assets/python/pyserial-3.5-py2.py3-none-any.whl"
FIXTURE = SOURCE / "tests/images/Radioddity_GA-510_V2.img"


def command_with_size(code, address, size):
    return bytes((code,)) + address.to_bytes(3, "little") + bytes((size,))


def _load_bridge():
    spec = importlib.util.spec_from_file_location(
        "newchirp_chirp_bridge_ga510_v2",
        ROOT / "scripts/chirp_bridge.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load chirp_bridge.py")
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


class FakeGA510V2Serial:
    BLOCK_ORDER = (2, 4, 6, 16, 24)
    DESCRIPTORS = (0x1FFF, 0x2FFF, 0x3FFF, 0x4FFF, 0x5FFF, 0x6FFF)

    def __init__(self, logical_image):
        self.timeout = 0.25
        self.writes = []
        self.responses = deque()
        self.logical = bytearray(logical_image)
        self.physical = bytearray(0x7000)
        for page_index, block_number in enumerate(self.BLOCK_ORDER, start=1):
            logical_start = page_index - 1
            logical_start *= 0x1000
            physical_start = page_index * 0x1000
            self.physical[
                physical_start:physical_start + 0x1000
            ] = self.logical[
                logical_start:logical_start + 0x1000
            ]
            self.physical[physical_start + 0xFFF] = self._encode_page(
                block_number
            )

    @staticmethod
    def _encode_page(number):
        return ((number // 10) << 4) | (number % 10)

    def flush(self):
        pass

    def reset_input_buffer(self):
        self.responses.clear()

    def write(self, data):
        data = bytes(data)
        self.writes.append(data)
        if data == b"PSEARCH":
            self._queue(b"\x06DMR1702")
        elif data == b"PASSSTA":
            self._queue(b"P\x00\x01")
        elif data in (b"SYSINFO", b"DMR1702"):
            self._queue(b"\x06")
        elif data == b"\x02":
            self._queue(b"\x06DMR1702")
        elif data == b"\x06":
            self._queue(b"\x06")
        elif data == b"\xFF\xFF\xFF\xFF\x0C":
            pass
        elif data[:1] == b"V":
            self._info_response(data)
        elif data[:1] == b"R":
            address = int.from_bytes(data[1:4], "little")
            size = data[4]
            self._record_read(address, size)
        elif data[:1] == b"W":
            address = int.from_bytes(data[1:4], "little")
            size = data[4]
            self.physical[address:address + size] = data[5:]
            self._queue(b"\x06")
        return len(data)

    def read(self, size):
        if not self.responses:
            return b""
        data = self.responses.popleft()
        if len(data) > size:
            self.responses.appendleft(data[size:])
            data = data[:size]
        return data

    def _queue(self, data):
        self.responses.extend(bytes((value,)) for value in data)

    def _record_read(self, address, size):
        if address in self.DESCRIPTORS:
            payload = bytes((self.physical[address],))
        else:
            payload = bytes(self.physical[address:address + size])
        self._queue(command_with_size(0x52, address, size) + payload)

    def _info_response(self, command):
        if command.endswith(b"\x0A\x0D"):
            size = 10
            payload = bytes(size)
        elif command == b"\x56\x00\x00\x00\x0A":
            size = 10
            payload = self._page_span_payload()
        else:
            raise AssertionError("Unexpected info command %s" % command.hex())
        self._queue(struct.pack(">BBB", 0x56, 0, size) + payload)

    def _page_span_payload(self):
        return bytes.fromhex("00 01 00 18 00 00 00 00 00 00")


class GA510V2CPSDriverTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        bridge = _load_bridge()
        directory = bridge.load_chirp(
            str(SOURCE),
            str(PYTHON_VENDOR),
            str(ROOT / "drivers"),
        )
        cls.radio_class = directory.get_radio("Radioddity_GA-510_V2")
        cls.generic_class = directory.get_radio("Radioddity_GA-510")
        cls.driver = sys.modules[cls.radio_class.__module__]

        fixture_radio = cls.radio_class(None)
        fixture_radio.load_mmap(str(FIXTURE))
        cls.fixture_image = fixture_radio._mmap.get_packed().ljust(
            cls.driver.IMAGE_SIZE,
            b"\xFF",
        )

    def _radio(self):
        radio = self.radio_class(None)
        radio.status_fn = lambda _status: None
        return radio

    def test_cps_driver_replaces_the_stock_v2_entry(self):
        self.assertEqual(
            self.radio_class.__module__,
            "newchirp.drivers.newchirp_ga510_v2",
        )
        self.assertEqual(self.radio_class.BAUD_RATE, 57600)
        prompts = self.radio_class.get_prompts()
        self.assertIn("CPS v1.00.36", prompts.experimental)
        self.assertIn("GA-510 V2", prompts.info)

    def test_generic_entry_steers_a_v2_radio_to_the_cps_driver(self):
        pipe = FakeGA510V2Serial(self.fixture_image)
        detected = self.generic_class.detect_from_serial(pipe)
        self.assertIs(detected, self.radio_class)
        self.assertEqual(pipe.writes[0], b"PSEARCH")
        self.assertTrue(getattr(pipe, "_newchirp_ga510_ready"))

    def test_detection_uses_the_complete_cps_handshake(self):
        pipe = FakeGA510V2Serial(self.fixture_image)
        detected = self.radio_class.detect_from_serial(pipe)
        self.assertIs(detected, self.radio_class)
        self.assertEqual(
            pipe.writes[:12],
            [
                b"PSEARCH",
                b"PASSSTA",
                b"SYSINFO",
                b"DMR1702",
                b"\x02",
                b"\x06",
                b"\x56\x00\x00\x0A\x0D",
                b"\x06",
                b"\x56\x00\x10\x0A\x0D",
                b"\x06",
                b"\x56\x00\x20\x0A\x0D",
                b"\x06",
            ],
        )
        self.assertIn(b"\xFF\xFF\xFF\xFF\x0C", pipe.writes)
        self.assertTrue(getattr(pipe, "_newchirp_ga510_ready"))

    def test_download_reassembles_all_five_memory_blocks(self):
        pipe = FakeGA510V2Serial(self.fixture_image)
        radio = self._radio()
        radio.pipe = pipe

        radio.sync_in()

        self.assertEqual(radio._mmap.get_packed(), self.fixture_image)
        self.assertFalse(radio.get_memory(1).empty)
        self.assertEqual(radio.get_memory(1).freq, 444_000_000)
        reads = [write for write in pipe.writes if write[:1] == b"R"]
        self.assertEqual(len(reads), 6 + 5 * 64)
        self.assertEqual(
            reads[0],
            command_with_size(0x52, 0x1FFF, 1),
        )

    def test_upload_writes_all_logical_blocks_to_mapped_pages(self):
        pipe = FakeGA510V2Serial(self.fixture_image)
        radio = self._radio()
        radio.pipe = pipe
        radio._mmap = self.driver.ga510.memmap.MemoryMapBytes(
            self.fixture_image
        )

        edited = bytearray(self.fixture_image)
        edited[0:16] = bytes.fromhex(
            "00 00 44 00 00 00 44 00 00 00 00 00 00 00 00 00"
        )
        edited[0xFFF] = 0x99
        radio._mmap = self.driver.ga510.memmap.MemoryMapBytes(bytes(edited))

        radio.sync_out()

        writes = [write for write in pipe.writes if write[:1] == b"W"]
        self.assertEqual(len(writes), 5 * 64)
        self.assertEqual(
            writes[0][:5],
            command_with_size(0x57, 0x1000, 0x40),
        )
        self.assertEqual(
            pipe.physical[0x1000:0x1010],
            edited[0:16],
        )
        self.assertEqual(pipe.physical[0x1FFF], 0x02)


if __name__ == "__main__":
    unittest.main()
