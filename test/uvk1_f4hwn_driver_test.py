"""Offline protocol and image checks for Quansheng F4HWN 6.3 support."""

from collections import deque
import importlib
import importlib.util
import struct
from pathlib import Path
import sys
import unittest


from chirp_test_source import chirp_source


ROOT = Path(__file__).resolve().parent.parent
SOURCE = chirp_source()
PYTHON_VENDOR = ROOT / "assets/python/pyserial-3.5-py2.py3-none-any.whl"

REPORTED_REPLY_PREFIX = bytes.fromhex(
    "ab cd 28 00 "
    "03 69 30 e6 68 a5 45 17 6f 15 a3 76 "
    "3d 30 c7 b0 16 6c 14 e6 2e 91 0d 40 21 35 d5 40"
)


def _load_bridge():
    spec = importlib.util.spec_from_file_location(
        "newchirp_chirp_bridge_uvk1_f4hwn",
        ROOT / "scripts/chirp_bridge.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load chirp_bridge.py")
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


def _wire_reply(body):
    from chirp.drivers import uvk5

    return (
        b"\xab\xcd"
        + struct.pack("<H", len(body))
        + uvk5.xorarr(body)
        + b"\x00\x00\xdc\xba"
    )


class _F4HWNFakeRadio:
    def __init__(self, image, firmware="F4HWN v6.3.0"):
        self.image = bytes(image)
        self.firmware = firmware
        self.timeout = 1.0
        self.chunks = deque()
        self.read_requests = []
        self.write_requests = []
        self.reset_sent = False

    def _queue_reply(self, reply):
        self.chunks.extend([reply[:4], reply[4:-4], reply[-4:]])

    def _reply_to_hello(self):
        payload = (
            self.firmware.encode("ascii").ljust(16, b"\x00")
            + b"\x00" * 20
        )
        body = b"\x15\x05" + struct.pack("<H", len(payload)) + payload
        self._queue_reply(_wire_reply(body))

    def _reply_to_read(self, plain):
        address = struct.unpack("<H", plain[4:6])[0]
        length = plain[6]
        self.read_requests.append((address, length))
        data = self.image[address:address + length]
        data = data.ljust(length, b"\xff")
        payload = (
            struct.pack("<HBB", address, len(data), 0)
            + data
        )
        body = b"\x1c\x05" + struct.pack("<H", len(payload)) + payload
        self._queue_reply(_wire_reply(body))

    def _reply_to_write(self, plain):
        address = struct.unpack("<H", plain[4:6])[0]
        length = plain[6]
        self.write_requests.append(
            (address, bytes(plain[12:12 + length]))
        )
        body = b"\x1e\x05\x04\x00" + struct.pack("<H", address)
        self._queue_reply(_wire_reply(body))

    def write(self, data):
        from chirp.drivers import uvk5

        wire = bytes(data)
        if wire[:2] != b"\xab\xcd" or wire[-2:] != b"\xdc\xba":
            raise AssertionError("malformed request frame")
        body_length = struct.unpack("<H", wire[2:4])[0]
        plain = uvk5.xorarr(wire[4:4 + body_length])
        command = plain[:2]
        if command == b"\x14\x05":
            self._reply_to_hello()
        elif command == b"\x1b\x05":
            self._reply_to_read(plain)
        elif command == b"\x1d\x05":
            self._reply_to_write(plain)
        elif command == b"\xdd\x05":
            self.reset_sent = True
        else:
            raise AssertionError("unexpected command %s" % command.hex())
        return len(wire)

    def read(self, size=1):
        if not self.chunks:
            return b""
        result = bytearray()
        while self.chunks and len(result) < size:
            remaining = size - len(result)
            result.extend(self.chunks.popleft()[:remaining])
        return bytes(result)

    def log(self, _message):
        pass


class UVK1F4HWNDriverTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        bridge = _load_bridge()
        cls.directory = bridge.load_chirp(
            str(SOURCE),
            str(PYTHON_VENDOR),
            str(ROOT / "drivers"),
        )
        cls.uvk5 = importlib.import_module("chirp.drivers.uvk5")
        cls.driver = importlib.import_module(
            "newchirp.drivers.newchirp_uvk5"
        )

    def _image(self):
        from chirp import bitwise, memmap

        image = memmap.MemoryMapBytes(
            b"\xff" * self.driver.F4HWN_MEM_SIZE
        )
        parsed = bitwise.parse(self.driver.F4HWN_MEM_FORMAT, image)
        parsed.channel[0].freq = 14_652_000
        parsed.channel[0].offset = 0
        parsed.channel[0].modulation = 0
        parsed.channel[0].bandwidth = 0
        parsed.channel[0].step = self.driver.F4HWN_STEPS.index(12.5)
        parsed.channel[0].txpower = self.driver.F4HWN_POWER_HIGH
        parsed.channelname[0].name = b"CALL\x00" + b"\x00" * 11
        parsed.ch_attr[0].band = 2
        parsed.ch_attr[0].scanlist = 1
        return bytes(image.get_packed())

    def _radio(self, fake):
        radio = self.driver.QuanshengUVK1F4HWN63(fake)
        radio.status_fn = lambda _status: None
        return radio

    def test_model_is_registered_with_f4hwn_map(self):
        radio_class = self.directory.get_radio(
            "Quansheng_UV-K1_F4HWN_6.3"
        )

        self.assertEqual(
            radio_class.MODEL,
            "UV-K1 (F4HWN 6.3)",
        )
        self.assertEqual(
            radio_class,
            self.driver.QuanshengUVK1F4HWN63,
        )
        radio = radio_class(_F4HWNFakeRadio(self._image()))
        features = radio.get_features()
        self.assertEqual(features.memory_bounds, (1, 1024))
        self.assertEqual(features.valid_modes, ["FM", "NFM", "AM", "NAM", "USB"])
        self.assertFalse(features.has_settings)

    def test_reported_handshake_is_f4hwn_6_3(self):
        firmware = "F4HWN v6.3.0"
        payload = firmware.encode("ascii").ljust(16, b"\x00") + b"\x00" * 20
        body = b"\x15\x05" + struct.pack("<H", len(payload)) + payload
        reply = _wire_reply(body)

        self.assertTrue(reply.startswith(REPORTED_REPLY_PREFIX))
        radio = _F4HWNFakeRadio(self._image())
        radio._queue_reply(reply)
        self.assertEqual(
            self.driver._f4hwn_sayhello(radio),
            "F4HWN v6.3.0",
        )

    def test_stock_uvk1_selection_routes_f4hwn_firmware(self):
        stock_class = self.directory.get_radio("Quansheng_UV-K1")
        f4hwn_fake = _F4HWNFakeRadio(self._image())
        detected = stock_class.detect_from_serial(f4hwn_fake)
        self.assertIs(detected, self.driver.QuanshengUVK1F4HWN63)

        stock_fake = _F4HWNFakeRadio(
            self._image(),
            firmware="7.03.05",
        )
        detected_stock = stock_class.detect_from_serial(stock_fake)
        self.assertIs(detected_stock, stock_class)

    def test_download_and_decode_first_channel(self):
        radio = self._radio(_F4HWNFakeRadio(self._image()))
        radio.sync_in()

        memory = radio.get_memory(1)
        self.assertFalse(memory.empty)
        self.assertEqual(memory.name, "CALL")
        self.assertEqual(memory.freq, 146_520_000)
        self.assertEqual(memory.mode, "FM")
        self.assertEqual(memory.tuning_step, 12.5)
        self.assertEqual(str(memory.power), "HIGH = 5W")
        self.assertEqual(str(memory.extra["scanlists"].value), "List [1]")
        self.assertEqual(
            radio.metadata["f4hwn_firmware"],
            "F4HWN v6.3.0",
        )

    def test_edit_round_trip_preserves_extras(self):
        radio = self._radio(_F4HWNFakeRadio(self._image()))
        radio.sync_in()
        memory = radio.get_memory(1)
        memory.name = "NEWCALL"
        memory.freq = 462_612_500
        memory.duplex = "+"
        memory.offset = 5_000_000
        memory.mode = "NFM"
        memory.power = self.driver.F4HWN_POWER_LEVELS[6]
        memory.extra["txLock"].value = "ON"
        memory.extra["scanlists"].value = "List [3]"
        radio.set_memory(memory)

        decoded = radio.get_memory(1)
        self.assertEqual(decoded.name, "NEWCALL")
        self.assertEqual(decoded.freq, 462_612_500)
        self.assertEqual(decoded.duplex, "+")
        self.assertEqual(decoded.offset, 5_000_000)
        self.assertEqual(decoded.mode, "NFM")
        self.assertEqual(str(decoded.power), "MID = 2W")
        self.assertEqual(str(decoded.extra["txLock"].value), "ON")
        self.assertEqual(str(decoded.extra["scanlists"].value), "List [3]")

    def test_upload_never_writes_calibration(self):
        fake = _F4HWNFakeRadio(self._image())
        radio = self._radio(fake)
        radio.sync_in()
        radio.sync_out()

        self.assertTrue(fake.reset_sent)
        self.assertTrue(fake.write_requests)
        self.assertEqual(
            max(address + len(data)
                for address, data in fake.write_requests),
            self.driver.F4HWN_PROG_SIZE,
        )
        self.assertTrue(all(
            address + len(data) <= self.driver.F4HWN_PROG_SIZE
            for address, data in fake.write_requests
        ))

    def test_saved_image_reopens_with_f4hwn_map(self):
        from chirp import memmap

        radio = self._radio(_F4HWNFakeRadio(self._image()))
        radio.sync_in()
        image = radio.get_mmap().get_packed()
        reopened = self._radio(_F4HWNFakeRadio(self._image()))
        reopened._mmap = memmap.MemoryMapBytes(image)
        reopened.process_mmap()

        self.assertEqual(reopened.get_memory(1).name, "CALL")
        self.assertEqual(reopened.get_memory(1).freq, 146_520_000)

    def test_wrong_firmware_is_rejected_before_read(self):
        fake = _F4HWNFakeRadio(self._image(), firmware="F4HWN v5.4.0")
        radio = self._radio(fake)

        with self.assertRaisesRegex(Exception, "requires F4HWN v6.3.x"):
            radio.sync_in()
        self.assertEqual(fake.read_requests, [])


if __name__ == "__main__":
    unittest.main()
