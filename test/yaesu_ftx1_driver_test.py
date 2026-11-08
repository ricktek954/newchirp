"""Offline tests for the experimental Yaesu FTX-1 CAT driver."""

import importlib.util
from pathlib import Path
import re
import sys
import unittest


from chirp_test_source import chirp_source


ROOT = Path(__file__).resolve().parent.parent
SOURCE = chirp_source()
PYTHON_VENDOR = ROOT / "assets/python/pyserial-3.5-py2.py3-none-any.whl"


def _load_bridge():
    spec = importlib.util.spec_from_file_location(
        "newchirp_chirp_bridge_ftx1",
        ROOT / "scripts/chirp_bridge.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load chirp_bridge.py")
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


class FakeFTX1Serial:
    def __init__(self, ack_ai=True):
        self.timeout = 0.35
        self.baudrate = 9600
        self._rx = bytearray()
        self.active = 1
        self.ack_ai = ack_ai
        self.commands = []
        self.memories = {
            1: {
                "freq": 146_940_000,
                "mode": "4",
                "shift": "2",
                "name": "146.94 RPT",
                "sql": "2",
                "tone_kind": "0",
                "tone_index": 22,
            },
            37: {
                "freq": 446_006_250,
                "mode": "B",
                "shift": "0",
                "name": "PMR 01",
                "sql": "0",
                "tone_kind": "0",
                "tone_index": 0,
            },
        }

    def _ack(self, text):
        self._rx.extend((text + ";").encode("ascii"))

    def _mr(self, number):
        record = self.memories.get(number)
        if record is None:
            self._ack("?")
            return
        self._ack(
            "MR%05i%09i+000000%s1%s00%s"
            % (
                number,
                record["freq"],
                record["mode"],
                record["sql"],
                record["shift"],
            )
        )

    def write(self, data):
        command = bytes(data).decode("ascii", errors="replace")
        self.commands.append(command)
        if command == "ID;":
            self._ack("ID0840")
        elif command == "AI0;":
            if self.ack_ai:
                self._ack("AI0")
        elif command == "MC0;":
            self._ack("MC0%05i" % self.active)
        elif re.fullmatch(r"MC0\d{5};", command):
            self.active = int(command[3:8])
        elif re.fullmatch(r"MR\d{5};", command):
            self._mr(int(command[2:7]))
        elif re.fullmatch(r"MT\d{5};", command):
            number = int(command[2:7])
            record = self.memories.get(number)
            if record is None:
                self._ack("?")
            else:
                self._ack("MT%05i%s" % (number, record["name"]))
        elif re.fullmatch(r"CT0;", command):
            self._ack("CT0%s" % self.memories[self.active]["sql"])
        elif re.fullmatch(r"CN0;", command):
            record = self.memories[self.active]
            self._ack(
                "CN0%s%03i"
                % (record["tone_kind"], record["tone_index"])
            )
        elif re.fullmatch(r"CT0[0-5];", command):
            self.memories[self.active]["sql"] = command[3]
            self._ack(command[:-1])
        elif re.fullmatch(r"CN0[01]\d{3};", command):
            self.memories[self.active]["tone_kind"] = command[3]
            self.memories[self.active]["tone_index"] = int(command[4:7])
            self._ack(command[:-1])
        elif re.fullmatch(r"MW\d{5}\d{9}[+-]\d{4}\d{2}[0-9A-F]1[0-5]00[012];", command):
            number = int(command[2:7])
            self.memories[number] = {
                "freq": int(command[7:16]),
                "mode": command[23],
                "shift": command[28],
                "name": self.memories.get(number, {}).get("name", ""),
                "sql": command[25],
                "tone_kind": "0",
                "tone_index": 0,
            }
            self._ack(command[:-1])
        elif re.fullmatch(r"MT\d{5}.*;", command):
            number = int(command[2:7])
            if number in self.memories:
                self.memories[number]["name"] = command[7:-1]
            self._ack(command[:-1])
        else:
            self._ack("?")
        return len(data)

    def read(self, size=1):
        data = bytes(self._rx[:size])
        del self._rx[:size]
        return data

    def flush(self):
        pass

    def reset_input_buffer(self):
        self._rx.clear()

    def close(self):
        pass


class YaesuFTX1Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = _load_bridge().load_chirp(
            str(SOURCE),
            str(PYTHON_VENDOR),
            str(ROOT / "drivers"),
        )
        cls.radio_class = cls.directory.get_radio("Yaesu_FTX-1")

    def test_catalog_and_detection(self):
        serial = FakeFTX1Serial()
        self.assertIs(
            self.radio_class.detect_from_serial(serial),
            self.radio_class,
        )
        features = self.radio_class(serial).get_features()
        self.assertEqual(features.memory_bounds, (1, 999))
        self.assertEqual(features.valid_name_length, 12)

    def test_reads_frequencies_names_modes_and_tone(self):
        serial = FakeFTX1Serial()
        radio = self.radio_class(serial)
        first = radio.get_memory(1)
        self.assertEqual(first.freq, 146_940_000)
        self.assertEqual(first.name, "146.94 RPT")
        self.assertEqual(first.mode, "FM")
        self.assertEqual(first.duplex, "-")
        self.assertEqual(first.offset, 600_000)
        self.assertEqual(first.tmode, "TSQL")
        self.assertEqual(first.rtone, 141.3)
        self.assertEqual(first.ctone, 141.3)
        self.assertIn("MC0;", serial.commands)
        self.assertIn("MC000001;", serial.commands)
        self.assertNotIn("MC;", serial.commands)

        second = radio.get_memory(37)
        self.assertEqual(second.freq, 446_006_250)
        self.assertEqual(second.name, "PMR 01")
        self.assertEqual(second.mode, "NFM")
        self.assertFalse(second.empty)
        self.assertTrue(radio.get_memory(2).empty)

    def test_writes_memory_and_tag(self):
        serial = FakeFTX1Serial()
        radio = self.radio_class(serial)
        memory = radio.get_memory(37)
        memory.freq = 446_031_250
        memory.name = "PMR 06"
        memory.tmode = "Tone"
        memory.rtone = 123.0
        radio.set_memory(memory)

        stored = serial.memories[37]
        self.assertEqual(stored["freq"], 446_031_250)
        self.assertEqual(stored["name"], "PMR 06")
        self.assertEqual(stored["sql"], "1")
        self.assertEqual(stored["tone_index"], 18)

    def test_accepts_silent_ai0_after_valid_identification(self):
        radio = self.radio_class(FakeFTX1Serial(ack_ai=False))
        memory = radio.get_memory(37)
        self.assertEqual(memory.freq, 446_006_250)
        self.assertEqual(memory.name, "PMR 01")


if __name__ == "__main__":
    unittest.main()
