"""Offline tests for the experimental Icom ID-50 and ID-52 drivers."""

import importlib.util
from pathlib import Path
import struct
import sys
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

    def test_drivers_are_registered_as_experimental_read_only(self):
        self.assertEqual(self.id50.__name__, "IcomId50Radio")
        self.assertEqual(self.id52.__name__, "IcomId52Radio")
        for radio_class in (self.id50, self.id52):
            prompts = radio_class.get_prompts()
            self.assertIn("experimental", prompts.experimental.lower())
            self.assertIn("uploads are disabled", prompts.experimental)
            self.assertIn("read-only", prompts.pre_download.lower())
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

    def test_upload_is_disabled(self):
        from chirp import memmap

        serial = FakeIcomSerial(b"\x00" * 32)
        radio = self.id50(serial)
        radio._mmap = memmap.MemoryMapBytes(bytes(range(32)))
        radio._memsize = 32
        radio._metadata["icom_model_id"] = MODEL_ID.hex()
        radio.status_fn = None

        with self.assertRaisesRegex(Exception, "read-only"):
            radio.sync_out()
        self.assertFalse(any(frame[4] in (0xE3, 0xE4, 0xE5)
                             for frame in serial.writes if len(frame) > 4))

    def test_physical_layout_decodes_analog_and_dstar_channels(self):
        from chirp import memmap
        from chirp.drivers import icf

        image = bytearray(b"\xFF" * 0x38125)
        analog = bytearray(51)
        analog[0:4] = (146_940_000).to_bytes(4, "big")
        analog[4:8] = (600_000).to_bytes(4, "big")
        analog[12:28] = b"ANALOG".ljust(16, b"\x00")
        # Analog records may contain nonzero D-STAR-area defaults.  The mode
        # selector, not those unrelated bytes, determines the CHIRP mode.
        analog[37:51] = b"\x01" * 14
        image[0:51] = analog

        digital = bytearray(51)
        digital[0:4] = (442_575_000).to_bytes(4, "big")
        digital[4:8] = (5_000_000).to_bytes(4, "big")
        digital[9] = 0x05
        digital[12:28] = b"D-STAR".ljust(16, b"\x00")
        for start, call in (
            (30, "CQCQCQ"),
            (37, "W1ABC  B"),
            (44, "W1ABC  G"),
        ):
            digital[start:start + 7] = bytes(
                icf.warp_byte_size(call.ljust(8), 8, 7)
            )
        image[51:102] = digital

        radio = self.id52(None)
        radio._mmap = memmap.MemoryMapBytes(bytes(image))
        radio._metadata["icom_model_id"] = MODEL_ID.hex()
        radio.process_mmap()

        analog_memory = radio.get_memory(1)
        self.assertEqual(analog_memory.freq, 146_940_000)
        self.assertEqual(analog_memory.duplex, "+")
        self.assertEqual(analog_memory.offset, 600_000)
        self.assertEqual(analog_memory.name, "ANALOG")
        self.assertEqual(analog_memory.mode, "FM")

        digital_memory = radio.get_memory(2)
        self.assertEqual(digital_memory.freq, 442_575_000)
        self.assertEqual(digital_memory.name, "D-STAR")
        self.assertEqual(digital_memory.mode, "DV")
        self.assertEqual(digital_memory.dv_urcall, "CQCQCQ")
        self.assertEqual(digital_memory.dv_rpt1call, "W1ABC  B")
        self.assertEqual(digital_memory.dv_rpt2call, "W1ABC  G")
        self.assertEqual(
            radio.get_features().memory_bounds,
            (1, 500),
        )


if __name__ == "__main__":
    unittest.main()
