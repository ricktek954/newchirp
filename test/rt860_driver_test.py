"""Offline tests for the read-only Radtel RT-860 driver."""

from collections import deque
from pathlib import Path
import importlib.util
import struct
import sys
import unittest
from unittest import mock


from chirp_test_source import chirp_source


ROOT = Path(__file__).resolve().parent.parent
SOURCE = chirp_source()
PYTHON_VENDOR = ROOT / "assets/python/pyserial-3.5-py2.py3-none-any.whl"
IMAGE_SIZE = 0xD5000


def _load_bridge():
    spec = importlib.util.spec_from_file_location(
        "newchirp_chirp_bridge_rt860",
        ROOT / "scripts/chirp_bridge.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load chirp_bridge.py")
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


def _record(
    rx,
    tx,
    *,
    name=b"",
    power=1,
    mode=0,
    narrow=0,
    skip=0,
    enabled=1,
):
    record = bytearray(b"\x00" * 32 + b"\xff" * 16)
    record[0] = mode
    record[2] = enabled
    record[3] = narrow
    record[6:10] = struct.pack("<I", rx // 10)
    record[10:14] = struct.pack("<I", tx // 10)
    record[16] = power
    record[19] = skip << 7
    record[32:48] = name.ljust(16, b"\xff")
    return bytes(record)


def _zone(name, channels):
    zone = bytearray(b"\xff" * 512)
    zone[0:2] = bytes((len(channels), len(channels)))
    if isinstance(name, str):
        name = name.encode("gb18030")
    zone[4:20] = name.ljust(16, b"\xff")
    for index, channel in enumerate(channels):
        zone[20 + index * 2:22 + index * 2] = struct.pack("<H", channel)
    return bytes(zone)


class FakeRT860Serial:
    def __init__(self, memory):
        self.memory = bytes(memory)
        self.responses = deque()
        self.writes = []
        self.read_addresses = []
        self.max_read_size = 113
        self.timeout = 2
        self.handshake_acks = 1
        self.handshake_attempts = 0
        self.corrupt_checksum = False
        self.wrong_echo = False
        self.truncate_response = False

    def write(self, data):
        data = bytes(data)
        self.writes.append(data)
        if data == b"4R\x05\x10\x9b":
            self.handshake_attempts += 1
            self.responses.append(
                b"\x06"
                if self.handshake_attempts >= self.handshake_acks
                else b""
            )
        elif data == b"4R\x05\xee\x79":
            pass
        elif data[:1] == b"R":
            page = (data[1] << 8) | data[2]
            self.read_addresses.append(page)
            payload = self._page(page)
            response = data[:3] + payload
            checksum = sum(response) & 0xFF
            if self.corrupt_checksum:
                checksum ^= 1
            if self.wrong_echo:
                response = b"R" + bytes((page ^ 1,)) + response[2:]
            result = response + bytes((checksum,))
            if self.truncate_response:
                result = result[:-1]
            self.responses.append(result)
        else:
            raise AssertionError("Unexpected RT-860 write: %r" % data)

    def read(self, size):
        result = bytearray()
        while self.responses and len(result) < size:
            chunk = self.responses[0]
            take = min(size - len(result), len(chunk), self.max_read_size)
            result.extend(chunk[:take])
            if take == len(chunk):
                self.responses.popleft()
            else:
                self.responses[0] = chunk[take:]
        return bytes(result)

    def _page(self, physical_page):
        for logical, first, count in (
            (0x00000, 0x008, 4),
            (0x02000, 0x010, 48),
            (0x1A000, 0x070, 128),
            (0xD4000, 0x358, 4),
        ):
            if first <= physical_page < first + count:
                offset = logical + (physical_page - first) * 0x400
                return self.memory[offset:offset + 0x400]
        raise AssertionError("Driver read unmapped page 0x%03x" % physical_page)


class RT860DriverTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        bridge = _load_bridge()
        cls.directory = bridge.load_chirp(
            str(SOURCE),
            str(PYTHON_VENDOR),
            str(ROOT / "drivers"),
        )
        cls.radio_class = cls.directory.get_radio("Radtel_RT-860")

    def _memory(self):
        memory = bytearray(b"\xff" * IMAGE_SIZE)
        memory[0x2000:0x2030] = _record(
            146_520_000,
            146_520_000,
            name=b"RT860 TEST",
        )
        memory[0x1A000:0x1A200] = _zone("EmComm", (0, 1))
        return memory

    def test_catalog_and_read_only_policy(self):
        from chirp import errors, memmap

        self.assertEqual(
            self.directory.get_radio("Radtel_RT-860"),
            self.radio_class,
        )
        self.assertEqual(self.radio_class.BAUD_RATE, 115200)
        self.assertTrue(self.radio_class.WANTS_DTR)
        self.assertFalse(self.radio_class.WANTS_RTS)
        self.assertFalse(self.radio_class.HARDWARE_FLOW)
        self.assertFalse(self.radio_class.XON_XOFF)

        radio = self.radio_class(
            memmap.MemoryMapBytes(b"\xff" * IMAGE_SIZE)
        )
        with self.assertRaises(errors.RadioError):
            radio.sync_out()

    def test_open_serial_matches_cps_control_lines(self):
        bridge = sys.modules["newchirp_chirp_bridge_rt860"]
        import serial

        handle = mock.MagicMock()
        with mock.patch.object(
            serial, "Serial", return_value=handle
        ) as serial_class:
            self.assertIs(
                bridge.open_serial(self.radio_class, "/dev/fake-rt860"),
                handle,
            )

        self.assertFalse(serial_class.call_args.kwargs["rtscts"])
        self.assertFalse(serial_class.call_args.kwargs["xonxoff"])
        self.assertEqual(serial_class.call_args.kwargs["baudrate"], 115200)
        self.assertFalse(handle.rts)
        self.assertTrue(handle.dtr)

    def test_cps_sparse_read_plan_and_frame_checksums(self):
        serial = FakeRT860Serial(self._memory())
        radio = self.radio_class(serial)
        statuses = []
        radio.status_fn = statuses.append

        radio.sync_in()

        expected = (
            list(range(0x008, 0x00C))
            + list(range(0x010, 0x040))
            + list(range(0x070, 0x0F0))
            + list(range(0x358, 0x35C))
        )
        self.assertEqual(serial.read_addresses, expected)
        self.assertEqual(serial.writes[0], b"4R\x05\x10\x9b")
        self.assertIn(b"R\x00\x08\x5a", serial.writes)
        self.assertEqual(serial.writes[-1], b"4R\x05\xee\x79")
        self.assertEqual(statuses[-1].cur, 184)
        self.assertEqual(statuses[-1].max, 184)

    def test_malformed_responses_fail_closed(self):
        from chirp import errors

        for attribute in (
            "corrupt_checksum",
            "wrong_echo",
            "truncate_response",
        ):
            with self.subTest(attribute=attribute):
                serial = FakeRT860Serial(self._memory())
                setattr(serial, attribute, True)
                radio = self.radio_class(serial)
                radio.status_fn = lambda _status: None

                with self.assertRaises(errors.RadioError):
                    radio.sync_in()

                self.assertEqual(serial.writes[-1], b"4R\x05\xee\x79")

    def test_handshake_retries_three_times_then_stops(self):
        from chirp import errors

        serial = FakeRT860Serial(self._memory())
        serial.handshake_acks = 99
        radio = self.radio_class(serial)

        with self.assertRaises(errors.RadioNoResponse):
            radio.sync_in()

        self.assertEqual(serial.handshake_attempts, 3)
        self.assertEqual(serial.read_addresses, [])

    def test_channel_and_zone_layout(self):
        serial = FakeRT860Serial(self._memory())
        radio = self.radio_class(serial)
        radio.status_fn = lambda _status: None
        radio.sync_in()

        channel = radio.get_memory(1)
        self.assertFalse(channel.empty)
        self.assertEqual(channel.freq, 146_520_000)
        self.assertEqual(channel.name, "RT860 TEST")
        self.assertEqual(channel.mode, "FM")
        self.assertEqual(str(channel.power), "High")
        self.assertEqual(
            [str(level) for level in radio.get_features().valid_power_levels],
            ["Low", "High"],
        )

        memory = bytearray(self._memory())
        memory[0x2000:0x2030] = _record(
            146_520_000,
            146_520_000,
            name=b"STALE",
            enabled=0,
        )
        inactive = self.radio_class(FakeRT860Serial(memory))
        inactive.status_fn = lambda _status: None
        inactive.sync_in()
        self.assertTrue(inactive.get_memory(1).empty)

        mappings = radio.get_bank_model().get_mappings()
        self.assertEqual(mappings[0].get_name(), "EmComm")
        self.assertEqual(
            [memory.number for memory in
             radio.get_bank_model().get_mapping_memories(mappings[0])],
            [1, 2],
        )

    def test_cps_gbk_names(self):
        memory = self._memory()
        memory[0x2000:0x2030] = _record(
            462_550_000,
            462_550_000,
            name="测试信道".encode("gb18030"),
        )
        memory[0x1A000:0x1A200] = _zone("测试区", (0,))
        serial = FakeRT860Serial(memory)
        radio = self.radio_class(serial)
        radio.status_fn = lambda _status: None
        radio.sync_in()

        self.assertEqual(radio.get_memory(1).name, "测试信道")
        bank = radio.get_bank_model().get_mappings()[0]
        self.assertEqual(bank.get_name(), "测试区")

    def test_editing_uses_cps_two_level_power_and_gbk_names(self):
        serial = FakeRT860Serial(self._memory())
        radio = self.radio_class(serial)
        radio.status_fn = lambda _status: None
        radio.sync_in()

        channel = radio.get_memory(1)
        channel.name = "本机"
        channel.power = radio.get_features().valid_power_levels[0]
        radio.set_memory(channel)
        self.assertEqual(radio._mmap.get(0x2010, 1), b"\x00")
        self.assertEqual(
            radio._mmap.get(0x2020, 4),
            "本机".encode("gb18030"),
        )

        channel.power = radio.get_features().valid_power_levels[1]
        radio.set_memory(channel)
        self.assertEqual(radio._mmap.get(0x2010, 1), b"\x01")


if __name__ == "__main__":
    unittest.main()
