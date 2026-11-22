"""Offline checks for RT22 identification (Retevis programmer rule)."""

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
        "newchirp_chirp_bridge_rt22",
        ROOT / "scripts/chirp_bridge.py",
    )
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


class FakeRT22Serial:
    """Answers PROGRGS with 06, 02 with an 8-byte ID, 06 with 06, 07 with N."""

    def __init__(self, ident):
        self.ident = ident
        self.writes = bytearray()
        self._rx = deque()

    def write(self, data):
        data = bytes(data)
        self.writes.extend(data)
        if self.writes.endswith(b"PROGRGS"):
            self._rx.extend(b"\x06")
        elif data == b"\x02":
            self._rx.extend(self.ident)
        elif data == b"\x06":
            self._rx.extend(b"\x06")
        elif data == b"\x07":
            self._rx.extend(b"\x4e")
        return len(data)

    def read(self, size=1):
        out = bytearray()
        while self._rx and len(out) < size:
            out.append(self._rx.popleft())
        return bytes(out)


class RetevisRT22DriverTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        bridge = _load_bridge()
        cls.directory = bridge.load_chirp(
            str(SOURCE),
            str(PYTHON_VENDOR),
            str(ROOT / "drivers"),
        )
        cls.radio_class = cls.directory.get_radio("Retevis_RT22")
        cls.module = sys.modules[cls.radio_class.__module__]

    def _enter(self, model_id, ident):
        radio = self.directory.get_radio(model_id)(None)
        radio.pipe = FakeRT22Serial(ident)
        with mock.patch("time.sleep", return_value=None):
            return self.module._rt22_enter_programming_mode(radio)

    def test_override_is_installed(self):
        self.assertTrue(hasattr(
            self.module._rt22_enter_programming_mode, "newchirp_original"))

    def test_known_ids_still_work(self):
        self.assertEqual(
            self._enter("Retevis_RT22", b"P32073\xf8\xff"),
            b"P32073\xf8\xff",
        )

    def test_new_rt22_id_is_accepted_like_the_retevis_software(self):
        # 2026-11-21 report: 2025 RT22 units return an ID CHIRP doesn't list.
        ident = bytes.fromhex("5033323037a1f8ff")
        self.assertEqual(self._enter("Retevis_RT22", ident), ident)

    def test_short_id_reports_the_bytes(self):
        with self.assertRaisesRegex(Exception, "got 5 .*50 33 32 30 37"):
            self._enter("Retevis_RT22", b"P3207")

    def test_other_family_models_keep_chirps_id_list(self):
        with self.assertRaisesRegex(Exception, "identification failed"):
            self._enter("Retevis_RT22FRS", bytes.fromhex("5033323037a1f8ff"))


if __name__ == "__main__":
    unittest.main()
