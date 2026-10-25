"""Offline tests for the experimental Radtel RT-950 driver."""

from collections import deque
from pathlib import Path
import importlib.util
import sys
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "build_support/chirp-20261023"
PYTHON_VENDOR = (
    ROOT / "assets/python/pyserial-3.5-py2.py3-none-any.whl"
)


def _load_bridge():
    spec = importlib.util.spec_from_file_location(
        "newchirp_chirp_bridge_rt950",
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
    return bytes(((part // 10) << 4) | (part % 10) for part in parts)


def _record(rx, tx, *, rx_tone=b"\x00\x00", tx_tone=b"\x00\x00",
            name=b"", power=0, flags=0x04):
    record = bytearray(32)
    record[0:4] = _frequency_bytes(rx)
    record[4:8] = _frequency_bytes(tx)
    record[8:10] = rx_tone
    record[10:12] = tx_tone
    record[14] = power
    record[15] = flags
    record[20:32] = name.ljust(12, b"\x00")[:12]
    return bytes(record)


class FakeRT950Serial:
    def __init__(self, memory):
        self.memory = memory
        self.responses = deque()
        self.writes = []
        self.ack_handshake = True
        self.model = b"BT-9000"
        self.max_read_size = 7

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
        elif data[:1] == b"R":
            address = (data[1] << 8) | data[2]
            length = data[3]
            self.responses.append(
                b"W" + data[1:] + self.memory[address:address + length]
            )

    def read(self, size):
        result = bytearray()
        while self.responses and len(result) < size:
            chunk = self.responses[0]
            take = min(
                size - len(result),
                len(chunk),
                self.max_read_size,
            )
            result.extend(chunk[:take])
            if take == len(chunk):
                self.responses.popleft()
            else:
                self.responses[0] = chunk[take:]
        return bytes(result)


class RT950DriverTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        bridge = _load_bridge()
        cls.directory = bridge.load_chirp(
            str(SOURCE),
            str(PYTHON_VENDOR),
            str(ROOT / "drivers"),
        )
        cls.radio_class = cls.directory.get_radio("Radtel_RT-950")

    def _radio_from_memory(self, memory):
        from chirp import memmap

        return self.radio_class(memmap.MemoryMapBytes(bytes(memory)))

    def test_catalog_and_read_only_policy(self):
        self.assertEqual(
            self.directory.get_radio("Radtel_RT-950"),
            self.radio_class,
        )
        self.assertEqual(self.radio_class.BAUD_RATE, 115200)
        self.assertTrue(self.radio_class.HARDWARE_FLOW)
        self.assertTrue(self.radio_class.XON_XOFF)

        radio = self._radio_from_memory(b"\xff" * 0xC100)
        from chirp import errors

        with self.assertRaises(errors.RadioError):
            radio.sync_out()
        with self.assertRaises(errors.RadioError):
            radio.set_memory(radio.get_memory(1))

    def test_open_serial_matches_the_cps_flow_control(self):
        bridge = sys.modules["newchirp_chirp_bridge_rt950"]
        import serial

        handle = mock.MagicMock()
        with mock.patch.object(
            serial, "Serial", return_value=handle
        ) as serial_class:
            self.assertIs(
                bridge.open_serial(self.radio_class, "/dev/fake-rt950"),
                handle,
            )

        self.assertTrue(serial_class.call_args.kwargs["rtscts"])
        self.assertTrue(serial_class.call_args.kwargs["xonxoff"])
        self.assertEqual(serial_class.call_args.kwargs["baudrate"], 115200)
        self.assertTrue(handle.rts)
        self.assertTrue(handle.dtr)
        handle.open.assert_called_once_with()

    def test_protocol_downloads_only_the_cps_memory_ranges(self):
        memory = bytearray(b"\xff" * 0xC100)
        memory[0:32] = _record(146_520_000, 146_520_000, name=b"TEST")
        memory[0xC0FC:0xC100] = b"LAST"
        serial = FakeRT950Serial(memory)
        radio = self.radio_class(serial)
        radio.status_fn = lambda _status: None

        radio.sync_in()

        reads = [write for write in serial.writes if write[:1] == b"R"]
        self.assertEqual(len(reads), 248)
        self.assertEqual(reads[0], b"R\x00\x00\x80")
        self.assertEqual(reads[239], b"R\x77\x80\x80")
        self.assertEqual(reads[240], b"R\x80\x00\x80")
        self.assertEqual(reads[-1], b"R\xc0\x80\x80")
        self.assertEqual(serial.writes[-1], b"E")
        self.assertEqual(radio._mmap.get(0, 4), _frequency_bytes(146_520_000))
        self.assertEqual(radio._mmap.get(0x7800, 4), b"\xff" * 4)
        self.assertEqual(radio._mmap.get(0xC0FC, 4), b"LAST")

    def test_protocol_rejects_a_different_model(self):
        serial = FakeRT950Serial(b"\xff" * 0xC100)
        serial.model = b"BT-9001"
        radio = self.radio_class(serial)
        from chirp import errors

        with self.assertRaises(errors.RadioError):
            radio.sync_in()

        self.assertNotIn(b"E", serial.writes)
        self.assertFalse(
            [write for write in serial.writes if write[:1] == b"R"]
        )

    def test_channel_layout_and_tone_decoding(self):
        ctc_tone = (1000).to_bytes(2, "little")
        memory = bytearray(b"\xff" * 0xC100)
        memory[0:32] = _record(
            146_520_000,
            146_520_000,
            rx_tone=ctc_tone,
            tx_tone=ctc_tone,
            name=b"LOCAL",
        )
        # CPS DCS table index 106 is D023I (DCS 023, reversed).
        memory[32:64] = _record(
            446_006_250,
            446_006_250,
            tx_tone=b"\x6a\x00",
            name=b"DCS",
            power=1,
            flags=0x44,
        )
        memory[64:96] = _record(
            118_100_000,
            118_100_000,
            name=b"AIR",
            power=2,
            flags=0x45,
        )

        radio = self._radio_from_memory(memory)
        first = radio.get_memory(1)
        self.assertEqual(first.freq, 146_520_000)
        self.assertEqual(first.duplex, "")
        self.assertEqual(first.mode, "FM")
        self.assertEqual(first.tmode, "TSQL")
        self.assertEqual(first.ctone, 100.0)
        self.assertEqual(first.power, "High")
        self.assertEqual(first.skip, "")
        self.assertEqual(first.name, "LOCAL")

        second = radio.get_memory(2)
        self.assertEqual(second.freq, 446_006_250)
        self.assertEqual(second.mode, "NFM")
        self.assertEqual(second.tmode, "Cross")
        self.assertEqual(second.cross_mode, "DTCS->")
        self.assertEqual(second.dtcs, 23)
        self.assertEqual(second.dtcs_polarity, "RN")
        self.assertEqual(second.power, "Middle")
        self.assertEqual(second.name, "DCS")

        third = radio.get_memory(3)
        self.assertEqual(third.mode, "NAM")
        self.assertEqual(third.power, "Low")
        self.assertEqual(third.name, "AIR")
        self.assertTrue(radio.get_memory(960).empty)

    def test_channel_fields_have_explanations(self):
        memory = bytearray(b"\xff" * 0xC100)
        memory[0:32] = _record(146_520_000, 146_520_000)
        radio = self._radio_from_memory(memory)

        docs = {
            setting.get_name(): setting.__doc__
            for setting in radio.get_memory(1).extra
        }

        self.assertIn("already busy", docs["bcl"])
        self.assertIn("voice-inversion", docs["scramble"])
        self.assertIn("frequency-hopping", docs["hopping"])


if __name__ == "__main__":
    unittest.main()
