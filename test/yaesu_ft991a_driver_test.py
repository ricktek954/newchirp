"""Offline tests for the Yaesu FT-991A live CAT driver."""

from collections import deque
import importlib.util
from pathlib import Path
import struct
import sys
import unittest

from chirp_test_source import chirp_source


ROOT = Path(__file__).resolve().parent.parent
SOURCE = chirp_source()
VENDOR = ROOT / "assets/python/pyserial-3.5-py2.py3-none-any.whl"


def _load_bridge():
    spec = importlib.util.spec_from_file_location(
        "newchirp_chirp_bridge_ft991a",
        ROOT / "scripts/chirp_bridge.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load chirp_bridge.py")
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


def _record_pairs(name=b"VK3REG      ", frequency=146_650_000):
    return {
        0x3249: 0x0500,
        0x324B: 0x0080,
        0x324D: 0x0000,
        0x324F: 0x0100,
        0x3251: 0x0350,
        0x3253: 0x0440,
        0x3255: 0x001E,
        0x3257: 0x0096,
        0x3259: 0x080D,
        0x325B: 0x0000,
        0x325D: 0x0540,
        0x328F: 0x0C00,
        0x3291: 0x0000,
        0x3293: 0x0000,
        0x3295: (frequency >> 16) & 0xFFFF,
        0x3297: frequency & 0xFFFF,
        0x3299: 0x0000,
        0x329B: 0x0000,
        0x329D: int.from_bytes(name[0:2], "big"),
        0x329F: int.from_bytes(name[2:4], "big"),
        0x32A1: int.from_bytes(name[4:6], "big"),
        0x32A3: int.from_bytes(name[6:8], "big"),
        0x32A5: int.from_bytes(name[8:10], "big"),
        0x32A7: int.from_bytes(name[10:12], "big"),
    }


class FakeFT991ASerial:
    def __init__(self, pairs=None):
        self.pairs = dict(pairs or {})
        self.timeout = 0.35
        self.baudrate = 38400
        self.writes = []
        self.responses = deque()

    def write(self, data):
        self.writes.append(bytes(data))
        if data == b"ID;":
            self.responses.append(b"ID0670;")
            return len(data)
        if data == b"AI0;":
            self.responses.append(b"AI0;")
            return len(data)
        body = data[:-2]
        if data[:3] == b"SPR" and len(data) == 7:
            if data[-2] != sum(body) & 0xFF:
                self.responses.append(b"?;")
                return len(data)
            address = struct.unpack(">H", data[3:5])[0]
            first, second = divmod(self.pairs.get(address, 0), 0x100)
            checksum = (sum(body) + first + second) & 0xFF
            self.responses.append(
                body + bytes((first, second, checksum)) + b";"
            )
            return len(data)
        if data[:3] == b"SPW" and len(data) == 9:
            if data[-2] != sum(body) & 0xFF:
                self.responses.append(b"?;")
                return len(data)
            address = struct.unpack(">H", data[3:5])[0]
            self.pairs[address] = data[5] << 8 | data[6]
            self.responses.append(b"A;")
            return len(data)
        self.responses.append(b"?;")
        return len(data)

    def read(self, size):
        if not self.responses:
            return b""
        response = self.responses[0]
        chunk = response[:size]
        if len(chunk) == len(response):
            self.responses.popleft()
        else:
            self.responses[0] = response[size:]
        return chunk

    def reset_input_buffer(self):
        self.responses.clear()

    def close(self):
        pass


class YaesuFT991ADriverTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        bridge = _load_bridge()
        cls.directory = bridge.load_chirp(
            str(SOURCE),
            str(VENDOR),
            str(ROOT / "drivers"),
        )
        cls.bridge = bridge
        cls.radio_class = cls.directory.get_radio("Yaesu_FT-991A")

    def _pairs(self):
        pairs = {0x3229: 0x0100, 0x3239: 0x0100}
        pairs.update(_record_pairs())
        return pairs

    def test_driver_is_registered_as_experimental_live_cat(self):
        from chirp import chirp_common

        self.assertTrue(issubclass(self.radio_class, chirp_common.LiveRadio))
        self.assertTrue(
            issubclass(self.radio_class, chirp_common.ExperimentalRadio)
        )
        self.assertEqual(self.radio_class.MODEL, "FT-991A")

    def test_identifies_ft991a_and_decodes_captured_channel(self):
        serial = FakeFT991ASerial(self._pairs())
        radio = self.radio_class(serial)

        memory = radio.get_memory(1)

        self.assertEqual(memory.freq, 146_650_000)
        self.assertEqual(memory.name, "VK3REG")
        self.assertEqual(memory.mode, "FM")
        self.assertEqual(memory.duplex, "")
        self.assertEqual(memory.tmode, "")

    def test_edit_preserves_unknown_neighbor_bytes(self):
        serial = FakeFT991ASerial(self._pairs())
        radio = self.radio_class(serial)
        memory = radio.get_memory(1)
        memory.freq = 147_000_000
        memory.name = "TEST"
        memory.mode = "USB"
        memory.skip = "S"
        memory.duplex = "+"
        memory.offset = 600_000

        radio.set_memory(memory)
        reread = radio.get_memory(1)

        self.assertEqual(reread.freq, 147_000_000)
        self.assertEqual(reread.name, "TEST")
        self.assertEqual(reread.mode, "USB")
        self.assertEqual(reread.skip, "S")
        self.assertEqual(reread.duplex, "+")
        self.assertEqual(reread.offset, 600_000)
        self.assertEqual(serial.pairs[0x3249], 0x0101)
        self.assertEqual(serial.pairs[0x324B], 0x2280)

    def test_headless_live_adapter_round_trips_known_fields(self):
        serial = FakeFT991ASerial(self._pairs())
        radio = self.radio_class(serial)
        adapter = self.bridge.headless_live_adapter(radio)
        adapter.status_fn = lambda _status: None

        adapter.sync_in()
        memory = adapter.get_memory(1)
        memory.freq = 145_500_000
        memory.name = "ADAPTER"
        adapter.set_memory(memory)
        adapter.sync_out()

        reread = radio.get_memory(1)
        self.assertEqual(reread.freq, 145_500_000)
        self.assertEqual(reread.name, "ADAPTER")

    def test_ctcss_uses_yaesu_tone_table(self):
        serial = FakeFT991ASerial(self._pairs())
        radio = self.radio_class(serial)
        memory = radio.get_memory(1)
        memory.tmode = "Tone"
        memory.rtone = 100.0

        radio.set_memory(memory)
        reread = radio.get_memory(1)

        self.assertEqual(reread.tmode, "Tone")
        self.assertEqual(reread.rtone, 100.0)
        self.assertEqual(serial.pairs[0x328F] >> 8, 12)

    def test_erase_only_clears_visibility(self):
        serial = FakeFT991ASerial(self._pairs())
        radio = self.radio_class(serial)

        radio.erase_memory(1)

        self.assertTrue(radio.get_memory(1).empty)
        self.assertEqual(serial.pairs[0x3249], 0x0500)

    def test_bad_spr_checksum_fails_closed(self):
        serial = FakeFT991ASerial(self._pairs())
        radio = self.radio_class(serial)
        original_write = serial.write

        def corrupt_write(data):
            result = original_write(data)
            if data[:3] == b"SPR" and serial.responses:
                response = bytearray(serial.responses.pop())
                response[7] ^= 0xFF
                serial.responses.append(bytes(response))
            return result

        serial.write = corrupt_write

        with self.assertRaisesRegex(Exception, "checksum mismatch"):
            radio.get_memory(1)


if __name__ == "__main__":
    unittest.main()
