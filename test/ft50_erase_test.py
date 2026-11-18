"""Regression: clearing an FT-50 channel must update both flag tables.

The FT-50 keeps each channel's flag byte at 0x001A + n and again at
0x079C + n. Both physical-radio images in the repository keep the two tables
identical, with empty slots stored as 0x00. Stock CHIRP cleared only the first
table, so channels blanked in NewChirp survived the upload.
"""

import importlib
import importlib.util
from pathlib import Path
import sys
import unittest

from chirp_test_source import chirp_source


ROOT = Path(__file__).resolve().parent.parent
SOURCE = chirp_source()
PYTHON_VENDOR = ROOT / "assets/python/pyserial-3.5-py2.py3-none-any.whl"
IMAGES = [
    ROOT / "test/fixtures/Yaesu_FT-50_UID_672.img",
    SOURCE / "tests/images/Yaesu_FT-50.img",
]
FLAG = 0x001A
FLAG_REPEAT = 0x079C


def _load_bridge():
    spec = importlib.util.spec_from_file_location(
        "newchirp_chirp_bridge_ft50_erase_test",
        ROOT / "scripts/chirp_bridge.py",
    )
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


class FT50EraseTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bridge = _load_bridge()
        cls.directory = cls.bridge.load_chirp(
            str(SOURCE), str(PYTHON_VENDOR), str(ROOT / "drivers"),
        )
        importlib.import_module("newchirp.drivers.newchirp_ft50_compat")
        from chirp.drivers import ft50
        cls.ft50 = ft50

    def _radio(self, path):
        from chirp import memmap
        radio = self.ft50.FT50Radio(None)
        radio._mmap = memmap.MemoryMapBytes(path.read_bytes())
        radio.process_mmap()
        return radio

    @staticmethod
    def _flags(radio, number):
        data = radio.get_mmap().get_packed()
        return data[FLAG + number - 1], data[FLAG_REPEAT + number - 1]

    def test_reference_images_keep_flag_tables_identical(self):
        for path in IMAGES:
            with self.subTest(image=path.name):
                data = path.read_bytes()
                self.assertEqual(
                    data[FLAG:FLAG + 100], data[FLAG_REPEAT:FLAG_REPEAT + 100]
                )

    def test_clearing_a_channel_empties_both_tables(self):
        for path in IMAGES:
            radio = self._radio(path)
            used = [
                n for n in range(1, 101)
                if not radio.get_memory(n).empty
            ]
            self.assertTrue(used, path.name)
            for number in used:
                with self.subTest(image=path.name, channel=number):
                    mem = radio.get_memory(number)
                    mem.empty = True
                    radio.set_memory(mem)
                    self.assertEqual(self._flags(radio, number), (0, 0))
                    self.assertTrue(radio.get_memory(number).empty)
            data = radio.get_mmap().get_packed()
            self.assertEqual(
                data[FLAG:FLAG + 100], data[FLAG_REPEAT:FLAG_REPEAT + 100]
            )

    def test_reusing_a_cleared_slot_marks_both_tables_used(self):
        from chirp import chirp_common
        radio = self._radio(IMAGES[0])
        empty = next(
            n for n in range(1, 101) if radio.get_memory(n).empty
        )
        mem = chirp_common.Memory()
        mem.number = empty
        mem.freq = 146520000
        radio.set_memory(mem)
        primary, repeat = self._flags(radio, empty)
        self.assertEqual(primary, repeat)
        self.assertEqual(primary & 0x03, 0x03)  # used + mask (visible)
        self.assertEqual(radio.get_memory(empty).freq, 146520000)

    def test_bridge_upload_image_sends_cleared_slots(self):
        """A cleared channel reaches the bytes NewChirp uploads."""
        radio = self._radio(IMAGES[0])
        number = next(
            n for n in range(1, 101) if not radio.get_memory(n).empty
        )
        mem = radio.get_memory(number)
        mem.empty = True
        radio.set_memory(mem)
        packed = radio.get_mmap().get_packed()
        self.assertEqual(packed[FLAG + number - 1], 0)
        self.assertEqual(packed[FLAG_REPEAT + number - 1], 0)


if __name__ == "__main__":
    unittest.main()
