"""Offline tests for the experimental Retevis MA1 A9305B driver."""

import importlib.util
from pathlib import Path
import struct
import sys
import unittest


from chirp_test_source import chirp_source


ROOT = Path(__file__).resolve().parent.parent
SOURCE = chirp_source()
PYTHON_VENDOR = ROOT / "assets/python/pyserial-3.5-py2.py3-none-any.whl"

MEM_SIZE = 0xD000
ACK = b"\xFE\xFE\xEF\xEE\xE6\x00\xFD"
HANDSHAKE_ACK = b"\xFE\xFE\xEF\xEE\xE1\x26\x72\x00\x00"
READ_COMMAND = b"\xFE\xFE\xEE\xEF\xEB"
READ_RESPONSE = b"\xFE\xFE\xEF\xEE\xE4"
WRITE_COMMAND = b"\xFE\xFE\xEE\xEF\xE4"
READ_RANGES = (
    (0x0000, 0x1680),
    (0x19C0, 0x2B80),
    (0x3200, 0x3284),
    (0x4000, 0xBED0),
)


def _load_bridge():
    spec = importlib.util.spec_from_file_location(
        "newchirp_chirp_bridge_retevis_ma1_a9305b",
        ROOT / "scripts/chirp_bridge.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load chirp_bridge.py")
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


def _frequency(value):
    return struct.pack("<I", value // 10)


def _record(
    rx=146_520_000,
    tx=146_520_000,
    name="TEST",
    power=1,
    narrow=False,
    am=False,
    step=4,
):
    raw = bytearray(b" " * 21)
    raw[0:4] = _frequency(rx)
    raw[4:8] = _frequency(tx)
    raw[8:12] = bytes.fromhex("FF0FFF0F")
    raw[12] = ((power & 0x03) << 6) | (0x20 if narrow else 0)
    raw[13] = (0x01 if am else 0) | (0x04 if name else 0)
    raw[14] = step
    raw[15:21] = name.encode("ascii", "replace")[:6].ljust(6, b" ")
    return raw


def _set_bitmap(image, offset, number, enabled=True):
    byte = offset + number // 8
    mask = 1 << (number % 8)
    if enabled:
        image[byte] |= mask
    else:
        image[byte] &= ~mask


def _image():
    image = bytearray(b"\xFF" * MEM_SIZE)
    image[0x19C0:0x19CA] = b"MA1-A9305B"
    image[0x1180:0x11BA] = b"\x00" * 0x3A
    image[0xB600:0xB6C8] = b"\x00" * 0xC8
    image[0x0000:0x0015] = _record(name="CALL", power=0)
    image[0x0015:0x002A] = _record(
        145_100_000,
        145_700_000,
        name="LOCAL",
        power=2,
        narrow=True,
    )
    image[0x4000:0x4015] = _record(
        430_125_000,
        438_125_000,
        name="UHF",
        am=True,
    )

    # Channel 1 uses a 6-character name plus the three-byte extension.
    image[0x000F:0x0015] = b"CHAN01"
    image[0x2300:0x230A] = b"234567890 "

    _set_bitmap(image, 0x1180, 0)
    _set_bitmap(image, 0x1180, 1)
    _set_bitmap(image, 0xB600, 0)
    _set_bitmap(image, 0x11A0, 1)
    return bytes(image)


def _checksum(data):
    total = sum(data) & 0xFF
    return 0 if total == 0 else 256 - total


class FakeA9305BSerial:
    def __init__(
        self,
        image,
        read_payload_limit=94,
        read_checksum_override=None,
    ):
        self.image = bytearray(image)
        self.read_payload_limit = read_payload_limit
        self.read_checksum_override = read_checksum_override
        self.baudrate = 9600
        self.timeout = 0.2
        self._responses = bytearray()
        self._baud_pending = False
        self.writes = []
        self.read_addresses = []
        self.write_addresses = []

    def _enqueue(self, data):
        self._responses.extend(data)

    def write(self, data):
        data = bytes(data)
        self.writes.append(data)
        command = data[4] if len(data) >= 5 else None
        if command == 0xE0:
            response = bytearray(36)
            response[:9] = HANDSHAKE_ACK
            response[-1] = 0xFD
            response[18:20] = b"00"
            self._enqueue(response)
        elif command == 0xE6:
            self._baud_pending = True
        elif command == 0xE7:
            self._enqueue(ACK)
        elif command in (0xE2, 0xE3, 0xE5):
            self._enqueue(ACK)
        elif command == 0xEB:
            address = int(data[5:9], 16)
            length = int(data[9:11], 16)
            self.read_addresses.append(address)
            returned_length = min(length, self.read_payload_limit)
            payload = bytes(self.image[address:address + returned_length])
            checksum = self.read_checksum_override
            if checksum is None:
                checksum = _checksum(
                    struct.pack(">I", address)
                    + bytes((returned_length,))
                    + payload
                )
            response = (
                READ_RESPONSE
                + ("%04X%02X" % (address, returned_length)).encode("ascii")
                + payload.hex().upper().encode("ascii")
                + ("%02X" % checksum).encode("ascii")
                + b"\xFD"
            )
            self._enqueue(response)
        elif command == 0xE4:
            address = int(data[5:9], 16)
            length = int(data[9:11], 16)
            self.write_addresses.append(address)
            payload = bytes.fromhex(data[11:11 + length * 2].decode("ascii"))
            response_checksum = int(data[11 + length * 2:13 + length * 2], 16)
            expected_checksum = _checksum(
                struct.pack(">I", address)
                + bytes((length,))
                + payload
            )
            if response_checksum != expected_checksum:
                raise AssertionError("invalid host checksum")
            self.image[address:address + length] = payload
            self._enqueue(ACK)
        return len(data)

    def read(self, size=1):
        if self._baud_pending and self.baudrate == 57600:
            self._baud_pending = False
            self._enqueue(ACK)
        data = bytes(self._responses[:size])
        del self._responses[:size]
        return data

    def reset_input_buffer(self):
        self._responses.clear()


class RetevisMA1A9305BDriverTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        bridge = _load_bridge()
        cls.directory = bridge.load_chirp(
            str(SOURCE),
            str(PYTHON_VENDOR),
            str(ROOT / "drivers"),
        )
        cls.radio_class = cls.directory.get_radio(
            "Retevis_MA1-A9305B"
        )

    def _radio(self, image=None):
        from chirp import memmap

        radio = self.radio_class(
            memmap.MemoryMapBytes(image or _image())
        )
        radio.process_mmap()
        return radio

    def test_both_ma1_driver_variants_are_registered(self):
        self.assertEqual(
            self.radio_class.__name__,
            "RetevisMA1A9305BRadio",
        )
        stock_ma1 = self.directory.get_radio("Retevis_MA1")
        self.assertEqual(stock_ma1.MODEL, "MA1")
        self.assertEqual(stock_ma1.BAUD_RATE, 38400)
        self.assertTrue(callable(stock_ma1.sync_in))
        self.assertTrue(callable(stock_ma1.sync_out))

    def test_original_ma1_reads_the_pinned_chirp_fixture(self):
        stock_ma1 = self.directory.get_radio("Retevis_MA1")
        radio = stock_ma1(None)
        radio.load_mmap(
            str(SOURCE / "tests/images/Retevis_MA1.img")
        )
        channel = radio.get_memory(1)
        self.assertFalse(channel.empty)
        self.assertEqual(channel.name, "CH-01")
        self.assertEqual(channel.freq, 144_975_000)
        self.assertEqual(radio.get_features().memory_bounds, (1, 999))

    def test_channel_record_map_names_and_extra_names(self):
        radio = self._radio()

        first = radio.get_memory(1)
        self.assertFalse(first.empty)
        self.assertEqual(first.freq, 146_520_000)
        self.assertEqual(first.name, "CHAN01234567890")
        self.assertEqual(str(first.power), "High")

        second = radio.get_memory(2)
        self.assertEqual(second.duplex, "+")
        self.assertEqual(second.offset, 600_000)
        self.assertEqual(second.mode, "NFM")
        self.assertEqual(str(second.power), "Low")
        self.assertEqual(second.skip, "")

        channel_201 = radio.get_memory(201)
        self.assertFalse(channel_201.empty)
        self.assertEqual(channel_201.freq, 430_125_000)
        self.assertEqual(channel_201.duplex, "+")
        self.assertEqual(channel_201.offset, 8_000_000)
        self.assertEqual(channel_201.mode, "AM")

    def test_cps_power_and_width_fields_match_the_reported_channels(self):
        image = bytearray(_image())
        power_codes = [
            1,
            2,
            2,
            2,
            2,
            2,
            2,
            2,
            2,
            2,
            2,
            2,
            2,
            2,
            1,
            0,
            1,
            1,
            1,
            1,
            1,
            2,
        ]
        expected = (
            ["Mid"]
            + ["Low"] * 13
            + ["Mid"]
            + ["High"]
            + ["Mid"] * 5
            + ["Low"]
        )
        frequencies = [
            462_562_500,
            462_587_500,
            462_612_500,
            462_637_500,
            462_662_500,
            462_687_500,
            462_712_500,
            467_562_500,
            467_587_500,
            467_612_500,
            467_637_500,
            467_662_500,
            467_687_500,
            467_712_500,
            462_550_000,
            462_575_000,
            462_600_000,
            462_625_000,
            462_650_000,
            462_675_000,
            462_700_000,
            462_725_000,
        ]
        for number, (frequency, power) in enumerate(
            zip(frequencies, power_codes),
            1,
        ):
            offset = (number - 1) * 21
            image[offset:offset + 21] = _record(
                frequency,
                frequency,
                name="FRS" if number < 15 else "GMRS",
                power=power,
            )
            _set_bitmap(image, 0x1180, number - 1)

        radio = self._radio(bytes(image))
        for number, power in enumerate(expected, 1):
            channel = radio.get_memory(number)
            self.assertEqual(str(channel.power), power)
            self.assertEqual(channel.mode, "FM")

    def test_set_memory_updates_proven_fields_and_preserves_tones(self):
        from chirp import chirp_common

        radio = self._radio()
        original = bytes(radio._mmap.get(0, 21))
        memory = radio.get_memory(1)
        memory.freq = 147_000_000
        memory.duplex = "split"
        memory.offset = 147_600_000
        memory.mode = "NFM"
        memory.power = radio.POWER_LEVELS[1]
        memory.name = "NEW-NAME"
        memory.skip = "S"
        memory.tmode = "TSQL"
        memory.rtone = 100.0
        memory.ctone = 100.0
        radio.set_memory(memory)

        restored = radio.get_memory(1)
        self.assertEqual(restored.freq, 147_000_000)
        self.assertEqual(restored.duplex, "+")
        self.assertEqual(restored.offset, 600_000)
        self.assertEqual(restored.mode, "NFM")
        self.assertEqual(restored.name, "NEW-NAME")
        self.assertEqual(restored.tmode, "TSQL")
        self.assertEqual(restored.ctone, 100.0)

        raw = bytes(radio._mmap.get(0, 21))
        self.assertEqual(raw[12] & 0x30, 0x20)
        self.assertEqual(raw[12] & 0xC0, 0x40)
        self.assertEqual(raw[8:10], bytes.fromhex("E803"))
        self.assertEqual(raw[10:12], bytes.fromhex("E803"))
        self.assertEqual(raw[15:21], b"NEW-NA")
        self.assertEqual(len(original), 21)

        empty = radio.get_memory(2)
        empty.empty = True
        radio.set_memory(empty)
        self.assertTrue(radio.get_memory(2).empty)

    def test_power_levels_write_cps_codes_and_round_trip(self):
        radio = self._radio()
        expected_codes = {"High": 0x00, "Mid": 0x40, "Low": 0x80}

        for level in radio.POWER_LEVELS:
            memory = radio.get_memory(1)
            memory.power = level
            radio.set_memory(memory)

            raw = bytes(radio._mmap.get(0, 21))
            self.assertEqual(raw[12] & 0xC0, expected_codes[str(level)])
            self.assertEqual(str(radio.get_memory(1).power), str(level))

    def test_serial_read_and_write_use_cps_ranges(self):
        serial = FakeA9305BSerial(_image())
        radio = self.radio_class(serial)
        radio.status_fn = lambda _status: None

        radio.sync_in()
        self.assertEqual(radio.get_memory(1).name, "CHAN01234567890")
        self.assertEqual(serial.read_addresses[0], 0)
        self.assertIn(0x3200, serial.read_addresses)
        self.assertIn(0x4000, serial.read_addresses)
        self.assertNotIn(0x1680, serial.read_addresses)
        self.assertNotIn(0x2B80, serial.read_addresses)

        channel = radio.get_memory(1)
        channel.name = "UPDATED"
        radio.set_memory(channel)
        radio.sync_out()
        self.assertIn(0, serial.write_addresses)
        self.assertIn(0x4000, serial.write_addresses)
        self.assertNotIn(0x1680, serial.write_addresses)
        self.assertNotIn(0x2B80, serial.write_addresses)
        self.assertEqual(bytes(serial.image[0:21])[15:21], b"UPDATE")
        self.assertEqual(
            bytes(serial.image[0x2300:0x230A]),
            b"D         ",
        )
        self.assertEqual(serial.baudrate, 9600)

    def test_serial_read_accepts_the_radios_shorter_mixed_frame(self):
        serial = FakeA9305BSerial(_image(), read_payload_limit=94)
        radio = self.radio_class(serial)
        radio.status_fn = lambda _status: None

        radio.sync_in()

        self.assertEqual(radio.get_memory(1).name, "CHAN01234567890")
        self.assertEqual(serial.read_addresses[:3], [0x0000, 0x005E, 0x00BC])

    def test_serial_read_accepts_the_radios_unchecked_cps_frame(self):
        serial = FakeA9305BSerial(
            _image(),
            read_payload_limit=240,
            read_checksum_override=0xF3,
        )
        radio = self.radio_class(serial)
        radio.status_fn = lambda _status: None

        radio.sync_in()

        self.assertEqual(radio.get_memory(1).name, "CHAN01234567890")
        self.assertEqual(serial.read_addresses[0], 0x0000)

    def test_serial_commands_use_cps_mixed_binary_and_ascii_hex_framing(self):
        serial = FakeA9305BSerial(_image(), read_payload_limit=100)
        radio = self.radio_class(serial)
        radio.status_fn = lambda _status: None

        radio.sync_in()

        self.assertEqual(
            serial.writes[3],
            READ_COMMAND + b"0000F0\xFD",
        )

    def test_image_model_matching_requires_marker(self):
        valid = _image()
        self.assertTrue(self.radio_class.match_model(valid, "test.img"))
        invalid = bytearray(valid)
        invalid[0x19C0:0x19CA] = b"NOT-MA1-A9"
        self.assertFalse(
            self.radio_class.match_model(bytes(invalid), "test.img")
        )

    def test_unknown_marker_image_remains_readable_but_not_writable(self):
        image = bytearray(_image())
        image[0x19C0:0x19CA] = b"\xFF" * 10

        radio = self._radio(bytes(image))

        self.assertEqual(radio.get_memory(1).name, "CHAN01234567890")
        with self.assertRaisesRegex(Exception, "marker is missing"):
            radio.sync_out()

    def test_binary_trace_identifies_addressed_blocks(self):
        trace = _load_bridge().RadioCommunicationTrace()
        frame = (
            b"\xFE\xFE\xEE\xEF\xEB"
            + struct.pack(">IH", 0x3200, 0x84)
            + b"\xFD"
        )
        trace.begin(frame)
        trace._finish_pending()
        self.assertIn(
            "TYT read block addr=0x3200 len=132",
            trace.format(),
        )

    def test_binary_trace_decodes_a9305b_ascii_address_fields(self):
        trace = _load_bridge().RadioCommunicationTrace()
        trace.begin(READ_COMMAND + b"320084\xFD")
        trace._finish_pending()
        self.assertIn(
            "TYT read block addr=0x3200 len=132",
            trace.format(),
        )


if __name__ == "__main__":
    unittest.main()
