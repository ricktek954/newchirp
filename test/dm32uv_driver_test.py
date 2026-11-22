"""Offline checks for NewChirp's DM-32UV handshake retries."""

from collections import deque
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
        "newchirp_chirp_bridge_dm32uv",
        ROOT / "scripts/chirp_bridge.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load chirp_bridge.py")
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


class _SequenceSerial:
    def __init__(self, responses):
        self.timeout = 0.5
        self.responses = deque(responses)
        self.writes = []

    def reset_input_buffer(self):
        pass

    def write(self, data):
        self.writes.append(bytes(data))

    def read(self, size):
        if not self.responses:
            return b""
        response = self.responses.popleft()
        return response[:size]


class _RetryQueryLink:
    def __init__(self):
        self.attempt = 0
        self.commands = []

    def send(self, data):
        self.commands.append(data)
        self.attempt += 1

    def recv(self, size, timeout=0.5):
        if self.attempt == 1:
            return b"V"[:size]
        if size == 3:
            return b"V\x07\x05"[:size]
        return b"ABCED"[:size]


class DM32UVDriverTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        bridge = _load_bridge()
        cls.bridge = bridge
        cls.directory = bridge.load_chirp(
            str(SOURCE),
            str(PYTHON_VENDOR),
            str(ROOT / "drivers"),
        )
        cls.radio_class = cls.directory.get_radio("Baofeng_DM-32UV")
        cls.driver = importlib.import_module(cls.radio_class.__module__)

    def test_newchirp_driver_replaces_bundled_dm32uv(self):
        self.assertEqual(self.radio_class.__name__, "DM32UV")
        self.assertEqual(
            self.radio_class.__module__,
            "newchirp.drivers.newchirp_dm32uv",
        )

    def test_upload_relabels_after_scan_and_reports_each_page(self):
        # 2026-11-21 report: the dialog sat on "Scanning flash pages" at ~18%
        # for most of a ~50 s write, and two working writes were cancelled.
        stock = sys.modules[self.radio_class.__mro__[1].__module__]
        driver = self.driver
        messages = []
        radio = self.radio_class(None)
        radio.status_fn = lambda status: messages.append(status.msg)

        def fake_upload(radio_):
            status = mock.Mock(msg="Scanning flash pages", cur=0, max=10)
            stock._scan(None, 0, 0x2FFF, radio_, status)
            status.msg = "Cloning to radio"
            stock._write_page(None, 0x1000, b"", 0, 0x2FFF)
            stock._write_page(None, 0x2000, b"", 0, 0x2FFF)

        with mock.patch.object(driver, "_original_scan",
                               return_value=({}, [])), \
                mock.patch.object(driver, "_original_write_page"), \
                mock.patch.object(stock, "do_upload", fake_upload):
            radio.sync_out()

        self.assertEqual(messages[0], driver.WRITE_LABEL)
        self.assertEqual(
            messages[1:],
            [
                driver.WRITE_LABEL + " (memory page 1)",
                driver.WRITE_LABEL + " (memory page 2)",
            ],
        )
        self.assertEqual(driver._upload_progress, {})

    def test_download_scan_is_not_relabelled(self):
        stock = sys.modules[self.radio_class.__mro__[1].__module__]
        messages = []
        radio = self.radio_class(None)
        radio.status_fn = lambda status: messages.append(status.msg)
        status = mock.Mock(msg="Scanning flash pages")
        with mock.patch.object(self.driver, "_original_scan",
                               return_value=({}, [])):
            stock._scan(None, 0, 0x2FFF, radio, status)
        self.assertEqual(messages, [])

    def test_airband_is_accepted_only_as_receive_only(self):
        radio = self.radio_class(None)
        features = radio.get_features()
        self.assertIn((108_000_000, 136_000_000), features.valid_bands)

        from chirp import chirp_common

        memory = chirp_common.Memory()
        memory.number = 1
        memory.freq = 122_975_000
        memory.mode = "FM"
        memory.duplex = "off"
        memory.offset = 0
        receive_errors = [
            message
            for message in radio.validate_memory(memory)
            if isinstance(message, chirp_common.ValidationError)
        ]
        self.assertEqual(receive_errors, [])

        memory.duplex = ""
        transmit_errors = [
            message
            for message in radio.validate_memory(memory)
            if isinstance(message, chirp_common.ValidationError)
        ]
        self.assertTrue(
            any("receive-only" in str(message) for message in transmit_errors)
        )

    def test_passsta_retries_a_transient_bad_reply(self):
        serial = _SequenceSerial([b"\x06\x00\x00", b"P\x00\x00"])
        link = self.driver.baofeng_dm32uv._Link(serial)

        reply = link.xfer(b"PASSSTA", 3)

        self.assertEqual(reply, b"P\x00\x00")
        self.assertEqual(serial.writes, [b"PASSSTA", b"PASSSTA"])

    def test_link_accumulates_fragmented_replies_without_changing_timeout(self):
        serial = _SequenceSerial([b"\x06", b"\x00", b"\x00"])
        link = self.driver.baofeng_dm32uv._Link(serial)

        reply = link.recv(3)

        self.assertEqual(reply, b"\x06\x00\x00")
        self.assertEqual(serial.timeout, 0.05)

    def test_passsta_failure_reports_the_reply_bytes(self):
        serial = _SequenceSerial([b"\x06\x00\x00"] * 3)
        link = self.driver.baofeng_dm32uv._Link(serial)

        with self.assertRaisesRegex(Exception, r"reply 060000"):
            link.xfer(b"PASSSTA", 3)

        self.assertEqual(len(serial.writes), 3)

    def test_sysinfo_retries_a_bad_one_byte_reply(self):
        serial = _SequenceSerial([b"\x15", b"\x06"])
        link = self.driver.baofeng_dm32uv._Link(serial)

        reply = link.xfer(b"SYSINFO", 1)

        self.assertEqual(reply, b"\x06")
        self.assertEqual(serial.writes, [b"SYSINFO", b"SYSINFO"])

    def test_sysinfo_failure_reports_the_reply_byte(self):
        serial = _SequenceSerial([b"\x15"] * 3)
        link = self.driver.baofeng_dm32uv._Link(serial)

        with self.assertRaisesRegex(Exception, r"reply 15"):
            link.xfer(b"SYSINFO", 1)

        self.assertEqual(len(serial.writes), 3)

    def test_trace_shows_handshake_response_bytes(self):
        trace = self.bridge.RadioCommunicationTrace()

        trace.begin(b"PASSSTA")
        trace.received(b"\x06\x00\x00")
        report = trace.format()

        self.assertIn("reply=06 00 00 (3 bytes)", report)

    def test_info_query_retries_fragmented_reply(self):
        link = _RetryQueryLink()

        response = self.driver.baofeng_dm32uv._Link.query_v(
            link,
            b"V\x00\x00\x00\x07",
        )

        self.assertEqual(response, b"ABCED")
        self.assertEqual(link.commands, [b"V\x00\x00\x00\x07"] * 2)


    def test_inserting_a_channel_shifts_analog_onto_dmr_slots(self):
        # 2026-11-21 report (mailbox INBOX:863): inserting a channel moves
        # each later channel one slot down, so an analog channel lands on a
        # slot that held a DMR one and its TX admit value is not in that
        # slot's list. The write must still keep every channel exactly.
        image = SOURCE / "tests/images/Baofeng_DM-32UV.img"
        source = self.radio_class(None)
        source.load_mmap(str(image))
        channels = [
            self.bridge.memory_json(source.get_memory(number))
            for number in range(1, source._count() + 1)
            if not source.get_memory(number).empty
        ]
        modes = [channel["mode"] for channel in channels]
        self.assertIn("DMR", modes)
        self.assertNotEqual(set(modes), {"DMR"})

        inserted = dict(channels[0], name="NEWCH", location=3)
        for channel in channels:
            if channel["location"] >= 3:
                channel["location"] += 1
        channels.append(inserted)
        channels.sort(key=lambda channel: channel["location"])

        radio = self.radio_class(None)
        radio.load_mmap(str(image))
        skipped, _adjusted, written = self.bridge.prepare_upload_channels(
            radio,
            channels,
        )

        self.assertEqual(skipped, [])
        self.assertEqual(written, len(channels))
        for channel in channels:
            self.assertEqual(
                self.bridge.memory_json(radio.get_memory(channel["location"])),
                self.bridge.memory_json(radio.get_memory(channel["location"]))
                | {key: channel[key] for key in channel},
                channel["location"],
            )

    def test_names_end_at_the_first_nul_like_the_radio(self):
        # Forum file drop 12 (2026-11-20): channel names stored as
        # "Channel 1\x00t Mode" showed the leftover "t Mode" text.
        radio = self.radio_class(None)
        radio.load_mmap(str(SOURCE / "tests/images/Baofeng_DM-32UV.img"))
        number = next(
            n for n in range(1, radio._count() + 1)
            if not radio.get_memory(n).empty
        )
        radio._chan(number).name.set_raw(b"Channel 1\x00t Mode")
        radio._forget()

        mem = radio.get_memory(number)
        self.assertEqual(mem.name, "Channel 1")
        self.assertEqual(radio._channel_names()[number], "Channel 1")

        radio.set_memory(mem)
        self.assertEqual(
            radio._chan(number).name.get_raw(),
            b"Channel 1" + b"\x00" * 7,
        )

    def test_zone_names_end_at_the_first_nul(self):
        radio = self.radio_class(None)
        radio.load_mmap(str(SOURCE / "tests/images/Baofeng_DM-32UV.img"))
        self.assertGreaterEqual(radio._zone_count(), 1)
        radio._zone(1).name.set_raw(b"Zone A\x00old name!")
        zone = radio.get_bank_model().get_mappings()[0]
        self.assertEqual(zone.get_name(), "Zone A")

if __name__ == "__main__":
    unittest.main()
