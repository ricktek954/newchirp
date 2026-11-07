"""Offline checks for TK-270G bank metadata safety."""

import importlib
import importlib.util
from collections import deque
from pathlib import Path
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
                self.assertEqual(
                    int(input_bnumb.value),
                    expected_bank_metadata[number][1],
                )
                radio.set_memory(memory)

            for number in active_numbers:
                channel = radio._memobj.memory[number - 1]
                self.assertEqual(
                    (int(channel.bank), int(channel.bnumb)),
                    expected_bank_metadata[number],
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


if __name__ == "__main__":
    unittest.main()
