"""Offline checks for the UV-5RM Plus OEM handshake retry."""

from collections import deque
import importlib
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
        "newchirp_chirp_bridge_uv5rm_plus",
        ROOT / "scripts/chirp_bridge.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load chirp_bridge.py")
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


class _SequenceSerial:
    def __init__(self, replies):
        self.replies = deque(replies)
        self.timeout = 1.5
        self.writes = []

    def read(self, size):
        if size == 256:
            return b""
        if not self.replies:
            return b""
        return self.replies.popleft()[:size]

    def write(self, data):
        self.writes.append(bytes(data))


class UV5RMPlusHandshakeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        bridge = _load_bridge()
        cls.bridge = bridge
        cls.directory = bridge.load_chirp(
            str(SOURCE),
            str(PYTHON_VENDOR),
            str(ROOT / "drivers"),
        )
        cls.radio_module = importlib.import_module(
            "chirp.drivers.baofeng_uv17Pro"
        )
        cls.compat = importlib.import_module(
            "newchirp.drivers.newchirp_uv5rm_plus"
        )

    def test_retries_stray_byte_like_official_cps(self):
        serial = _SequenceSerial([
            b"\x05",
            b"\x06",
            b"F" * 16,
            b"M" * 15,
            b"\x06",
        ])
        radio = self.radio_module.BaofengUV5RMPlus(serial)

        with mock.patch.object(self.compat.time, "sleep") as sleep:
            self.assertTrue(self.radio_module._do_ident(radio))

        sleep.assert_called_once_with(self.compat.RETRY_DELAY)
        self.assertEqual(serial.writes[:2], [
            b"PROGRAMBFNORMALU",
            b"PROGRAMBFNORMALU",
        ])

    def test_does_not_retry_other_handshake_failures(self):
        serial = _SequenceSerial([])
        radio = self.radio_module.BaofengUV5RMPlus(serial)

        with self.assertRaisesRegex(Exception, "No response"):
            self.radio_module._do_ident(radio)

        self.assertEqual(serial.writes, [b"PROGRAMBFNORMALU"])

    def test_unprogrammed_pttid_is_exposed_as_off(self):
        radio = self.bridge.radio_from_image(
            self.directory,
            "Baofeng_UV-5RM_Plus",
            str(SOURCE / "tests/images/Baofeng_UV-5RM_Plus.img"),
        )
        radio._memobj.memory[0].pttid = 0xFF

        memory = radio.get_memory(1)
        pttid = next(
            setting
            for setting in memory.extra
            if setting.get_name() == "pttid"
        )

        self.assertEqual(str(pttid.value), "Off")
        self.assertEqual(int(radio._memobj.memory[0].pttid), 0)


if __name__ == "__main__":
    unittest.main()
