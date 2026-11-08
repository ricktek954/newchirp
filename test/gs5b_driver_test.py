"""Offline transport and memory-map tests for the Radioddity GS-5B 1.XX."""

from collections import deque
import importlib.util
from pathlib import Path
import struct
import sys
import unittest
from unittest import mock

from chirp_test_source import chirp_source


ROOT = Path(__file__).resolve().parent.parent
SOURCE = chirp_source()
PYTHON_VENDOR = ROOT / "assets/python/pyserial-3.5-py2.py3-none-any.whl"


def _load_bridge():
    spec = importlib.util.spec_from_file_location(
        "newchirp_chirp_bridge_gs5b",
        ROOT / "scripts/chirp_bridge.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load chirp_bridge.py")
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


class FakeGS5BSerial:
    def __init__(self, image, fragment_replies=False):
        self.timeout = 0.25
        self.writes = []
        self.responses = deque()
        self.memory = bytearray(image)
        self.fragment_replies = fragment_replies
        self.ident = b"GS-5BPRO-1.XX\x00\x00\x00"

    def reset_input_buffer(self):
        self.responses.clear()

    def flush(self):
        pass

    def write(self, data):
        data = bytes(data)
        self.writes.append(data)
        if data == b"PROGRAMSHXPU":
            self._queue(b"\x06")
        elif data == b"F":
            self._queue(self.ident)
        elif data == b"E":
            return len(data)
        elif data[:1] == b"R":
            address, length = struct.unpack(">HB", data[1:4])
            self._queue(data + self.memory[address:address + length])
        elif data[:1] == b"W":
            address, length = struct.unpack(">HB", data[1:4])
            self.memory[address:address + length] = data[4:]
            self._queue(b"\x06")
        return len(data)

    def read(self, size):
        if not self.responses:
            return b""
        data = self.responses.popleft()
        if len(data) > size:
            self.responses.appendleft(data[size:])
            data = data[:size]
        return data

    def _queue(self, data):
        if not self.fragment_replies:
            self.responses.append(data)
            return
        self.responses.extend(bytes((value,)) for value in data)


def _image():
    return bytearray(b"\xff" * 0xB040)


def _memory(chirp_common, number=1, **fields):
    memory = chirp_common.Memory()
    memory.number = number
    memory.freq = 146_520_000
    memory.duplex = ""
    memory.offset = 0
    memory.mode = "NFM"
    memory.tmode = ""
    memory.skip = ""
    memory.name = ""
    for name, value in fields.items():
        setattr(memory, name, value)
    return memory


class GS5BDriverTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        bridge = _load_bridge()
        cls.directory = bridge.load_chirp(
            str(SOURCE),
            str(PYTHON_VENDOR),
            str(ROOT / "drivers"),
        )
        cls.radio_class = cls.directory.get_radio("Radioddity_GS-5B_1.XX")
        cls.driver = sys.modules[cls.radio_class.__module__]

        from chirp import chirp_common
        from chirp.settings import RadioSettingGroup, RadioSettingValueBoolean
        from chirp.settings import RadioSetting

        cls.chirp_common = chirp_common
        cls.RadioSetting = RadioSetting
        cls.RadioSettingGroup = RadioSettingGroup
        cls.RadioSettingValueBoolean = RadioSettingValueBoolean

    def _new_radio(self, image=None):
        radio = self.radio_class(None)
        radio._mmap = self.driver.memmap.MemoryMapBytes(
            bytes(image if image is not None else _image())
        )
        radio.process_mmap()
        radio.status_fn = lambda _status: None
        return radio

    def test_driver_is_registered_as_experimental(self):
        self.assertEqual(
            self.radio_class.__module__,
            "newchirp.drivers.newchirp_gs5b",
        )
        self.assertTrue(
            issubclass(
                self.radio_class,
                self.chirp_common.ExperimentalRadio,
            )
        )
        features = self.radio_class(None).get_features()
        self.assertEqual(features.memory_bounds, (1, 512))
        self.assertEqual(features.valid_name_length, 12)
        self.assertTrue(features.has_name)
        prompts = self.radio_class.get_prompts()
        self.assertIn("experimental", prompts.experimental.lower())
        self.assertIn("2025", prompts.experimental)
        self.assertIn("OEM CPS backup", prompts.pre_upload)
        legacy = self.directory.get_radio("Radioddity_GS-5B")
        self.assertNotEqual(legacy, self.radio_class)
        self.assertEqual(legacy.MODEL, "GS-5B")

    def test_download_uses_cps_handshake_and_all_mapped_pages(self):
        image = _image()
        radio = self._new_radio()
        radio.pipe = FakeGS5BSerial(image)
        radio.sync_in()

        self.assertEqual(
            radio.pipe.writes[:2],
            [b"PROGRAMSHXPU", b"F"],
        )
        reads = [write for write in radio.pipe.writes if write[:1] == b"R"]
        self.assertEqual(len(reads), 323)
        self.assertEqual(reads[0], b"R\x00\x00\x40")
        self.assertEqual(reads[255], b"R\x3f\xc0\x40")
        self.assertEqual(reads[256], b"R\x80\x00\x40")
        self.assertEqual(reads[257], b"R\x90\x00\x40")
        self.assertEqual(reads[258], b"R\xa0\x00\x40")
        self.assertEqual(reads[-1], b"R\xb0\x00\x40")
        self.assertEqual(radio.pipe.writes[-1], b"E")

    def test_fragmented_replies_are_accumulated_exactly(self):
        image = _image()
        image[0:4] = bytes.fromhex("00 20 65 14")
        radio = self._new_radio()
        radio.pipe = FakeGS5BSerial(image, fragment_replies=True)
        radio.sync_in()
        self.assertEqual(radio.get_memory(1).freq, 146_520_000)

    def test_upload_writes_all_mapped_pages_and_exits(self):
        image = _image()
        radio = self._new_radio(image)
        radio.pipe = FakeGS5BSerial(_image())
        radio.sync_out()

        writes = [write for write in radio.pipe.writes if write[:1] == b"W"]
        self.assertEqual(len(writes), 323)
        self.assertTrue(all(len(write) == 68 for write in writes))
        self.assertEqual(writes[0][:4], b"W\x00\x00\x40")
        self.assertEqual(writes[-1][:4], b"W\xb0\x00\x40")
        self.assertEqual(radio.pipe.writes[-1], b"E")

    def test_channel_fields_round_trip_using_cps_encoding(self):
        radio = self._new_radio()
        memory = _memory(
            self.chirp_common,
            number=17,
            freq=146_520_000,
            duplex="split",
            offset=147_520_000,
            mode="FM",
            power=self.driver.POWER_LEVELS[1],
            skip="S",
            name="TEST 5B",
            tmode="Cross",
            cross_mode="Tone->DTCS",
            rtone=100.0,
            rx_dtcs=23,
            dtcs_polarity="RN",
        )
        memory.extra = self.RadioSettingGroup("extra", "Extra")
        memory.extra.append(
            self.RadioSetting(
                "busylock",
                "Busy Lock",
                self.RadioSettingValueBoolean(True),
            )
        )

        radio.set_memory(memory)
        radio._mmap.set(
            16 * 32 + 16,
            bytes.fromhex("de ad be ef"),
        )
        radio.set_memory(memory)
        raw = bytes(radio._mmap[16 * 32:17 * 32])
        restored = radio.get_memory(17)

        self.assertEqual(raw[0:8], bytes.fromhex(
            "00 20 65 14 00 20 75 14"
        ))
        self.assertEqual(
            raw[8:10],
            bytes((len(self.driver.DCS_CODES) + 1, 0)),
        )
        self.assertEqual(raw[10:12], bytes.fromhex("e8 03"))
        self.assertEqual(raw[14], 1)
        self.assertEqual(raw[15], 0x08)
        self.assertEqual(raw[16:20], bytes.fromhex("de ad be ef"))
        self.assertEqual(raw[20:32], b"TEST 5B\xff\xff\xff\xff\xff")
        self.assertEqual(restored.name, "TEST 5B")
        self.assertEqual(restored.freq, 146_520_000)
        self.assertEqual(restored.offset, 147_520_000)
        self.assertEqual(restored.tmode, "Cross")
        self.assertEqual(restored.cross_mode, "Tone->DTCS")
        self.assertEqual(restored.rtone, 100.0)
        self.assertEqual(restored.rx_dtcs, 23)
        self.assertEqual(restored.dtcs_polarity, "RN")
        self.assertTrue(bool(restored.extra["busylock"].value))

    def test_dcs_normal_and_inverted_indices_match_cps_table(self):
        self.assertEqual(self.driver._encode_tone(("DCS", 23, False)), b"\x01\x00")
        self.assertEqual(
            self.driver._encode_tone(("DCS", 23, True)),
            bytes((len(self.driver.DCS_CODES) + 1, 0)),
        )
        self.assertEqual(
            self.driver._decode_tone(b"\x01\x00"),
            ("DCS", 23, False),
        )
        self.assertEqual(
            self.driver._decode_tone(
                bytes((len(self.driver.DCS_CODES) + 1, 0))
            ),
            ("DCS", 23, True),
        )
        self.assertEqual(
            self.driver._encode_tone(("DCS", 645, False)),
            bytes((self.driver.DCS_CODES.index(645) + 1, 0)),
        )

    def test_empty_channel_uses_cps_ff_record(self):
        radio = self._new_radio()
        memory = _memory(self.chirp_common, number=512)
        radio.set_memory(memory)
        self.assertFalse(radio.get_memory(512).empty)
        memory.empty = True
        radio.set_memory(memory)
        self.assertTrue(radio.get_memory(512).empty)
        self.assertEqual(
            bytes(radio._mmap[511 * 32:512 * 32]),
            b"\xff" * 32,
        )

    def test_short_and_mismatched_reads_fail(self):
        radio = self._new_radio()
        radio.pipe = FakeGS5BSerial(_image())
        original = radio.pipe.write

        def short_write(data):
            if data[:1] == b"R":
                radio.pipe.writes.append(bytes(data))
                radio.pipe._queue(data + b"\x00" * 4)
                return len(data)
            return original(data)

        radio.pipe.write = short_write
        with mock.patch.object(self.driver, "READ_TIMEOUT", 0.01):
            with mock.patch.object(self.driver, "RETRIES", 1):
                with self.assertRaisesRegex(
                    self.driver.errors.RadioError,
                    "Short reply",
                ):
                    radio.sync_in()
        self.assertEqual(radio.pipe.writes[-1], b"E")


if __name__ == "__main__":
    unittest.main()
