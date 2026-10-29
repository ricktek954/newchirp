"""Offline checks for the UV-9R write-acknowledgment retry."""

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
        "newchirp_chirp_bridge_uv9r",
        ROOT / "scripts/chirp_bridge.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load chirp_bridge.py")
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


class UV9RDriverTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        bridge = _load_bridge()
        cls.directory = bridge.load_chirp(
            str(SOURCE),
            str(PYTHON_VENDOR),
            str(ROOT / "drivers"),
        )
        cls.radio_class = cls.directory.get_radio("Baofeng_UV-9R")
        cls.driver = importlib.import_module(cls.radio_class.__module__)

    def test_newchirp_driver_replaces_bundled_uv9r(self):
        self.assertEqual(self.radio_class.__name__, "UV9R")
        self.assertEqual(
            self.radio_class.__module__,
            "newchirp.drivers.newchirp_uv9r",
        )

    def test_retry_resends_identical_write_block_until_ack(self):
        frame = b"X" + bytes.fromhex("000010") + b"\xAA" * 16
        replies = [
            self.driver.errors.RadioNoContactLikelyK1(),
            b"\x00",
            b"\x06",
        ]
        sends = []

        def send(_radio, data):
            sends.append(bytes(data))

        def receive(_radio, _amount):
            reply = replies.pop(0)
            if isinstance(reply, Exception):
                raise reply
            return reply

        ack = self.driver._read_write_ack(
            object(),
            frame,
            send,
            receive,
        )

        self.assertEqual(ack, b"\x06")
        self.assertEqual(sends, [frame, frame])

    def test_failure_names_the_unacknowledged_block(self):
        frame = b"X" + bytes.fromhex("002000") + b"\xAA" * 16

        with self.assertRaisesRegex(
            Exception,
            r"write block 0x0020 after 3 attempts",
        ):
            self.driver._read_write_ack(
                object(),
                frame,
                lambda _radio, _data: None,
                lambda _radio, _amount: b"",
            )


if __name__ == "__main__":
    unittest.main()
