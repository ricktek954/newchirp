"""Offline tests for the experimental Radtel RT-950 Pro driver."""

from collections import deque
from pathlib import Path
import importlib.util
import sys
import unittest
from unittest import mock

from chirp_test_source import chirp_source


ROOT = Path(__file__).resolve().parent.parent
SOURCE = chirp_source()
PYTHON_VENDOR = ROOT / "assets/python/pyserial-3.5-py2.py3-none-any.whl"


def _load_bridge():
    spec = importlib.util.spec_from_file_location(
        "newchirp_chirp_bridge_rt950pro",
        ROOT / "scripts/chirp_bridge.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load chirp_bridge.py")
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


def _frequency_bytes(frequency):
    tens = frequency // 10
    parts = (
        (tens // 1_000_000) % 100,
        (tens // 10_000) % 100,
        (tens // 100) % 100,
        tens % 100,
    )
    return bytes(
        ((part // 10) << 4) | (part % 10)
        for part in reversed(parts)
    )


def _record(rx, tx, *, name=b"", power=0, flags=0x04):
    record = bytearray(32)
    record[0:4] = _frequency_bytes(rx)
    record[4:8] = _frequency_bytes(tx)
    record[14] = power
    record[15] = flags
    record[20:32] = name.ljust(12, b"\x00")[:12]
    return bytes(record)


class FakeRT950ProSerial:
    def __init__(self, memory):
        self.memory = memory
        self.responses = deque()
        self.writes = []
        self.ack_handshake = True
        self.model = b"RT-950 Pro"
        self.encryption_symbol = b"    "

    def reset_input_buffer(self):
        self.responses.clear()

    def write(self, data):
        data = bytes(data)
        self.writes.append(data)
        if data == b"PROGRAMBT9000U":
            self.responses.append(b"\x06" if self.ack_handshake else b"")
        elif data == b"F":
            self.responses.append(b"\x00" * 16)
        elif data == b"M":
            self.responses.append(self.model.ljust(12, b"\x00"))
        elif data[:4] == b"SEND":
            compat = sys.modules["newchirp.drivers.newchirp_rt950"]
            index = (
                (data[4] - 32) * 2 + 1
                if data[4] & 0x20
                else (data[4] - 16) * 2
            ) + 1
            self.encryption_symbol = compat.SEND_SYMBOLS[
                data[4 + index]
            ].encode("ascii")
            self.responses.append(b"\x06")
        elif len(data) == 4 and data[0] in (0x52, 0x54):
            address = (data[1] << 8) | data[2]
            length = data[3]
            payload = bytearray(self.memory[address:address + length])
            for index, value in enumerate(payload):
                key = self.encryption_symbol[index % 4]
                if (
                    key != 0x20
                    and value not in (0, 0xFF, key, key ^ 0xFF)
                ):
                    payload[index] ^= key
            self.responses.append(b"W" + data[1:] + payload)

    def read(self, size):
        result = bytearray()
        while self.responses and len(result) < size:
            chunk = self.responses[0]
            take = min(size - len(result), len(chunk), 7)
            result.extend(chunk[:take])
            if take == len(chunk):
                self.responses.popleft()
            else:
                self.responses[0] = chunk[take:]
        return bytes(result)


class RT950ProDriverTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        bridge = _load_bridge()
        cls.directory = bridge.load_chirp(
            str(SOURCE),
            str(PYTHON_VENDOR),
            str(ROOT / "drivers"),
        )
        cls.radio_class = cls.directory.get_radio("Radtel_RT-950_Pro")
        cls.base_class = cls.directory.get_radio("Radtel_RT-950")

    def _radio_from_memory(self, memory):
        from chirp import memmap

        return self.radio_class(memmap.MemoryMapBytes(bytes(memory)))

    def test_catalog_has_separate_base_and_pro_models(self):
        self.assertIsNot(self.radio_class, self.base_class)
        self.assertEqual(self.radio_class.MODEL, "RT-950 Pro")
        self.assertEqual(self.base_class.MODEL, "RT-950")
        self.assertEqual(self.radio_class._memsize, 0xD300)
        self.assertEqual(self.radio_class.INITIAL_ACK_TIMEOUT, 3.0)

    def test_protocol_reads_the_complete_pro_map(self):
        memory = bytearray(b"\xff" * 0xD300)
        memory[0:32] = _record(
            462_575_000,
            467_575_000,
            name=b"PRO",
        )
        memory[0xD0FC:0xD100] = b"LAST"
        serial = FakeRT950ProSerial(memory)
        radio = self.radio_class(serial)
        radio.status_fn = lambda _status: None

        radio.sync_in()

        reads = [
            write
            for write in serial.writes
            if len(write) == 4 and write[0] in (0x52, 0x54)
        ]
        self.assertEqual(len(reads), 259)
        self.assertEqual(reads[0], b"R\x00\x00\x80")
        self.assertEqual(reads[239], b"R\x77\x80\x80")
        self.assertEqual(reads[240], b"R\x80\x00\x80")
        self.assertEqual(reads[-1], b"T\x00\x00\x80")
        self.assertEqual(serial.writes[-1], b"E")
        self.assertEqual(radio._mmap.get(0xD0FC, 4), b"LAST")
        self.assertEqual(radio.get_memory(1).name, "PRO")
        self.assertEqual(radio.get_memory(1).duplex, "+")
        self.assertEqual(radio.get_memory(1).offset, 5_000_000)

    def test_driver_is_read_only(self):
        radio = self._radio_from_memory(b"\xff" * self.radio_class._memsize)
        from chirp import errors

        with self.assertRaisesRegex(errors.RadioError, "read-only"):
            radio.sync_out()
        with self.assertRaisesRegex(errors.RadioError, "read-only"):
            radio.set_memory(radio.get_memory(1))

    def test_unknown_model_is_rejected(self):
        serial = FakeRT950ProSerial(b"\xff" * self.radio_class._memsize)
        serial.model = b"OTHER-9000"
        radio = self.radio_class(serial)
        radio.status_fn = lambda _status: None
        from chirp import errors

        with self.assertRaisesRegex(
            errors.RadioError,
            "unrecognized model code",
        ):
            radio.sync_in()
        self.assertNotIn(b"E", serial.writes)

    def test_no_ack_uses_the_three_second_profile_and_does_not_read(self):
        serial = FakeRT950ProSerial(b"\xff" * self.radio_class._memsize)
        serial.ack_handshake = False
        radio = self.radio_class(serial)
        radio.status_fn = lambda _status: None
        from chirp import errors

        with mock.patch.object(radio, "_read_exact", return_value=b""):
            with self.assertRaisesRegex(errors.RadioNoResponse, "3.0 seconds"):
                radio.sync_in()
        self.assertEqual(serial.writes.count(b"PROGRAMBT9000U"), 3)
        self.assertFalse(
            [write for write in serial.writes if write == b"F"]
        )


if __name__ == "__main__":
    unittest.main()
