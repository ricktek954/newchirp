"""Offline checks for reserved KG-UV8D DCS words in reporter images."""

import importlib
import importlib.util
from pathlib import Path
import sys
import unittest

from chirp_test_source import chirp_source


ROOT = Path(__file__).resolve().parent.parent
SOURCE = chirp_source()
PYTHON_VENDOR = ROOT / "assets/python/pyserial-3.5-py2.py3-none-any.whl"
IMAGE = SOURCE / "tests/images/Wouxun_KG-UV8D.img"


def _load_bridge():
    spec = importlib.util.spec_from_file_location(
        "newchirp_chirp_bridge_kg_uv8d_test",
        ROOT / "scripts/chirp_bridge.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load chirp_bridge.py")
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


class KGUV8DReservedDCSTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bridge = _load_bridge()
        cls.directory = cls.bridge.load_chirp(
            str(SOURCE),
            str(PYTHON_VENDOR),
            str(ROOT / "drivers"),
        )
        importlib.import_module("newchirp.drivers.newchirp_kg_uv8d_compat")
        from chirp import memmap

        cls.memmap = memmap
        cls.image = IMAGE.read_bytes()

    def _radio(self, rx_tone=None, tx_tone=None):
        image = bytearray(self.image)
        radio = self.directory.get_radio("Wouxun_KG-UV8D")(
            self.memmap.MemoryMapBytes(bytes(image))
        )
        radio.process_mmap()
        raw_memory = radio._memobj.memory[1]
        if rx_tone is not None:
            raw_memory.rxtone.set_value(rx_tone)
        if tx_tone is not None:
            raw_memory.txtone.set_value(tx_tone)
        return radio

    def _raw_tones(self, radio):
        raw_memory = radio._memobj.memory[1]
        return int(raw_memory.rxtone), int(raw_memory.txtone)

    def test_reserved_dcs_word_no_longer_aborts_channel_decode(self):
        radio = self._radio(rx_tone=0x2FFF, tx_tone=0x2FFF)

        memory = radio.get_memory(1)

        self.assertEqual(memory.freq, 440_150_000)
        self.assertEqual(memory.tmode, "")
        self.assertEqual(
            radio.get_mmap().get_packed()[0x918:0x91C],
            b"\x2f\xff\x2f\xff",
        )

    def test_reserved_words_are_preserved_when_editing_another_field(self):
        radio = self._radio(rx_tone=0x2FFF, tx_tone=0x2FFF)
        memory = radio.get_memory(1)
        memory.name = "RESERVED"

        radio.set_memory(memory)

        self.assertEqual(self._raw_tones(radio), (0x2FFF, 0x2FFF))
        self.assertEqual(radio.get_memory(1).name, "RESERVED")

    def test_valid_dcs_still_decodes_and_writes(self):
        radio = self._radio(rx_tone=0x2813, tx_tone=0x2813)

        memory = radio.get_memory(1)
        self.assertEqual(memory.tmode, "DTCS")
        self.assertEqual(memory.dtcs, 23)
        self.assertEqual(memory.dtcs_polarity, "NN")

        memory.name = "DCS23"
        radio.set_memory(memory)

        round_tripped = radio.get_memory(1)
        self.assertEqual(round_tripped.tmode, "DTCS")
        self.assertEqual(round_tripped.dtcs, 23)
        self.assertEqual(self._raw_tones(radio), (0x2813, 0x2813))

    def test_no_tone_sentinel_is_unchanged(self):
        radio = self._radio(rx_tone=0xFFFF, tx_tone=0xFFFF)

        memory = radio.get_memory(1)

        self.assertEqual(memory.tmode, "")
        self.assertEqual(self._raw_tones(radio), (0xFFFF, 0xFFFF))

    def test_reporter_style_map_decode_succeeds_for_every_slot(self):
        radio = self._radio(rx_tone=0x2FFF, tx_tone=0x2FFF)

        channels = [radio.get_memory(number) for number in range(1, 1000)]

        self.assertEqual(sum(not memory.empty for memory in channels), 6)


if __name__ == "__main__":
    unittest.main()
