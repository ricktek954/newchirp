"""Offline tests for the read-only AnyTone AT-D878UVII Plus driver."""

import importlib.util
from pathlib import Path
import sys
import unittest

from chirp_test_source import chirp_source

sys.path.insert(0, str(Path(__file__).resolve().parent))
import anytone_d578uviii_driver_test as d578  # noqa: E402


ROOT = Path(__file__).resolve().parent.parent
SOURCE = chirp_source()
PYTHON_VENDOR = ROOT / "assets/python/pyserial-3.5-py2.py3-none-any.whl"

# QDMR channelBanks + (i / 128) * 0x40000 + (i % 128) * 0x40
CHANNEL_129 = d578.CHANNEL_BANKS + 0x40000


class FakeD878Serial(d578.FakeAnyToneSerial):
    """The D578 fake with a D878UV2 identity and a channel in bank 1."""

    def __init__(self, model=b"D878UV2"):
        super().__init__()
        self.model = model
        bitmap = bytearray(self.memory[d578.CHANNEL_BITMAP])
        bitmap[128 // 8] |= 1 << (128 % 8)      # channel 129
        self.memory[d578.CHANNEL_BITMAP] = bytes(bitmap)
        record = bytearray(d578._channel(
            145_500_000, digital=False, name="BANK TWO"))
        record[8] |= 3 << 2                     # Turbo power
        self._put(CHANNEL_129, record)
        self.writes = []

    def write(self, data):
        data = bytes(data)
        if data == b"\x02":
            self._rx.extend(b"I" + self.model.ljust(7, b"\x00")[:7] +
                            b"\x0e" + b"V4.00\x00" + b"\x06")
            return len(data)
        if data[:1] == b"W":
            self.writes.append(data)
        return super().write(data)


class AnyToneD878UVIITest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location(
            "newchirp_chirp_bridge_d878", ROOT / "scripts/chirp_bridge.py")
        bridge = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = bridge
        spec.loader.exec_module(bridge)
        cls.directory = bridge.load_chirp(
            str(SOURCE), str(PYTHON_VENDOR), str(ROOT / "drivers"))
        cls.d878 = cls.directory.get_radio("AnyTone_AT-D878UVII_Plus")
        cls.d578 = cls.directory.get_radio("AnyTone_AT-D578UVIII_Plus")

    def _read(self, radio_class, serial):
        radio = radio_class(serial)
        radio.status_fn = None
        radio.sync_in()
        return radio

    def test_registered_read_only_with_two_bands(self):
        self.assertTrue(self.d878.NEWCHIRP_WRITE_DISABLED)
        features = self.d878(None).get_features()
        self.assertEqual(
            features.valid_bands,
            [(136000000, 174000000), (400000000, 480000000)],
        )

    def test_reads_channels_across_banks_and_zones(self):
        radio = self._read(self.d878, FakeD878Serial())
        first = radio.get_memory(1)
        self.assertEqual((first.freq, first.name, first.mode),
                         (438_800_000, "Alabama", "DMR"))
        self.assertEqual(radio.get_memory(2).name, "CALL 2M")
        bank_two = radio.get_memory(129)
        self.assertEqual((bank_two.freq, bank_two.name),
                         (145_500_000, "BANK TWO"))
        self.assertEqual(str(bank_two.power), "Turbo")
        zones = radio.get_bank_model().get_mappings()
        self.assertEqual(zones[0].get_name(), "Mississippi")

    def test_write_is_refused_before_any_radio_io(self):
        serial = FakeD878Serial()
        radio = self._read(self.d878, serial)
        with self.assertRaisesRegex(Exception, "not enabled"):
            radio.sync_out()
        self.assertEqual(serial.writes, [])

    def test_each_driver_refuses_the_other_model(self):
        with self.assertRaisesRegex(Exception, "D878UVII family"):
            self._read(self.d878, FakeD878Serial(model=b"D578UV2"))
        with self.assertRaisesRegex(Exception, "D578UV family"):
            self._read(self.d578, FakeD878Serial(model=b"D878UV2"))

    def test_d578_channel_129_is_in_the_second_bank(self):
        # 2026-11-23: the D578 driver used 1000 channels per bank, putting
        # channel 129 at 0x00802000 (the channel-extension area).
        radio = self.d578(None)
        self.assertEqual(radio._channel_address(129), CHANNEL_129)
        self.assertEqual(radio._channel_address(128),
                         d578.CHANNEL_BANKS + 127 * 0x40)
        self.assertEqual(radio._channel_address(4000),
                         d578.CHANNEL_BANKS + 31 * 0x40000 + 31 * 0x40)


if __name__ == "__main__":
    unittest.main()
