"""Offline checks for the Baofeng UV-29 Pro model alias."""

import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest


from chirp_test_source import chirp_source


ROOT = Path(__file__).resolve().parent.parent
SOURCE = chirp_source()
PYTHON_VENDOR = ROOT / "assets/python/pyserial-3.5-py2.py3-none-any.whl"
UV28_IMAGE = SOURCE / "tests/images/Baofeng_UV-28Plus.img"


def _load_bridge():
    spec = importlib.util.spec_from_file_location(
        "newchirp_chirp_bridge_uv29pro",
        ROOT / "scripts/chirp_bridge.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load chirp_bridge.py")
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


class BaofengUV29ProAliasTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bridge = _load_bridge()
        cls.directory = cls.bridge.load_chirp(
            str(SOURCE),
            str(PYTHON_VENDOR),
            str(ROOT / "drivers"),
        )
        cls.base_class = cls.directory.get_radio("Baofeng_UV-28Plus")
        cls.alias_class = cls.directory.get_radio("Baofeng_UV-29Pro")

    def _radio(self, model):
        return self.bridge.radio_from_image(
            self.directory,
            model,
            str(UV28_IMAGE),
        )

    def test_alias_is_registered_without_replacing_uv28plus(self):
        self.assertIsNot(self.alias_class, self.base_class)
        self.assertTrue(issubclass(self.alias_class, self.base_class))
        self.assertEqual(self.alias_class._idents, self.base_class._idents)
        self.assertEqual(self.alias_class._magics, self.base_class._magics)
        self.assertEqual(
            self.alias_class.__module__,
            "newchirp.drivers.newchirp_baofeng_uv29pro",
        )

    def test_alias_uses_uv28plus_transport_and_channel_decode(self):
        alias = self._radio("Baofeng_UV-29Pro")
        base = self._radio("Baofeng_UV-28Plus")

        alias_features = alias.get_features()
        base_features = base.get_features()
        self.assertEqual(
            alias_features.memory_bounds,
            base_features.memory_bounds,
        )
        self.assertEqual(alias_features.valid_bands, base_features.valid_bands)
        self.assertEqual(
            [str(level) for level in alias_features.valid_power_levels],
            [str(level) for level in base_features.valid_power_levels],
        )
        for number in (1, 500, alias_features.memory_bounds[1]):
            with self.subTest(channel=number):
                self.assertEqual(
                    self.bridge.memory_json(alias.get_memory(number)),
                    self.bridge.memory_json(base.get_memory(number)),
                )

    def test_saved_alias_image_reopens_as_uv29pro(self):
        radio = self._radio("Baofeng_UV-29Pro")
        with tempfile.TemporaryDirectory() as temp:
            image = Path(temp) / "Baofeng_UV-29Pro.img"
            radio.save(str(image))
            reopened = self.directory.get_radio_by_image(str(image))

        self.assertIsInstance(reopened, self.alias_class)
        self.assertEqual(reopened.VENDOR, "Baofeng")
        self.assertEqual(reopened.MODEL, "UV-29Pro")


if __name__ == "__main__":
    unittest.main()
