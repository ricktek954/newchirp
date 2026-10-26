"""Offline tests for the experimental Baofeng GM-32 driver."""

from collections import deque
from pathlib import Path
import importlib.util
import sys
import unittest


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "build_support/chirp-20261023"
PYTHON_VENDOR = ROOT / "assets/python/pyserial-3.5-py2.py3-none-any.whl"
MEM_SIZE = 0x8380
IMAGE = Path.home() / "Downloads/gm32/Baofeng_UV-32_20261025.img"
ENCRYPTION_KEY = b"CO 7"
READ_RANGES = (
    (0x0000, 0x8040),
    (0x9000, 0x0040),
    (0xA000, 0x02C0),
    (0xD000, 0x0040),
)


def _load_bridge():
    spec = importlib.util.spec_from_file_location(
        "newchirp_chirp_bridge_gm32",
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
    result = bytearray(4)
    for index in range(4):
        part = tens % 100
        tens //= 100
        result[index] = (part // 10) << 4 | part % 10
    return bytes(result)


def _crypt(data):
    result = bytearray(data)
    for index, value in enumerate(result):
        key = ENCRYPTION_KEY[index % len(ENCRYPTION_KEY)]
        if key != 0x20 and value not in (0, 0xFF, key, key ^ 0xFF):
            result[index] ^= key
    return bytes(result)


def _record(rx, tx, name):
    record = bytearray(b"\xff" * 32)
    record[0:4] = _frequency_bytes(rx)
    record[4:8] = _frequency_bytes(tx)
    record[8:12] = b"\x00\x00\x00\x00"
    record[12:14] = b"\x00\x00"
    record[14] = 0
    record[15] = 0x22
    record[16:20] = b"\xff" * 4
    record[20:32] = name.encode("ascii").ljust(12, b"\xff")
    return bytes(record)


def _memory(radio, number, freq, **overrides):
    from chirp import chirp_common

    mem = chirp_common.Memory()
    mem.number = number
    mem.freq = freq
    mem.name = overrides.pop("name", "GM32")
    mem.duplex = overrides.pop("duplex", "")
    mem.offset = overrides.pop("offset", 0)
    mem.mode = overrides.pop("mode", "FM")
    mem.power = overrides.pop("power", radio.POWER_LEVELS[0])
    mem.tuning_step = 5.0
    for name, value in overrides.items():
        setattr(mem, name, value)
    return mem


def _expected_addresses():
    for start, size in READ_RANGES:
        yield from range(start, start + size, 0x40)


class FakeUV32CPS:
    def __init__(self, memory):
        self.memory = memory
        self.responses = deque()
        self.writes = []
        self.read_addresses = []
        self.write_addresses = []
        self.max_read_size = 256
        self.timeout = 2

    def log(self, _message):
        pass

    def write(self, data):
        data = bytes(data)
        self.writes.append(data)
        if data == b"PROGRAMCOLORPROU":
            self.responses.append(b"\x06")
        elif data == b"F":
            self.responses.append(b"\x88\x68\x90\x20" + b"\x00" * 12)
        elif data == b"M":
            self.responses.append(b"UV32PRO")
        elif data[:4] == b"SEND":
            self.responses.append(b"\x06")
        elif data[:1] == b"R":
            address = (data[1] << 8) | data[2]
            self.read_addresses.append(address)
            payload = _crypt(self.memory[address:address + data[3]])
            self.responses.append(
                b"W" + data[1:3] + bytes((data[3],)) + payload
            )
        elif data[:1] == b"W":
            address = (data[1] << 8) | data[2]
            self.write_addresses.append(address)
            length = data[3]
            self.memory[address:address + length] = _crypt(
                data[4:4 + length]
            )
            self.responses.append(b"\x06")

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


class GM32DriverTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        bridge = _load_bridge()
        cls.directory = bridge.load_chirp(
            str(SOURCE),
            str(PYTHON_VENDOR),
            str(ROOT / "drivers"),
        )
        cls.radio_class = cls.directory.get_radio("Baofeng_GM-32")

    def setUp(self):
        from chirp import memmap

        self.radio = self.radio_class(
            memmap.MemoryMapBytes(b"\xff" * MEM_SIZE)
        )

    def _radio_from_memory(self, memory):
        from chirp import memmap

        return self.radio_class(memmap.MemoryMapBytes(bytes(memory)))

    def test_catalog_and_memory_contract(self):
        self.assertEqual(
            self.directory.get_radio("Baofeng_GM-32"),
            self.radio_class,
        )
        self.assertEqual(self.radio_class.MEM_TOTAL, MEM_SIZE)
        self.assertEqual(self.radio_class.BLOCK_SIZE, 0x40)
        self.assertEqual(self.radio_class.BAUD_RATE, 115200)
        self.assertTrue(self.radio_class._has_support_for_banknames)
        self.assertTrue(self.radio_class.WANTS_DTR)
        self.assertTrue(self.radio_class.WANTS_RTS)
        self.assertFalse(self.radio_class.HARDWARE_FLOW)
        self.assertFalse(self.radio_class.XON_XOFF)

    def test_channel_names_use_cps_record_offset(self):
        memory = bytearray(b"\xff" * MEM_SIZE)
        memory[0:32] = _record(462_550_000, 467_550_000, "BROWARD")
        radio = self._radio_from_memory(memory)

        channel = radio.get_memory(1)
        self.assertFalse(channel.empty)
        self.assertEqual(channel.freq, 462_550_000)
        self.assertEqual(channel.name, "BROWARD")

        channel.name = "POMPANO"
        radio.set_memory(channel)
        self.assertEqual(radio._mmap.get(0x14, 12), b"POMPANO".ljust(12, b"\xff"))

    def test_bank_names_and_settings_map_to_cps_offsets(self):
        memory = bytearray(b"\xff" * MEM_SIZE)
        memory[0x8000:0x8040] = b"\x00" * 0x40
        memory[0x8000:0x8008] = b"\x04\x06\x02\x05\x05\x00\x00\x00"
        memory[0x8020:0x8028] = b"\x04\x06\x02\x05\x05\x00\x00\x00"
        memory[0x8040:0x8080] = b"\x00" * 0x40
        radio = self._radio_from_memory(memory)
        settings = list(radio.get_settings().walk())

        bank_name = next(
            item for item in settings
            if item.get_name() == "bank_name/0.name"
        )
        bank_name.value.set_value("BROWARD")

        squelch = next(
            item for item in settings
            if item.get_name() == "settings.squelch"
        )
        squelch.value.set_value(4)

        radio.set_settings(settings)

        self.assertEqual(radio._mmap.get(0x8280, 7), b"BROWARD")
        self.assertEqual(radio._mmap.get(0x8040, 1), b"\x04")

    def test_protocol_uses_cps_block_ranges(self):
        source_memory = bytearray(b"\xff" * 0xD040)
        source_memory[0:32] = _record(462_550_000, 467_550_000, "BROWARD")
        serial = FakeUV32CPS(source_memory)
        radio = self.radio_class(serial)
        radio.status_fn = lambda _status: None

        radio.sync_in()
        self.assertEqual(serial.read_addresses, list(_expected_addresses()))
        self.assertEqual(radio.get_memory(1).name, "BROWARD")

        channel = radio.get_memory(1)
        channel.name = "POMPANO"
        radio.set_memory(channel)
        radio.sync_out()
        self.assertEqual(serial.write_addresses, list(_expected_addresses()))
        self.assertTrue(
            bytes(serial.memory[0x14:0x20]).startswith(b"POMPANO")
        )
    def test_model_prompts_and_features(self):
        prompts = self.radio_class.get_prompts()
        self.assertIn("experimental", prompts.experimental.lower())
        self.assertIn("Turn off the radio", prompts.pre_download)
        self.assertIn("Turn off the radio", prompts.pre_upload)
        self.assertIn("backup", prompts.experimental.lower())
        self.assertIn("tested on a radio", prompts.experimental.lower())
        self.assertFalse(self.radio_class._gmrs)

        features = self.radio.get_features()
        self.assertEqual(features.memory_bounds, (1, 1000))
        self.assertEqual(features.valid_duplexes, ["", "+", "off"])
        self.assertTrue(features.has_settings)
        self.assertTrue(features.has_bank)
        self.assertEqual(
            [str(level) for level in features.valid_power_levels],
            ["High", "Low", "Medium"],
        )

    def test_channel_8_is_forced_simplex_narrow_low(self):
        mem = _memory(
            self.radio,
            8,
            467562500,
            duplex="+",
            offset=5000000,
            mode="FM",
            power=self.radio.POWER_LEVELS[0],
        )
        self.assertEqual(self.radio.validate_memory(mem), [])
        self.assertEqual(mem.duplex, "+")
        self.radio.set_memory(mem)
        stored = self.radio.get_memory(8)
        self.assertEqual(stored.duplex, "")
        self.assertEqual(stored.offset, 0)
        self.assertEqual(stored.mode, "NFM")
        self.assertEqual(str(stored.power), "Low")

    def test_channel_8_receive_only_stays_off_and_narrow(self):
        mem = _memory(
            self.radio,
            9,
            467587500,
            duplex="off",
            mode="FM",
            power=self.radio.POWER_LEVELS[0],
        )
        self.radio.set_memory(mem)
        stored = self.radio.get_memory(9)
        self.assertEqual(stored.duplex, "off")
        self.assertEqual(stored.mode, "NFM")
        self.assertEqual(str(stored.power), "Low")

    def test_repeater_output_keeps_plus_five(self):
        mem = _memory(
            self.radio,
            16,
            462575000,
            duplex="+",
            offset=600000,
        )
        self.radio.set_memory(mem)
        stored = self.radio.get_memory(16)
        self.assertEqual(stored.duplex, "+")
        self.assertEqual(stored.offset, 5000000)

    def test_repeater_output_minus_becomes_simplex(self):
        mem = _memory(
            self.radio,
            16,
            462575000,
            duplex="-",
            offset=5000000,
        )
        self.assertEqual(self.radio.validate_memory(mem), [])
        self.assertEqual(mem.duplex, "-")
        self.radio.set_memory(mem)
        stored = self.radio.get_memory(16)
        self.assertEqual(stored.duplex, "")
        self.assertEqual(stored.offset, 0)

    def test_simplex_channels_drop_a_shift(self):
        mem = _memory(
            self.radio,
            1,
            462562500,
            duplex="+",
            offset=5000000,
        )
        self.radio.set_memory(mem)
        stored = self.radio.get_memory(1)
        self.assertEqual(stored.duplex, "")
        self.assertEqual(stored.offset, 0)

    def test_repeater_input_cannot_use_plus(self):
        mem = _memory(self.radio, 40, 467550000, duplex="+", offset=5000000)
        self.radio.set_memory(mem)
        stored = self.radio.get_memory(40)
        self.assertEqual(stored.duplex, "")
        self.assertEqual(stored.offset, 0)
        self.assertFalse(stored.empty)

    def test_non_gmrs_frequency_is_receive_only(self):
        mem = _memory(
            self.radio,
            31,
            470550000,
            name="HAMs",
            duplex="",
            mode="FM",
            power=self.radio.POWER_LEVELS[0],
        )
        self.radio.set_memory(mem)
        stored = self.radio.get_memory(31)
        self.assertEqual(stored.name, "HAMs")
        self.assertEqual(stored.freq, 470550000)
        self.assertEqual(stored.duplex, "off")
        self.assertEqual(stored.offset, 0)
        self.assertEqual(stored.mode, "FM")
        self.assertEqual(str(stored.power), "High")

    def test_unset_frequency_is_stored_empty(self):
        mem = _memory(self.radio, 50, 0, name="NEW 50")
        mem.empty = False
        self.assertEqual(self.radio.validate_memory(mem), [])
        self.radio.set_memory(mem)
        self.assertTrue(self.radio.get_memory(50).empty)

    @unittest.skipUnless(IMAGE.is_file(), "GM-32 sample image is not in Downloads")
    def test_sample_image_keeps_uv32_identity_and_gm32_write_rules(self):
        from chirp.settings import RadioSettingGroup

        opened = self.directory.get_radio_by_image(str(IMAGE))
        self.assertEqual(opened.MODEL, "UV-32")
        self.assertNotIsInstance(opened, self.radio_class)

        radio = self.radio_class(str(IMAGE))
        channel8 = radio.get_memory(8)
        self.assertEqual(channel8.freq, 467562500)
        self.assertEqual(channel8.duplex, "")
        self.assertEqual(channel8.mode, "NFM")
        self.assertEqual(str(channel8.power), "Low")

        ranchino = radio.get_memory(25)
        self.assertIn("Ranchino", ranchino.name)

        hams = radio.get_memory(31)
        self.assertIn("HAM", hams.name.upper())
        self.assertEqual(hams.freq, 470550000)
        self.assertEqual(hams.duplex, "")
        radio.set_memory(hams)
        stored = radio.get_memory(31)
        self.assertEqual(stored.duplex, "off")
        self.assertIn("HAM", stored.name.upper())

        labels = [
            group.get_shortname()
            for group in radio.get_settings()
            if isinstance(group, RadioSettingGroup)
        ]
        self.assertIn("Basic Settings", labels)
        self.assertIn("Bank names", labels)
if __name__ == "__main__":
    unittest.main()
