"""Quansheng TK11 upload opens its own session, like the OEM CPS (UID 1044)."""

import importlib.util
from pathlib import Path
import struct
import sys
import unittest
from unittest import mock

from chirp_test_source import chirp_source

ROOT = Path(__file__).resolve().parent.parent
SOURCE = chirp_source()
VENDOR = ROOT / "assets/python/pyserial-3.5-py2.py3-none-any.whl"


def _load_bridge():
    spec = importlib.util.spec_from_file_location(
        "newchirp_chirp_bridge_tk11", ROOT / "scripts/chirp_bridge.py")
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


class FakeTK11:
    """Answers like a TK11: writes only count inside a connected session."""

    def __init__(self, tk11, password=False, refuse_at=None, session=False):
        self.tk11 = tk11
        self.password = password
        self.refuse_at = refuse_at
        self.connected = session
        self.rx = bytearray()
        self.sent = []
        self.written = []
        self.rebooted = False

    def reset_input_buffer(self):
        self.rx.clear()

    def flush(self):
        pass

    def _payload(self, message):
        length = message[2] | (message[3] << 8)
        body = bytearray(message[4:4 + length])
        self.tk11.content_nor_or(body)
        return bytes(body)

    def _reply(self, payload):
        self.rx.extend(self.tk11.encapsulate_message(payload))

    def write(self, message):
        payload = self._payload(bytes(message))
        kind = struct.unpack_from("<H", payload, 0)[0]
        self.sent.append(kind)
        if kind == self.tk11.MessageType.CONNECT_REQUEST:
            self.connected = True
            version = b"5.00.18".ljust(16, b"\0")
            self._reply(struct.pack("<HH", 0x1F5, 52) + version
                        + bytes([1 if self.password else 0, 0, 8, 0])
                        + bytes(32))
        elif kind == self.tk11.MessageType.MEMORY_WRITE_REQUEST:
            address = struct.unpack_from("<I", payload, 4)[0] - 0x80000
            if not self.connected:
                return len(message)            # no session: radio stays silent
            self.written.append(address)
            ok = address != self.refuse_at
            self._reply(struct.pack("<HHI", 0x1FE if ok else 0x1FF, 4, 0))
        elif kind == self.tk11.MessageType.REBOOT_REQUEST:
            self.rebooted = True
        return len(message)

    def read(self, size):
        data = bytes(self.rx[:size])
        del self.rx[:size]
        return data


class TK11UploadTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        directory = _load_bridge().load_chirp(
            str(SOURCE), str(VENDOR), str(ROOT / "drivers"))
        cls.radio_class = directory.get_radio("Quansheng_TK11")
        from chirp.drivers import tk11
        from chirp import memmap
        cls.tk11 = tk11
        cls.memmap = memmap

    def _radio(self, serial):
        radio = self.radio_class(serial)
        radio._mmap = self.memmap.MemoryMapBytes(bytes(0x1000))
        radio.status_fn = lambda _status: None
        return radio

    def test_upload_connects_first_then_writes_every_block_and_reboots(self):
        serial = FakeTK11(self.tk11)
        with mock.patch("time.sleep", return_value=None):
            self._radio(serial).sync_out()
        self.assertEqual(serial.sent[0], self.tk11.MessageType.CONNECT_REQUEST)
        self.assertEqual(serial.written, list(range(0, 0x1000, 0x200)))
        self.assertTrue(serial.rebooted)

    def test_a_refused_block_stops_the_write(self):
        serial = FakeTK11(self.tk11, refuse_at=0x400)
        with mock.patch("time.sleep", return_value=None):
            with self.assertRaisesRegex(Exception, "0x00400"):
                self._radio(serial).sync_out()
        self.assertEqual(serial.written, [0x000, 0x200, 0x400])
        self.assertFalse(serial.rebooted)

    def test_password_protected_radio_is_refused_before_any_write(self):
        serial = FakeTK11(self.tk11, password=True)
        with mock.patch("time.sleep", return_value=None):
            with self.assertRaisesRegex(Exception, "password"):
                self._radio(serial).sync_out()
        self.assertEqual(serial.written, [])

    def test_stock_upload_fails_without_a_session(self):
        # The reported failure: stock do_upload never connects.
        serial = FakeTK11(self.tk11)
        original = self.tk11.do_upload.newchirp_original
        with self.assertRaises(Exception):
            original(self._radio(serial))
        self.assertNotIn(self.tk11.MessageType.CONNECT_REQUEST, serial.sent)


if __name__ == "__main__":
    unittest.main()
