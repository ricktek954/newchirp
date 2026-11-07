"""Offline tests for the NewChirp IC-E90 clone transport."""

import importlib.util
from pathlib import Path
import struct
import sys
import unittest

from chirp_test_source import chirp_source


ROOT = Path(__file__).resolve().parent.parent
PYTHON_VENDOR = ROOT / "assets/python/pyserial-3.5-py2.py3-none-any.whl"
MODEL_ID = b"\x25\x07\x00\x01"
IMAGE_SIZE = 0x2D40


def _load_bridge():
    spec = importlib.util.spec_from_file_location(
        "newchirp_chirp_bridge_icx90",
        ROOT / "scripts/chirp_bridge.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load chirp_bridge.py")
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


def _frame(source, destination, command, payload=b""):
    return (
        b"\xfe\xfe"
        + bytes((source, destination, command))
        + payload
        + b"\xfd"
    )


def _data_payload(address, data):
    prefix = struct.pack(">HB", address, len(data))
    checksum = (-sum(prefix + data)) & 0xFF
    raw = prefix + data + bytes((checksum,))
    return raw.hex().upper().encode("ascii")


class FakeIcomSerial:
    def __init__(
        self,
        image,
        *,
        send_end_frame=False,
        complete=True,
        echo=False,
        ident_failures=0,
        send_clone_ok=True,
        corrupt_checksum=False,
    ):
        self.image = bytearray(image)
        self.send_end_frame = send_end_frame
        self.complete = complete
        self.echo = echo
        self.ident_failures = ident_failures
        self.send_clone_ok = send_clone_ok
        self.corrupt_checksum = corrupt_checksum
        self.timeout = 1
        self.baudrate = 9600
        self._rx = bytearray()
        self.writes = []
        self.ident_queries = 0
        self.clone_in = False
        self.wrong_direction_writes = 0

    def _queue(self, source, destination, command, payload=b""):
        self._rx.extend(_frame(source, destination, command, payload))

    def write(self, data):
        data = bytes(data)
        self.writes.append(data)
        if self.echo:
            self._rx.extend(data)
        if len(data) < 5 or data[:2] != b"\xfe\xfe":
            return len(data)
        command = data[4]
        if command == 0xE0:
            self.ident_queries += 1
            if self.ident_queries <= self.ident_failures:
                return len(data)
            payload = MODEL_ID + bytes(29)
            self._queue(0xEF, 0xEE, 0xE1, payload)
        elif command == 0xE2:
            stop = len(self.image) if self.complete else len(self.image) // 2
            for address in range(0, stop, 32):
                chunk = self.image[address:min(address + 32, stop)]
                payload = bytearray(_data_payload(address, chunk))
                if self.corrupt_checksum and address == 0:
                    payload[-1] = (
                        ord("0") if payload[-1] != ord("0") else ord("1")
                    )
                self._queue(0xEF, 0xEE, 0xE4, bytes(payload))
            if self.send_end_frame:
                self._queue(0xEF, 0xEE, 0xE5, b"Icom Inc.")
        elif command == 0xE3:
            self.clone_in = True
        elif command == 0xE4:
            if not self.clone_in:
                self.wrong_direction_writes += 1
            payload = bytes.fromhex(data[5:-1].decode("ascii"))
            address, length = struct.unpack(">HB", payload[:3])
            body = payload[3:3 + length]
            checksum = payload[-1]
            if checksum != (-sum(payload[:-1])) & 0xFF:
                raise AssertionError("fake radio received a bad checksum")
            self.image[address:address + length] = body
        elif command == 0xE5 and self.send_clone_ok:
            self._queue(0xEF, 0xEE, 0xE6, b"\x00")
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


class Icx90CompletionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bridge = _load_bridge()
        cls.directory = cls.bridge.load_chirp(
            str(chirp_source()),
            str(PYTHON_VENDOR),
            str(ROOT / "drivers"),
        )
        cls.radio_class = cls.directory.get_radio("Icom_IC-E90")

    def _radio(self, serial):
        radio = self.radio_class(serial)
        radio.status_fn = None
        return radio

    def _radio_for_upload(self, serial, image):
        from chirp import memmap

        radio = self._radio(serial)
        radio._mmap = memmap.MemoryMapBytes(bytes(image))
        radio._memsize = len(radio._mmap)
        return radio

    def setUp(self):
        self.driver_module = sys.modules[self.radio_class.__module__]
        self._patch("IDENT_TIMEOUT", 0.01)
        self._patch("IDENT_RETRY_DELAY", 0)
        self._patch("READ_TIMEOUT", 0.05)
        self._patch("READ_POLL", 0.01)
        self._patch("WRITE_TURNAROUND", 0)
        self._patch("ECHO_TIMEOUT", 0.05)
        self._patch("WRITE_RESULT_TIMEOUT", 0.05)

    def _patch(self, name, value):
        original = getattr(self.driver_module, name)
        setattr(self.driver_module, name, value)
        self.addCleanup(setattr, self.driver_module, name, original)

    def test_full_coverage_succeeds_without_end_frame(self):
        serial = FakeIcomSerial(bytes(IMAGE_SIZE))
        radio = self._radio(serial)

        radio.sync_in()

        self.assertEqual(len(radio.get_mmap()), IMAGE_SIZE)
        commands = [frame[4] for frame in serial.writes if len(frame) > 4]
        self.assertEqual(commands[:2], [0xE0, 0xE2])

    def test_normal_end_frame_still_succeeds(self):
        serial = FakeIcomSerial(bytes(IMAGE_SIZE), send_end_frame=True)
        radio = self._radio(serial)

        radio.sync_in()

        self.assertEqual(len(radio.get_mmap()), IMAGE_SIZE)

    def test_identity_query_is_retried(self):
        serial = FakeIcomSerial(bytes(IMAGE_SIZE), ident_failures=2)
        radio = self._radio(serial)

        radio.sync_in()

        self.assertEqual(serial.ident_queries, 3)
        self.assertEqual(len(radio.get_mmap()), IMAGE_SIZE)

    def test_clone_in_is_sent_before_image_blocks(self):
        serial = FakeIcomSerial(bytes(IMAGE_SIZE))
        radio = self._radio_for_upload(serial, bytes(IMAGE_SIZE))

        radio.sync_out()

        commands = [frame[4] for frame in serial.writes if len(frame) > 4]
        self.assertEqual(commands[:2], [0xE0, 0xE3])
        self.assertEqual(commands[-2:], [0xE4, 0xE5])
        self.assertEqual(commands.count(0xE4), IMAGE_SIZE // 32)
        self.assertEqual(serial.wrong_direction_writes, 0)
        self.assertEqual(bytes(serial.image), bytes(IMAGE_SIZE))

    def test_write_round_trips_exact_image_with_echoing_cable(self):
        source = bytes((index * 17) & 0xFF for index in range(IMAGE_SIZE))
        serial = FakeIcomSerial(source, echo=True)
        radio = self._radio_for_upload(serial, source)

        radio.sync_out()

        self.assertEqual(bytes(serial.image), source)
        self.assertEqual(serial.wrong_direction_writes, 0)

    def test_upload_prompt_requires_a_fresh_clone_in_session(self):
        prompts = self.radio_class.get_prompts()
        self.assertIn("power-cycle", prompts.pre_upload)
        self.assertIn("change to CL IN", prompts.pre_upload)
        self.assertIn("power-cycle", prompts.pre_upload)

    def test_icom_clone_frames_are_not_labeled_as_tyt(self):
        trace = self.bridge.RadioCommunicationTrace()
        trace.set_radio_class(self.radio_class)
        frame = _frame(
            0xEE,
            0xEF,
            0xE4,
            _data_payload(0x29A0, bytes(32)),
        )
        self.assertEqual(trace._command_summary(frame),
                         "Icom clone data addr=0x29a0 len=32 (78 bytes)")

    def test_incomplete_image_still_fails(self):
        from chirp import errors

        serial = FakeIcomSerial(bytes(IMAGE_SIZE), complete=False)
        radio = self._radio(serial)

        with self.assertRaises(errors.RadioError):
            radio.sync_in()

    def test_bad_checksum_still_fails(self):
        from chirp import errors

        serial = FakeIcomSerial(
            bytes(IMAGE_SIZE),
            corrupt_checksum=True,
        )
        radio = self._radio(serial)

        with self.assertRaises(errors.InvalidDataError):
            radio.sync_in()

    def test_missing_clone_completion_fails(self):
        from chirp import errors

        serial = FakeIcomSerial(
            bytes(IMAGE_SIZE),
            send_clone_ok=False,
        )
        radio = self._radio_for_upload(serial, bytes(IMAGE_SIZE))

        with self.assertRaises(errors.RadioNoResponse):
            radio.sync_out()

    def test_incomplete_image_with_end_frame_still_fails(self):
        from chirp import errors

        serial = FakeIcomSerial(
            bytes(IMAGE_SIZE),
            send_end_frame=True,
            complete=False,
        )
        radio = self._radio(serial)

        with self.assertRaises(errors.RadioError):
            radio.sync_in()

    def test_invisible_memory_is_empty_even_with_stale_channel_data(self):
        from chirp import memmap

        radio = self.radio_class(memmap.MemoryMapBytes(bytes(IMAGE_SIZE)))
        radio.process_mmap()
        radio.get_features()
        radio.memobj.memory[83].freq = 86_008
        radio.memobj.memory[83].tone_mode = 4
        radio.memobj.banks[83].invisible_channel = 1

        self.assertTrue(radio.get_memory(83).empty)

        radio.memobj.memory[1].freq = 29_000
        radio.memobj.banks[1].invisible_channel = 0
        self.assertFalse(radio.get_memory(1).empty)


if __name__ == "__main__":
    unittest.main()
