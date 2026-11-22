"""Offline checks for the UV-5R Mini block-read retry (OEM CPS policy)."""

from collections import deque
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest import mock

from chirp_test_source import chirp_source


ROOT = Path(__file__).resolve().parent.parent
SOURCE = chirp_source()
PYTHON_VENDOR = ROOT / "assets/python/pyserial-3.5-py2.py3-none-any.whl"


def _load_bridge():
    spec = importlib.util.spec_from_file_location(
        "newchirp_chirp_bridge_uv5r_mini",
        ROOT / "scripts/chirp_bridge.py",
    )
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


class FakeMiniSerial:
    """Answers R <hi> <lo> 40 with 68 bytes; can drop chosen replies."""

    def __init__(self, drops=None):
        self.timeout = 1
        self.drops = dict(drops or {})
        self.requests = []
        self._rx = deque()

    def write(self, data):
        data = bytes(data)
        if data[:1] == b"R" and len(data) == 4:
            addr = (data[1] << 8) | data[2]
            self.requests.append(addr)
            if self.drops.get(addr, 0):
                self.drops[addr] -= 1
                return len(data)
            self._rx.extend(b"R" + data[1:4] + bytes([addr >> 8 & 0xFF]) * 64)
        return len(data)

    def read(self, size=1):
        out = bytearray()
        while self._rx and len(out) < size:
            out.append(self._rx.popleft())
        return bytes(out)

    def log(self, _message):
        pass


class UV5RMiniDriverTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        bridge = _load_bridge()
        cls.bridge = bridge
        cls.directory = bridge.load_chirp(
            str(SOURCE),
            str(PYTHON_VENDOR),
            str(ROOT / "drivers"),
        )
        cls.radio_class = cls.directory.get_radio("Baofeng_UV-5R_Mini")
        cls.stock = sys.modules[cls.radio_class.__module__]

    def _download(self, serial):
        radio = self.radio_class(None)
        radio.pipe = serial
        radio.status_fn = lambda _status: None
        with mock.patch.object(self.stock, "_do_ident", return_value=True), \
                mock.patch("time.sleep", return_value=None):
            return radio.download_function()

    def test_full_read_walks_the_cps_address_map(self):
        serial = FakeMiniSerial()
        data = self._download(serial)

        self.assertEqual(len(data), 0x8240)
        self.assertEqual(serial.requests[0], 0x0000)
        self.assertEqual(serial.requests[513], 0x9000)
        self.assertEqual(serial.requests[514], 0xA000)
        self.assertEqual(serial.requests[-1], 0xA1C0 - 0x40)

    def test_unanswered_block_is_requested_again(self):
        # 2026-11-21 report: ~75 blocks read, then one request got no reply
        # and stock CHIRP abandoned the read. The CPS resends it.
        serial = FakeMiniSerial(drops={0x12C0: 2})
        data = self._download(serial)

        self.assertEqual(len(data), 0x8240)
        self.assertEqual(serial.requests.count(0x12C0), 3)

    def test_gives_up_after_the_cps_retry_limit_and_names_the_block(self):
        serial = FakeMiniSerial(drops={0x12C0: 99})
        with self.assertRaisesRegex(Exception, "block 0x12C0 after 6"):
            self._download(serial)
        self.assertEqual(serial.requests.count(0x12C0), 6)

    def test_block_failure_is_not_replaced_by_the_port_checklist(self):
        serial = FakeMiniSerial(drops={0x12C0: 99})
        with self.assertRaises(Exception) as raised:
            self._download(serial)
        message = self.bridge.bridge_error_message(
            raised.exception, command="download", model="Baofeng_UV-5R_Mini"
        )
        self.assertIn("stopped answering at memory block 0x12C0", message)
        self.assertNotIn("Confirm the selected port", message)

    def test_5rm_no_response_gets_the_port_checklist(self):
        from chirp import errors

        message = self.bridge.bridge_error_message(
            errors.RadioNoResponse(), command="download", model="Baofeng_5RM"
        )
        self.assertTrue(message.startswith("No response from the 5RM."))
        self.assertIn("Confirm the selected port", message)

    def test_uv5g_mini_keeps_the_stock_read(self):
        radio_class = self.directory.get_radio("Baofeng_UV-5G_Mini")
        radio = radio_class(None)
        radio.pipe = FakeMiniSerial(drops={0x0000: 1})
        radio.status_fn = lambda _status: None
        with mock.patch.object(self.stock, "_do_ident", return_value=True):
            with self.assertRaises(Exception):
                radio.download_function()


if __name__ == "__main__":
    unittest.main()
