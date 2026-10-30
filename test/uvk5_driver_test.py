"""Offline checks for UV-K5 firmware identification retries."""

from collections import deque
import importlib
import importlib.util
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "build_support/chirp-20261023"
PYTHON_VENDOR = ROOT / "assets/python/pyserial-3.5-py2.py3-none-any.whl"


def _load_bridge():
    spec = importlib.util.spec_from_file_location(
        "newchirp_chirp_bridge_uvk5",
        ROOT / "scripts/chirp_bridge.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load chirp_bridge.py")
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


def _reply(body):
    from chirp.drivers import uvk5

    encoded = uvk5.xorarr(body)
    return (
        b"\xab\xcd"
        + bytes([len(body), 0])
        + encoded
        + b"\x00\x00\xdc\xba"
    )


class _SequenceSerial:
    def __init__(self, replies):
        self.chunks = deque()
        for reply in replies:
            self.chunks.extend([
                reply[:4],
                reply[4:-4],
                reply[-4:],
            ])
        self.writes = []

    def write(self, data):
        self.writes.append(bytes(data))

    def log(self, _message):
        pass

    def read(self, size):
        if not self.chunks:
            return b""
        return self.chunks.popleft()[:size]


class UVK5DriverTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        bridge = _load_bridge()
        cls.directory = bridge.load_chirp(
            str(SOURCE),
            str(PYTHON_VENDOR),
            str(ROOT / "drivers"),
        )
        cls.uvk5 = importlib.import_module("chirp.drivers.uvk5")
        cls.retry_driver = importlib.import_module(
            "newchirp.drivers.newchirp_uvk5"
        )

    def test_newchirp_hello_retry_is_loaded(self):
        self.assertTrue(
            getattr(self.uvk5._sayhello, "newchirp_hello_retry", False)
        )

    def test_hello_retries_after_reply_without_printable_firmware(self):
        serial = _SequenceSerial([
            _reply(b"\x00\x00\x00\x00"),
            _reply(b"\x00\x00\x00\x00XYZ123"),
        ])

        firmware = self.uvk5._sayhello(serial)

        self.assertEqual(firmware, "XYZ123")
        self.assertEqual(len(serial.writes), 2)

    def test_hello_failure_reports_the_malformed_reply(self):
        bad = _reply(b"\x00\x00\x00\x00")
        serial = _SequenceSerial([bad] * self.retry_driver.HELLO_RETRIES)

        with self.assertRaisesRegex(Exception, r"reply 00 00 00 00"):
            self.uvk5._sayhello(serial)

        self.assertEqual(
            len(serial.writes),
            self.retry_driver.HELLO_RETRIES,
        )

    def test_trace_identifies_uvk5_hello_and_reply_bytes(self):
        bridge = _load_bridge()
        trace = bridge.RadioCommunicationTrace()
        reply = _reply(b"\x00\x00\x00\x00\xde\xad")

        trace.begin(b"\xab\xcd\x08\x00" + b"\x00" * 12)
        trace.received(reply)
        rendered = trace.format()

        self.assertIn("UV-K5 hello | reply=", rendered)
        self.assertIn("ab cd 06 00", rendered)


if __name__ == "__main__":
    unittest.main()
