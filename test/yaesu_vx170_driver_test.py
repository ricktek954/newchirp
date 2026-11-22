"""Offline checks for the VX-170/VX-177 split-tone squelch modes."""

import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

from chirp_test_source import chirp_source


ROOT = Path(__file__).resolve().parent.parent
SOURCE = chirp_source()
PYTHON_VENDOR = ROOT / "assets/python/pyserial-3.5-py2.py3-none-any.whl"

MEMSIZE = 6057
MEMORY_BASE = 0x0168
RECORD = 16


def _load_bridge():
    spec = importlib.util.spec_from_file_location(
        "newchirp_chirp_bridge_vx170",
        ROOT / "scripts/chirp_bridge.py",
    )
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


def _image(model_id, tmodes):
    """A blank clone image with one 146.520 MHz channel per raw tmode."""
    data = bytearray(b"\xff" * MEMSIZE)
    data[0:6] = model_id
    for index in range(200):
        data[MEMORY_BASE + index * RECORD] = 0x00  # unused
    # 200 name records of 8 bytes at 0x0F28 (name[6], enabled, used): unused.
    data[0x0F28:0x0F28 + 200 * 8] = bytes(200 * 8)
    for index, tmode in enumerate(tmodes):
        offset = MEMORY_BASE + index * RECORD
        record = bytearray(RECORD)
        record[0] = 0x80                    # used, FM, simplex
        record[1:4] = bytes((0x01, 0x46, 0x52))  # bbcd 14652 x 10 kHz
        record[4] = tmode & 0x07            # tune_step 0, tmode
        record[8] = 12                      # power Hi, tone index 12
        record[9] = 5                       # DTCS index 5
        data[offset:offset + RECORD] = record
    return bytes(data)


class YaesuVX170DriverTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bridge = _load_bridge()
        cls.directory = cls.bridge.load_chirp(
            str(SOURCE),
            str(PYTHON_VENDOR),
            str(ROOT / "drivers"),
        )

    def _radio(self, driver_id, model_id, tmodes):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        path = Path(temp.name) / "radio.img"
        path.write_bytes(_image(model_id, tmodes))
        radio = self.directory.get_radio(driver_id)(None)
        radio.load_mmap(str(path))
        return radio

    def test_newchirp_driver_supersedes_chirp_registration(self):
        for driver_id in ("Yaesu_VX-170", "Yaesu_VX-177"):
            radio_class = self.directory.get_radio(driver_id)
            self.assertIn("newchirp_yaesu_vx170", radio_class.__module__)

    def test_split_tone_channels_decode(self):
        # 2026-11-22 report: a 193-channel codeplug from another tool failed
        # with "list index out of range" on self.TMODES[_mem.tmode].
        radio = self._radio("Yaesu_VX-170", b"AH022$", range(8))
        decoded = [radio.get_memory(n) for n in range(1, 9)]

        self.assertEqual(
            [m.tmode for m in decoded],
            ["", "Tone", "TSQL", "TSQL-R", "DTCS", "Cross", "Cross", "Cross"],
        )
        self.assertEqual(
            [m.cross_mode for m in decoded[5:]],
            ["DTCS->", "Tone->DTCS", "DTCS->Tone"],
        )
        features = radio.get_features()
        self.assertIn("Cross", features.valid_tmodes)
        for mem in decoded:
            self.assertEqual(radio.validate_memory(mem), [])

    def test_split_tone_round_trips_to_the_same_raw_value(self):
        radio = self._radio("Yaesu_VX-177", b"AH022U", [0])
        mem = radio.get_memory(1)
        mem.freq = 446_000_000
        for raw, cross_mode in enumerate(
            ["DTCS->", "Tone->DTCS", "DTCS->Tone"], start=5
        ):
            mem.tmode = "Cross"
            mem.cross_mode = cross_mode
            radio.set_memory(mem)
            self.assertEqual(int(radio._memobj.memory[0].tmode), raw)
            self.assertEqual(mem.tmode, "Cross")  # caller's memory untouched
            again = radio.get_memory(1)
            self.assertEqual(
                (again.tmode, again.cross_mode), ("Cross", cross_mode)
            )

        mem.tmode = "TSQL"
        radio.set_memory(mem)
        self.assertEqual(int(radio._memobj.memory[0].tmode), 2)


if __name__ == "__main__":
    unittest.main()
