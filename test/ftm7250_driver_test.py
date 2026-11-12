"""Offline checks for NewChirp's FTM-7250D power-level correction."""

import importlib.util
from pathlib import Path
import sys
import unittest


from chirp_test_source import chirp_source


ROOT = Path(__file__).resolve().parent.parent
SOURCE = chirp_source()
PYTHON_VENDOR = ROOT / "assets/python/pyserial-3.5-py2.py3-none-any.whl"
FIXTURE = SOURCE / "tests/images/Yaesu_FTM-7250D_R.img"


def _load_bridge():
    spec = importlib.util.spec_from_file_location(
        "newchirp_chirp_bridge_ftm7250",
        ROOT / "scripts/chirp_bridge.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load chirp_bridge.py")
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


class FTM7250DriverTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bridge = _load_bridge()
        cls.directory = cls.bridge.load_chirp(
            str(SOURCE),
            str(PYTHON_VENDOR),
            str(ROOT / "drivers"),
        )

    def test_newchirp_driver_replaces_the_power_inverted_driver(self):
        radio = self.directory.get_radio_by_image(str(FIXTURE))
        self.assertEqual(radio.MODEL, "FTM-7250D")
        self.assertEqual(
            radio._orig_rclass.__module__.rsplit(".", 1)[-1],
            "newchirp_ftm7250",
        )

    def test_power_levels_round_trip_with_cps_codes(self):
        radio = self.directory.get_radio_by_image(str(FIXTURE))
        raw_memory = radio._memobj.memory[0]
        expected_codes = {"Low": 1, "Mid": 2, "Hi": 3}

        for power in radio.get_features().valid_power_levels:
            memory = radio.get_memory(1)
            memory.power = power
            radio.set_memory(memory)

            self.assertEqual(int(raw_memory.power), expected_codes[str(power)])
            self.assertEqual(radio.get_memory(1).power, power)


if __name__ == "__main__":
    unittest.main()
