"""Offline checks for NewChirp's DM-32UV handshake retries."""

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
        "newchirp_chirp_bridge_dm32uv",
        ROOT / "scripts/chirp_bridge.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load chirp_bridge.py")
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


class _SequenceSerial:
    def __init__(self, responses):
        self.timeout = 0.5
        self.responses = deque(responses)
        self.writes = []

    def reset_input_buffer(self):
        pass

    def write(self, data):
        self.writes.append(bytes(data))

    def read(self, size):
        if not self.responses:
            return b""
        response = self.responses.popleft()
        return response[:size]


class DM32UVDriverTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        bridge = _load_bridge()
        cls.bridge = bridge
        cls.directory = bridge.load_chirp(
            str(SOURCE),
            str(PYTHON_VENDOR),
            str(ROOT / "drivers"),
        )
        cls.radio_class = cls.directory.get_radio("Baofeng_DM-32UV")
        cls.driver = importlib.import_module(cls.radio_class.__module__)

    def test_newchirp_driver_replaces_bundled_dm32uv(self):
        self.assertEqual(self.radio_class.__name__, "DM32UV")
        self.assertEqual(
            self.radio_class.__module__,
            "newchirp.drivers.newchirp_dm32uv",
        )

    def test_passsta_retries_a_transient_bad_reply(self):
        serial = _SequenceSerial([b"\x06\x00\x00", b"P\x00\x00"])
        link = self.driver.baofeng_dm32uv._Link(serial)

        reply = link.xfer(b"PASSSTA", 3)

        self.assertEqual(reply, b"P\x00\x00")
        self.assertEqual(serial.writes, [b"PASSSTA", b"PASSSTA"])

    def test_link_accumulates_fragmented_replies_without_changing_timeout(self):
        serial = _SequenceSerial([b"\x06", b"\x00", b"\x00"])
        link = self.driver.baofeng_dm32uv._Link(serial)

        reply = link.recv(3)

        self.assertEqual(reply, b"\x06\x00\x00")
        self.assertEqual(serial.timeout, 0.05)

    def test_passsta_failure_reports_the_reply_bytes(self):
        serial = _SequenceSerial([b"\x06\x00\x00"] * 3)
        link = self.driver.baofeng_dm32uv._Link(serial)

        with self.assertRaisesRegex(Exception, r"reply 060000"):
            link.xfer(b"PASSSTA", 3)

        self.assertEqual(len(serial.writes), 3)

    def test_trace_shows_handshake_response_bytes(self):
        trace = self.bridge.RadioCommunicationTrace()

        trace.begin(b"PASSSTA")
        trace.received(b"\x06\x00\x00")
        report = trace.format()

        self.assertIn("reply=06 00 00 (3 bytes)", report)


if __name__ == "__main__":
    unittest.main()
