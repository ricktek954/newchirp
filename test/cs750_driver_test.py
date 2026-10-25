"""Offline tests for the Connect Systems CS750 CPS importer."""

from pathlib import Path
import importlib.util
import sys
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "build_support/chirp-20261023"
PYTHON_VENDOR = (
    ROOT / "assets/python/pyserial-3.5-py2.py3-none-any.whl"
)
sys.path.insert(0, str(ROOT / "scripts"))

from newchirp_mass_storage import (  # noqa: E402
    CS750Profile,
    CS750_SCSI_WRITE,
    parse_rap_packet,
    rap_packet,
)
ALIAS_ALPHABET = (
    "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz ."
)


def _load_bridge():
    spec = importlib.util.spec_from_file_location(
        "newchirp_chirp_bridge_cs750",
        ROOT / "scripts/chirp_bridge.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load chirp_bridge.py")
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


def _encode_alias(name):
    values = [ALIAS_ALPHABET.index(char) for char in name.ljust(16)[:16]]
    encoded = bytearray()
    for offset in range(0, 16, 4):
        first, second, third, fourth = values[offset:offset + 4]
        encoded.extend((
            (first << 2) | (second >> 4),
            ((second & 0x0F) << 4) | (third >> 2),
            ((third & 0x03) << 6) | fourth,
        ))
    return bytes(encoded) + b"\x00" * 4


def _codeplug(model=b"M100000"):
    data = bytearray(0x44010)
    data[0x2000:0x2005] = b"CS750"
    data[0x2010:0x2017] = b"D4.0.03"
    data[0x2068:0x206F] = model

    data[0xA000:0xA010] = _encode_alias("Analog 1")
    data[0xA010:0xA020] = _encode_alias("Digital 2")

    analog = data[0x12000:0x12020]
    analog[0:4] = (146_520_000).to_bytes(4, "little")
    analog[4:8] = (146_520_000).to_bytes(4, "little")
    analog[8] = 0x17
    data[0x12000:0x12020] = analog

    digital = data[0x12020:0x12040]
    digital[0:4] = (446_006_250).to_bytes(4, "little")
    digital[4:8] = (446_006_250).to_bytes(4, "little")
    digital[8] = 0x16
    data[0x12020:0x12040] = digital

    data[0x21F60:0x21F62] = (2).to_bytes(2, "little")
    data[0x21F62:0x21F64] = (1).to_bytes(2, "little")
    data[0x21F64:0x21F66] = (2).to_bytes(2, "little")
    return bytes(data)


class FakeCS750Transport:
    def __init__(self, image):
        self.image = image
        self.request = None
        self.closed = False

    def transfer(self, cdb, size, write_data=None):
        if bytes(cdb) == CS750_SCSI_WRITE:
            self.request = write_data
            return b""

        command, payload = parse_rap_packet(self.request)
        if command == 0x0003:
            response = rap_packet(0x8003, b"\x00" * 257)
        elif command == 0x0015:
            response = rap_packet(0x8015, b"\x00\x00")
        elif command == 0x0010:
            block = int.from_bytes(payload[0:2], "big")
            data = self.image[
                block * CS750Profile.BLOCK_SIZE:
                (block + 1) * CS750Profile.BLOCK_SIZE
            ].ljust(CS750Profile.BLOCK_SIZE, b"\x00")
            units = (
                len(self.image) + CS750Profile.PAGE_SIZE - 1
            ) // CS750Profile.PAGE_SIZE
            response = rap_packet(
                0x8010,
                b"\x00\x00\x00" + units.to_bytes(4, "big") + data,
            )
        else:
            raise AssertionError("Unexpected RAP command 0x%04x" % command)
        return response.ljust(size, b"\x00")

    def close(self):
        self.closed = True


class CS750DriverTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        bridge = _load_bridge()
        cls.bridge = bridge
        cls.directory = bridge.load_chirp(
            str(SOURCE),
            str(PYTHON_VENDOR),
            str(ROOT / "drivers"),
        )
        cls.radio_class = cls.directory.get_radio(
            "Connect_Systems_CS750"
        )

    def _radio(self, data=None):
        from chirp import memmap

        return self.radio_class(
            memmap.MemoryMapBytes(data or _codeplug())
        )

    def test_catalog_and_codeplug_detection(self):
        data = _codeplug()
        self.assertTrue(self.radio_class.match_model(data, "sample.rdb"))
        self.assertFalse(
            self.radio_class.match_model(data[:-1], "sample.rdb")
        )

    def test_imports_ordered_channels_and_alias_encoding(self):
        radio = self._radio()
        self.assertEqual(radio.get_features().memory_bounds, (1, 2))

        first = radio.get_memory(1)
        self.assertEqual(first.freq, 146_520_000)
        self.assertEqual(first.duplex, "")
        self.assertEqual(first.mode, "FM")
        self.assertEqual(first.name, "Analog 1")

        second = radio.get_memory(2)
        self.assertEqual(second.freq, 446_006_250)
        self.assertEqual(second.mode, "DMR")
        self.assertEqual(second.name, "Digital 2")

    def test_live_read_uses_newchirp_transport_and_parses_channels(self):
        image = _codeplug()
        transport = FakeCS750Transport(image)
        radio = self.radio_class(transport)
        radio.status_fn = lambda _status: None

        radio.sync_in()

        self.assertEqual(radio.get_features().memory_bounds, (1, 2))
        self.assertEqual(radio.get_memory(1).name, "Analog 1")
        self.assertEqual(radio.get_memory(2).name, "Digital 2")
        self.assertTrue(transport.closed)

    def test_bridge_selects_mass_storage_transport_without_serial(self):
        transport = FakeCS750Transport(_codeplug())
        with mock.patch(
            "newchirp_mass_storage.ScsiPassthrough",
            return_value=transport,
        ) as factory:
            radio = self.bridge.radio_for(
                self.directory,
                "Connect_Systems_CS750",
                "/dev/rdisk-test",
            )
        factory.assert_called_once_with("/dev/rdisk-test")
        radio.status_fn = lambda _status: None
        radio.sync_in()
        self.assertEqual(radio.get_memory(1).name, "Analog 1")

    def test_upload_is_disabled_and_other_models_are_rejected(self):
        from chirp import errors

        radio = self._radio()
        with self.assertRaises(errors.RadioError):
            radio.sync_out()
        with self.assertRaises(errors.RadioError):
            radio.set_memory(radio.get_memory(1))
        with self.assertRaises(errors.RadioError):
            self._radio(_codeplug(b"M100100"))

    def test_importer_has_clear_experimental_guidance(self):
        prompts = self.radio_class.get_prompts()
        self.assertIn("experimental", prompts.experimental)
        self.assertIn("not enabled", prompts.experimental)
        self.assertIn(".rdb", prompts.info)


if __name__ == "__main__":
    unittest.main()
