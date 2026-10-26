"""Offline tests for the experimental Baofeng GM-32 driver."""

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
MAIN = Path("/Users/randybrown/AI Projects/newchirp")
IMAGE = Path("/Users/randybrown/Downloads/gm32/Baofeng_UV-32_20261025.img")


def _first_existing(*paths):
    for path in paths:
        if path.exists():
            return path
    return paths[0]


CHIRP = _first_existing(
    ROOT / "build_support/chirp-20261016",
    MAIN / "build_support/chirp-20261016",
)
VENDOR = _first_existing(
    ROOT / "assets/python/pyserial-3.5-py2.py3-none-any.whl",
    MAIN / "assets/python/pyserial-3.5-py2.py3-none-any.whl",
)

spec = importlib.util.spec_from_file_location(
    "newchirp_chirp_bridge_gm32",
    ROOT / "scripts/chirp_bridge.py",
)
if spec is None or spec.loader is None:
    raise RuntimeError("Could not load chirp_bridge.py")
bridge = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = bridge
spec.loader.exec_module(bridge)


def _memory(radio, number, freq, **overrides):
    from chirp import chirp_common

    mem = chirp_common.Memory()
    mem.number = number
    mem.freq = freq
    mem.name = overrides.pop("name", "GM32")
    mem.duplex = overrides.pop("duplex", "")
    mem.offset = overrides.pop("offset", 0)
    mem.mode = overrides.pop("mode", "FM")
    mem.power = overrides.pop("power", radio.POWER_LEVELS[0])
    mem.tuning_step = 5.0
    for name, value in overrides.items():
        setattr(mem, name, value)
    return mem


@unittest.skipUnless(CHIRP.is_dir(), "CHIRP source is not on this Mac")
class GM32DriverTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = bridge.load_chirp(
            str(CHIRP),
            str(VENDOR),
            newchirp_driver_dir=str(ROOT / "drivers"),
        )
        cls.radio_class = cls.directory.get_radio("Baofeng_GM-32")

    def setUp(self):
        from chirp import memmap

        self.radio = self.radio_class(
            memmap.MemoryMapBytes(b"\xff" * self.radio_class._mem_size)
        )

    def test_model_prompts_and_features(self):
        prompts = self.radio_class.get_prompts()
        self.assertIn("experimental", prompts.experimental.lower())
        self.assertIn("Turn off the radio", prompts.pre_download)
        self.assertIn("Turn off the radio", prompts.pre_upload)
        self.assertIn("backup", prompts.experimental.lower())
        self.assertIn("tested on a radio", prompts.experimental.lower())
        self.assertFalse(self.radio_class._gmrs)

        features = self.radio.get_features()
        self.assertEqual(features.memory_bounds, (1, 1000))
        self.assertEqual(features.valid_duplexes, ["", "+", "off"])
        self.assertTrue(features.has_settings)
        self.assertTrue(features.has_bank)
        self.assertEqual(
            [str(level) for level in features.valid_power_levels],
            ["High", "Low", "Medium"],
        )

    def test_channel_8_is_forced_simplex_narrow_low(self):
        mem = _memory(
            self.radio,
            8,
            467562500,
            duplex="+",
            offset=5000000,
            mode="FM",
            power=self.radio.POWER_LEVELS[0],
        )
        self.assertEqual(self.radio.validate_memory(mem), [])
        self.assertEqual(mem.duplex, "+")
        self.radio.set_memory(mem)
        stored = self.radio.get_memory(8)
        self.assertEqual(stored.duplex, "")
        self.assertEqual(stored.offset, 0)
        self.assertEqual(stored.mode, "NFM")
        self.assertEqual(str(stored.power), "Low")

    def test_channel_8_receive_only_stays_off_and_narrow(self):
        mem = _memory(
            self.radio,
            9,
            467587500,
            duplex="off",
            mode="FM",
            power=self.radio.POWER_LEVELS[0],
        )
        self.radio.set_memory(mem)
        stored = self.radio.get_memory(9)
        self.assertEqual(stored.duplex, "off")
        self.assertEqual(stored.mode, "NFM")
        self.assertEqual(str(stored.power), "Low")

    def test_repeater_output_keeps_plus_five(self):
        mem = _memory(
            self.radio,
            16,
            462575000,
            duplex="+",
            offset=600000,
        )
        self.radio.set_memory(mem)
        stored = self.radio.get_memory(16)
        self.assertEqual(stored.duplex, "+")
        self.assertEqual(stored.offset, 5000000)

    def test_repeater_output_minus_becomes_simplex(self):
        mem = _memory(
            self.radio,
            16,
            462575000,
            duplex="-",
            offset=5000000,
        )
        self.assertEqual(self.radio.validate_memory(mem), [])
        self.assertEqual(mem.duplex, "-")
        self.radio.set_memory(mem)
        stored = self.radio.get_memory(16)
        self.assertEqual(stored.duplex, "")
        self.assertEqual(stored.offset, 0)

    def test_simplex_channels_drop_a_shift(self):
        mem = _memory(
            self.radio,
            1,
            462562500,
            duplex="+",
            offset=5000000,
        )
        self.radio.set_memory(mem)
        stored = self.radio.get_memory(1)
        self.assertEqual(stored.duplex, "")
        self.assertEqual(stored.offset, 0)

    def test_repeater_input_cannot_use_plus(self):
        mem = _memory(self.radio, 40, 467550000, duplex="+", offset=5000000)
        self.radio.set_memory(mem)
        stored = self.radio.get_memory(40)
        self.assertEqual(stored.duplex, "")
        self.assertEqual(stored.offset, 0)
        self.assertFalse(stored.empty)

    def test_non_gmrs_frequency_is_receive_only(self):
        mem = _memory(
            self.radio,
            31,
            470550000,
            name="HAMs",
            duplex="",
            mode="FM",
            power=self.radio.POWER_LEVELS[0],
        )
        self.radio.set_memory(mem)
        stored = self.radio.get_memory(31)
        self.assertEqual(stored.name, "HAMs")
        self.assertEqual(stored.freq, 470550000)
        self.assertEqual(stored.duplex, "off")
        self.assertEqual(stored.offset, 0)
        self.assertEqual(stored.mode, "FM")
        self.assertEqual(str(stored.power), "High")

    def test_unset_frequency_is_stored_empty(self):
        mem = _memory(self.radio, 50, 0, name="NEW 50")
        mem.empty = False
        self.assertEqual(self.radio.validate_memory(mem), [])
        self.radio.set_memory(mem)
        self.assertTrue(self.radio.get_memory(50).empty)

    @unittest.skipUnless(IMAGE.is_file(), "GM-32 sample image is not in Downloads")
    def test_sample_image_keeps_uv32_identity_and_gm32_write_rules(self):
        from chirp.settings import RadioSettingGroup

        opened = self.directory.get_radio_by_image(str(IMAGE))
        self.assertEqual(opened.MODEL, "UV-32")
        self.assertNotIsInstance(opened, self.radio_class)

        radio = self.radio_class(str(IMAGE))
        channel8 = radio.get_memory(8)
        self.assertEqual(channel8.freq, 467562500)
        self.assertEqual(channel8.duplex, "")
        self.assertEqual(channel8.mode, "NFM")
        self.assertEqual(str(channel8.power), "Low")

        ranchino = radio.get_memory(25)
        self.assertIn("Ranchino", ranchino.name)

        hams = radio.get_memory(31)
        self.assertIn("HAM", hams.name.upper())
        self.assertEqual(hams.freq, 470550000)
        self.assertEqual(hams.duplex, "")
        radio.set_memory(hams)
        stored = radio.get_memory(31)
        self.assertEqual(stored.duplex, "off")
        self.assertIn("HAM", stored.name.upper())

        labels = [
            group.get_shortname()
            for group in radio.get_settings()
            if isinstance(group, RadioSettingGroup)
        ]
        self.assertIn("Basic Settings", labels)
        self.assertIn("Bank names", labels)


if __name__ == "__main__":
    unittest.main()
