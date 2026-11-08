"""Offline tests for the selectable read-only BQ-889 transport probe."""

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
        "newchirp_chirp_bridge_bq889",
        ROOT / "scripts/chirp_bridge.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load chirp_bridge.py")
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


class FakeProbeSerial:
    def __init__(self, replies=None):
        self.replies = replies or {}
        self.writes = []
        self.responses = deque()
        self.timeout = 0.25
        self.baudrate = 115200

    def write(self, data):
        data = bytes(data)
        self.writes.append(data)
        command = data.rstrip(b"\r")
        self.responses.append(self.replies.get(command, b""))

    def flush(self):
        pass

    def reset_input_buffer(self):
        pass

    def read(self, _size):
        return self.responses.popleft() if self.responses else b""


class BQ889ProbeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        bridge = _load_bridge()
        cls.directory = bridge.load_chirp(
            str(SOURCE),
            str(PYTHON_VENDOR),
            str(ROOT / "drivers"),
        )
        cls.radio_class = cls.directory.get_radio(
            "Binqi_BQ-889_Analog_Probe"
        )

    def test_catalog_entry_and_read_only_policy(self):
        from chirp import errors, memmap

        self.assertEqual(
            self.directory.get_radio("Binqi_BQ-889_Analog_Probe"),
            self.radio_class,
        )
        radio = self.radio_class(memmap.MemoryMapBytes(b"\xff"))
        self.assertTrue(radio.get_memory(1).empty)
        with self.assertRaisesRegex(errors.RadioError, "read-only"):
            radio.sync_out()

    def test_probe_sends_only_read_commands(self):
        from chirp import errors

        serial = FakeProbeSerial({
            b"AT": b"\r\nOK\r\n",
            b"AT*READVER": b"Release_Version:1.2.3(BQ889)\r\n",
            b"AT+CGMR": b"+CGMR: BQ889-TEST\r\n",
            b"AT+HSQ=R": b"HSQ=1\r\n",
            b"AT+HXTO=R": b"HXTO=40000000\r\n",
            b"AT+HCHDATA=R": b"\x01\x02\x03\x04",
        })
        radio = self.radio_class(serial)
        radio.status_fn = lambda _status: None

        with self.assertRaisesRegex(
            errors.RadioError,
            "read-only probe completed",
        ) as raised:
            radio.sync_in()

        commands = [write.rstrip(b"\r") for write in serial.writes]
        self.assertEqual(
            commands,
            [
                b"AT",
                b"AT*READVER",
                b"AT+CGMR",
                b"AT+HSQ=R",
                b"AT+HXTO=R",
                b"AT+HCHDATA=R",
            ],
        )
        self.assertFalse(
            any(
                command.endswith(b"=")
                or b"=W" in command
                or b"SET" in command.upper()
                for command in commands
            )
        )
        path = str(raised.exception).split("Full transcript: ", 1)[1]
        transcript = Path(path.splitlines()[0])
        self.addCleanup(transcript.unlink, missing_ok=True)
        text = transcript.read_text(encoding="utf-8")
        self.assertIn("TX: AT+HCHDATA=R", text)
        self.assertIn("RX: \\x01\\x02\\x03\\x04", text)

    def test_no_AT_response_is_reported_without_further_commands(self):
        from chirp import errors

        serial = FakeProbeSerial()
        radio = self.radio_class(serial)
        radio.status_fn = lambda _status: None

        with self.assertRaisesRegex(
            errors.RadioNoResponse,
            "No radio write was attempted",
        ) as raised:
            radio.sync_in()

        self.assertTrue(serial.writes)
        self.assertEqual(
            {write.rstrip(b"\r") for write in serial.writes},
            {b"AT"},
        )
        path = str(raised.exception).split("transcript at ", 1)[1]
        transcript = Path(path.splitlines()[0].rstrip("."))
        self.addCleanup(transcript.unlink, missing_ok=True)
        self.assertTrue(transcript.is_file())


if __name__ == "__main__":
    unittest.main()
