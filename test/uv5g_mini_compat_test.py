"""Offline checks for UV-5G Mini GMRS channel duplex editing."""

import importlib
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
        "newchirp_chirp_bridge_uv5g_mini",
        ROOT / "scripts/chirp_bridge.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load chirp_bridge.py")
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


class UV5GMiniCompatTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bridge = _load_bridge()
        cls.directory = cls.bridge.load_chirp(
            str(SOURCE),
            str(PYTHON_VENDOR),
            str(ROOT / "drivers"),
        )
        cls.driver = importlib.import_module(
            "newchirp.drivers.newchirp_uv5g_mini"
        )
        cls.upstream = importlib.import_module(
            "chirp.drivers.baofeng_uv17Pro"
        )

    def _radio(self):
        return self.bridge.radio_from_image(
            self.directory,
            "Baofeng_UV-5G_Mini",
            str(SOURCE / "tests/images/Baofeng_UV-5G_Mini.img"),
        )

    def test_channels_15_through_22_round_trip_as_simplex_or_repeater(self):
        for number in range(15, 23):
            with self.subTest(channel=number):
                radio = self._radio()
                memory = radio.get_memory(number)

                self.assertEqual(
                    memory.freq,
                    self.upstream.UV5G_GMRS_PRESETS[number - 1],
                )
                self.assertEqual(memory.duplex, "")
                self.assertEqual(memory.offset, 0)
                self.assertEqual(memory.immutable, ["freq"])

                memory.duplex = "+"
                memory.offset = 5_000_000
                radio.set_memory(memory)

                round_tripped = radio.get_memory(number)
                self.assertEqual(
                    round_tripped.freq,
                    self.upstream.UV5G_GMRS_PRESETS[number - 1],
                )
                self.assertEqual(round_tripped.duplex, "+")
                self.assertEqual(round_tripped.offset, 5_000_000)
                self.assertEqual(round_tripped.immutable, ["freq"])

    def test_upload_can_apply_repeater_to_channel_15(self):
        radio = self._radio()
        memory = radio.get_memory(15)
        item = self.bridge.memory_json(memory)
        item["duplex"] = "+"
        item["offset"] = 5

        skipped = self.bridge.apply_json(radio, memory, item)
        radio.set_memory(memory)

        self.assertNotIn("duplex", skipped)
        self.assertNotIn("offset", skipped)
        round_tripped = radio.get_memory(15)
        self.assertEqual(round_tripped.duplex, "+")
        self.assertEqual(round_tripped.offset, 5_000_000)

    def test_channels_23_through_30_remain_fixed_repeaters(self):
        radio = self._radio()
        for number in range(23, 31):
            with self.subTest(channel=number):
                memory = radio.get_memory(number)

                self.assertEqual(
                    memory.freq,
                    self.upstream.UV5G_GMRS_PRESETS[number - 1],
                )
                self.assertEqual(memory.duplex, "+")
                self.assertEqual(memory.offset, 5_000_000)
                self.assertEqual(
                    memory.immutable,
                    ["freq", "duplex", "offset"],
                )


if __name__ == "__main__":
    unittest.main()
