"""Offline protocol and memory-map tests for the Radioddity X1 Pro."""

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
        "newchirp_chirp_bridge_x1pro",
        ROOT / "scripts/chirp_bridge.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load chirp_bridge.py")
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


class FakeX1ProSerial:
    def __init__(self, image, fragment_replies=False):
        self.timeout = 0.25
        self.writes = []
        self.responses = deque()
        self.memory = bytearray(image)
        self.fragment_replies = fragment_replies
        self.bad_write_ack = None
        self.read_override = None

    def reset_input_buffer(self):
        self.responses.clear()

    def flush(self):
        pass

    def write(self, data):
        data = bytes(data)
        self.writes.append(data)
        if data == b"\x02PROGRAM":
            self._queue(b"\x06")
        elif data == b"\x02":
            self._queue(b"SMP558\xff\xff")
        elif data == b"\x06":
            self._queue(b"\x06")
        elif data[:1] == b"R":
            address, length = struct.unpack(">HB", data[1:])
            payload = self.memory[address:address + length]
            reply = data + payload
            self._queue(
                self.read_override if self.read_override is not None else reply
            )
        elif data[:1] == b"W":
            address, length = struct.unpack(">HB", data[1:4])
            if self.bad_write_ack == address:
                self._queue(b"\x15")
            else:
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


def _download_image():
    image = bytearray(b"\xff" * 0xE010)
    image[0xE000:0xE010] = bytes.fromhex(
        "6B 00 00 00 00 00 01 00 00 00 00 00 00 00 00 00"
    )
    for number in range(1, 31):
        offset = (number - 1) * 16
        rx = 462_562_500 + (number - 1) * 12_500
        tx = rx + (5_000_000 if number >= 23 else 0)
        flags = (number % 3) | (0x04 if number % 2 else 0)
        image[offset:offset + 16] = (
            struct.pack(">II", rx, tx)
            + bytes.fromhex("e8 03 9e 02")
            + bytes((flags, number, number + 1, number + 2))
        )
    return image


def _setting_by_name(radio, name):
    for item_name, item in radio.get_settings().items():
        if item_name == name:
            return item
    raise AssertionError(name)


def _memory(chirp_common, number=1, **fields):
    memory = chirp_common.Memory()
    memory.number = number
    memory.freq = 462_562_500
    memory.duplex = ""
    memory.offset = 0
    memory.mode = "FM"
    memory.tmode = ""
    memory.skip = ""
    for name, value in fields.items():
        setattr(memory, name, value)
    return memory


class X1ProDriverTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        bridge = _load_bridge()
        cls.directory = bridge.load_chirp(
            str(SOURCE),
            str(PYTHON_VENDOR),
            str(ROOT / "drivers"),
        )
        cls.radio_class = cls.directory.get_radio("Radioddity_X1_Pro")
        cls.driver = sys.modules[cls.radio_class.__module__]

        from chirp import chirp_common
        from chirp.settings import RadioSettingGroup, RadioSettingValueBoolean
        from chirp.settings import RadioSetting, RadioSettingValueList

        cls.chirp_common = chirp_common
        cls.RadioSetting = RadioSetting
        cls.RadioSettingGroup = RadioSettingGroup
        cls.RadioSettingValueBoolean = RadioSettingValueBoolean
        cls.RadioSettingValueList = RadioSettingValueList

    def _new_radio(self, image=None):
        radio = self.radio_class(None)
        radio._mmap = self.driver.memmap.MemoryMapBytes(
            bytes(image if image is not None else b"\x00" * self.driver.IMAGE_SIZE)
        )
        radio.process_mmap()
        radio.status_fn = lambda _status: None
        return radio

    def test_driver_is_registered_as_experimental_read_write(self):
        self.assertEqual(
            self.radio_class.__module__,
            "newchirp.drivers.newchirp_x1pro",
        )
        self.assertTrue(
            issubclass(
                self.radio_class,
                self.chirp_common.ExperimentalRadio,
            )
        )
        prompts = self.radio_class.get_prompts()
        self.assertIn("experimental", prompts.experimental.lower())
        self.assertIn("write path", prompts.experimental)
        self.assertIn("30-channel map", prompts.experimental)
        self.assertIn("115200 8N1", prompts.info)
        self.assertIn("backup", prompts.pre_download.lower())
        self.assertIn("read the radio back", prompts.pre_upload.lower())

        features = self.radio_class(None).get_features()
        self.assertEqual(features.memory_bounds, (1, 30))
        self.assertFalse(features.has_name)
        self.assertTrue(features.has_settings)

    def test_download_uses_oem_handshake_settings_then_all_channel_pages(self):
        image = _download_image()
        radio = self._new_radio()
        radio.pipe = FakeX1ProSerial(image)

        radio.sync_in()

        self.assertEqual(
            radio.pipe.writes[:3],
            [b"\x02PROGRAM", b"\x02", b"\x06"],
        )
        reads = [write for write in radio.pipe.writes if write[:1] == b"R"]
        self.assertEqual(len(reads), 31)
        self.assertEqual(reads[0], b"R\xe0\x00\x10")
        self.assertEqual(
            reads[1:],
            [
                struct.pack(">BHB", 0x52, index * 16, 16)
                for index in range(30)
            ],
        )
        self.assertEqual(radio.pipe.writes[-1], b"\x62")
        downloaded = radio._mmap.get_packed()
        self.assertEqual(
            downloaded[:30 * 16],
            bytes(image[:30 * 16]),
        )
        self.assertEqual(
            downloaded[self.driver.PARAM_BASE:self.driver.IMAGE_SIZE],
            bytes(image[self.driver.PARAM_BASE:self.driver.IMAGE_SIZE]),
        )

    def test_fragmented_download_replies_are_accumulated_exactly(self):
        image = _download_image()
        radio = self._new_radio()
        radio.pipe = FakeX1ProSerial(image, fragment_replies=True)

        radio.sync_in()

        downloaded = radio._mmap.get_packed()
        self.assertEqual(downloaded[:30 * 16], bytes(image[:30 * 16]))
        self.assertEqual(
            downloaded[self.driver.PARAM_BASE:self.driver.IMAGE_SIZE],
            bytes(image[self.driver.PARAM_BASE:self.driver.IMAGE_SIZE]),
        )
        self.assertEqual(radio.get_memory(30).freq, 462_925_000)

    def test_upload_writes_settings_first_then_all_channel_pages(self):
        image = _download_image()
        radio = self._new_radio(image)
        radio.pipe = FakeX1ProSerial(b"\xff" * self.driver.IMAGE_SIZE)

        with mock.patch.object(self.driver, "INTER_BLOCK_DELAY", 0):
            radio.sync_out()

        writes = [write for write in radio.pipe.writes if write[:1] == b"W"]
        self.assertEqual(len(writes), 31)
        self.assertEqual(writes[0][:4], b"W\xe0\x00\x10")
        self.assertEqual(
            [write[:4] for write in writes[1:]],
            [
                struct.pack(">BHB", 0x57, index * 16, 16)
                for index in range(30)
            ],
        )
        self.assertTrue(all(len(write) == 20 for write in writes))
        self.assertEqual(
            radio.pipe.memory[self.driver.PARAM_BASE:self.driver.IMAGE_SIZE],
            image[self.driver.PARAM_BASE:self.driver.IMAGE_SIZE],
        )
        expected_channels = bytearray()
        for index in range(30):
            page = bytearray(image[index * 16:(index + 1) * 16])
            page[8:10] = bytes((page[9], page[8]))
            page[10:12] = bytes((page[11], page[10]))
            expected_channels.extend(page)
        self.assertEqual(
            radio.pipe.memory[:30 * self.driver.BLOCK_SIZE],
            expected_channels,
        )
        self.assertEqual(radio.pipe.writes[-1], b"\x62")

    def test_upload_uses_oem_big_endian_tone_words_without_changing_other_bytes(
        self,
    ):
        image = bytearray(self.driver.IMAGE_SIZE)
        image[22 * 16:23 * 16] = (
            struct.pack(">II", 462_550_000, 467_550_000)
            + bytes.fromhex("9e 02 ff ff 21 a5 c3 d4")
        )
        radio = self._new_radio(image)
        radio.pipe = FakeX1ProSerial(b"\xff" * self.driver.IMAGE_SIZE)

        with mock.patch.object(self.driver, "INTER_BLOCK_DELAY", 0):
            radio.sync_out()

        written = radio.pipe.memory[22 * 16:23 * 16]
        self.assertEqual(
            written,
            bytes.fromhex(
                "1b 91 f3 f0 1b de 3f 30 "
                "02 9e ff ff 21 a5 c3 d4"
            ),
        )
        self.assertEqual(
            bytes(radio._mmap[22 * 16:23 * 16]),
            bytes(image[22 * 16:23 * 16]),
        )
        decoded = radio.get_memory(23)
        self.assertEqual(decoded.tmode, "Cross")
        self.assertEqual(decoded.cross_mode, "->Tone")
        self.assertEqual(decoded.ctone, 67.0)

    def test_inclusive_upper_frequency_bound_is_writable(self):
        radio = self._new_radio()
        memory = _memory(
            self.chirp_common,
            number=30,
            freq=467_725_000,
        )

        radio.set_memory(memory)

        self.assertEqual(radio.get_memory(30).freq, 467_725_000)

    def test_every_write_must_return_the_oem_ack(self):
        radio = self._new_radio()
        radio.pipe = FakeX1ProSerial(b"\x00" * self.driver.IMAGE_SIZE)
        radio.pipe.bad_write_ack = 0x0010

        with self.assertRaisesRegex(
            self.driver.errors.RadioError,
            "did not acknowledge write block 0x0010",
        ):
            with mock.patch.object(self.driver, "INTER_BLOCK_DELAY", 0):
                radio.sync_out()

        self.assertEqual(radio.pipe.writes[-1], b"\x62")

    def test_short_and_mismatched_read_replies_fail(self):
        radio = self._new_radio()
        radio.pipe = FakeX1ProSerial(
            b"\x00" * self.driver.IMAGE_SIZE,
        )
        radio.pipe.read_override = b"R\xe0\x00\x10short"

        with mock.patch.object(self.driver, "READ_TIMEOUT", 0.01):
            with self.assertRaisesRegex(
                self.driver.errors.RadioError,
                "Short reply.*0xE000",
            ):
                radio.sync_in()
        self.assertEqual(radio.pipe.writes[-1], b"\x62")

        radio = self._new_radio()
        radio.pipe = FakeX1ProSerial(
            b"\x00" * self.driver.IMAGE_SIZE,
        )
        radio.pipe.read_override = b"S\xe0\x00\x10" + b"\x00" * 16
        with mock.patch.object(self.driver, "READ_TIMEOUT", 0.01):
            with self.assertRaisesRegex(
                self.driver.errors.RadioError,
                "mismatched read header",
            ):
                radio.sync_in()
        self.assertEqual(radio.pipe.writes[-1], b"\x62")

    def test_channel_fields_round_trip(self):
        radio = self._new_radio()
        memory = _memory(
            self.chirp_common,
            number=23,
            freq=462_550_000,
            duplex="+",
            offset=5_000_000,
            mode="NFM",
            power=self.driver.POWER_LEVELS[2],
            skip="S",
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
        restored = radio.get_memory(23)
        raw = bytes(radio._mmap[22 * 16:23 * 16])

        self.assertEqual(struct.unpack(">II", raw[:8]), (462_550_000, 467_550_000))
        self.assertEqual(raw[8:10], b"\x13\xa8")
        self.assertEqual(raw[10:12], bytes.fromhex("e8 03"))
        self.assertEqual(raw[12], 0x22)
        self.assertEqual(restored.freq, 462_550_000)
        self.assertEqual(restored.duplex, "+")
        self.assertEqual(restored.offset, 5_000_000)
        self.assertEqual(restored.mode, "NFM")
        self.assertEqual(restored.power, self.driver.POWER_LEVELS[2])
        self.assertEqual(restored.skip, "S")
        self.assertEqual(restored.tmode, "Cross")
        self.assertEqual(restored.cross_mode, "Tone->DTCS")
        self.assertEqual(restored.rtone, 100.0)
        self.assertEqual(restored.rx_dtcs, 23)
        self.assertEqual(restored.dtcs_polarity, "RN")
        self.assertTrue(bool(restored.extra["busylock"].value))

    def test_dtcs_split_and_empty_channel_round_trip(self):
        radio = self._new_radio()
        memory = _memory(
            self.chirp_common,
            number=8,
            freq=467_562_500,
            mode="NFM",
            power=self.driver.POWER_LEVELS[0],
            tmode="DTCS",
            dtcs=606,
            rx_dtcs=306,
            dtcs_polarity="RN",
        )
        radio.set_memory(memory)

        restored = radio.get_memory(8)
        self.assertEqual(restored.tmode, "DTCS")
        self.assertEqual(restored.dtcs, 606)
        self.assertEqual(restored.rx_dtcs, 306)
        self.assertEqual(restored.dtcs_polarity, "RN")

        restored.empty = True
        radio.set_memory(restored)
        self.assertTrue(radio.get_memory(8).empty)

    def test_settings_round_trip_and_preserve_unknown_bits(self):
        image = bytearray(self.driver.IMAGE_SIZE)
        image[self.driver.PARAM_BASE:self.driver.PARAM_BASE + 16] = bytes.fromhex(
            "EB 20 08 00 00 00 01 00 5A 00 00 00 00 00 00 00"
        )
        radio = self._new_radio(image)

        self.assertEqual(str(_setting_by_name(radio, "sqlevel").value), "5")
        self.assertTrue(bool(_setting_by_name(radio, "keytone").value))
        self.assertTrue(bool(_setting_by_name(radio, "rogerbeep").value))
        self.assertTrue(bool(_setting_by_name(radio, "powsave").value))
        self.assertEqual(str(_setting_by_name(radio, "scanmode").value), "TS")
        self.assertEqual(str(_setting_by_name(radio, "nrc").value), "1")
        self.assertEqual(str(_setting_by_name(radio, "vox").value), "Off")

        settings = radio.get_settings()
        replacements = {
            "sqlevel": "8",
            "keytone": False,
            "rogerbeep": False,
            "powsave": True,
            "scanmode": "OS",
            "nrc": "3",
            "vox": "On",
        }
        for item_name, item in settings.items():
            if item_name in replacements:
                item.value.set_value(replacements[item_name])
        radio.set_settings(settings)

        raw = bytes(
            radio._mmap[
                self.driver.PARAM_BASE:self.driver.PARAM_BASE + 16
            ]
        )
        self.assertEqual(raw[0], 0x70)
        self.assertEqual(raw[1], 0x20)
        self.assertEqual(raw[2], 0x00)
        self.assertEqual(raw[6], 0x03)
        self.assertEqual(raw[7], 0x01)
        self.assertEqual(raw[8], 0x5A)
        self.assertEqual(raw[9:], b"\x00" * 7)
        self.assertEqual(str(_setting_by_name(radio, "sqlevel").value), "8")
        self.assertEqual(str(_setting_by_name(radio, "vox").value), "On")

    def test_invalid_frequency_is_rejected_before_image_changes(self):
        radio = self._new_radio()
        before = radio._mmap.get_packed()
        memory = _memory(self.chirp_common, freq=450_000_000)

        with self.assertRaisesRegex(
            self.driver.errors.RadioError,
            "GMRS range",
        ):
            radio.set_memory(memory)

        self.assertEqual(radio._mmap.get_packed(), before)


if __name__ == "__main__":
    unittest.main()
