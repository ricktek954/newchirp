"""Offline tests for the experimental Icom ID-50 and ID-52 drivers."""

import importlib.util
from pathlib import Path
import struct
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "build_support/chirp-20261023"
PYTHON_VENDOR = ROOT / "assets/python/pyserial-3.5-py2.py3-none-any.whl"
MODEL_ID = b"\x3a\x90\x00\x09"


def _load_bridge():
    spec = importlib.util.spec_from_file_location(
        "newchirp_chirp_bridge_icom_id50_id52",
        ROOT / "scripts/chirp_bridge.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load chirp_bridge.py")
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


def _frame(source, destination, command, payload=b""):
    return (
        b"\xfe\xfe"
        + bytes((source, destination, command))
        + bytes(payload)
        + b"\xfd"
    )


def _model_payload():
    data = bytearray(49)
    data[:4] = MODEL_ID
    data[5] = 2
    data[6:22] = b"ID-50/52 TEST  "
    data[35:49] = b"00000000000000"
    return bytes(data)


def _data_payload(address, data, *, large):
    if large:
        prefix = struct.pack(">IB", address, len(data))
    else:
        prefix = struct.pack(">HB", address, len(data))
    checksum = (-sum(prefix + data)) & 0xFF
    raw = prefix + data + bytes((checksum,))
    escaped = bytearray()
    for byte in raw:
        if byte > 0xF9:
            escaped.extend((0xFF, byte & 0x0F))
        else:
            escaped.append(byte)
    return bytes(escaped)


class FakeIcomSerial:
    def __init__(self, image):
        self.image = bytes(image)
        self.timeout = 1
        self.baudrate = 9600
        self._rx = bytearray()
        self.writes = []

    def write(self, data):
        data = bytes(data)
        self.writes.append(data)
        if len(data) < 5 or data[:2] != b"\xfe\xfe":
            return len(data)
        command = data[4]
        if command == 0xE0:
            self._rx.extend(_frame(0xEF, 0xEE, 0xE0, _model_payload()))
        elif command == 0xE2:
            self._rx.extend(
                _frame(
                    0xEF,
                    0xEE,
                    0xE4,
                    _data_payload(0, self.image, large=True),
                )
            )
            self._rx.extend(_frame(0xEF, 0xEE, 0xE5, b"Icom Inc."))
        elif command == 0xE5:
            self._rx.extend(_frame(0xEF, 0xEE, 0xE6, b"\x00"))
        return len(data)

    def read(self, size=1):
        if not self._rx:
            return b""
        data = bytes(self._rx[:size])
        del self._rx[:size]
        return data

    def flush(self):
        pass

    def reset_input_buffer(self):
        self._rx.clear()

    def close(self):
        pass


class IcomId50Id52DriverTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = _load_bridge().load_chirp(
            str(SOURCE),
            str(PYTHON_VENDOR),
            str(ROOT / "drivers"),
        )
        cls.id50 = cls.directory.get_radio("Icom_ID-50")
        cls.id52 = cls.directory.get_radio("Icom_ID-52")

    def test_drivers_are_registered_as_experimental_read_write(self):
        self.assertEqual(self.id50.__name__, "IcomId50Radio")
        self.assertEqual(self.id52.__name__, "IcomId52Radio")
        for radio_class in (self.id50, self.id52):
            prompts = radio_class.get_prompts()
            self.assertIn("experimental", prompts.experimental.lower())
            self.assertIn("Reading and writing are enabled", prompts.experimental)
            self.assertIn("backup", prompts.pre_upload.lower())
            self.assertFalse(radio_class._can_hispeed)

    def test_download_uses_reported_model_and_radio_end_address(self):
        image = b"\x80" * 32
        serial = FakeIcomSerial(image)
        radio = self.id52(serial)
        radio.process_mmap = lambda: None
        radio.status_fn = None

        radio.sync_in()

        self.assertEqual(radio.get_model(), MODEL_ID)
        self.assertEqual(radio.metadata["icom_model_id"], MODEL_ID.hex())
        self.assertEqual(radio.metadata["icom_image_size"], 32)
        self.assertEqual(radio.get_ranges(), [(0, 32, 32)])
        self.assertEqual(radio._mmap.get_packed(), b"\x00" * 32)
        self.assertEqual(radio.get_mmap().get_packed(), image)
        self.assertTrue(any(frame[4] == 0xE2 for frame in serial.writes))

    def test_upload_waits_for_clone_ok(self):
        from chirp import memmap

        serial = FakeIcomSerial(b"\x00" * 32)
        radio = self.id50(serial)
        radio._mmap = memmap.MemoryMapBytes(bytes(range(32)))
        radio._memsize = 32
        radio._metadata["icom_model_id"] = MODEL_ID.hex()
        radio.status_fn = None

        self.assertTrue(radio.sync_out())

        commands = [frame[4] for frame in serial.writes if len(frame) > 4]
        self.assertIn(0xE3, commands)
        self.assertIn(0xE4, commands)
        self.assertEqual(commands[-1], 0xE5)

    def test_provisional_map_round_trips_channels_and_saved_model(self):
        from chirp import chirp_common, memmap

        radio = self.id52(None)
        radio._mmap = memmap.MemoryMapBytes(b"\xFF" * 0x2A3C0)
        radio._metadata["icom_model_id"] = MODEL_ID.hex()
        radio.process_mmap()

        memory = chirp_common.DVMemory()
        memory.number = 1
        memory.freq = 146520000
        memory.duplex = ""
        memory.offset = 0
        memory.tmode = ""
        memory.mode = "FM"
        memory.name = "TEST"
        memory.dv_urcall = "CQCQCQ"
        memory.dv_rpt1call = ""
        memory.dv_rpt2call = ""
        memory.dv_code = 0

        radio.set_memory(memory)
        restored = radio.get_memory(1)
        self.assertEqual(restored.freq, 146520000)
        self.assertEqual(restored.name, "TEST")
        self.assertEqual(restored.mode, "FM")
        self.assertEqual(restored.dv_urcall, "CQCQCQ  ")

        with tempfile.NamedTemporaryFile(suffix=".img") as image:
            radio.save(image.name)
            loaded = self.directory.get_radio_by_image(image.name)

        self.assertEqual(loaded.MODEL, "ID-52")
        self.assertEqual(loaded.get_model(), MODEL_ID)
        self.assertEqual(loaded.get_features().memory_bounds, (0, 999))


if __name__ == "__main__":
    unittest.main()
