"""Offline replay tests for the CPS-derived Radioddity DB25-G driver."""

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


def _load_bridge():
    spec = importlib.util.spec_from_file_location(
        "newchirp_chirp_bridge_db25g",
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

from chirp import errors  # noqa: E402
from chirp.drivers import btech  # noqa: E402

db25g = sys.modules["newchirp.drivers.newchirp_db25g"]
db25g.time.sleep = lambda *_args, **_kwargs: None


def _identity(fingerprint=b"VC7062"):
    response = bytearray(b"\xFF" * db25g.IDENT_SIZE)
    response[0] = 0x06
    response[12:18] = fingerprint
    response[-2] = 0x55
    return bytes(response)


class FakeDB25GSerial:
    def __init__(
        self,
        image=None,
        *,
        silent_handshakes=0,
        fragmented=False,
        bad_read_ack=False,
        bad_write_ack=False,
        wrong_read_address=False,
    ):
        self.image = bytearray(
            image if image is not None else b"\xFF" * btech.MEM_SIZE
        )
        self.baudrate = 9600
        self.timeout = 1.5
        self.parity = "N"
        self.silent_handshakes = silent_handshakes
        self.fragmented = fragmented
        self.bad_read_ack = bad_read_ack
        self.bad_write_ack = bad_write_ack
        self.wrong_read_address = wrong_read_address
        self.writes = []
        self.read_addresses = []
        self.write_addresses = []
        self._responses = bytearray()

    def _queue(self, data):
        self._responses.extend(data)

    def write(self, data):
        data = bytes(data)
        self.writes.append(data)
        if data == btech.MSTRING_KT8900D:
            if self.silent_handshakes:
                self.silent_handshakes -= 1
            else:
                self._queue(_identity())
            return len(data)
        if len(data) not in (5, 21) or data[:1] != b"\x06":
            raise AssertionError("Unexpected DB25-G write: %s" % data.hex())
        command, address, length = struct.unpack(">BHB", data[1:5])
        if command == ord("S"):
            self.read_addresses.append(address)
            returned_address = address ^ 1 if self.wrong_read_address else address
            ack = 0x00 if self.bad_read_ack else 0x06
            self._queue(
                bytes((ack, ord("X")))
                + struct.pack(">HB", returned_address, length)
                + self.image[address:address + length]
            )
        elif command == ord("X") and len(data) == length + 5:
            self.write_addresses.append(address)
            self.image[address:address + length] = data[5:]
            self._queue(b"\x00" if self.bad_write_ack else b"\x06")
        else:
            raise AssertionError("Unexpected DB25-G command: %02x" % command)
        return len(data)

    def read(self, size):
        if not self._responses:
            return b""
        take = min(size, 7 if self.fragmented else size, len(self._responses))
        result = bytes(self._responses[:take])
        del self._responses[:take]
        return result

    def reset_input_buffer(self):
        self._responses.clear()


class DB25GDriverTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.radio_class = directory.get_radio("Radioddity_DB25-G")

    def setUp(self):
        self.old_ident_timeout = db25g.IDENT_TIMEOUT
        self.old_read_timeout = db25g.READ_TIMEOUT
        db25g.IDENT_TIMEOUT = 0.01
        db25g.READ_TIMEOUT = 0.01

    def tearDown(self):
        db25g.IDENT_TIMEOUT = self.old_ident_timeout
        db25g.READ_TIMEOUT = self.old_read_timeout

    def _radio(self, serial):
        radio = self.radio_class(serial)
        radio.status_fn = lambda _status: None
        return radio

    def test_registration_and_oem_handshake(self):
        self.assertEqual(self.radio_class.__name__, "DB25G")
        self.assertEqual(
            self.radio_class.__module__,
            "newchirp.drivers.newchirp_db25g",
        )
        self.assertFalse(self.radio_class.WANTS_DTR)
        self.assertFalse(self.radio_class.WANTS_RTS)
        self.assertFalse(self.radio_class.HARDWARE_FLOW)
        self.assertFalse(self.radio_class.XON_XOFF)
        serial = FakeDB25GSerial()
        radio = self._radio(serial)

        radio.sync_in()

        self.assertEqual(serial.writes[0], b"\x55\x20\x16\x08\x01\xFF\xDC\x02")
        self.assertEqual(serial.read_addresses[0], 0)
        self.assertEqual(serial.read_addresses[-1], btech.MEM_SIZE - 64)
        self.assertEqual(len(serial.read_addresses), btech.MEM_SIZE // 64)

    def test_handshake_retries_like_the_official_cps(self):
        serial = FakeDB25GSerial(silent_handshakes=2)
        radio = self._radio(serial)

        radio.sync_in()

        magic = [
            write for write in serial.writes
            if write == btech.MSTRING_KT8900D
        ]
        self.assertEqual(len(magic), 3)

    def test_fragmented_read_is_accumulated(self):
        image = bytearray(b"\x00" * btech.MEM_SIZE)
        image[0:64] = bytes(range(64))
        serial = FakeDB25GSerial(image, fragmented=True)
        radio = self._radio(serial)

        radio.sync_in()

        self.assertEqual(radio._mmap.get(0, 64), bytes(range(64)))

    def test_inherited_db25g_layout_decodes_a_channel(self):
        image = bytearray(b"\xFF" * btech.MEM_SIZE)
        image[0:16] = b"\x00" * 16
        image[0:4] = b"\x50\x62\x25\x46"
        image[4:8] = b"\x50\x62\x25\x46"
        image[0x1000:0x1008] = b"FRS 1   "
        serial = FakeDB25GSerial(image)
        radio = self._radio(serial)

        radio.sync_in()
        radio.get_features()
        memory = radio.get_memory(0)

        self.assertFalse(memory.empty)
        self.assertEqual(memory.freq, 462_562_500)
        self.assertEqual(memory.name.rstrip(), "FRS 1")

    def test_missing_block_ack_is_reported(self):
        serial = FakeDB25GSerial(bad_read_ack=True)
        radio = self._radio(serial)

        with self.assertRaisesRegex(errors.RadioError, "did not acknowledge"):
            radio.sync_in()

    def test_wrong_block_address_is_reported(self):
        serial = FakeDB25GSerial(wrong_read_address=True)
        radio = self._radio(serial)

        with self.assertRaisesRegex(errors.RadioError, "mismatched block header"):
            radio.sync_in()

    def test_silent_handshake_reports_retry_guidance(self):
        serial = FakeDB25GSerial(silent_handshakes=db25g.IDENT_ATTEMPTS)
        radio = self._radio(serial)

        with self.assertRaises(errors.RadioNoResponse) as raised:
            radio.sync_in()

        self.assertIn("after 4 attempts", str(raised.exception))
        self.assertIn("official CPS retries", str(raised.exception))
        self.assertEqual(
            [
                write for write in serial.writes
                if write == btech.MSTRING_KT8900D
            ],
            [btech.MSTRING_KT8900D] * db25g.IDENT_ATTEMPTS,
        )

    def test_write_uses_all_784_sixteen_byte_oem_blocks(self):
        from chirp import memmap

        image = bytearray(b"\xFF" * btech.MEM_SIZE)
        image[0:16] = bytes(range(16))
        serial = FakeDB25GSerial()
        radio = self.radio_class(memmap.MemoryMapBytes(bytes(image)))
        radio.pipe = serial
        radio.status_fn = lambda _status: None

        radio.sync_out()

        self.assertEqual(len(serial.write_addresses), 784)
        self.assertEqual(serial.write_addresses[0], 0)
        self.assertEqual(serial.write_addresses[-1], 0x30F0)
        self.assertEqual(serial.image[0:16], bytes(range(16)))

    def test_missing_write_ack_is_reported(self):
        from chirp import memmap

        image = bytes(b"\xFF" * btech.MEM_SIZE)
        serial = FakeDB25GSerial(bad_write_ack=True)
        radio = self.radio_class(memmap.MemoryMapBytes(image))
        radio.pipe = serial
        radio.status_fn = lambda _status: None

        with self.assertRaisesRegex(errors.RadioError, "did not acknowledge write"):
            radio.sync_out()
