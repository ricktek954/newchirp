"""Offline checks for IC-7100 unknown-mode handling."""

import importlib
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest import mock

from chirp_test_source import chirp_source


ROOT = Path(__file__).resolve().parent.parent
SOURCE = chirp_source()
PYTHON_VENDOR = ROOT / "assets/python/pyserial-3.5-py2.py3-none-any.whl"


def _load_bridge():
    spec = importlib.util.spec_from_file_location(
        "newchirp_chirp_bridge_ic7100",
        ROOT / "scripts/chirp_bridge.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load chirp_bridge.py")
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


class IcomIC7100DriverTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        bridge = _load_bridge()
        cls.directory = bridge.load_chirp(
            str(SOURCE),
            str(PYTHON_VENDOR),
            str(ROOT / "drivers"),
        )
        cls.radio_class = cls.directory.get_radio("Icom_IC-7100")
        cls.driver = importlib.import_module(cls.radio_class.__module__)
        from chirp import chirp_common

        cls.chirp_common = chirp_common

    def test_newchirp_driver_replaces_stock_ic7100(self):
        self.assertEqual(self.radio_class.__name__, "NewChirpIcom7100")
        self.assertEqual(
            self.radio_class.__module__,
            "newchirp.drivers.newchirp_icom_ic7100",
        )

    def test_unknown_and_reserved_mode_values_fall_back_to_fm(self):
        modes = self.driver._FallbackModes(
            self.driver.icomciv.IcomCIVRadio._MODES
        )

        self.assertEqual(modes[0x85], "FM")
        self.assertEqual(modes.last_unknown_index, 0x85)
        self.assertEqual(modes[11], "FM")
        self.assertEqual(modes.last_unknown_index, 11)
        self.assertEqual(modes[5], "FM")
        self.assertIsNone(modes.last_unknown_index)

    def test_opaque_mode_is_marked_immutable_and_explained(self):
        memory = self.chirp_common.Memory()
        memory.number = 7
        memory.comment = "Factory channel"

        self.driver._mark_opaque_mode(memory, 0x85)

        self.assertEqual(memory.mode, "FM")
        self.assertIn("mode", memory.immutable)
        self.assertIn("0x85", memory.comment)
        self.assertIn("cannot be uploaded", memory.comment)

    def test_upload_is_blocked_before_write_for_unknown_mode(self):
        radio = object.__new__(self.radio_class)
        radio._existing_mode_index = lambda _number: 0x85
        memory = self.chirp_common.Memory()
        memory.number = 7
        memory.mode = "FM"

        with mock.patch.object(
            self.driver.icomciv.Icom7100Radio,
            "set_memory",
        ) as stock_write:
            with self.assertRaisesRegex(
                self.driver.errors.InvalidValueError,
                "unsupported CI-V mode 0x85",
            ):
                self.radio_class.set_memory(radio, memory)

        stock_write.assert_not_called()


if __name__ == "__main__":
    unittest.main()
