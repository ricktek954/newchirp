"""Offline protocol and image tests for the Wouxun KG-689E/KG-699E driver.

The fake radio follows the exchange recovered from Wouxun's KG-699E/689E
programming software (see docs/WOUXUN_KG689E_PROTOCOL.md). These are replay
tests only; they say nothing about physical-radio behaviour.
"""

import importlib
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest import mock

from chirp_test_source import chirp_source


ROOT = Path(__file__).resolve().parent.parent
SOURCE = chirp_source()
PYTHON_VENDOR = ROOT / "assets/python/pyserial-3.5-py2.py3-none-any.whl"


def _load_bridge():
    spec = importlib.util.spec_from_file_location(
        "newchirp_chirp_bridge_kg689e", ROOT / "scripts/chirp_bridge.py"
    )
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


def _bcd_le(hz):
    digits = "%08d" % (hz // 10)
    return bytes(int(digits[i:i + 2]) // 10 * 16 + int(digits[i:i + 2]) % 10
                 for i in (6, 4, 2, 0))


class FakeKG689E:
    """Answers like the radio the CPS talks to."""

    def __init__(self, memory, limits=(b"\x01\x36", b"\x01\x74")):
        self.memory = bytearray(memory)
        low, high = limits
        self.memory[0x0970:0x09B0] = (
            b"\x00" * 4 + low + high + b"\x00" * 4 + low + high
            + b"\x00" * 48
        )
        self.pending = b""
        self.writes = []
        self.reads = []
        self.stage = "wake"

    def reset_input_buffer(self):
        self.pending = b""

    def write(self, data):
        data = bytes(data)
        if self.stage == "wake":
            assert data == b"HiWOUXUN\x02", data
            self.pending, self.stage = b"\x06", "ident"
        elif self.stage == "ident":
            assert data == b"\x02", data
            self.pending, self.stage = b"\x06KG669V\xf8", "enter"
        elif self.stage == "enter":
            assert data == b"\x06", data
            self.pending, self.stage = b"\x06", "ready"
        elif self.stage == "ack":
            assert data == b"\x06", data
            self.pending, self.stage = b"\x06", "ready"
        elif data[0] == 0x52:
            assert len(data) == 4 and data[3] == 0x40, data
            address = data[1] << 8 | data[2]
            self.reads.append(address)
            self.pending = b"W" + data[1:4] + bytes(
                self.memory[address:address + 0x40])
            self.stage = "ack"
        elif data[0] == 0x57:
            assert len(data) == 20 and data[3] == 0x10, data
            address = data[1] << 8 | data[2]
            self.writes.append(address)
            self.memory[address:address + 0x10] = data[4:]
            self.pending = b"\x06"
        else:
            raise AssertionError("unexpected %r" % data)

    def read(self, length):
        chunk, self.pending = self.pending[:length], self.pending[length:]
        return chunk


class EchoCable:
    """A cable that returns every host byte before the radio's reply.

    With radio=None it models an echoing cable on a radio that never
    answers (for example an Icom cable on a Wouxun).
    """

    def __init__(self, radio):
        self.radio = radio
        self.pending = b""

    def reset_input_buffer(self):
        self.pending = b""
        if self.radio:
            self.radio.reset_input_buffer()

    def write(self, data):
        self.pending += bytes(data)
        if self.radio:
            self.radio.write(data)

    def read(self, length):
        chunk, self.pending = self.pending[:length], self.pending[length:]
        if self.radio and len(chunk) < length:
            chunk += self.radio.read(length - len(chunk))
        return chunk


class WouxunKG689EDriverTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        bridge = _load_bridge()
        cls.directory = bridge.load_chirp(
            str(SOURCE), str(PYTHON_VENDOR), str(ROOT / "drivers"))
        cls.radio_class = cls.directory.get_radio("Wouxun_KG-689E")
        cls.driver = importlib.import_module(cls.radio_class.__module__)

    def _radio_memory(self):
        memory = bytearray(b"\xff" * 0x2000)
        # Channel 1: 146.520 simplex, CTCSS 100.0 TX, wide, high, scan.
        memory[0x0010:0x0020] = (
            _bcd_le(146_520_000) + _bcd_le(146_520_000)
            + b"\xff\xff" + (1000).to_bytes(2, "little")
            + bytes((0x08, 0x70)) + b"\xab\xcd"
        )
        # Channel 2: 145.000 RX, 144.400 TX, DCS 023 inverted both ways,
        # narrow, low, not scanned, DTMF optional signal, mute QT*DTMF.
        dcs = (0xA800 | int("23", 8)).to_bytes(2, "little")
        memory[0x0020:0x0030] = (
            _bcd_le(145_000_000) + _bcd_le(144_400_000) + dcs + dcs
            + bytes((0x42, 0x00)) + b"\x00\x00"
        )
        memory[0x1010:0x1016] = bytes((17, 14, 25, 14, 2, 38))  # HEPE2-
        memory[0x1020:0x1026] = bytes((10, 11)) + b"\xff" * 4    # AB
        for address in (0x0810, 0x0E20, 0x1810):
            memory[address:address + 0x40] = bytes(range(0x40))
        return memory

    def _read(self, fake):
        radio = self.radio_class(fake)
        radio.status_fn = lambda _status: None
        with mock.patch("time.sleep", return_value=None):
            radio.sync_in()
        return radio

    def test_read_follows_cps_block_order(self):
        fake = FakeKG689E(self._radio_memory())
        self._read(fake)
        expected = (
            [0x0010 + i * 0x40 for i in range(32)]
            + [0x1010 + i * 0x40 for i in range(32)]
            + [0x0810, 0x0E20, 0x1810, 0x0970]
        )
        self.assertEqual(fake.reads, expected)

    def test_channel_fields_decode_like_the_cps(self):
        radio = self._read(FakeKG689E(self._radio_memory()))
        first = radio.get_memory(1)
        self.assertEqual(first.freq, 146_520_000)
        self.assertEqual(first.duplex, "")
        self.assertEqual(first.tmode, "Tone")
        self.assertEqual(first.rtone, 100.0)
        self.assertEqual(first.mode, "FM")
        self.assertEqual(str(first.power), "High")
        self.assertEqual(first.skip, "")
        self.assertEqual(first.name, "HEPE2-")
        extras = {s.get_name(): s.value for s in first.extra}
        self.assertTrue(bool(extras["busy_lock"]))
        self.assertFalse(bool(extras["optional_dtmf"]))
        self.assertEqual(str(extras["mute_mode"]), "QT")

        second = radio.get_memory(2)
        self.assertEqual(second.duplex, "-")
        self.assertEqual(second.offset, 600_000)
        self.assertEqual(second.tmode, "DTCS")
        self.assertEqual(second.dtcs, 23)
        self.assertEqual(second.dtcs_polarity, "RR")
        self.assertEqual(second.mode, "NFM")
        self.assertEqual(str(second.power), "Low")
        self.assertEqual(second.skip, "S")
        self.assertEqual(second.name, "AB")
        extras = {s.get_name(): s.value for s in second.extra}
        self.assertTrue(bool(extras["optional_dtmf"]))
        self.assertEqual(str(extras["mute_mode"]), "QT*DTMF")

        self.assertTrue(radio.get_memory(3).empty)
        self.assertEqual(radio.get_features().valid_bands,
                         [(136_000_000, 174_995_001)])

    def test_write_sends_only_cps_regions_and_preserves_unknowns(self):
        memory = self._radio_memory()
        fake = FakeKG689E(memory)
        radio = self._read(fake)

        edited = radio.get_memory(1)
        edited.name = "NEW"
        edited.skip = "S"
        radio.set_memory(edited)
        radio.set_memory(radio.get_memory(2))

        writer = FakeKG689E(memory)
        radio.pipe = writer
        with mock.patch("time.sleep", return_value=None):
            radio.sync_out()

        expected = []
        for base in ([0x0010 + i * 0x40 for i in range(32)]
                     + [0x1010 + i * 0x40 for i in range(32)]):
            expected += [base + offset for offset in (0, 0x10, 0x20, 0x30)]
        expected += [0x0810, 0x0820, 0x0E20, 0x0E30, 0x0E40, 0x0E50,
                     0x1810, 0x1820]
        self.assertEqual(writer.writes, expected)
        self.assertEqual(writer.reads, [0x0970])

        written = writer.memory
        self.assertEqual(written[0x001C:0x0020], bytes((0x08, 0x30)) + b"\xab\xcd")
        self.assertEqual(written[0x1010:0x1016], bytes((23, 14, 32)) + b"\xff" * 3)
        self.assertEqual(written[0x0020:0x0030], memory[0x0020:0x0030])
        # Never written by the CPS: second half of 0x0810 and 0x1810.
        self.assertEqual(written[0x0830:0x0850], memory[0x0830:0x0850])
        self.assertEqual(written[0x1830:0x1850], memory[0x1830:0x1850])

    def test_write_refuses_channel_outside_radio_limits(self):
        memory = self._radio_memory()
        radio = self._read(FakeKG689E(memory))
        channel = radio.get_memory(3)
        channel.empty = False
        channel.freq = 446_000_000
        radio.set_memory(channel)

        writer = FakeKG689E(memory)
        radio.pipe = writer
        with mock.patch("time.sleep", return_value=None):
            with self.assertRaisesRegex(Exception, "Channel 3 receives"):
                radio.sync_out()
        self.assertEqual(writer.writes, [])

    def test_upper_limit_allows_cps_tolerance(self):
        memory = self._radio_memory()
        radio = self._read(FakeKG689E(memory))
        channel = radio.get_memory(3)
        channel.empty = False
        channel.freq = 174_995_000
        radio.set_memory(channel)
        writer = FakeKG689E(memory)
        radio.pipe = writer
        with mock.patch("time.sleep", return_value=None):
            radio.sync_out()
        self.assertTrue(writer.writes)

    def test_wrong_identity_stops_before_reading(self):
        fake = FakeKG689E(self._radio_memory())
        original = fake.write

        def write(data):
            original(data)
            if bytes(data) == b"\x02":
                fake.pending = b"\x06KG816V\xf8"

        fake.write = write
        with self.assertRaisesRegex(Exception, "KG669V"):
            self._read(fake)
        self.assertEqual(fake.reads, [])

    def test_echo_cable_is_stripped_for_read_and_write(self):
        fake = EchoCable(FakeKG689E(self._radio_memory()))
        radio = self._read(fake)
        self.assertEqual(len(fake.radio.reads), 68)
        self.assertEqual(radio.get_memory(1).freq, 146_520_000)
        writer = EchoCable(FakeKG689E(self._radio_memory()))
        radio.pipe = writer
        with mock.patch("time.sleep", return_value=None):
            radio.sync_out()
        self.assertTrue(writer.radio.writes)

    def test_echo_without_radio_reports_cable_type(self):
        fake = EchoCable(None)
        with self.assertRaisesRegex(Exception, "Wouxun 2-pin"):
            self._read(fake)

    def test_tone_codec_matches_cps_encoder(self):
        self.assertEqual(self.driver._encode_tone("Tone", 88.5, None), 885)
        self.assertEqual(self.driver._encode_tone("DTCS", 23, "N"), 0x2813)
        self.assertEqual(self.driver._encode_tone("DTCS", 754, "R"), 0xA9EC)
        self.assertEqual(self.driver._decode_tone(0x2813), ("DTCS", 23, "N"))
        self.assertEqual(self.driver._decode_tone(0xFFFF), ("", None, None))

    def test_name_stops_at_first_unsupported_character(self):
        radio = self._read(FakeKG689E(self._radio_memory()))
        channel = radio.get_memory(1)
        channel.name = "AB CD"
        radio.set_memory(channel)
        self.assertEqual(radio.get_memory(1).name, "AB")

    def test_delete_erases_channel_and_name(self):
        radio = self._read(FakeKG689E(self._radio_memory()))
        channel = radio.get_memory(1)
        channel.empty = True
        radio.set_memory(channel)
        self.assertTrue(radio.get_memory(1).empty)
        raw = radio._mmap.get_packed()
        self.assertEqual(raw[0x0010:0x0020], b"\xff" * 16)
        self.assertEqual(raw[0x1010:0x1016], b"\xff" * 6)

    def test_kg699e_shares_the_driver(self):
        cls = self.directory.get_radio("Wouxun_KG-699E")
        self.assertTrue(issubclass(cls, self.driver.KG689EBase))
        self.assertFalse(cls.match_model(b"\xff" * 0x2000, "x.img"))


if __name__ == "__main__":
    unittest.main()
