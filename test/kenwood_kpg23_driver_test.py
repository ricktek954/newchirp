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
        self.written = []
        self.write_reply = b"\x06"

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
        elif len(data) == 132 and data[:1] == b"W":
            address = struct.unpack(">H", data[1:3])[0]
            self.written.append(address)
            offset = address - 0xF000
            image = bytearray(self.image)
            image[offset:offset + 128] = data[4:]
            self.image = bytes(image)
            self._rx.extend(self.write_reply)
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
        self.frames = []

    def _store(self, offset, data):
        image = bytearray(self.image.ljust(0x5400, b"\xff"))
        image[offset:offset + len(data)] = data
        self.image = bytes(image)

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
        elif data in (b"\x06", b"\x15", b"E", b"\x03"):
            self._rx.extend(b"\x06")
        elif len(data) == 6 and data[:1] == b"Z":
            offset = (((data[2] - 0xAC) & 0xFF) << 8) | data[3]
            self.frames.append(("Z", offset))
            self._store(offset, data[5:6] * data[4])
            self._rx.extend(b"\x06")
        elif len(data) == 134 and data[:1] == b"X":
            offset = (((data[2] - 0xAC) & 0xFF) << 8) | data[3]
            assert sum(data[5:133]) & 0xFF == data[133]
            self.frames.append(("X", offset))
            self._store(offset, data[5:133])
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
        cls.driver = sys.modules[cls.tk350.__module__]
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
            radio = radio_class(FakeKpgSerial(_synthetic_image()))
            if radio_class.MODEL == "TK-359":
                # Writes stay gated until a physical write/read-back passes.
                self.assertTrue(radio_class.NEWCHIRP_WRITE_DISABLED)
                with self.assertRaisesRegex(Exception, "read-only"):
                    radio.sync_out()
            else:
                # TK-350: enabled for the controlled owner test.
                self.assertFalse(radio_class.NEWCHIRP_WRITE_DISABLED)
                self.assertIn("backup", prompts.experimental)
                self.assertIn("off and on", prompts.pre_upload)

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

    # --- writes (KPG-23D / KPG-32D write sessions traced 2026-11-26) ---

    def _tk350_image(self):
        image = bytearray(b"\xFF" * MEM_SIZE)
        image[0:16] = self.TK350_U1F_CH1
        image[16:32] = self.TK350_U1F_CH2
        image[0x0D00:0x0D06] = b"P3501\x01"
        image[0x0C00:0x0C10] = bytes(range(16))   # alignment area
        return bytes(image)

    def _writable(self, radio):
        radio.NEWCHIRP_WRITE_DISABLED = False
        radio.status_fn = lambda _status: None
        return radio

    def test_tk350_tones_decode_from_kpg23d_values(self):
        image = bytearray(b"\xFF" * MEM_SIZE)
        base = bytearray(self.TK350_U1F_CH1)
        cases = {
            1: ("e8c3", "e8c3"),   # SAMPLE.V1B: QT 100.0 / 100.0
            2: ("55c4", "55c4"),   # VARFF.V1B: 110.9 / 110.9
            3: ("ffff", "02c3"),   # encode only, 77.0 (owner's ch1 list)
            4: ("e8c3", "55c4"),   # decode 100.0, encode 110.9
            5: ("b8cb", "ffff"),   # 300.0: not a standard tone
        }
        for number, (decode, encode) in cases.items():
            record = bytearray(base)
            record[4:6] = bytes.fromhex(decode)
            record[6:8] = bytes.fromhex(encode)
            record[2:4] = record[0:2]   # give it a TX word
            image[(number - 1) * 16:number * 16] = record
        radio = self._radio_from_image(self.tk350, image)
        one = radio.get_memory(1)
        self.assertEqual((one.tmode, one.ctone), ("TSQL", 100.0))
        self.assertEqual((radio.get_memory(2).tmode, radio.get_memory(2).ctone),
                         ("TSQL", 110.9))
        three = radio.get_memory(3)
        self.assertEqual((three.tmode, three.rtone), ("Tone", 77.0))
        four = radio.get_memory(4)
        self.assertEqual((four.tmode, four.cross_mode, four.rtone, four.ctone),
                         ("Cross", "Tone->Tone", 110.9, 100.0))
        self.assertEqual(radio.get_memory(5).tmode, "")

        # Frequency edits keep the tone bytes; tone edits are refused.
        three.freq = 433_025_000
        radio.set_memory(three)
        self.assertEqual(radio.get_mmap().get_packed()[36:40],
                         bytes.fromhex("ffff02c3"))
        self.assertEqual(radio.get_memory(3).rtone, 77.0)
        three.rtone = 88.5
        with self.assertRaisesRegex(Exception, "tones"):
            radio.set_memory(three)

    def test_tk350_write_matches_kpg23d_trace(self):
        image = self._tk350_image()
        serial = FakeKpgSerial(image, identity=b"P3501\x01", strict=True)
        radio = self._writable(self.tk350(serial))
        radio._mmap = self.memmap.MemoryMapBytes(image)
        radio.process_mmap()
        memory = radio.get_memory(1)
        memory.freq = 461_000_000
        memory.name = "RPT"
        radio.set_memory(memory)
        with mock.patch("time.sleep", return_value=None):
            radio.sync_out()
        self.assertEqual(serial.writes[:2], [b"\x02", b"\x06"])
        expected = [0xF000 + n * 0x80 for n in range(28)
                    if not 0xFC00 <= 0xF000 + n * 0x80 < 0xFD00]
        self.assertEqual(serial.written, expected)
        self.assertEqual(len(serial.written), 26)
        self.assertEqual(serial.writes[-1][:1], b"W", "no exit command")
        self.assertEqual(serial.image[0x0C00:0x0C10], bytes(range(16)))
        written = self._radio_from_image(self.tk350, serial.image)
        self.assertEqual(written.get_memory(1).freq, 461_000_000)
        self.assertEqual(written.get_memory(1).name, "RPT")
        self.assertEqual(written.get_memory(2).freq, 462_562_500)

    def test_tk350_write_refuses_a_different_model_or_band(self):
        serial = FakeKpgSerial(self._tk350_image(), identity=b"P3504\x01")
        radio = self._writable(self.tk350(serial))
        radio._mmap = self.memmap.MemoryMapBytes(self._tk350_image())
        with mock.patch("time.sleep", return_value=None):
            with self.assertRaisesRegex(Exception, "P3504.*P3501"):
                radio.sync_out()
        self.assertEqual(serial.written, [])

    def test_tk350_write_waits_for_the_identity_ack(self):
        class NoIdentityAck(FakeKpgSerial):
            def write(self, data):
                if bytes(data) == b"\x06":
                    self.writes.append(bytes(data))
                    return 1
                return super().write(data)

        serial = NoIdentityAck(self._tk350_image(), identity=b"P3501\x01")
        radio = self._writable(self.tk350(serial))
        radio._mmap = self.memmap.MemoryMapBytes(self._tk350_image())
        with mock.patch.object(self.driver, "WRITE_REPLY_TIMEOUT", 0.05), \
                mock.patch("time.sleep", return_value=None):
            with self.assertRaisesRegex(Exception, "identity"):
                radio.sync_out()
        self.assertEqual(serial.written, [])

    def test_tk350_write_stops_on_a_refused_block(self):
        serial = FakeKpgSerial(self._tk350_image(), identity=b"P3501\x01")
        serial.write_reply = b"\x15"
        radio = self._writable(self.tk350(serial))
        radio._mmap = self.memmap.MemoryMapBytes(self._tk350_image())
        with mock.patch("time.sleep", return_value=None):
            with self.assertRaisesRegex(Exception, "0xF000"):
                radio.sync_out()
        self.assertEqual(serial.written, [0xF000])

    def test_tk350_edits_are_limited_and_round_trip(self):
        radio = self._radio_from_image(self.tk350, self._tk350_image())
        # A blank TX word is KPG-23D's empty Transmit column.
        self.assertEqual(radio.get_memory(1).duplex, "off")
        memory = radio.get_memory(2)
        memory.duplex = "+"
        memory.offset = 5_000_000
        radio.set_memory(memory)
        again = radio.get_memory(2)
        self.assertEqual((again.duplex, again.offset), ("+", 5_000_000))
        empty = radio.get_memory(5)
        empty.empty = False
        empty.freq = 460_000_000
        with self.assertRaisesRegex(Exception, "existing channels"):
            radio.set_memory(empty)
        memory.freq = 460_001_000
        with self.assertRaisesRegex(Exception, "6.25 kHz"):
            radio.set_memory(memory)

    def _tk359_radio_after_read(self, fill_blank=True):
        image = bytearray(b"\xFF" * 0x53FF)
        image[0x0500:0x0508] = bytes.fromhex("00 81 31 39 35 33 30 50")
        image[0x3400:0x3420] = self.TK359_CH1
        image[0x3420:0x3440] = self.TK359_CH2
        image[0x5390:0x5394] = b"TAIL"
        serial = FakeKpg32Serial(bytes(image) + b"\x5a", fill_blank=fill_blank)
        radio = self._writable(self.tk359(serial))
        with mock.patch("time.sleep", return_value=None):
            radio.sync_in()
        serial.writes.clear()
        serial.frames.clear()
        return radio, serial

    def test_tk359_write_sends_only_changed_blocks_like_kpg32d(self):
        radio, serial = self._tk359_radio_after_read()
        memory = radio.get_memory(2)
        memory.freq = 456_000_000
        radio.set_memory(memory)
        with mock.patch("time.sleep", return_value=None):
            radio.sync_out()
        self.assertEqual(serial.frames, [("X", 0x3400)])
        index = serial.writes.index(next(w for w in serial.writes if w[:1] == b"X"))
        self.assertEqual(serial.writes[index + 1], b"\x03", "commit after X")
        self.assertEqual(serial.writes[-1], b"E")
        reread = self._radio_from_image(self.tk359, serial.image[:0x53FF])
        self.assertEqual(reread.get_memory(2).freq, 456_000_000)
        self.assertEqual(reread.get_memory(1).freq, 460_012_500)

    def test_tk359_uniform_block_goes_as_z_and_tail_byte_is_kept(self):
        radio, serial = self._tk359_radio_after_read()
        self.assertEqual(radio._metadata["newchirp_kpg32_tail"], "5a")
        with mock.patch("time.sleep", return_value=None):
            self.driver._kpg32_open(radio)
            self.driver._kpg32_write_block(radio, 0x0000, b"\xff" * 128)
        self.assertEqual(serial.writes[-1], bytes.fromhex("5a 03 ac 00 80 ff"))
        changed = self.driver._kpg32_changed_blocks(
            radio, radio.get_mmap().get_packed()[:0x5390] + b"tail"
            + radio.get_mmap().get_packed()[0x5394:])
        self.assertEqual([offset for offset, _ in changed], [0x5380])
        self.assertEqual(changed[0][1][-1], 0x5A)

    def test_tk359_write_needs_a_read_from_this_version(self):
        image = bytearray(b"\xFF" * 0x53FF)
        image[0x3400:0x3420] = self.TK359_CH1
        radio = self._writable(self._radio_from_image(self.tk359, image))
        with self.assertRaisesRegex(Exception, "Read the radio"):
            radio.sync_out()

    def test_tk359_rejects_renames_and_tx_off_until_confirmed(self):
        radio, _serial = self._tk359_radio_after_read()
        memory = radio.get_memory(1)
        memory.name = "NEW"
        with self.assertRaisesRegex(Exception, "Renaming"):
            radio.set_memory(memory)
        memory = radio.get_memory(1)
        memory.duplex = "off"
        with self.assertRaisesRegex(Exception, "TX off"):
            radio.set_memory(memory)


if __name__ == "__main__":
    unittest.main()
