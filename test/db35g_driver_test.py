"""Offline protocol and memory-map tests for the Radioddity DB35-G."""

from collections import deque
import importlib.util
from pathlib import Path
import struct
import sys
import unittest


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "build_support/chirp-20261023"
PYTHON_VENDOR = ROOT / "assets/python/pyserial-3.5-py2.py3-none-any.whl"


def _load_bridge():
    spec = importlib.util.spec_from_file_location(
        "newchirp_chirp_bridge_db35g",
        ROOT / "scripts/chirp_bridge.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load chirp_bridge.py")
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


class FakeDB35GSerial:
    def __init__(self):
        self.timeout = 2
        self.responses = deque()
        self.writes = []

    def write(self, data):
        data = bytes(data)
        self.writes.append(data)
        if data == b"\x02PROGRAM" or data == b"\x06":
            self.responses.append(b"\x06")
        elif data == b"\x02":
            self.responses.append(b"SMP558\xff\xff")
        elif data[:1] == b"R":
            address, length = struct.unpack(">HB", data[1:])
            self.responses.append(
                data + bytes([address & 0xFF]) * length
            )
        elif data[:1] == b"W":
            self.responses.append(b"\x06")
        return len(data)

    def read(self, size):
        if not self.responses:
            return b""
        data = self.responses.popleft()
        if len(data) > size:
            self.responses.appendleft(data[size:])
            data = data[:size]
        return data


class DB35GDriverTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = _load_bridge().load_chirp(
            str(SOURCE),
            str(PYTHON_VENDOR),
            str(ROOT / "drivers"),
        )
        cls.radio_class = cls.directory.get_radio("Radioddity_DB35-G")
        cls.driver = sys.modules[cls.radio_class.__module__]

    def _blank_radio(self):
        radio = self.radio_class(None)
        radio._mmap = self.driver.memmap.MemoryMapBytes(
            b"\xFF" * self.driver.MEM_SIZE
        )
        radio.process_mmap()
        radio.status_fn = lambda _status: None
        return radio

    def test_new_driver_is_registered(self):
        self.assertEqual(
            self.radio_class.__module__,
            "newchirp.drivers.newchirp_db35g",
        )
        self.assertEqual(self.radio_class.BAUD_RATE, 115200)
        self.assertEqual(self.driver.NUM_CHANNELS, 80)
        self.assertEqual(self.driver.PAGE_SIZE, 16)
        self.assertEqual(self.driver.SETTINGS_ADDR, 0xE000)

    def test_channel_round_trip_preserves_frequency_tone_and_flags(self):
        from chirp import chirp_common
        from chirp.settings import (
            RadioSetting,
            RadioSettingGroup,
            RadioSettingValueBoolean,
        )

        radio = self._blank_radio()
        memory = chirp_common.Memory()
        memory.number = 1
        memory.freq = 462562500
        memory.duplex = "+"
        memory.offset = 5000000
        memory.tmode = "Cross"
        memory.cross_mode = "Tone->DTCS"
        memory.rtone = 100.0
        memory.rx_dtcs = 23
        memory.mode = "NFM"
        memory.power = self.driver.POWER_LEVELS[0]
        memory.skip = "S"
        memory.extra = RadioSettingGroup("extra", "Extra")
        memory.extra.append(
            RadioSetting(
                "busylock",
                "Busy Lock",
                RadioSettingValueBoolean(True),
            )
        )

        radio.set_memory(memory)
        restored = radio.get_memory(1)

        self.assertEqual(restored.freq, 462562500)
        self.assertEqual(restored.duplex, "+")
        self.assertEqual(restored.offset, 5000000)
        self.assertEqual(restored.tmode, "Cross")
        self.assertEqual(restored.cross_mode, "Tone->DTCS")
        self.assertEqual(restored.mode, "NFM")
        self.assertEqual(restored.power, self.driver.POWER_LEVELS[0])
        self.assertEqual(restored.skip, "S")
        self.assertTrue(bool(restored.extra["busylock"].value))

    def test_download_reads_all_channels_then_settings_page(self):
        radio = self._blank_radio()
        radio.pipe = FakeDB35GSerial()

        downloaded = self.driver.do_download(radio)
        raw = downloaded.get_packed()

        self.assertEqual(len(raw), self.driver.MEM_SIZE)
        self.assertEqual(
            raw[self.driver.SETTINGS_OFFSET:self.driver.SETTINGS_OFFSET + 16],
            b"\x00" * 16,
        )
        read_commands = [
            data
            for data in radio.pipe.writes
            if data.startswith(b"R")
        ]
        self.assertEqual(len(read_commands), 81)
        self.assertEqual(
            read_commands[-1],
            struct.pack(">cHB", b"R", 0xE000, 16),
        )

    def test_upload_writes_only_known_channel_and_settings_pages(self):
        radio = self._blank_radio()
        radio.pipe = FakeDB35GSerial()

        self.driver.do_upload(radio)

        write_commands = [
            data for data in radio.pipe.writes if data.startswith(b"W")
        ]
        self.assertEqual(len(write_commands), 81)
        self.assertEqual(len(write_commands[0]), 4 + 16)
        self.assertEqual(
            write_commands[-1][:4],
            struct.pack(">cHB", b"W", 0xE000, 16),
        )
        self.assertEqual(radio.pipe.writes[-1], b"\x62")

    def test_user_upload_is_blocked_pending_hardware_validation(self):
        radio = self._blank_radio()
        radio.pipe = FakeDB35GSerial()

        with self.assertRaisesRegex(Exception, "disabled"):
            radio.sync_out()

        self.assertEqual(radio.pipe.writes, [])


if __name__ == "__main__":
    unittest.main()
