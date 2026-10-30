"""Offline checks for the TH-D75 echoed-CAT response handling."""

from collections import deque
import importlib
import importlib.util
from pathlib import Path
import subprocess
import sys
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "build_support/chirp-20261023"
PYTHON_VENDOR = ROOT / "assets/python/pyserial-3.5-py2.py3-none-any.whl"


def _load_bridge():
    spec = importlib.util.spec_from_file_location(
        "newchirp_chirp_bridge_thd75",
        ROOT / "scripts/chirp_bridge.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load chirp_bridge.py")
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


class _TextPipe:
    def __init__(self, text):
        self.data = deque(text.encode("ascii"))
        self.writes = []

    def write(self, data):
        self.writes.append(bytes(data))

    def read(self, _size=1):
        if not self.data:
            return b""
        return bytes([self.data.popleft()])


class _ClockTextPipe(_TextPipe):
    """Model an adapter that holds its echo for about one second."""

    def __init__(self, text, delay):
        super().__init__(text)
        self.delay = delay
        self.elapsed = 0.0

    def read(self, size=1):
        self.elapsed += 0.01
        if self.elapsed < self.delay:
            return b""
        return super().read(size)


class THD75DriverTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        bridge = _load_bridge()
        cls.directory = bridge.load_chirp(
            str(SOURCE),
            str(PYTHON_VENDOR),
            str(ROOT / "drivers"),
        )
        cls.radio_class = cls.directory.get_radio("Kenwood_TH-D75")

    def test_newchirp_driver_replaces_bundled_thd75(self):
        self.assertEqual(self.radio_class.__name__, "THD75Radio")
        self.assertEqual(
            self.radio_class.__module__,
            "newchirp.drivers.newchirp_thd75",
        )

    def test_driver_can_replace_bundled_thd75_first(self):
        script = f"""
import importlib.util
import pathlib
import sys
sys.path.insert(0, {str(SOURCE)!r})
from chirp.drivers import thd74
from chirp import directory
assert directory.get_radio("Kenwood_TH-D75") is thd74.THD75Radio
path = pathlib.Path({str(ROOT / "drivers" / "newchirp_thd75.py")!r})
spec = importlib.util.spec_from_file_location("order_check_thd75", path)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
assert directory.get_radio("Kenwood_TH-D75").__name__ == "THD75Radio"
"""
        subprocess.run([sys.executable, "-c", script], check=True)

    def test_echoed_id_is_skipped(self):
        radio = self.radio_class(None)
        radio.pipe = _TextPipe("ID\rID TH-D75\r")

        self.assertEqual(radio.command("ID"), "ID TH-D75")
        self.assertEqual(radio.pipe.writes, [b"ID\r"])

    def test_non_echoed_id_is_returned_normally(self):
        radio = self.radio_class(None)
        radio.pipe = _TextPipe("ID TH-D75\r")

        self.assertEqual(radio.command("ID"), "ID TH-D75")

    def test_delayed_echo_is_skipped_before_accepting_actual_id(self):
        radio = self.radio_class(None)
        radio.pipe = _ClockTextPipe("ID\rID TH-D75\r", delay=1.03)
        driver_module = sys.modules[self.radio_class.__module__]

        with mock.patch.object(
            driver_module.time,
            "monotonic",
            side_effect=lambda: radio.pipe.elapsed,
        ):
            self.assertEqual(radio.command("ID"), "ID TH-D75")
        self.assertEqual(radio.pipe.writes, [b"ID\r"])

    def test_echo_without_radio_reply_times_out(self):
        radio = self.radio_class(None)
        radio.pipe = _ClockTextPipe("ID\r", delay=1.03)
        driver_module = sys.modules[self.radio_class.__module__]

        with mock.patch.object(
            driver_module.time,
            "monotonic",
            side_effect=lambda: radio.pipe.elapsed,
        ):
            self.assertEqual(radio.command("ID"), "")
        self.assertGreaterEqual(radio.pipe.elapsed, 2.0)

    def test_trace_shows_unexpected_id_reply_text(self):
        bridge = _load_bridge()
        trace = bridge.RadioCommunicationTrace()

        trace.begin(b"ID\r")
        trace.received(b"ID\r")

        self.assertIn("reply=ID", trace.format())


if __name__ == "__main__":
    unittest.main()
