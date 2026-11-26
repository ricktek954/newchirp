"""Offline tests for the experimental Kenwood TK-350 and TK-359 drivers."""

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

MEM_SIZE = 0x0E00
CHANNEL_SIZE = 16
RX_BASE = 0x4D18
TX_BASE = 0x6940


def _load_bridge():
    spec = importlib.util.spec_from_file_location(
        "newchirp_chirp_bridge_kpg23",
        ROOT / "scripts/chirp_bridge.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load chirp_bridge.py")
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


def _frequency_word(frequency, base):
    steps = (frequency - 450_000_000) // 6_250
    return (base + steps) & 0xFFFF


def _channel(rx, tx, name):
    record = bytearray(b"\xFF" * CHANNEL_SIZE)
    record[0:2] = struct.pack("<H", _frequency_word(rx, RX_BASE))
    record[2:4] = struct.pack("<H", _frequency_word(tx, TX_BASE))
    record[8:12] = name.encode("ascii").ljust(4, b" ")[:4]
    return bytes(record)


def _synthetic_image():
    image = bytearray(b"\xFF" * MEM_SIZE)
    image[0:CHANNEL_SIZE] = _channel(
        451_787_500, 456_787_500, "RPT"
    )
    image[CHANNEL_SIZE:CHANNEL_SIZE * 2] = _channel(
        451_006_250, 451_006_250, "SIMP"
    )
    return bytes(image)


class FakeKpgSerial:
    """Radio as KPG-23D 1.01 was traced against (2026-11-26): it only
    answers at the CPS's 4800 8N2 when ``strict`` is set, sends a 6-byte
    identity and echoes the address in each W reply."""

    def __init__(self, image, chunk_size=128, identity=b"P350S\x00",
                 strict=False):
        self.image = bytes(image)
        self.identity = identity
        self.strict = strict
        self.dtr = True
        self.rts = True
        self.chunk_size = chunk_size
        self.timeout = 1
        self.baudrate = 9600
        self.bytesize = 8
        self.parity = "N"
        self.stopbits = 1
        self.rtscts = False
        self.xonxoff = False
        self._rx = bytearray()
        self.writes = []
        self.rts_during_writes = []
        self.addresses = []
        self.block_lengths = []

    def write(self, data):
        data = bytes(data)
        self.writes.append(data)
        self.rts_during_writes.append(self.rts)
        if self.strict and (self.baudrate, self.stopbits) != (4800, 2):
            return len(data)  # wrong framing: the radio hears nothing
        if data == b"\x02":
            self._rx.extend(self.identity)
        elif data == b"\x06":
            self._rx.extend(b"\x06")
        elif data == b"E":
            self._rx.extend(b"\x06")
        elif len(data) == 4 and data[:1] == b"R":
            address = struct.unpack(">H", data[1:3])[0]
            length = data[3]
            self.addresses.append(address)
            self.block_lengths.append(length)
            offset = address - 0xF000
            payload = self.image[offset:offset + length].ljust(
                length, b"\xff"
            )
            self._rx.extend(b"W" + data[1:3])
            self._rx.extend(bytes((length,)))
            self._rx.extend(payload)
        return len(data)

    def read(self, size=1):
        count = min(size, self.chunk_size, len(self._rx))
        data = bytes(self._rx[:count])
        del self._rx[:count]
        return data

    def reset_input_buffer(self):
        self._rx.clear()

    def flush(self):
        pass

    def close(self):
        pass


class FakeKpg32Serial:
    """TK-359 as KPG-32D 1.00 talks to it (2026-11-26 QEMU trace)."""

    def __init__(self, image, identity=bytes.fromhex("00 81 31 39 35 33 30 50"),
                 corrupt_first=False, fill_blank=False):
        self.image = bytes(image)
        self.fill_blank = fill_blank
        self.identity = identity
        self.corrupt_first = corrupt_first
        self.timeout = 1
        self.baudrate = 9600
        self.bytesize = 8
        self.parity = "N"
        self.stopbits = 1
        self.rtscts = False
        self.xonxoff = False
        self.dtr = False
        self.rts = True
        self._rx = bytearray()
        self.writes = []
        self.rts_during_writes = []
        self.offsets = []

    def write(self, data):
        data = bytes(data)
        self.writes.append(data)
        self.rts_during_writes.append(self.rts)
        if (self.baudrate, self.stopbits) != (9600, 2):
            return len(data)
        if data == b"PROGRAM":
            self._rx.extend(b"\x06")
        elif data == b"\x02":
            self._rx.extend(self.identity)
        elif data in (b"\x06", b"\x15", b"E"):
            self._rx.extend(b"\x06")
        elif len(data) == 5 and data[:1] == b"S":
            offset = (((data[2] - 0xAC) & 0xFF) << 8) | data[3]
            self.offsets.append(offset)
            length = data[4]
            payload = self.image[offset:offset + length].ljust(length, b"\xff")
            if self.fill_blank and payload == payload[:1] * length:
                # A real TK-359 answers a uniform block with Z + one byte
                # (2026-11-26 owner reports: "5a 03 ac 00 80" then "ff").
                self._rx.extend(b"Z" + data[1:] + payload[:1])
                return len(data)
            checksum = sum(payload) & 0xFF
            if self.corrupt_first:
                checksum ^= 0xFF
                self.corrupt_first = False
            self._rx.extend(b"X" + data[1:] + payload + bytes((checksum,)))
        return len(data)

    def read(self, size=1):
        count = min(size, len(self._rx))
        data = bytes(self._rx[:count])
        del self._rx[:count]
        return data

    def reset_input_buffer(self):
        self._rx.clear()

    def flush(self):
        pass


class KenwoodKPG23DriverTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = _load_bridge().load_chirp(
            str(SOURCE),
            str(PYTHON_VENDOR),
            str(ROOT / "drivers"),
        )
        cls.tk350 = cls.directory.get_radio("Kenwood_TK-350")
        cls.tk359 = cls.directory.get_radio("Kenwood_TK-359")
        from chirp import memmap

        cls.memmap = memmap

    def _radio_from_image(self, radio_class, image):
        radio = radio_class(FakeKpgSerial(image))
        radio._mmap = self.memmap.MemoryMapBytes(bytes(image))
        radio.process_mmap()
        return radio

    def test_models_are_registered_and_read_only(self):
        for radio_class in (self.tk350, self.tk359):
            prompts = radio_class.get_prompts()
            self.assertIn("experimental", prompts.experimental.lower())
            self.assertIn("read-only", prompts.experimental.lower())
            radio = radio_class(FakeKpgSerial(_synthetic_image()))
            with self.assertRaisesRegex(Exception, "read-only"):
                radio.sync_out()
            with self.assertRaisesRegex(Exception, "disabled"):
                radio.set_memory(None)

    def test_tk350_channel_layout_and_frequency_decode(self):
        radio = self._radio_from_image(self.tk350, _synthetic_image())
        repeater = radio.get_memory(1)
        self.assertEqual(repeater.freq, 451_787_500)
        self.assertEqual(repeater.offset, 5_000_000)
        self.assertEqual(repeater.duplex, "+")
        self.assertEqual(repeater.name, "RPT")

        simplex = radio.get_memory(2)
        self.assertEqual(simplex.freq, 451_006_250)
        self.assertEqual(simplex.offset, 0)
        self.assertEqual(simplex.duplex, "")
        self.assertEqual(simplex.name, "SIMP")
        self.assertTrue(radio.get_memory(3).empty)

    def test_fragmented_reads_cover_full_image_and_preserve_bytes(self):
        image = _synthetic_image()
        serial = FakeKpgSerial(image, chunk_size=3)
        radio = self.tk350(serial)
        radio.status_fn = lambda _status: None

        with mock.patch("time.sleep", return_value=None):
            radio.sync_in()

        self.assertEqual(radio.get_mmap().get_packed(), image)
        self.assertEqual(serial.addresses[0], 0xF000)
        self.assertEqual(serial.addresses[1], 0xF080)
        self.assertEqual(serial.addresses[-1], 0xF000 + 0x0D80)
        self.assertEqual(serial.writes[0], b"\x02")
        # KPG-23D ends after the last block's ACK; it sends no exit command.
        self.assertEqual(serial.writes[-1], b"\x06")
        self.assertNotIn(b"E", serial.writes)

    def test_identity_request_is_retried_when_radio_enters_pc_mode_late(self):
        class SlowIdentitySerial(FakeKpgSerial):
            def __init__(self, image):
                super().__init__(image)
                self.identity_requests = 0

            def write(self, data):
                if bytes(data) == b"\x02":
                    self.identity_requests += 1
                    self.writes.append(bytes(data))
                    if self.identity_requests >= 2:
                        self._rx.extend(self.identity)
                    return len(data)
                return super().write(data)

        serial = SlowIdentitySerial(_synthetic_image())
        radio = self.tk350(serial)
        radio.status_fn = lambda _status: None

        with mock.patch("time.sleep", return_value=None):
            radio.sync_in()

        self.assertEqual(serial.identity_requests, 2)
        self.assertEqual(serial.writes[-1], b"\x06")

    def test_tk350_session_matches_kpg23d_trace(self):
        """KPG-23D 1.01 in QEMU: 4800 8N2, DTR/RTS never raised, 6-byte
        identity, 28 blocks from 0xF000, no exit command (2026-11-26)."""
        image = _synthetic_image()
        serial = FakeKpgSerial(image, strict=True)
        radio = self.tk350(serial)
        radio.status_fn = lambda _status: None

        with mock.patch("time.sleep", return_value=None):
            radio.sync_in()

        self.assertEqual((serial.baudrate, serial.bytesize, serial.parity,
                          serial.stopbits), (4800, 8, "N", 2))
        # KPG-23D sends through BIOS INT 14h AH=01 and receives with AH=02:
        # DTR stays raised, RTS is raised only while a byte is sent.
        self.assertTrue(serial.dtr)
        self.assertFalse(serial.rts)
        self.assertTrue(all(serial.rts_during_writes))
        self.assertEqual(self.tk350.BAUD_RATE, 4800)
        self.assertTrue(self.tk350.WANTS_DTR)
        self.assertFalse(self.tk350.WANTS_RTS)
        self.assertEqual(radio.get_mmap().get_packed(), image)
        self.assertEqual(len(serial.addresses), 28)
        self.assertEqual(serial.addresses[-1], 0xFD80)

    def test_tk350_reads_whatever_identity_the_radio_sends(self):
        # KPG-23D read a simulated radio that sent "P250S" without
        # complaint; it does not check the identity before reading.
        serial = FakeKpgSerial(_synthetic_image(), identity=b"P250S\x00")
        radio = self.tk350(serial)
        radio.status_fn = lambda _status: None
        with mock.patch("time.sleep", return_value=None):
            radio.sync_in()
        self.assertEqual(len(serial.addresses), 28)

    def test_tk350_rejects_a_z_fill_reply_like_kpg23d(self):
        class ZSerial(FakeKpgSerial):
            def write(self, data):
                if len(data) == 4 and data[:1] == b"R":
                    self.writes.append(bytes(data))
                    self._rx.extend(b"Z" + bytes(data[1:]))
                    return len(data)
                return super().write(data)

        radio = self.tk350(ZSerial(_synthetic_image()))
        radio.status_fn = lambda _status: None
        with mock.patch("time.sleep", return_value=None):
            with self.assertRaisesRegex(Exception, "0xF000"):
                radio.sync_in()

    def test_tk359_session_matches_kpg32d_trace(self):
        image = bytes((i * 7) & 0xFF for i in range(0x53FF))
        serial = FakeKpg32Serial(image)
        radio = self.tk359(serial)
        radio.status_fn = lambda _status: None
        with mock.patch("time.sleep", return_value=None):
            radio.sync_in()

        self.assertEqual((serial.baudrate, serial.stopbits), (9600, 2))
        self.assertEqual(serial.writes[0], b"PROGRAM")
        self.assertEqual(serial.writes[1], b"\x02")
        self.assertEqual(serial.writes[-1], b"E")
        self.assertTrue(all(serial.rts_during_writes))
        self.assertTrue(serial.dtr)
        self.assertFalse(serial.rts)
        # Every 0x80 block except 0x0400-0x04FF, which KPG-32D never reads.
        self.assertNotIn(0x0400, serial.offsets)
        self.assertNotIn(0x0480, serial.offsets)
        self.assertEqual(serial.offsets[0], 0x0000)
        self.assertEqual(serial.offsets[-1], 0x5380)
        got = radio.get_mmap().get_packed()
        self.assertEqual(len(got), 0x53FF)
        self.assertEqual(got[:0x400], image[:0x400])
        self.assertEqual(got[0x500:], image[0x500:])
        self.assertEqual(got[0x400:0x500], b"\xff" * 0x100)

    def test_tk359_wire_address_is_base_plus_offset_without_carry(self):
        serial = FakeKpg32Serial(bytes(0x53FF))
        radio = self.tk359(serial)
        radio.status_fn = lambda _status: None
        with mock.patch("time.sleep", return_value=None):
            radio.sync_in()
        requests = [w for w in serial.writes if w[:1] == b"S"]
        self.assertEqual(requests[0], bytes.fromhex("53 03 ac 00 80"))
        self.assertEqual(requests[-1], bytes.fromhex("53 03 ff 80 80"))

    def test_tk359_bad_checksum_is_naked_and_retried(self):
        serial = FakeKpg32Serial(bytes(0x53FF), corrupt_first=True)
        radio = self.tk359(serial)
        radio.status_fn = lambda _status: None
        with mock.patch("time.sleep", return_value=None):
            radio.sync_in()
        self.assertIn(b"\x15", serial.writes)
        self.assertEqual(serial.offsets.count(0), 2)

    def test_tk359_rejects_other_identities_like_kpg32d(self):
        for identity, message in (
                (bytes.fromhex("00 81 31 39 35 32 30 50"), "TK-259"),
                (b"P359S\x00\xe2\x00", "not a TK-259/TK-359")):
            serial = FakeKpg32Serial(bytes(0x53FF), identity=identity)
            radio = self.tk359(serial)
            radio.status_fn = lambda _status: None
            with mock.patch("time.sleep", return_value=None):
                with self.assertRaisesRegex(Exception, message):
                    radio.sync_in()
            self.assertIn(b"\x15", serial.writes)

    def test_short_block_is_retried_then_fails(self):
        class ShortSerial(FakeKpgSerial):
            def write(self, data):
                if len(data) == 4 and data[:1] == b"R":
                    self.writes.append(bytes(data))
                    self._rx.extend(b"W\x00\x00")
                    return len(data)
                return super().write(data)

        radio = self.tk350(ShortSerial(_synthetic_image()))
        radio.status_fn = lambda _status: None
        with mock.patch("time.sleep", return_value=None):
            with self.assertRaisesRegex(Exception, "0xF000"):
                radio.sync_in()

    # Records saved by the OEM programmers in QEMU with known frequencies
    # typed in (2026-11-26); see docs/KPG23_PROTOCOL.md.
    TK350_U1F_CH1 = bytes.fromhex("5a53ffffb8cbffff20203120ffe0ffff")   # RX 460.0125
    TK350_U1F_CH2 = bytes.fromhex("f254ffffb8cbffff20203220ffe0ffff")   # RX 462.5625
    TK350_U4F_TEST1 = bytes.fromhex("28394055ffffffffffffffffffffffff")  # 418.1 / 418.0 (400-430)
    TK359_CH1 = bytes.fromhex(
        "ffffef1f82f0ffff22a0801fffffffff" "ffff20312001ffffffffffffffffffff")  # 460.0125 / 465.000
    TK359_CH2 = bytes.fromhex(
        "ffffef1cb0f0ffff1cb0801fffffffff" "ffff20322001ffffffffffffffffffff")  # 455.5 simplex

    def test_tk350_decodes_kpg23d_saved_records_in_any_uhf_band(self):
        image = bytearray(b"\xFF" * MEM_SIZE)
        image[0:16] = self.TK350_U1F_CH1
        image[16:32] = self.TK350_U1F_CH2
        image[32:48] = self.TK350_U4F_TEST1
        image[0x0D00:0x0D05] = b"P3504"
        radio = self._radio_from_image(self.tk350, image)
        self.assertEqual(radio.get_memory(1).freq, 460_012_500)
        self.assertEqual(radio.get_memory(1).name, "1")
        self.assertEqual(radio.get_memory(2).freq, 462_562_500)
        low = radio.get_memory(3)
        self.assertFalse(low.empty, "400-430 MHz channels must not be hidden")
        self.assertEqual(low.freq, 418_100_000)
        self.assertEqual((low.duplex, low.offset), ("-", 100_000))
        # KPG-23D leaves erased slots as FF words with an E0 option byte.
        self.assertTrue(radio.get_memory(4).empty)

    def test_tk359_decodes_kpg32d_channel_records(self):
        image = bytearray(b"\xFF" * 0x53FF)
        image[0x3400:0x3420] = self.TK359_CH1
        image[0x3420:0x3440] = self.TK359_CH2
        radio = self._radio_from_image(self.tk359, image)
        first = radio.get_memory(1)
        self.assertEqual(first.freq, 460_012_500)
        self.assertEqual((first.duplex, first.offset), ("+", 4_987_500))
        self.assertEqual(first.name, "1")
        second = radio.get_memory(2)
        self.assertEqual((second.freq, second.duplex), (455_500_000, ""))
        self.assertTrue(radio.get_memory(3).empty)
        self.assertTrue(radio.get_memory(250).empty)

    def test_tk359_frequency_flags(self):
        decode = self.tk359._kpg32_frequency
        self.assertEqual(decode(0x81, 0x1F90, True), 460_100_000)   # test freq 1
        self.assertEqual(decode(0x00, 0x6760, False), 460_000_000)  # 5 kHz step
        self.assertEqual(decode(0x01, 0x6760, True), 460_000_000)
        self.assertEqual(decode(0x80, 0xFDC0, False), 406_000_000)  # below bit 16

    def test_tk359_accepts_z_fill_blocks_like_kpg32d(self):
        image = bytearray(b"\xFF" * 0x53FF)
        image[0x3400:0x3420] = self.TK359_CH1
        serial = FakeKpg32Serial(image, fill_blank=True)
        radio = self.tk359(serial)
        radio.status_fn = lambda _status: None
        with mock.patch("time.sleep", return_value=None):
            radio.sync_in()
        got = radio.get_mmap().get_packed()
        self.assertEqual(got, bytes(image))
        self.assertEqual(serial.offsets.count(0), 1, "no retries")
        self.assertEqual(radio.get_memory(1).freq, 460_012_500)


if __name__ == "__main__":
    unittest.main()
