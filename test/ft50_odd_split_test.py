"""Offline checks for Yaesu FT-50 odd-split channel decoding."""

import importlib
import importlib.util
from pathlib import Path
import sys
import unittest
from types import SimpleNamespace
from unittest import mock


from chirp_test_source import chirp_source


ROOT = Path(__file__).resolve().parent.parent
SOURCE = chirp_source()
PYTHON_VENDOR = ROOT / "assets/python/pyserial-3.5-py2.py3-none-any.whl"
IMAGE = ROOT / "test/fixtures/Yaesu_FT-50_UID_672.img"


def _load_bridge():
    spec = importlib.util.spec_from_file_location(
        "newchirp_chirp_bridge_ft50_test",
        ROOT / "scripts/chirp_bridge.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load chirp_bridge.py")
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


class FT50OddSplitTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bridge = _load_bridge()
        cls.directory = cls.bridge.load_chirp(
            str(SOURCE),
            str(PYTHON_VENDOR),
            str(ROOT / "drivers"),
        )
        importlib.import_module("newchirp.drivers.newchirp_ft50_compat")

    def _radio(self):
        return self.bridge.radio_from_image(
            self.directory,
            "Yaesu_FT-50",
            str(IMAGE),
        )

    def test_reporter_image_exposes_odd_split_channels(self):
        radio = self._radio()
        memory = radio.get_memory(6)

        self.assertEqual(memory.freq, 155_700_000)
        self.assertEqual(memory.duplex, "split")
        self.assertEqual(memory.offset, 154_755_000)
        self.assertEqual(memory.tmode, "TSQL")
        self.assertEqual(memory.rtone, 118.8)

    def test_all_active_reporter_channels_decode(self):
        radio = self._radio()
        channels = [
            radio.get_memory(number)
            for number in range(1, 101)
        ]

        self.assertEqual(
            sum(not memory.empty for memory in channels),
            57,
        )
        self.assertEqual(
            [
                memory.number
                for memory in channels
                if memory.duplex == "split"
            ],
            [6, 7, 60, 77, 81, 83, 85, 86, 87, 89],
        )

    def test_split_edit_round_trips_through_stock_encoder(self):
        radio = self._radio()
        memory = radio.get_memory(6)
        memory.name = "TEST"
        memory.offset = 154_830_000
        radio.set_memory(memory)

        updated = radio.get_memory(6)
        self.assertEqual(updated.name, "TEST")
        self.assertEqual(updated.duplex, "split")
        self.assertEqual(updated.offset, 154_830_000)

    def test_features_advertise_odd_split_editing(self):
        features = self._radio().get_features()

        self.assertTrue(features.can_odd_split)
        self.assertIn("split", features.valid_duplexes)

    def test_oem_serial_framing_uses_two_stop_bits(self):
        self.assertEqual(
            self.directory.get_radio("Yaesu_FT-50").SERIAL_STOPBITS,
            2,
        )
        radio_class = SimpleNamespace(
            MODEL="FT-50",
            BAUD_RATE=9600,
            HARDWARE_FLOW=False,
            WANTS_RTS=True,
            WANTS_DTR=True,
            SERIAL_STOPBITS=2,
        )

        with mock.patch("serial.Serial") as serial_constructor:
            self.bridge.open_serial(radio_class, "COM6")

        serial_constructor.assert_called_once_with(
            baudrate=9600,
            rtscts=False,
            xonxoff=False,
            timeout=0.25,
            stopbits=2,
        )


if __name__ == "__main__":
    unittest.main()
