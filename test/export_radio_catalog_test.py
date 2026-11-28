"""Offline tests for the pinned CHIRP radio catalog export."""

import importlib.util
from pathlib import Path
import unittest

from chirp_test_source import chirp_source


ROOT = Path(__file__).resolve().parent.parent


def _load_exporter():
    spec = importlib.util.spec_from_file_location(
        "newchirp_export_radio_catalog", ROOT / "scripts/export_radio_catalog.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ExportRadioCatalogTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.exporter = _load_exporter()
        cls.source = Path(chirp_source())
        cls.vendors = {
            vendor["name"]: vendor["models"]
            for vendor in cls.exporter.collect(cls.source)
        }

    def test_source_is_the_pinned_commit(self):
        self.assertIn(self.exporter.pinned_commit(), str(self.source))

    def test_drivers_aliases_and_alias_map_entries(self):
        self.assertIn("UV-5R", self.vendors["Baofeng"])
        self.assertIn("UV-S9 (tri-power: use BF-F8HP)",
                      self.vendors["Baofeng/Pofung"])
        self.assertIn("UV-K5", self.vendors["Quansheng"])
        self.assertNotIn("UV-K5 (egzumer)", self.vendors["Quansheng"])

    def test_untested_drivers_are_starred(self):
        self.assertIn("FT-1802M *", self.vendors["Yaesu"])

    def test_file_only_formats_are_left_out(self):
        self.assertNotIn("Generic", self.vendors)
        self.assertNotIn("RT Systems", self.vendors)

    def test_models_are_unique_and_sorted(self):
        for models in self.vendors.values():
            self.assertEqual(models, sorted(set(models)))


if __name__ == "__main__":
    unittest.main()
