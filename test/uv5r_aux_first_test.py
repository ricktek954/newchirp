"""Offline checks for the UV-5R aux-first download and the UV-3R retry."""

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
IDENT = bytes.fromhex("aa 30 76 04 00 05 20 dd")


def _load_bridge():
    spec = importlib.util.spec_from_file_location(
        "newchirp_chirp_bridge_uv5r_aux_first",
        ROOT / "scripts/chirp_bridge.py",
    )
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


def _block(addr, size, dropped=False):
    body = bytearray([(addr >> 4) & 0x7F] * size)
    if dropped and addr == 0x1FC0:
        body[15] = 0xFF
    return bytes(body)


class FakeUV5RSerial:
    """Answers S <hi> <lo> <size>. ``refuse_main_to_aux`` reproduces
    INBOX:985: once a channel block (< 0x1800) has been read, a request for
    the settings area gets no reply at all."""

    def __init__(self, refuse_main_to_aux=False, dropped=False):
        self.timeout = 1
        self.refuse = refuse_main_to_aux
        self.dropped = dropped
        self.requests = []
        self._rx = deque()
        self._seen_main = False

    def write(self, data):
        data = bytes(data)
        if data[:1] == b"S" and len(data) == 4:
            addr = (data[1] << 8) | data[2]
            size = data[3]
            first = not self.requests
            self.requests.append((addr, size))
            if addr < 0x1800:
                self._seen_main = True
            elif self.refuse and self._seen_main:
                return len(data)
            if not first:
                self._rx.append(0x06)
            self._rx.extend(b"X" + data[1:4] + _block(addr, size,
                                                     self.dropped))
        return len(data)

    def read(self, size=1):
        out = bytearray()
        while self._rx and len(out) < size:
            out.append(self._rx.popleft())
        return bytes(out)

    def log(self, _message):
        pass


class UV5RAuxFirstTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bridge = _load_bridge()
        cls.directory = cls.bridge.load_chirp(
            str(SOURCE), str(PYTHON_VENDOR), str(ROOT / "drivers"))
        cls.uv5r = sys.modules["chirp.drivers.uv5r"]

    def _download(self, model, serial):
        radio = self.directory.get_radio(model)(None)
        radio.pipe = serial
        radio.status_fn = lambda _status: None
        with mock.patch.object(self.uv5r, "_ident_radio",
                               return_value=IDENT), \
                mock.patch("time.sleep", return_value=None):
            return self.uv5r._do_download(radio)

    def _expected(self, dropped=False):
        data = IDENT
        for addr in range(0, 0x1800, 0x40):
            data += _block(addr, 0x40)
        if dropped:
            for addr in range(0x1EC0, 0x1FC0, 0x40):
                data += _block(addr, 0x40)
            for addr in range(0x1FC0, 0x2000, 0x10):
                data += _block(addr, 0x10, dropped)
        else:
            for addr in range(0x1EC0, 0x2000, 0x40):
                data += _block(addr, 0x40)
        return data

    def test_stock_order_fails_like_the_report(self):
        radio = self.directory.get_radio("Baofeng_UV-5R")(None)
        radio.pipe = FakeUV5RSerial(refuse_main_to_aux=True)
        radio.status_fn = lambda _status: None
        original = self.uv5r._do_download.newchirp_original
        with mock.patch.object(self.uv5r, "_ident_radio",
                               return_value=IDENT), \
                mock.patch("time.sleep", return_value=None):
            with self.assertRaisesRegex(Exception, "second block 0x1ec0"):
                original(radio)

    def test_radio_refusing_the_jump_back_reads_completely(self):
        for model in ("Baofeng_UV-5R", "Baofeng_BF-F8HP",
                      "Radioddity_UV-5RX3"):
            with self.subTest(model=model):
                serial = FakeUV5RSerial(refuse_main_to_aux=True)
                data = self._download(model, serial).get_packed()
                self.assertEqual(data, self._expected())
                addrs = [addr for addr, _size in serial.requests]
                self.assertEqual(addrs[:3], [0x1E80, 0x1EC0, 0x1FC0])
                self.assertLess(addrs.index(0x1FC0, 3), addrs.index(0x0000))

    def test_image_layout_matches_stock_on_a_normal_radio(self):
        stock_serial = FakeUV5RSerial()
        radio = self.directory.get_radio("Baofeng_UV-5R")(None)
        radio.pipe = stock_serial
        radio.status_fn = lambda _status: None
        with mock.patch.object(self.uv5r, "_ident_radio",
                               return_value=IDENT), \
                mock.patch("time.sleep", return_value=None):
            stock = self.uv5r._do_download.newchirp_original(radio)
        our_serial = FakeUV5RSerial()
        ours = self._download("Baofeng_UV-5R", our_serial)
        self.assertEqual(ours.get_packed(), stock.get_packed())
        # Same blocks, only the order changes.
        self.assertEqual(sorted(our_serial.requests),
                         sorted(stock_serial.requests))

    def test_dropped_byte_radio_keeps_the_0x10_tail_reads(self):
        serial = FakeUV5RSerial(refuse_main_to_aux=True, dropped=True)
        data = self._download("Baofeng_UV-5R", serial).get_packed()
        self.assertEqual(data, self._expected(dropped=True))
        self.assertIn((0x1FF0, 0x10), serial.requests)

    def test_image_loads_in_the_driver(self):
        mmap = self._download("Baofeng_UV-5R",
                              FakeUV5RSerial(refuse_main_to_aux=True))
        radio = self.directory.get_radio("Baofeng_UV-5R")(mmap)
        radio.get_memory(1)


class UV3RPrepTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        bridge = _load_bridge()
        bridge.load_chirp(str(SOURCE), str(PYTHON_VENDOR),
                          str(ROOT / "drivers"))
        cls.uv3r = sys.modules["chirp.drivers.baofeng_uv3r"]

    def test_silent_radio_reports_the_handshake_error(self):
        from chirp import errors

        failure = errors.RadioError("Radio did not ACK first command")
        with mock.patch.object(self.uv3r, "_uv3r_prep",
                               side_effect=failure) as prep, \
                mock.patch("time.sleep", return_value=None):
            with self.assertRaisesRegex(errors.RadioError,
                                        "did not ACK first command"):
                self.uv3r.uv3r_download(object())
        self.assertEqual(prep.call_count, 10)


if __name__ == "__main__":
    unittest.main()
