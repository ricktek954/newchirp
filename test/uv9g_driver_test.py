"""Offline checks for Baofeng UV-9G service-setting compatibility."""

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
        "newchirp_chirp_bridge_uv9g",
        ROOT / "scripts/chirp_bridge.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load chirp_bridge.py")
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


def _find_setting(group, name):
    from chirp.settings import RadioSetting

    for element in group:
        if isinstance(element, RadioSetting):
            if element.get_name() == name:
                return element
        else:
            match = _find_setting(element, name)
            if match is not None:
                return match
    return None


class UV9GDriverTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        bridge = _load_bridge()
        cls.bridge = bridge
        cls.directory = bridge.load_chirp(
            str(SOURCE),
            str(PYTHON_VENDOR),
            str(ROOT / "drivers"),
        )
        cls.compat = importlib.import_module(
            "newchirp.drivers.newchirp_uv9g"
        )

    def test_out_of_range_service_squelch_is_read_only_and_preserved(self):
        radio = self.bridge.radio_from_image(
            self.directory,
            "Baofeng_UV-9G",
            str(SOURCE / "tests/images/Baofeng_UV-9G.img"),
        )
        radio._memobj.squelch.vhf.sql4 = 124
        radio._memobj.squelch.vhf.sql9 = 129

        settings = radio.get_settings()
        sql4 = _find_setting(settings, "squelch.vhf.sql4")
        sql9 = _find_setting(settings, "squelch.vhf.sql9")

        self.assertIsNotNone(sql4)
        self.assertIsNotNone(sql9)
        self.assertFalse(sql4.value.get_mutable())
        self.assertFalse(sql9.value.get_mutable())
        self.assertEqual(int(radio._memobj.squelch.vhf.sql4), 124)
        self.assertEqual(int(radio._memobj.squelch.vhf.sql9), 129)

        radio.set_settings(settings)

        self.assertEqual(int(radio._memobj.squelch.vhf.sql4), 124)
        self.assertEqual(int(radio._memobj.squelch.vhf.sql9), 129)


if __name__ == "__main__":
    unittest.main()
