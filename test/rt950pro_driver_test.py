"""Offline tests for the Radtel RT-950 Pro driver (Pro CPS 1.3.3)."""

from collections import deque
from pathlib import Path
import importlib.util
import sys
import unittest
from unittest import mock

from chirp_test_source import chirp_source


ROOT = Path(__file__).resolve().parent.parent
SOURCE = chirp_source()
PYTHON_VENDOR = ROOT / "assets/python/pyserial-3.5-py2.py3-none-any.whl"


def _load_bridge():
    spec = importlib.util.spec_from_file_location(
        "newchirp_chirp_bridge_rt950pro",
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
    parts = (
        (tens // 1_000_000) % 100,
        (tens // 10_000) % 100,
        (tens // 100) % 100,
        tens % 100,
    )
    return bytes(
        ((part // 10) << 4) | (part % 10)
        for part in reversed(parts)
    )


def _record(rx, tx, *, name=b"", power=0, flags=0x04):
    record = bytearray(32)
    record[0:4] = _frequency_bytes(rx)
    record[4:8] = _frequency_bytes(tx)
    record[14] = power
    record[15] = flags
    record[20:32] = name.ljust(12, b"\x00")[:12]
    return bytes(record)


def _scramble(payload, symbol):
    out = bytearray(payload)
    for index, value in enumerate(out):
        key = symbol[index % 4]
        if key != 0x20 and value not in (0, 0xFF, key, key ^ 0xFF):
            out[index] ^= key
    return bytes(out)


class FakeRT950ProSerial:
    """A radio with the Pro CPS address spaces (0x52/0x57 and 0x54/0x58)."""

    def __init__(self, memory=None, aprs=None):
        self.memory = bytearray(memory or b"\xff" * 0x10000)
        self.aprs = bytearray(aprs or b"\xff" * 0x80)
        self.responses = deque()
        self.writes = []
        self.ack_handshake = True
        self.model = b"RT-950"
        self.encryption_symbol = b"    "
        self.withhold_acks = {}      # address -> number of ACKs to drop

    def reset_input_buffer(self):
        self.responses.clear()

    def write(self, data):
        data = bytes(data)
        self.writes.append(data)
        if data == b"PROGRAMBT9000U":
            self.responses.append(b"\x06" if self.ack_handshake else b"")
        elif data == b"F":
            self.responses.append(b"\x00" * 16)
        elif data == b"M":
            self.responses.append(self.model.ljust(12, b"\x00"))
        elif data[:4] == b"SEND":
            compat = sys.modules["newchirp.drivers.newchirp_rt950"]
            index = (
                (data[4] - 32) * 2 + 1
                if data[4] & 0x20
                else (data[4] - 16) * 2
            ) + 1
            self.encryption_symbol = compat.SEND_SYMBOLS[
                data[4 + index]
            ].encode("ascii")
            self.responses.append(b"\x06")
        elif len(data) == 4 and data[0] in (0x52, 0x54):
            address = (data[1] << 8) | data[2]
            store = self.memory if data[0] == 0x52 else self.aprs
            payload = store[address:address + data[3]]
            self.responses.append(
                b"W" + data[1:] + _scramble(payload, self.encryption_symbol))
        elif len(data) == 132 and data[0] in (0x57, 0x58):
            address = (data[1] << 8) | data[2]
            if self.withhold_acks.get(address, 0):
                self.withhold_acks[address] -= 1
                return
            store = self.memory if data[0] == 0x57 else self.aprs
            store[address:address + 128] = _scramble(
                data[4:], self.encryption_symbol)
            self.responses.append(b"\x06")

    def read(self, size):
        result = bytearray()
        while self.responses and len(result) < size:
            chunk = self.responses[0]
            take = min(size - len(result), len(chunk), 7)
            result.extend(chunk[:take])
            if take == len(chunk):
                self.responses.popleft()
            else:
                self.responses[0] = chunk[take:]
        return bytes(result)


class RT950ProDriverTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        bridge = _load_bridge()
        cls.directory = bridge.load_chirp(
            str(SOURCE),
            str(PYTHON_VENDOR),
            str(ROOT / "drivers"),
        )
        cls.radio_class = cls.directory.get_radio("Radtel_RT-950_Pro")
        cls.base_class = cls.directory.get_radio("Radtel_RT-950")
        cls.pro = sys.modules["newchirp.drivers.newchirp_rt950pro"]

    def _radio(self, serial):
        radio = self.radio_class(serial)
        radio.status_fn = lambda _status: None
        # Protocol tests exercise the (suspended) write path directly.
        radio.WRITES_SUSPENDED = False
        return radio

    def _radio_memory(self):
        memory = bytearray(b"\xff" * 0x10000)
        memory[0:32] = _record(462_575_000, 467_575_000, name=b"PRO")
        memory[989 * 32:990 * 32] = _record(146_520_000, 146_520_000,
                                            name=b"LAST990")
        memory[0x8000:0x8010] = bytes(range(16))          # VFO
        memory[0x9000:0x9010] = bytes(range(16, 32))      # settings
        memory[0xA0FC:0xA100] = b"DTMF"
        memory[0xB000:0xB004] = b"MODU"
        memory[0xC000:0xC008] = b"ZONE A\xff\xff"
        memory[0xD2FC:0xD300] = b"LAST"
        return memory

    def test_catalog_uses_the_pro_cps_layout(self):
        self.assertIsNot(self.radio_class, self.base_class)
        self.assertEqual(self.radio_class.MODEL, "RT-950 Pro")
        self.assertEqual(self.radio_class._memsize, 0xD380)
        self.assertEqual(self.radio_class.INITIAL_ACK_TIMEOUT, 3.0)
        radio = self.radio_class(None)
        self.assertEqual(radio.get_features().memory_bounds, (1, 990))
        self.assertTrue(self.base_class.NEWCHIRP_WRITE_DISABLED)

    def test_writes_are_suspended_before_any_radio_traffic(self):
        # 2026-11-20 no-TX report (ledger w-20261120-9877).
        self.assertTrue(self.radio_class.NEWCHIRP_WRITE_DISABLED)
        self.assertTrue(self.radio_class.WRITES_SUSPENDED)

        class Untouchable:
            def __getattr__(self, name):
                raise AssertionError("serial used: %s" % name)

        radio = self.radio_class(Untouchable())
        with self.assertRaisesRegex(Exception, "paused"):
            radio.sync_out()

    def test_read_follows_the_cps_block_order(self):
        serial = FakeRT950ProSerial(self._radio_memory(), b"APRS" + b"\xff" * 124)
        radio = self._radio(serial)
        radio.sync_in()

        reads = [w for w in serial.writes
                 if len(w) == 4 and w[0] in (0x52, 0x54)]
        addresses = [(w[0], (w[1] << 8) | w[2]) for w in reads]
        expected = (
            [(0x52, a) for a in range(0x0000, 0x8000, 0x80)]
            + [(0x52, 0x8000), (0x52, 0x9000)]
            + [(0x52, a) for a in range(0xA000, 0xA180, 0x80)]
            + [(0x52, a) for a in range(0xB000, 0xB100, 0x80)]
            + [(0x52, a) for a in range(0xC000, 0xC100, 0x80)]
            + [(0x52, a) for a in range(0xD000, 0xD300, 0x80)]
            + [(0x54, 0x0000)]
        )
        self.assertEqual(addresses, expected)
        self.assertEqual(len(reads), 272)
        self.assertEqual(serial.writes[-1], b"E")
        self.assertEqual(radio._mmap.get(0xC000, 6), b"ZONE A")
        self.assertEqual(radio._mmap.get(0xD300, 4), b"APRS")
        self.assertEqual(radio._mmap.get(0xD2FC, 4), b"LAST")
        self.assertEqual(radio.get_memory(1).name, "PRO")
        self.assertEqual(radio.get_memory(1).duplex, "+")
        self.assertEqual(radio.get_memory(990).name, "LAST990")

    def test_write_round_trip_changes_only_edited_channels(self):
        original = self._radio_memory()
        serial = FakeRT950ProSerial(original, b"APRS" + b"\xff" * 124)
        radio = self._radio(serial)
        radio.sync_in()

        from chirp import chirp_common
        mem = radio.get_memory(1)
        mem.name = "EDITED"
        mem.tmode = "TSQL"
        mem.ctone = 141.3
        radio.set_memory(mem)
        new = chirp_common.Memory()
        new.number = 500
        new.freq = 446_006_250
        new.mode = "NFM"
        new.power = "Low"
        new.name = "NEW500"
        radio.set_memory(new)

        serial.writes.clear()
        radio.sync_out()

        frames = [w for w in serial.writes if len(w) == 132]
        self.assertEqual(len(frames), 272)
        self.assertTrue(all(f[0] == 0x57 for f in frames[:-1]))
        self.assertEqual(frames[-1][0], 0x58)
        self.assertEqual(serial.writes[-1], b"E")
        changed = [
            offset for offset in range(0, 0x10000, 32)
            if serial.memory[offset:offset + 32] != original[offset:offset + 32]
        ]
        self.assertEqual(changed, [0, 499 * 32])
        self.assertEqual(bytes(serial.aprs[:4]), b"APRS")

        check = self._radio(serial)
        check.sync_in()
        first = check.get_memory(1)
        self.assertEqual((first.name, first.tmode, first.ctone),
                         ("EDITED", "TSQL", 141.3))
        added = check.get_memory(500)
        self.assertEqual((added.freq, added.mode, added.power, added.name),
                         (446_006_250, "NFM", "Low", "NEW500"))

    def test_encoder_matches_the_cps_record_rules(self):
        from chirp import chirp_common
        mem = chirp_common.Memory()
        mem.number = 2
        mem.freq = 462_562_500
        mem.duplex = "off"
        mem.tmode = "Cross"
        mem.cross_mode = "DTCS->Tone"
        mem.dtcs = 754
        mem.dtcs_polarity = "RN"
        mem.ctone = 141.3
        mem.mode = "NAM"
        mem.power = "Middle"
        mem.skip = "S"
        mem.name = "频道A"
        radio = self._radio(FakeRT950ProSerial())
        radio._mmap = __import__("chirp").memmap.MemoryMapBytes(
            b"\xff" * self.radio_class._memsize)
        base = radio.get_memory(2)
        for setting in base.extra:
            if setting.get_name() == "scramble":
                setting.value = "Scramble 3"
            elif setting.get_name() == "ptt_id":
                setting.value = "EOT"
            elif setting.get_name() == "fhss_code":
                setting.value = "1A2B3C"
        mem.extra = base.extra

        record = self.pro.encode_channel(mem)
        self.assertEqual(record[0:4], bytes.fromhex("50622546"))
        self.assertEqual(record[4:8], b"\xff" * 4)        # TX off
        self.assertEqual(record[8:10], bytes((0x85, 0x05)))  # RX 141.3
        self.assertEqual(record[10:12], bytes((210, 0)))   # TX D754I
        self.assertEqual(record[13], 2)                    # EOT
        self.assertEqual(record[14], (3 << 4) | 1)         # scramble 3, Middle
        self.assertEqual(record[15], 0x40 | 0x01)          # narrow AM, no scan
        self.assertEqual(record[16:20], bytes((0x3C, 0x2B, 0x1A, 0xA0)))
        self.assertEqual(record[20:25], "频道A".encode("gb2312"))
        self.assertEqual(record[25:32], b"\xff" * 7)

        mem.empty = True
        self.assertEqual(self.pro.encode_channel(mem), b"\xff" * 32)

    def test_app_round_trip_rewrites_unedited_channels_identically(self):
        """Every channel the app sends back is re-encoded by the bridge;
        untouched channels must reach the radio byte-identical."""
        import random
        bridge = sys.modules["newchirp_chirp_bridge_rt950pro"]
        memory = bytearray(b"\xff" * 0x10000)
        rnd = random.Random(7)
        for n in range(990):
            if rnd.random() < 0.6:
                rx = rnd.choice([146_520_000, 462_562_500, 446_006_250,
                                 118_100_000, 433_500_000, 462_712_500])
                record = bytearray(b"\xff" * 32)
                record[0:4] = _frequency_bytes(rx)
                if rnd.random() < 0.8:
                    record[4:8] = _frequency_bytes(
                        rx + rnd.choice([0, 5_000_000, -600_000]))
                record[8:10] = rnd.choice(
                    [0, 0x029E, 0x0585, 0x03E8, 0x0001, 0x006E]
                ).to_bytes(2, "little")
                record[10:12] = rnd.choice(
                    [0, 0x0585, 0x0003, 0x00D2]).to_bytes(2, "little")
                record[12] = rnd.randrange(15)
                record[13] = rnd.randrange(4)
                record[14] = (rnd.randrange(9) << 4) | rnd.randrange(3)
                record[15] = ((rnd.randrange(2) << 7) | (rnd.randrange(2) << 6)
                              | (rnd.randrange(4) << 4) | (rnd.randrange(2) << 3)
                              | (rnd.randrange(2) << 2) | rnd.randrange(2))
                if rnd.random() < 0.2:
                    record[16:20] = bytes((0x3C, 0x2B, 0x1A, 0xA0))
                name = ("CH%d" % n).encode()
                record[20:20 + len(name)] = name
                memory[n * 32:(n + 1) * 32] = record
        memory[0x9000:0x9080] = bytes(range(128))
        serial = FakeRT950ProSerial(memory)
        radio = self._radio(serial)
        radio.sync_in()
        items = [bridge.memory_json(radio.get_memory(n))
                 for n in range(1, 991) if not radio.get_memory(n).empty]

        skipped, adjusted, written = bridge.prepare_upload_channels(
            radio, items)
        self.assertEqual((skipped, adjusted, written), ([], [], len(items)))
        serial.writes.clear()
        radio.sync_out()
        self.assertEqual(bytes(serial.memory), bytes(memory))

    def test_fhss_code_uses_the_cps_byte_order(self):
        memory = bytearray(b"\xff" * 0x10000)
        record = bytearray(_record(146_520_000, 146_520_000))
        record[16:20] = bytes((0x3C, 0x2B, 0x1A, 0xA0))
        memory[0:32] = record
        radio = self._radio(FakeRT950ProSerial(memory))
        radio.sync_in()
        code = {s.get_name(): str(s.value)
                for s in radio.get_memory(1).extra}["fhss_code"]
        self.assertEqual(code, "1A2B3C")

    def test_write_refuses_a_base_rt950_and_old_images(self):
        from chirp import errors, memmap
        serial = FakeRT950ProSerial(self._radio_memory())
        radio = self._radio(serial)
        radio.sync_in()
        serial.model = b"BT-9000"
        serial.writes.clear()
        with self.assertRaisesRegex(errors.RadioError, "BT-9000"):
            radio.sync_out()
        self.assertFalse([w for w in serial.writes if len(w) == 132])

        legacy = self._radio(FakeRT950ProSerial())
        legacy._mmap = memmap.MemoryMapBytes(b"\xff" * 0xD300)
        with self.assertRaisesRegex(errors.RadioError, "older NewChirp"):
            legacy.sync_out()
        with self.assertRaisesRegex(errors.RadioError, "Read the radio"):
            legacy.set_memory(legacy.get_memory(1))
        self.assertTrue(legacy.get_memory(970).empty)

    def test_write_resends_unacknowledged_blocks_then_stops(self):
        from chirp import errors
        serial = FakeRT950ProSerial(self._radio_memory())
        radio = self._radio(serial)
        radio.sync_in()
        serial.withhold_acks = {0x8000: 2}
        with mock.patch.object(self.pro, "WRITE_ACK_TIMEOUT", 0.01):
            serial.writes.clear()
            radio.sync_out()
        sends = [w for w in serial.writes
                 if len(w) == 132 and w[1:3] == b"\x80\x00"]
        self.assertEqual(len(sends), 3)

        serial.withhold_acks = {0x9000: 99}
        with mock.patch.object(self.pro, "WRITE_ACK_TIMEOUT", 0.01):
            serial.writes.clear()
            with self.assertRaisesRegex(errors.RadioNoResponse,
                                        "partly written"):
                radio.sync_out()
        sends = [w for w in serial.writes
                 if len(w) == 132 and w[1:3] == b"\x90\x00"]
        self.assertEqual(len(sends), 4)       # first try + 3 resends
        self.assertEqual(serial.writes[-1], b"E")

    def test_unknown_model_is_rejected(self):
        serial = FakeRT950ProSerial()
        serial.model = b"OTHER-9000"
        radio = self._radio(serial)
        from chirp import errors

        with self.assertRaisesRegex(
            errors.RadioError,
            "unrecognized model code",
        ):
            radio.sync_in()
        self.assertNotIn(b"E", serial.writes)

    def test_no_ack_uses_the_three_second_profile_and_does_not_read(self):
        serial = FakeRT950ProSerial()
        serial.ack_handshake = False
        radio = self._radio(serial)
        from chirp import errors

        with mock.patch.object(radio, "_read_exact", return_value=b""):
            with self.assertRaisesRegex(errors.RadioNoResponse, "3.0 seconds"):
                radio.sync_in()
        self.assertEqual(serial.writes.count(b"PROGRAMBT9000U"), 3)
        self.assertFalse(
            [write for write in serial.writes if write == b"F"]
        )


if __name__ == "__main__":
    unittest.main()
