"""Offline checks for NewChirp's TD-H3 settings compatibility."""

import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "build_support/chirp-20261023"
PYTHON_VENDOR = ROOT / "assets/python/pyserial-3.5-py2.py3-none-any.whl"
TDH3_IMAGE = SOURCE / "tests/images/TIDRADIO_TD-H3.img"
BRIGHTNESS_OFFSET = 0x0CA5


def _load_bridge():
    spec = importlib.util.spec_from_file_location(
        "newchirp_chirp_bridge_tdh3",
        ROOT / "scripts/chirp_bridge.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load chirp_bridge.py")
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


def _find_setting(elements, name):
    for element in elements:
        if not hasattr(element, "get_name"):
            continue
        if element.get_name() == name:
            return element
        try:
            found = _find_setting(element, name)
        except TypeError:
            continue
        if found is not None:
            return found
    return None


class TDH3DriverTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = _load_bridge().load_chirp(
            str(SOURCE),
            str(PYTHON_VENDOR),
            str(ROOT / "drivers"),
        )
        cls.radio_class = cls.directory.get_radio("TIDRADIO_TD-H3-GMRS")

    def _radio_with_brightness(self, value):
        image = bytearray(TDH3_IMAGE.read_bytes())
        image[BRIGHTNESS_OFFSET] = value
        handle = tempfile.NamedTemporaryFile(suffix=".img", delete=False)
        handle.write(image)
        handle.close()
        self.addCleanup(Path(handle.name).unlink)
        radio = self.radio_class(handle.name)
        radio.load_mmap(handle.name)
        return radio

    def test_newchirp_driver_replaces_bundled_tdh3(self):
        self.assertEqual(
            self.radio_class.__module__,
            "newchirp.drivers.newchirp_tdh3",
        )

    def test_unset_brightness_becomes_a_visible_setting(self):
        radio = self._radio_with_brightness(0xFF)

        settings = radio.get_settings()
        brightness = _find_setting(settings, "brightness")

        self.assertIsNotNone(brightness)
        self.assertEqual(str(brightness.value), "5")
        self.assertEqual(int(radio._memobj.settings.brightness), 0)

    def test_shortcut_key_change_applies_with_sanitized_brightness(self):
        radio = self._radio_with_brightness(0xFF)
        settings = radio.get_settings()
        shortcut = _find_setting(settings, "ssidekey1")

        shortcut.value = "Monitor"
        radio.set_settings(settings)

        self.assertEqual(int(radio._memobj.press.ssidekey1), 3)
