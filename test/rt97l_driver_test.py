"""Offline tests for the experimental Retevis RT97L driver."""

from collections import deque
from pathlib import Path
import importlib.util
import sys
import unittest


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "build_support/chirp-20261023"
PYTHON_VENDOR = ROOT / "assets/python/pyserial-3.5-py2.py3-none-any.whl"


def _load_bridge():
    spec = importlib.util.spec_from_file_location(
        "newchirp_chirp_bridge_rt97l",
        ROOT / "scripts/chirp_bridge.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load chirp_bridge.py")
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


def _frequency_bytes(frequency):
    digits = ("%08i" % (frequency // 10))
    return bytes(
        int(digits[index]) << 4 | int(digits[index + 1])
        for index in range(0, 8, 2)
    )


def _record(rx, tx, *, encode_tone=0, decode_tone=0, flags1=0,
            squelch=0xFF, flags2=0):
    record = bytearray(16)
    record[0:4] = _frequency_bytes(rx)
    record[4:8] = _frequency_bytes(tx)
    record[8] = encode_tone
    record[9] = decode_tone
    record[10] = flags1
    record[11] = squelch
    record[12] = flags2
    return bytes(record)


class FakeRT97LSerial:
    def __init__(self, memory):
        self.memory = memory
        self.responses = deque([b"\x06"])
        self.writes = []
        self.identity = b"P3\x01\x02\x03\x04\x05\xff"
        self.max_read_size = 7
        self.ended = False
        self.timeout = 2

    def write(self, data):
        data = bytes(data)
        self.writes.append(data)
        if data == b"\x02":
            self.responses.append(self.identity)
        elif data == b"\x06":
            self.responses.append(b"\x06")
        elif data[:1] == b"R":
            address = (data[1] << 8) | data[2]
            length = data[3]
            self.responses.append(
                b"W" + data[1:] + self.memory[address:address + length]
            )
        elif data == b"E":
            self.ended = True

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


class WakeOnStxRT97LSerial(FakeRT97LSerial):
    """Simulate a radio that requires STX before announcing programming mode."""

    def __init__(self, memory):
        super().__init__(memory)
        self.responses.clear()
        self.wakeup_sent = False

    def write(self, data):
        data = bytes(data)
        if data == b"\x02" and not self.wakeup_sent:
            self.wakeup_sent = True
            self.writes.append(data)
            self.responses.append(b"\x06")
            return
        super().write(data)


class SilentRT97LSerial(FakeRT97LSerial):
    def __init__(self):
        super().__init__(b"\xff" * 0x100)
        self.responses.clear()

    def read(self, _size):
        return b""

    def write(self, data):
        self.writes.append(bytes(data))


class RT97LDriverTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        bridge = _load_bridge()
        cls.directory = bridge.load_chirp(
            str(SOURCE),
            str(PYTHON_VENDOR),
            str(ROOT / "drivers"),
        )
        cls.radio_class = cls.directory.get_radio("Retevis_RT97L")

    def _radio_from_memory(self, memory):
        from chirp import memmap

        return self.radio_class(memmap.MemoryMapBytes(bytes(memory)))

    def test_catalog_and_read_only_policy(self):
        self.assertEqual(
            self.directory.get_radio("Retevis_RT97L"),
            self.radio_class,
        )
        self.assertEqual(self.radio_class.BAUD_RATE, 9600)
        self.assertTrue(self.radio_class.WANTS_DTR)
        self.assertTrue(self.radio_class.WANTS_RTS)

        radio = self._radio_from_memory(b"\xff" * 0x100)
        from chirp import errors

        with self.assertRaises(errors.RadioError):
            radio.sync_out()
        with self.assertRaises(errors.RadioError):
            radio.set_memory(radio.get_memory(1))

    def test_protocol_reads_eight_blocks_and_ends_session(self):
        memory = bytearray(b"\xff" * 0x100)
        memory[0:16] = _record(462_550_000, 467_550_000)
        serial = FakeRT97LSerial(memory)
        radio = self.radio_class(serial)
        radio.status_fn = lambda _status: None

        radio.sync_in()

        reads = [write for write in serial.writes if write[:1] == b"R"]
        self.assertEqual(len(reads), 8)
        self.assertEqual(reads[0], b"R\x00\x00\x20")
        self.assertEqual(reads[-1], b"R\x00\xe0\x20")
        self.assertTrue(serial.ended)
        self.assertEqual(radio._mmap.get(0, 4), _frequency_bytes(462_550_000))

    def test_protocol_wakes_radio_when_initial_ack_is_missing(self):
        serial = WakeOnStxRT97LSerial(b"\xff" * 0x100)
        radio = self.radio_class(serial)
        radio.status_fn = lambda _status: None
        radio.INITIAL_ACK_TIMEOUT = 0.01
        radio.WAKE_ACK_TIMEOUT = 0.01
        radio.WAKE_DELAY = 0

        radio.sync_in()

        self.assertEqual(serial.writes[:2], [b"\x02", b"\x02"])
        self.assertEqual(
            len([write for write in serial.writes if write[:1] == b"R"]),
            8,
        )
        self.assertTrue(serial.ended)

    def test_protocol_reports_failure_after_wakeup_when_radio_is_silent(self):
        serial = SilentRT97LSerial()
        radio = self.radio_class(serial)
        radio.status_fn = lambda _status: None
        radio.INITIAL_ACK_TIMEOUT = 0.01
        radio.WAKE_ACK_TIMEOUT = 0.01
        radio.WAKE_DELAY = 0
        from chirp import errors

        with self.assertRaises(errors.RadioNoResponse) as raised:
            radio.sync_in()

        self.assertIn("STX wake-up", str(raised.exception))
        self.assertEqual(serial.writes, [b"\x02"])

    def test_protocol_rejects_a_different_device(self):
        serial = FakeRT97LSerial(b"\xff" * 0x100)
        serial.identity = b"X3\x01\x02\x03\x04\x05\xff"
        radio = self.radio_class(serial)
        radio.status_fn = lambda _status: None
        from chirp import errors

        with self.assertRaises(errors.RadioError):
            radio.sync_in()

        self.assertFalse([write for write in serial.writes if write[:1] == b"R"])

    def test_channel_fields_and_radio_specific_extras(self):
        memory = bytearray(b"\xff" * 0x100)
        # 100.0 Hz is CTCSS table index 13; D023N is DCS table index 51.
        memory[0:16] = _record(
            462_550_000,
            467_550_000,
            encode_tone=13,
            decode_tone=51,
            flags1=0x0D,
            squelch=7,
            flags2=0x02,
        )
        radio = self._radio_from_memory(memory)
        mem = radio.get_memory(1)

        self.assertFalse(mem.empty)
        self.assertEqual(mem.freq, 462_550_000)
        self.assertEqual(mem.duplex, "+")
        self.assertEqual(mem.offset, 5_000_000)
        self.assertEqual(mem.tmode, "Cross")
        self.assertEqual(mem.cross_mode, "Tone->DTCS")
        self.assertEqual(mem.rtone, 100.0)
        self.assertEqual(mem.rx_dtcs, 23)
        self.assertEqual(mem.mode, "NFM")
        self.assertEqual(str(mem.power), "Low")
        self.assertEqual(mem.skip, "S")

        extras = {setting.get_name(): setting.value.get_value()
                  for setting in mem.extra}
        self.assertEqual(extras["squelch"], "7")
        self.assertEqual(extras["channel_mode"], "CH+Frequency")
        self.assertEqual(extras["compand"], "Narrow")
        self.assertEqual(extras["scan_add"], False)
        self.assertEqual(extras["channel_lock"], True)

    def test_zero_frequency_channel_is_empty(self):
        radio = self._radio_from_memory(b"\x00" * 0x100)
        self.assertTrue(radio.get_memory(1).empty)


if __name__ == "__main__":
    unittest.main()
