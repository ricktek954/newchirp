"""Offline checks for the Baofeng GM-21 firmware compatibility override."""

from collections import deque
import importlib.util
import sys
import unittest
from pathlib import Path

from chirp_test_source import chirp_source


ROOT = Path(__file__).resolve().parent.parent
SOURCE = chirp_source()
PYTHON_VENDOR = ROOT / "assets/python/pyserial-3.5-py2.py3-none-any.whl"


def _load_bridge():
    spec = importlib.util.spec_from_file_location(
        "newchirp_chirp_bridge_gm21",
        ROOT / "scripts/chirp_bridge.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load chirp_bridge.py")
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


class BaofengGM21DriverTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = _load_bridge().load_chirp(
            str(SOURCE),
            str(PYTHON_VENDOR),
            str(ROOT / "drivers"),
        )
        cls.radio_class = cls.directory.get_radio("Baofeng_GM-21")

    def test_newchirp_driver_replaces_the_pinned_chirp_gm21(self):
        self.assertEqual(
            self.radio_class.__module__,
            "newchirp.drivers.newchirp_baofeng_gm21",
        )

    def test_later_firmware_tries_the_gm5rh_handshake_first(self):
        from chirp.drivers import baofeng_uv17Pro

        self.assertEqual(
            self.radio_class._idents,
            [
                baofeng_uv17Pro.MSTRING_GM5RH,
                baofeng_uv17Pro.MSTRING_UV17PROGPS,
            ],
        )

    def test_gm5rh_profile_uses_the_gm5rh_magic_sequence(self):
        from chirp.drivers import baofeng_uv17Pro

        serial = _SequenceSerial([
            b"\x06",
            b"F" * 16,
            b"M" * 15,
            b"\x06",
        ])
        radio = self.radio_class(serial)

        self.assertTrue(baofeng_uv17Pro._do_ident(radio))
        self.assertEqual(serial.writes[0], baofeng_uv17Pro.MSTRING_GM5RH)
        self.assertEqual(
            serial.writes[1:],
            [magic for magic, _length in baofeng_uv17Pro.GM5RH._magics],
        )
        self.assertEqual(serial.writes[2], b"M")

    def test_gps_fallback_uses_the_gps_magic_sequence(self):
        from chirp.drivers import baofeng_uv17Pro

        serial = _SequenceSerial([
            b"\x05",
            b"\x06",
            b"F" * 16,
            b"M" * 7,
            b"\x06",
        ])
        radio = self.radio_class(serial)

        self.assertTrue(baofeng_uv17Pro._do_ident(radio))
        self.assertEqual(
            serial.writes[:2],
            [
                baofeng_uv17Pro.MSTRING_GM5RH,
                baofeng_uv17Pro.MSTRING_UV17PROGPS,
            ],
        )
        self.assertEqual(
            serial.writes[2:],
            [
                magic
                for magic, _length in baofeng_uv17Pro.UV17ProGPS._magics
            ],
        )


class _SequenceSerial:
    def __init__(self, replies):
        self.replies = deque(replies)
        self.timeout = 1.5
        self.writes = []

    def read(self, size):
        if size == 256 or not self.replies:
            return b""
        return self.replies.popleft()[:size]

    def write(self, data):
        self.writes.append(bytes(data))


if __name__ == "__main__":
    unittest.main()
