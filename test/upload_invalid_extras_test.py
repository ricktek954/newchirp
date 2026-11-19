"""Uploads must not fail on a slot whose stored extras are out of range.

2026-11-18 Baofeng 5RM report (macOS, NewChirp 1.0.58): writing a CSV
failed with "Failed to load pttid value 0: Value for 255 is out of range"
and "Could not prepare channel 7 (GMRS-21): None is not in list". The slot
held a programmed record whose PTT-ID byte was 0xFF.
"""

from pathlib import Path
import importlib.util
import sys
import unittest

from chirp_test_source import chirp_source


ROOT = Path(__file__).resolve().parent.parent
SOURCE = chirp_source()
VENDOR = ROOT / "assets/python/pyserial-3.5-py2.py3-none-any.whl"


def _load_bridge():
    spec = importlib.util.spec_from_file_location(
        "newchirp_chirp_bridge_invalid_extras", ROOT / "scripts/chirp_bridge.py"
    )
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


class UploadInvalidExtrasTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bridge = _load_bridge()
        cls.directory = cls.bridge.load_chirp(
            str(SOURCE), str(VENDOR), str(ROOT / "drivers"))

    def test_5rm_slot_with_invalid_pttid_accepts_a_csv_channel(self):
        radio = self.directory.get_radio("Baofeng_5RM")(None)
        radio.load_mmap(str(SOURCE / "tests/images/Baofeng_5RM.img"))
        raw = radio._get_raw_memory(7)
        record = bytearray(raw.get_raw())
        record[13] = 0xFF      # PTT-ID outside LIST_PTTID
        raw.set_raw(bytes(record))
        item = dict(
            location=7, name="GMRS-21", frequency=462.7125, offset=0,
            duplex="", tone="", txTone=88.5, rxTone=88.5, dtcs=23,
            dtcsPolarity="NN", rxDtcs=23, crossMode="Tone->Tone",
            mode="NFM", step=12.5, skip="", comment="", power="High",
            extras=[],
        )

        skipped, adjusted, written = self.bridge.prepare_upload_channels(
            radio, [item])

        self.assertEqual((skipped, written), ([], 1))
        mem = radio.get_memory(7)
        self.assertEqual((mem.freq, mem.name), (462712500, "GMRS-21"))
        pttid = {s.get_name(): str(s.value) for s in mem.extra}["pttid"]
        self.assertEqual(pttid, "Off")
        self.assertEqual(radio._get_raw_memory(7).get_raw()[13], 0)


if __name__ == "__main__":
    unittest.main()
