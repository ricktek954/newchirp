"""Offline tests for the CPS-derived Baofeng K67 Pro driver."""

import importlib.util
from pathlib import Path
import struct
import sys
import unittest

from chirp_test_source import chirp_source


ROOT = Path(__file__).resolve().parent.parent
SOURCE = chirp_source()
VENDOR = ROOT / "assets/python/pyserial-3.5-py2.py3-none-any.whl"
DRIVER_ID = "Baofeng_K67_Pro_CPS_V1.1.2"


def _load_bridge():
    spec = importlib.util.spec_from_file_location(
        "newchirp_chirp_bridge_k67pro_test",
        ROOT / "scripts/chirp_bridge.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load chirp_bridge.py")
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


bridge = _load_bridge()
directory = bridge.load_chirp(str(SOURCE), str(VENDOR), str(ROOT / "drivers"))

from chirp import errors  # noqa: E402
from chirp import memmap  # noqa: E402

k67 = sys.modules["newchirp.drivers.newchirp_baofeng_k67pro"]


def _bcd_frequency(frequency):
    return k67._encode_frequency(frequency)


def _image():
    image = bytearray(b"\xff" * k67.MEM_SIZE)
    offset = 0
    image[offset:offset + 8] = (
        _bcd_frequency(146_520_000) + _bcd_frequency(146_520_000)
    )
    image[offset + 8:offset + 12] = b"\x7c\x04\x7c\x04"
    image[offset + 14] = 0x20
    image[offset + 15] = 0x44
    image[offset + 20:offset + 29] = b"K67 TEST\x00"
    return image


class FakeK67Serial:
    def __init__(self):
        self.image = _image()
        self.queue = bytearray()
        self.writes = []
        self.read_addresses = []
        self.sent_f = False

    @property
    def in_waiting(self):
        return len(self.queue)

    def reset_input_buffer(self):
        self.queue.clear()

    def read(self, count):
        data = bytes(self.queue[:count])
        del self.queue[:count]
        return data

    def write(self, data):
        data = bytes(data)
        self.writes.append(data)
        if data == k67.PROGRAM:
            self.queue.extend(b"\x06")
        elif data == b"F":
            self.sent_f = True
            self.queue.extend(
                b"K6PROU".ljust(16, b"\x00")
                + b"1702/06+00000".ljust(15, b"\x00")
            )
        elif data[:1] == k67.READ_COMMAND:
            address, length = struct.unpack(">HB", data[1:])
            self.read_addresses.append(address)
            payload = self.image[address:address + length]
            self.queue.extend(
                k67.READ_COMMAND
                + struct.pack(">HB", address, length)
                + payload
            )
        return len(data)


class BaofengK67ProTest(unittest.TestCase):
    def _radio(self, pipe=None, image=None):
        driver = directory.get_radio(DRIVER_ID)
        if pipe is not None:
            return driver(pipe)
        return driver(memmap.MemoryMapBytes(bytes(image)))

    def test_frequency_raw_vectors(self):
        self.assertEqual(
            k67._decode_frequency(b"\x00\x52\x46\x01"),
            146_520_000,
        )
        self.assertEqual(
            k67._decode_frequency(b"\x50\x97\x22\x01"),
            122_975_000,
        )
        self.assertEqual(
            k67._encode_frequency(146_520_000),
            b"\x00\x52\x46\x01",
        )
        self.assertEqual(
            k67._encode_frequency(122_975_000),
            b"\x50\x97\x22\x01",
        )

    def test_handshake_and_full_read_ranges(self):
        serial = FakeK67Serial()
        radio = self._radio(serial)
        radio.status_fn = lambda _status: None

        radio.sync_in()

        self.assertEqual(serial.writes[0], k67.PROGRAM)
        self.assertTrue(serial.sent_f)
        self.assertEqual(
            directory.get_radio(DRIVER_ID).MODEL,
            "K67 Pro",
        )
        expected = []
        for start, end in k67.READ_RANGES:
            expected.extend(range(start, end, 64))
        self.assertEqual(serial.read_addresses, expected)
        self.assertEqual(serial.writes[-1], b"E")

    def test_channel_decode(self):
        radio = self._radio(image=_image())
        memory = radio.get_memory(1)

        self.assertFalse(memory.empty)
        self.assertEqual(memory.freq, 146_520_000)
        self.assertEqual(memory.duplex, "")
        self.assertEqual(memory.tmode, "TSQL")
        self.assertEqual(memory.ctone, 114.8)
        self.assertEqual(memory.mode, "FM")
        self.assertEqual(memory.name, "K67 TEST")

    def test_airband_channel_decodes_as_am(self):
        image = _image()
        offset = 0
        image[offset:offset + 8] = (
            _bcd_frequency(122_975_000)
            + _bcd_frequency(122_975_000)
        )
        radio = self._radio(image=image)

        self.assertEqual(radio.get_memory(1).mode, "AM")

    def test_dcs_codes_use_cps_table(self):
        image = _image()
        offset = 0
        image[offset + 8:offset + 12] = b"\x01\x00\x01\x00"
        radio = self._radio(image=image)
        memory = radio.get_memory(1)

        self.assertEqual(memory.tmode, "DTCS")
        self.assertEqual(memory.dtcs, 23)
        self.assertEqual(memory.rx_dtcs, 23)

    def test_upload_is_disabled(self):
        radio = self._radio(image=_image())
        with self.assertRaises(errors.RadioError):
            radio.sync_out()

    def test_channel_one_and_one_thousand_use_cps_indexes(self):
        image = _image()
        last_offset = 999 * k67.CHANNEL_SIZE
        image[last_offset:last_offset + 8] = (
            _bcd_frequency(446_000_000) + _bcd_frequency(446_000_000)
        )
        image[last_offset + 20:last_offset + 31] = b"CHANNEL 1000"
        radio = self._radio(image=image)

        self.assertEqual(radio.get_memory(1).name, "K67 TEST")
        self.assertEqual(radio.get_memory(1000).freq, 446_000_000)
        self.assertEqual(radio.get_memory(1000).name, "CHANNEL 1000")


if __name__ == "__main__":
    unittest.main()
