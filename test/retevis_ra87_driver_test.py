"""Offline checks for RA87 download identification (OEM CPS rule)."""

from collections import deque
import importlib.util
from pathlib import Path
import sys
import unittest

from chirp_test_source import chirp_source


ROOT = Path(__file__).resolve().parent.parent
SOURCE = chirp_source()
PYTHON_VENDOR = ROOT / "assets/python/pyserial-3.5-py2.py3-none-any.whl"


def _load_bridge():
    spec = importlib.util.spec_from_file_location(
        "newchirp_chirp_bridge_ra87",
        ROOT / "scripts/chirp_bridge.py",
    )
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


class EchoingRA87Serial:
    """Single-wire cable: every write is echoed before the radio replies."""

    def __init__(self, ident):
        self.ident = ident
        self.writes = []
        self._rx = deque()

    def write(self, data):
        data = bytes(data)
        self.writes.append(data)
        self._rx.extend(data)
        if data == b"PROGRAM":
            self._rx.extend(b"\x06")
        elif data == b"\x02":
            self._rx.extend(self.ident)
        elif data == b"\x06":
            self._rx.extend(b"\x06")
        return len(data)

    def read(self, size=1):
        out = bytearray()
        while self._rx and len(out) < size:
            out.append(self._rx.popleft())
        return bytes(out)


class RetevisRA87DriverTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        bridge = _load_bridge()
        cls.directory = bridge.load_chirp(
            str(SOURCE),
            str(PYTHON_VENDOR),
            str(ROOT / "drivers"),
        )
        cls.radio_class = cls.directory.get_radio("Retevis_RA87")
        cls.module = sys.modules[cls.radio_class.__module__]

    def _handshake(self, ident):
        serial = EchoingRA87Serial(ident)
        radio = self.radio_class(None)
        radio.pipe = serial
        self.module._enter_programming_mode_download(radio)
        return serial

    def test_override_is_installed(self):
        self.assertTrue(
            hasattr(
                self.module._enter_programming_mode_download,
                "newchirp_original",
            )
        )

    def test_known_fingerprints_still_identify(self):
        for ident in (
            bytes.fromhex("ffffffffffa52cff"),
            bytes.fromhex("ffffffffffa526ff"),
        ):
            serial = self._handshake(ident)
            self.assertEqual(
                serial.writes,
                [b"PROGRAM", b"\x02", b"\x06", b"\x06"],
            )

    def test_new_ident_with_uhf_model_byte_is_accepted(self):
        # 2026-11-21 report: an RA87 returned an 8-byte ident matching
        # neither captured fingerprint. The OEM CPS accepts any 8 bytes
        # (RX VA x8) and checks only the 0x1F05 model byte.
        self._handshake(bytes.fromhex("ffffffffffa531ff"))
        self._handshake(bytes.fromhex("0102ffffffa5ffff"))

    def test_other_band_versions_are_refused_by_name(self):
        for model, band in ((0x5A, "134-176 MHz"), (0x79, "340-400 MHz")):
            ident = bytes.fromhex("ffffffffff") + bytes((model, 0x2C, 0xFF))
            with self.assertRaisesRegex(Exception, band):
                self._handshake(ident)

    def test_unknown_model_byte_reports_the_reply(self):
        with self.assertRaisesRegex(Exception, "ff ff ff ff ff 11 2c ff"):
            self._handshake(bytes.fromhex("ffffffffff112cff"))

    def test_sample_image_ident_block_holds_the_model_byte(self):
        image = (SOURCE / "tests/images/Retevis_RA87.img").read_bytes()
        self.assertEqual(image[0x1F00:0x1F08], bytes.fromhex("ffffffffffa52cff"))


if __name__ == "__main__":
    unittest.main()
