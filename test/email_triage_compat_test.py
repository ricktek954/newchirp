"""Regression checks from the 2026-11-02 second-pass email triage."""

import importlib
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest


from chirp_test_source import chirp_source


ROOT = Path(__file__).resolve().parent.parent
SOURCE = chirp_source()
PYTHON_VENDOR = ROOT / "assets/python/pyserial-3.5-py2.py3-none-any.whl"
IMAGES = SOURCE / "tests" / "images"


def _load_bridge():
    spec = importlib.util.spec_from_file_location(
        "newchirp_chirp_bridge_email_triage",
        ROOT / "scripts/chirp_bridge.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load chirp_bridge.py")
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


class EmailTriageCompatibilityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bridge = _load_bridge()
        cls.directory = cls.bridge.load_chirp(
            str(SOURCE),
            str(PYTHON_VENDOR),
            str(ROOT / "drivers"),
        )

    def test_th9800_reserved_tone_does_not_abort_channel_read(self):
        radio = self.directory.get_radio_by_image(
            str(IMAGES / "TYT_TH-9800.img")
        )
        radio._memobj.memory[0].ctcss.set_raw(b"\xff\xff")

        memory = radio.get_memory(1)

        self.assertFalse(memory.empty)
        self.assertEqual(memory.freq, 144_000_000)
        self.assertEqual(memory.rtone, 88.5)
        self.assertEqual(memory.ctone, 88.5)

    def test_th9800_reserved_dtcs_does_not_abort_channel_read(self):
        radio = self.directory.get_radio_by_image(
            str(IMAGES / "TYT_TH-9800.img")
        )
        radio._memobj.memory[0].dtcs.set_raw(b"\x30\x12")

        memory = radio.get_memory(1)

        self.assertFalse(memory.empty)
        self.assertEqual(memory.freq, 144_000_000)
        self.assertEqual(memory.dtcs, 23)
        # Keep the malformed DTCS field unchanged in the saved radio image.
        self.assertEqual(int(radio._memobj.memory[0].dtcs), 1230)

    def test_uv17progps_malformed_ctcss_does_not_abort_channel_read(self):
        radio = self.directory.get_radio_by_image(
            str(IMAGES / "Baofeng_UV-17ProGPS.img")
        )
        raw = radio._memobj.memory[0]
        raw.txtone.set_raw(b"\x12\x43")
        raw.rxtone.set_raw(b"\x12\x43")
        original = radio._mmap.get_packed()

        memory = radio.get_memory(1)

        self.assertFalse(memory.empty)
        self.assertEqual(memory.tmode, "")
        self.assertEqual(radio._mmap.get_packed(), original)

        memory.name = "TEST"
        radio.set_memory(memory)
        self.assertEqual(int(raw.txtone), 0x4312)
        self.assertEqual(int(raw.rxtone), 0x4312)

    def test_vx6_unprogrammable_slot_does_not_abort_radio_read(self):
        radio = self.directory.get_radio_by_image(
            str(IMAGES / "Yaesu_VX-6.img")
        )
        radio._memobj.memory[0].freq.set_value(666_666)

        broken = radio.get_memory(1)
        neighboring = radio.get_memory(2)

        self.assertTrue(broken.empty)
        self.assertFalse(neighboring.empty)
        self.assertEqual(neighboring.freq, 146_940_000)
        # The compatibility decoder must not erase the underlying image data.
        self.assertEqual(int(radio._memobj.memory[0].freq), 666_666)

    def test_radio_catalog_excludes_file_only_models(self):
        grouped = self.bridge.live_models_by_vendor(self.directory)
        identifiers = {
            identifier
            for models in grouped.values()
            for identifier in models
        }

        self.assertNotIn("TYT_TH-9800_File", identifiers)
        self.assertIn("TYT_TH-9800", identifiers)
        self.assertIn("Yaesu_VX-6", identifiers)

    def test_module_wx_dependency_has_actionable_error(self):
        with tempfile.TemporaryDirectory() as temp:
            module = Path(temp) / "module.py"
            module.write_text("import wx\n", encoding="utf-8")

            with self.assertRaisesRegex(
                RuntimeError,
                "wx GUI toolkit.*driver-only version",
            ):
                self.bridge._load_module(str(module), self.directory)


if __name__ == "__main__":
    unittest.main()
