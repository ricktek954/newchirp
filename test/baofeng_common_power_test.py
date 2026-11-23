"""Unrecognised Baofeng power values must not fail the read (INBOX:922)."""

import importlib.util
from pathlib import Path
import sys
import unittest

from chirp_test_source import chirp_source


ROOT = Path(__file__).resolve().parent.parent
SOURCE = chirp_source()
PYTHON_VENDOR = ROOT / "assets/python/pyserial-3.5-py2.py3-none-any.whl"
IMAGES = Path(SOURCE) / "tests/images"


class BaofengCommonPowerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location(
            "newchirp_chirp_bridge_bfpower", ROOT / "scripts/chirp_bridge.py")
        bridge = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = bridge
        spec.loader.exec_module(bridge)
        cls.directory = bridge.load_chirp(
            str(SOURCE), str(PYTHON_VENDOR), str(ROOT / "drivers"))

    def _radio(self, image):
        return self.directory.get_radio_by_image(str(IMAGES / image))

    def _first_used(self, radio):
        lo, hi = radio.get_features().memory_bounds
        for number in range(lo, hi + 1):
            if not radio.get_memory(number).empty:
                return number
        self.fail("no used channel in sample image")

    def test_5rx_family_uses_the_oem_cps_power_bit(self):
        # Baofeng UV-5RX CPS 20231124: byte 14 is 0 for High, 1 for Low,
        # and Low is read from bit 0.
        for image in ("Baofeng_5RX.img", "Baofeng_UV-S9X3.img"):
            with self.subTest(image=image):
                radio = self._radio(image)
                number = self._first_used(radio)
                _mem = radio._memobj.memory[number]
                for raw, shown in ((0, "High"), (1, "Low"), (2, "High"),
                                   (3, "Low")):
                    _mem.lowpower = raw
                    mem = radio.get_memory(number)  # stock: 1 and 3 crash
                    self.assertEqual(str(mem.power), shown, raw)
                    mem.name = "EDITED"             # power untouched
                    radio.set_memory(mem)
                    self.assertEqual(int(_mem.lowpower), raw)

                _mem.lowpower = 0
                radio.get_memory(number)
                for level, raw in ((1, 1), (0, 0), (1, 1)):
                    mem = radio.get_memory(number)
                    mem.power = radio.POWER_LEVELS[level]
                    radio.set_memory(mem)
                    self.assertEqual(_mem.get_raw()[14], raw)
                    self.assertEqual(str(radio.get_memory(number).power),
                                     str(radio.POWER_LEVELS[level]))

                _mem.lowpower = 2                   # a stock CHIRP "Low"
                mem = radio.get_memory(number)
                mem.power = radio.POWER_LEVELS[1]
                radio.set_memory(mem)
                self.assertEqual(_mem.get_raw()[14], 1)

    def test_other_tri_band_unknown_value_reads_and_is_kept(self):
        radio = self._radio("Baofeng_BF-A58S.img")
        number = self._first_used(radio)
        _mem = radio._memobj.memory[number]
        for raw in (1, 3):
            _mem.lowpower = raw
            mem = radio.get_memory(number)          # stock: AttributeError
            self.assertEqual(str(mem.power), "High")
            mem.name = "EDITED"
            radio.set_memory(mem)
            self.assertEqual(int(_mem.lowpower), raw)
        mem = radio.get_memory(number)
        mem.power = radio.POWER_LEVELS[1]
        radio.set_memory(mem)
        self.assertEqual(int(_mem.lowpower), 2)     # stock encoding kept
        self.assertEqual(str(radio.get_memory(number).power), "Low")

    def test_known_values_unchanged(self):
        radio = self._radio("Baofeng_BF-A58S.img")
        number = self._first_used(radio)
        _mem = radio._memobj.memory[number]
        for raw, name in ((0, "High"), (2, "Low")):
            _mem.lowpower = raw
            mem = radio.get_memory(number)
            self.assertEqual(str(mem.power), name)
            radio.set_memory(mem)
            self.assertEqual(int(_mem.lowpower), raw)


if __name__ == "__main__":
    unittest.main()
