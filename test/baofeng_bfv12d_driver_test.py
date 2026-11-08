"""Offline tests for the CPS-derived Baofeng BF-V12D transport."""

import importlib
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest import mock

from chirp_test_source import chirp_source


ROOT = Path(__file__).resolve().parent.parent
SOURCE = chirp_source()
VENDOR = ROOT / "assets/python/pyserial-3.5-py2.py3-none-any.whl"


def _load_bridge():
    spec = importlib.util.spec_from_file_location(
        "newchirp_chirp_bridge_bfv12d",
        ROOT / "scripts/chirp_bridge.py",
    )
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


class FakeSerial:
    def __init__(self, radio_id=b"\x00\x0a\x01\x10", fragment_size=None):
        self.radio_id = radio_id
        self.fragment_size = fragment_size
        self.writes = []
        self.replies = bytearray()
        self.timeout = 1.5

    def write(self, data):
        self.writes.append(bytes(data))
        if data == b"\x02ucbfpwd":
            self.replies.extend(b"\x06")
        elif data == b"\x10\xc5\xea\x35":
            self.replies.extend(b"\x06")
        elif data == b"Q041OTUwMA==\x00\x00\x00\x00":
            self.replies.extend(b"\x06")
            self.replies.extend(self.radio_id)
        elif data == b"\x02\x80\x82OGRAM":
            self.replies.extend(b"\x06")
        elif data == b"\x02":
            self.replies.extend(b"P3107\xf7\x00\x00")
        elif data == b"R\x01\x30\x08":
            self.replies.extend(b"W\x01\x30\x08" + b"\xff" * 8)
        elif data == b"\x06":
            self.replies.extend(b"\x06")

    def read(self, size=1):
        if self.fragment_size is not None:
            size = min(size, self.fragment_size)
        data = bytes(self.replies[:size])
        del self.replies[:size]
        return data


class BaofengBFV12DDriverTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bridge = _load_bridge()
        cls.directory = cls.bridge.load_chirp(
            str(SOURCE),
            str(VENDOR),
            str(ROOT / "drivers"),
        )
        cls.driver = importlib.import_module(
            "newchirp.drivers.newchirp_baofeng_bfv12d"
        )

    def test_cps_unlock_sequence_is_byte_exact(self):
        pipe = FakeSerial()
        radio = object.__new__(self.driver.NewChirpBaofengBFV12D)
        radio.pipe = pipe

        self.assertEqual(radio._get_radio_id(), b"\x00\x0a\x01\x10")
        self.assertEqual(
            pipe.writes,
            [
                b"\x02ucbfpwd",
                b"\x10\xc5\xea\x35",
                b"Q041OTUwMA==\x00\x00\x00\x00",
            ],
        )

    def test_read_program_entry_matches_cps_magic_and_probe(self):
        pipe = FakeSerial()
        radio = object.__new__(self.driver.NewChirpBaofengBFV12D)
        radio.pipe = pipe
        radio._metadata = {}

        self.assertIsNone(radio._enter_programming(False))
        self.assertEqual(
            pipe.writes,
            [
                b"\x02ucbfpwd",
                b"\x10\xc5\xea\x35",
                b"Q041OTUwMA==\x00\x00\x00\x00",
                b"\x02\x80\x82OGRAM",
                b"\x02",
                b"\x06",
                b"R\x01\x30\x08",
                b"\x06",
            ],
        )
        self.assertEqual(radio._metadata["fw_region"], 0)
        self.assertEqual(radio._metadata["fw_version"], 0x0110)

    def test_fragmented_radio_id_is_reassembled(self):
        pipe = FakeSerial(fragment_size=1)
        radio = object.__new__(self.driver.NewChirpBaofengBFV12D)
        radio.pipe = pipe

        self.assertEqual(radio._get_radio_id(), b"\x00\x0a\x01\x10")

    def test_empty_unlock_is_retried_five_times_then_fails_closed(self):
        from chirp import errors

        pipe = FakeSerial()
        radio = object.__new__(self.driver.NewChirpBaofengBFV12D)
        radio.pipe = pipe

        with mock.patch.object(
            self.driver,
            "_read_exact",
            return_value=b"",
        ), mock.patch.object(self.driver.time, "sleep"):
            with self.assertRaisesRegex(
                errors.RadioNoResponse,
                "V1.19 and V2.02",
            ):
                radio._get_radio_id()

        unlock_writes = [
            write for write in pipe.writes if write == b"\x02ucbfpwd"
        ]
        exit_writes = [write for write in pipe.writes if write == b"E"]
        self.assertEqual(len(unlock_writes), self.driver.IDENT_ATTEMPTS)
        self.assertEqual(
            len(exit_writes),
            self.driver.IDENT_ATTEMPTS - 1,
        )

    def test_driver_prompts_explain_cable_and_firmware_limits(self):
        prompts = self.driver.NewChirpBaofengBFV12D.get_prompts()
        self.assertIn("standard Baofeng K-type", prompts.experimental)
        self.assertIn("V1.19", prompts.experimental)
        self.assertIn("V2.02", prompts.experimental)

    def test_driver_replaces_upstream_bfv12d_catalog_entry(self):
        from chirp import directory

        driver_id = directory.get_driver(
            self.driver.NewChirpBaofengBFV12D
        )
        radio_class = directory.get_radio(driver_id)
        self.assertIs(
            radio_class,
            self.driver.NewChirpBaofengBFV12D,
        )
