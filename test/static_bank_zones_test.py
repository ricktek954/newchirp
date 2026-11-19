"""Fixed-zone radios must report their zones (read-only).

2026-11-19 BF-F8HP-PRO forum report: zones could not be seen or chosen.
Stock StaticBankModel sized banks with "/" and raised TypeError, so the
bridge dropped the whole zone model for 13 radios.
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
        "newchirp_chirp_bridge_static_zones", ROOT / "scripts/chirp_bridge.py")
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


class StaticZoneTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bridge = _load_bridge()
        cls.directory = cls.bridge.load_chirp(
            str(SOURCE), str(VENDOR), str(ROOT / "drivers"))

    def _radio(self, model, image):
        radio = self.directory.get_radio(model)(None)
        radio.load_mmap(str(SOURCE / "tests/images" / image))
        return radio

    def test_bf_f8hp_pro_reports_ten_read_only_zones(self):
        radio = self._radio("Baofeng_BF-F8HP-PRO", "Baofeng_BF-F8HP-PRO.img")
        payload = self.bridge.mapping_payload(radio)
        self.assertEqual(len(payload), 1)
        zones = payload[0]
        self.assertEqual(zones["name"], "Zones")
        self.assertFalse(zones["editable"])
        self.assertEqual([m["name"] for m in zones["mappings"]],
                         ["Zone %i" % n for n in range(1, 11)])
        first, second = zones["mappings"][:2]
        self.assertEqual((first["channelLocations"][0],
                          first["channelLocations"][-1]), (1, 100))
        self.assertEqual((second["channelLocations"][0],
                          second["channelLocations"][-1]), (101, 200))
        model = radio.get_bank_model()
        self.assertEqual(
            [b.get_name() for b in model.get_memory_mappings(
                radio.get_memory(115))], ["Zone 2"])

    def test_every_fixed_zone_radio_produces_its_zones(self):
        from chirp import chirp_common
        checked = 0
        for ident, cls in sorted(self.directory.DRV_TO_RADIO.items()):
            image = SOURCE / "tests/images" / (ident + ".img")
            if not image.exists():
                continue
            radio = cls(None)
            radio.load_mmap(str(image))
            if not isinstance(getattr(radio, "get_bank_model", lambda: None)(),
                              chirp_common.StaticBankModel):
                continue
            payload = self.bridge.mapping_payload(radio)
            self.assertTrue(payload and payload[0]["mappings"], ident)
            checked += 1
        self.assertGreaterEqual(checked, 5)


if __name__ == "__main__":
    unittest.main()
