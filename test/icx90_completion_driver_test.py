"""Offline tests for the IC-E90 completion-safe clone download."""

import importlib.util
from pathlib import Path
import struct
import sys
import unittest


ROOT = Path(__file__).resolve().parent.parent
PYTHON_VENDOR = ROOT / "assets/python/pyserial-3.5-py2.py3-none-any.whl"
MODEL_ID = b"\x25\x07\x00\x01"
IMAGE_SIZE = 0x2D40


def _load_bridge():
    spec = importlib.util.spec_from_file_location(
        "newchirp_chirp_bridge_icx90",
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
        + payload
        + b"\xfd"
    )


def _data_payload(address, data):
    prefix = struct.pack(">HB", address, len(data))
    checksum = (-sum(prefix + data)) & 0xFF
    raw = prefix + data + bytes((checksum,))
    return raw.hex().upper().encode("ascii")


class FakeIcomSerial:
    def __init__(self, image, *, send_end_frame=False, complete=True):
        self.image = bytes(image)
        self.send_end_frame = send_end_frame
        self.complete = complete
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
            payload = MODEL_ID + bytes(29)
            self._rx.extend(_frame(0xEF, 0xEE, 0xE1, payload))
        elif command == 0xE2:
            stop = len(self.image) if self.complete else len(self.image) // 2
            for address in range(0, stop, 32):
                chunk = self.image[address:min(address + 32, stop)]
                self._rx.extend(
                    _frame(
                        0xEF,
                        0xEE,
                        0xE4,
                        _data_payload(address, chunk),
                    )
                )
            if self.send_end_frame:
                self._rx.extend(_frame(0xEF, 0xEE, 0xE5, b"Icom Inc."))
        return len(data)

    def read(self, size=1):
        data = bytes(self._rx[:size])
        del self._rx[:size]
        return data

    def flush(self):
        pass

    def reset_input_buffer(self):
        self._rx.clear()

    def close(self):
        pass


class Icx90CompletionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = ROOT / "build_support/chirp-20261023"
        cls.directory = _load_bridge().load_chirp(
            str(source),
            str(PYTHON_VENDOR),
            str(ROOT / "drivers"),
        )
        cls.radio_class = cls.directory.get_radio("Icom_IC-E90")

    def _radio(self, serial):
        radio = self.radio_class(serial)
        radio.status_fn = None
        return radio

    def test_full_coverage_succeeds_without_end_frame(self):
        serial = FakeIcomSerial(bytes(IMAGE_SIZE))
        radio = self._radio(serial)

        radio.sync_in()

        self.assertEqual(len(radio.get_mmap()), IMAGE_SIZE)
        commands = [frame[4] for frame in serial.writes if len(frame) > 4]
        self.assertEqual(commands[:2], [0xE0, 0xE2])

    def test_normal_end_frame_still_succeeds(self):
        serial = FakeIcomSerial(bytes(IMAGE_SIZE), send_end_frame=True)
        radio = self._radio(serial)

        radio.sync_in()

        self.assertEqual(len(radio.get_mmap()), IMAGE_SIZE)

    def test_incomplete_image_still_fails(self):
        from chirp import errors

        driver_module = sys.modules[self.radio_class.__module__]
        original_timeout = driver_module.CLONE_TIMEOUT
        driver_module.CLONE_TIMEOUT = 0.01
        self.addCleanup(setattr, driver_module, "CLONE_TIMEOUT", original_timeout)
        serial = FakeIcomSerial(bytes(IMAGE_SIZE), complete=False)
        radio = self._radio(serial)

        with self.assertRaises(errors.RadioError):
            radio.sync_in()

    def test_incomplete_image_with_end_frame_still_fails(self):
        from chirp import errors

        serial = FakeIcomSerial(
            bytes(IMAGE_SIZE),
            send_end_frame=True,
            complete=False,
        )
        radio = self._radio(serial)

        with self.assertRaises(errors.RadioError):
            radio.sync_in()


if __name__ == "__main__":
    unittest.main()
