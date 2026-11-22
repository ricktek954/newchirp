"""Offline checks for TK-270G bank metadata safety."""

import importlib
import importlib.util
from collections import deque
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest import mock


from chirp_test_source import chirp_source


ROOT = Path(__file__).resolve().parent.parent
SOURCE = chirp_source()
PYTHON_VENDOR = ROOT / "assets/python/pyserial-3.5-py2.py3-none-any.whl"


class FakeTK270GSerial:
    def __init__(self):
        self.timeout = 1
        self.baudrate = 9600
        self.parity = "E"
        self.stopbits = 1
        self.writes = []
        self._responses = deque()
        self.rejected_writes = {}

    def write(self, data):
        data = bytes(data)
        self.writes.append(data)
        if data == b"PROGRAM":
            self._responses.append(b"\x06")
        elif data == b"\x02":
            self._responses.append(b"P2700\x05\xff")
        elif data == b"\x06":
            self._responses.append(b"\x06")
        elif data == b"E":
            self._responses.append(b"\x06")
        elif data[:1] in (b"W", b"Z"):
            address = struct.unpack(">H", data[1:3])[0]
            if self.rejected_writes.get(address, 0):
                self.rejected_writes[address] -= 1
                self._responses.append(b"\x15")
            else:
                self._responses.append(b"\x06")
        return len(data)

    def read(self, size=1):
        result = bytearray()
        while self._responses and len(result) < size:
            chunk = self._responses[0]
            take = min(size - len(result), len(chunk))
            result.extend(chunk[:take])
            if take == len(chunk):
                self._responses.popleft()
            else:
                self._responses[0] = chunk[take:]
        return bytes(result)

    def flush(self):
        pass

    def close(self):
        pass


def _load_bridge():
    spec = importlib.util.spec_from_file_location(
        "newchirp_chirp_bridge_tk270g",
        ROOT / "scripts/chirp_bridge.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load chirp_bridge.py")
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


class KenwoodTK270GDriverTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        bridge = _load_bridge()
        cls.bridge = bridge
        cls.directory = bridge.load_chirp(
            str(SOURCE),
            str(PYTHON_VENDOR),
            str(ROOT / "drivers"),
        )
        cls.radio_class = cls.directory.get_radio("Kenwood_TK-270G")

    def test_newchirp_driver_supersedes_chirp_registration(self):
        self.assertEqual(self.radio_class.__name__, "NewChirpTK270G")
        prompts = self.radio_class.get_prompts()
        self.assertIn("experimental", prompts.experimental.lower())
        self.assertIn("KPG-56D backup", prompts.experimental)

    def test_unprogrammed_bank_index_is_normalized(self):
        with tempfile.TemporaryDirectory() as temp:
            image = Path(temp) / "Kenwood_TK-270G.img"
            data = bytearray(
                (SOURCE / "tests/images/Kenwood_TK-272G.img").read_bytes()
            )
            data[0xA7:0xAE] = b"P2700\x05\xff"
            image.write_bytes(data)

            radio = self.bridge.radio_from_image(
                self.directory,
                "Kenwood_TK-270G",
                str(image),
            )
            radio._memobj.memory[0].bnumb = 128
            raw_before = bytes(radio._memobj.memory[0].get_raw(asbytes=True))

            memory = radio.get_memory(1)
            bank = next(
                setting
                for setting in memory.extra
                if setting.get_name() == "bank"
            )
            bnumb = next(
                setting
                for setting in memory.extra
                if setting.get_name() == "bnumb"
            )

        self.assertEqual(
            bytes(radio._memobj.memory[0].get_raw(asbytes=True)),
            raw_before,
        )
        self.assertEqual(int(bank.value), 1)
        self.assertEqual(int(bnumb.value), 0)

    def test_round_trip_preserves_bank_metadata_and_channel_count(self):
        with tempfile.TemporaryDirectory() as temp:
            image = Path(temp) / "Kenwood_TK-270G.img"
            data = bytearray(
                (SOURCE / "tests/images/Kenwood_TK-272G.img").read_bytes()
            )
            data[0xA7:0xAE] = b"P2700\x05\xff"
            image.write_bytes(data)

            radio = self.bridge.radio_from_image(
                self.directory,
                "Kenwood_TK-270G",
                str(image),
            )
            active_numbers = [
                number
                for number in range(1, 129)
                if radio._memobj.memory[number - 1].rxfreq[0].get_raw(
                    asbytes=True
                ) != b"\xff"
            ]
            original_table = {
                data[offset + 3]: data[offset + 1]
                for offset in range(0x300, 0x500, 4)
                if data[offset] != 0xFF
            }
            expected_bank_metadata = {
                number: (
                    int(radio._memobj.memory[number - 1].bank),
                    int(radio._memobj.memory[number - 1].bnumb),
                )
                for number in active_numbers
            }

            for number in active_numbers:
                memory = radio.get_memory(number)
                input_bank = next(
                    setting
                    for setting in memory.extra
                    if setting.get_name() == "bank"
                )
                input_bnumb = next(
                    setting
                    for setting in memory.extra
                    if setting.get_name() == "bnumb"
                )
                self.assertEqual(
                    int(input_bank.value),
                    expected_bank_metadata[number][0],
                )
                self.assertTrue(0 <= int(input_bnumb.value) <= 127)
                radio.set_memory(memory)

            # Banks are kept. Positions become 1..n per bank in the order
            # of the original 0x300 table (slot order in this CHIRP-written
            # sample, whose record positions hold duplicates and zeros).
            by_bank = {}
            for number in active_numbers:
                bank, _old = expected_bank_metadata[number]
                table_position = original_table.get(number - 1, 999)
                by_bank.setdefault(bank, []).append((table_position, number))
            for bank, members in by_bank.items():
                for position, (_t, number) in enumerate(sorted(members), 1):
                    channel = radio._memobj.memory[number - 1]
                    self.assertEqual(
                        (int(channel.bank), int(channel.bnumb)),
                        (bank, position),
                    )
            self.assertEqual(
                int(radio._memobj.settings.banks),
                len({bank for bank, _index in expected_bank_metadata.values()}),
            )
            self.assertEqual(
                int(radio._memobj.settings.channels),
                len(active_numbers),
            )

    def test_upload_sequence_preserves_nonzero_counts(self):
        with tempfile.TemporaryDirectory() as temp:
            image = Path(temp) / "Kenwood_TK-270G.img"
            data = bytearray(
                (SOURCE / "tests/images/Kenwood_TK-272G.img").read_bytes()
            )
            data[0xA7:0xAE] = b"P2700\x05\xff"
            image.write_bytes(data)

            serial = FakeTK270GSerial()
            radio = self.radio_class(serial)
            radio.load_mmap(str(image))
            radio.status_fn = lambda _status: None

            with mock.patch("time.sleep", return_value=None):
                radio.sync_out()

            self.assertEqual(serial.writes[0], b"PROGRAM")
            self.assertEqual(serial.writes[1], b"\x02")
            self.assertTrue(
                any(write[:1] in (b"W", b"Z") for write in serial.writes)
            )
            self.assertEqual(serial.writes[-1], b"E")
            self.assertEqual(int(radio._memobj.settings.banks), 4)
            self.assertEqual(int(radio._memobj.settings.channels), 36)

    def test_upload_normalizes_erased_bank_index(self):
        with tempfile.TemporaryDirectory() as temp:
            image = Path(temp) / "Kenwood_TK-270G.img"
            data = bytearray(
                (SOURCE / "tests/images/Kenwood_TK-272G.img").read_bytes()
            )
            data[0xA7:0xAE] = b"P2700\x05\xff"
            image.write_bytes(data)

            serial = FakeTK270GSerial()
            radio = self.radio_class(serial)
            radio.load_mmap(str(image))
            radio.status_fn = lambda _status: None
            number = next(
                index
                for index, memory in enumerate(radio._memobj.memory, start=1)
                if memory.rxfreq[0].get_raw(asbytes=True) != b"\xff"
            )
            channel = radio._memobj.memory[number - 1]
            channel.bank = 1
            channel.bnumb = 128

            with mock.patch("time.sleep", return_value=None):
                radio.sync_out()

            self.assertEqual(int(radio._memobj.memory[number - 1].bank), 1)
            # The erased sentinel is replaced by a real 1-based position.
            self.assertTrue(
                1 <= int(radio._memobj.memory[number - 1].bnumb) <= 128
            )
            self.assertEqual(serial.writes[-1], b"E")

    def test_editing_one_channel_tolerates_erased_index_elsewhere(self):
        # 2026-11-19 report: channel 24 read back with bnumb=128, and editing
        # channel 1 stopped with "invalid bank metadata" before radio I/O.
        with tempfile.TemporaryDirectory() as temp:
            image = Path(temp) / "Kenwood_TK-270G.img"
            data = bytearray(
                (SOURCE / "tests/images/Kenwood_TK-272G.img").read_bytes()
            )
            data[0xA7:0xAE] = b"P2700\x05\xff"
            image.write_bytes(data)

            radio = self.radio_class(None)
            radio.load_mmap(str(image))
            programmed = [
                index
                for index, memory in enumerate(radio._memobj.memory, start=1)
                if memory.rxfreq[0].get_raw(asbytes=True) != b"\xff"
            ]
            self.assertGreaterEqual(len(programmed), 2)
            edited, other = programmed[0], programmed[-1]
            radio._memobj.memory[other - 1].bank = 1
            radio._memobj.memory[other - 1].bnumb = 128

            memory = radio.get_memory(edited)
            memory.name = "EDITED"
            radio.set_memory(memory)

            self.assertEqual(int(radio._memobj.memory[other - 1].bank), 1)
            self.assertTrue(
                1 <= int(radio._memobj.memory[other - 1].bnumb) <= 128
            )
            self.assertEqual(radio.get_memory(edited).name.strip(), "EDITED")

    def _radio_from_sample(self, name):
        data = bytearray((SOURCE / "tests/images" / name).read_bytes())
        data[0xA7:0xAE] = b"P2700\x05\xff"
        radio = self.radio_class(None)
        with tempfile.TemporaryDirectory() as temp:
            image = Path(temp) / "Kenwood_TK-270G.img"
            image.write_bytes(data)
            radio.load_mmap(str(image))
        return radio, bytes(data)

    @staticmethod
    def _table(radio):
        data = radio.get_mmap().get_packed()
        entries = []
        for offset in range(0x300, 0x500, 4):
            entry = tuple(data[offset:offset + 4])
            if entry[0] == 0xFF:
                break
            entries.append(entry)
        return entries

    def test_kpg_programmed_bank_table_is_rebuilt_unchanged(self):
        # CHIRP's TK-760G sample keeps 1-based record positions that match
        # the 0x300 table, out of slot order (slot 41 is bank 1 position
        # 16). Rebuilding must reproduce it byte for byte.
        radio, original = self._radio_from_sample("Kenwood_TK-760G.img")
        radio._prep_data()
        rebuilt = radio.get_mmap().get_packed()
        self.assertEqual(rebuilt[0x300:0x300 + 51 * 4], original[0x300:0x300 + 51 * 4])
        self.assertEqual(rebuilt[0x1000:0x1040], original[0x1000:0x1040])
        for slot in range(51):
            self.assertEqual(rebuilt[0x2000 + slot * 48], original[0x2000 + slot * 48])
        radio._validate_bank_state()

    def test_added_last_channel_gets_the_next_position(self):
        # 2026-11-20 report (ledger w-20261120-8af9): a KPG-programmed radio
        # had channels 1-24 at positions 1-24 (channel 24 holding the 0x80
        # sentinel); NewChirp gave channel 24 position 23 and a new channel
        # 25 position 24, so position 25 was empty and the radio dropped
        # the last channel.
        from chirp.settings import RadioSettingGroup
        radio, _original = self._radio_from_sample("Kenwood_TK-760G.img")
        template = radio.get_memory(1)
        for slot in range(128):
            radio._memobj.memory[slot].set_raw(b"\xFF" * 48)
        for number in range(1, 25):
            memory = template.dupe()
            memory.number = number
            memory.name = "CH%02d" % number
            memory.extra = RadioSettingGroup("extra", "Extra")
            radio.set_memory(memory)
            radio._memobj.memory[number - 1].bank = 1
            radio._memobj.memory[number - 1].bnumb = number   # KPG 1-based
        radio._memobj.memory[23].bnumb = 0x80                 # sentinel
        added = template.dupe()
        added.number = 25
        added.name = "CH25"
        added.extra = RadioSettingGroup("extra", "Extra")
        radio.set_memory(added)

        positions = [int(radio._memobj.memory[s].bnumb) for s in range(25)]
        self.assertEqual(positions, list(range(1, 26)))
        table = self._table(radio)
        self.assertEqual(len(table), 25)
        self.assertEqual(table[-1], (1, 25, 0, 24))
        self.assertEqual(int(radio._memobj.settings.channels), 25)
        packed = radio.get_mmap().get_packed()
        self.assertEqual(tuple(packed[0x1000:0x1002]), (1, 25))
        radio._validate_bank_state()

    def test_deleting_channels_compacts_positions_without_stale_entries(self):
        radio, _original = self._radio_from_sample("Kenwood_TK-760G.img")
        before = len(self._table(radio))
        for number in (2, 3, 42):    # two from bank 1's start, one (slot 41)
            empty = radio.get_memory(number)
            empty.empty = True
            radio.set_memory(empty)
        radio._prep_data()   # as sync_out does before writing
        table = self._table(radio)
        self.assertEqual(len(table), before - 3)
        bank1 = [entry for entry in table if entry[0] == 1]
        self.assertEqual([entry[1] for entry in bank1], list(range(1, 14)))
        packed = radio.get_mmap().get_packed()
        self.assertEqual(packed[0x300 + len(table) * 4:0x500], b"\xFF" * (0x200 - len(table) * 4))
        radio._validate_bank_state()

    def test_transient_block_checksum_rejection_is_retried(self):
        with tempfile.TemporaryDirectory() as temp:
            image = Path(temp) / "Kenwood_TK-270G.img"
            data = bytearray(
                (SOURCE / "tests/images/Kenwood_TK-272G.img").read_bytes()
            )
            data[0xA7:0xAE] = b"P2700\x05\xff"
            image.write_bytes(data)

            serial = FakeTK270GSerial()
            serial.rejected_writes[0x51] = 1
            radio = self.radio_class(serial)
            radio.load_mmap(str(image))
            radio.status_fn = lambda _status: None

            with mock.patch("time.sleep", return_value=None):
                radio.sync_out()

            block_51_frames = [
                write
                for write in serial.writes
                if write[:1] in (b"W", b"Z")
                and struct.unpack(">H", write[1:3])[0] == 0x51
            ]
            self.assertEqual(len(block_51_frames), 2)
            self.assertEqual(block_51_frames[0], block_51_frames[1])
            self.assertEqual(serial.writes[-1], b"E")

    def test_persistent_block_checksum_rejection_stops_after_three(self):
        with tempfile.TemporaryDirectory() as temp:
            image = Path(temp) / "Kenwood_TK-270G.img"
            data = bytearray(
                (SOURCE / "tests/images/Kenwood_TK-272G.img").read_bytes()
            )
            data[0xA7:0xAE] = b"P2700\x05\xff"
            image.write_bytes(data)

            serial = FakeTK270GSerial()
            serial.rejected_writes[0x51] = 3
            radio = self.radio_class(serial)
            radio.load_mmap(str(image))
            radio.status_fn = lambda _status: None

            with mock.patch("time.sleep", return_value=None):
                with self.assertRaisesRegex(
                    Exception,
                    "after 3 attempts",
                ):
                    radio.sync_out()

            self.assertEqual(serial.writes[-1], b"E")

    def test_upload_writes_rebuilt_bank_counts_block(self):
        # 2026-11-21 read-back after a 1.0.66 write: 25 channels in the
        # header and 0x300 table, but 0x1000 still held the KPG-56D count
        # (bank 1: 24) because block 0x10 was never sent, so the radio
        # stopped at channel 24.
        with tempfile.TemporaryDirectory() as temp:
            image = Path(temp) / "Kenwood_TK-270G.img"
            data = bytearray(
                (SOURCE / "tests/images/Kenwood_TK-272G.img").read_bytes()
            )
            data[0xA7:0xAE] = b"P2700\x05\xff"
            # Stale per-bank counts, one short in every bank.
            for offset in range(0x1000, 0x1100, 16):
                if data[offset] != 0xFF:
                    data[offset + 1] -= 1
            image.write_bytes(data)

            serial = FakeTK270GSerial()
            radio = self.radio_class(serial)
            radio.load_mmap(str(image))
            radio.status_fn = lambda _status: None

            with mock.patch("time.sleep", return_value=None):
                radio.sync_out()

            frames = {}
            for write in serial.writes:
                if write[:1] in (b"W", b"Z"):
                    frames.setdefault(
                        struct.unpack(">H", write[1:3])[0], []
                    ).append(write)

            packed = radio.get_mmap().get_packed()
            if isinstance(packed, str):
                packed = packed.encode("latin-1")
            self.assertEqual(len(frames.get(0x10, [])), 1)
            self.assertEqual(frames[0x10][0][:1], b"W")
            self.assertEqual(frames[0x10][0][3:3 + 256], packed[0x1000:0x1100])
            written_total = sum(
                packed[offset + 1]
                for offset in range(0x1000, 0x1100, 16)
                if packed[offset] != 0xFF
            )
            self.assertEqual(
                written_total, int(radio._memobj.settings.channels)
            )
            # Empty optional blocks and the non-programmable 0x59-0x5E area
            # are still never sent.
            for address in range(0x11, 0x1F):
                if packed[address * 256:(address + 1) * 256] == b"\xff" * 256:
                    self.assertNotIn(address, frames)
            for address in range(0x59, 0x5F):
                self.assertNotIn(address, frames)


if __name__ == "__main__":
    unittest.main()
