"""Offline regressions for reported regional and generation identities."""

import importlib.util
import importlib
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
        "newchirp_chirp_bridge_followup",
        ROOT / "scripts/chirp_bridge.py",
    )
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


class FakeTDH8G4Serial:
    def __init__(self, identity, bad_ack_at=None):
        self.identity = identity
        self.bad_ack_at = bad_ack_at
        self.writes = []
        self.frames = []
        self._replies = bytearray()

    def write(self, data):
        self.writes.append(data)
        if data == b"PVOJH\\\x14":
            self._replies.extend(b"\x06")
        elif data == b"\x02":
            self._replies.extend(self.identity)
        elif data == b"\x06":
            self._replies.extend(b"\x06")
        elif data[:1] == b"W":
            frame_index = len(self.frames)
            self.frames.append(data)
            if frame_index == self.bad_ack_at:
                self._replies.extend(b"\x15")
            else:
                self._replies.extend(b"\x06")
        else:
            self._replies.extend(b"\x15")

    def read(self, size=1):
        data = bytes(self._replies[:size])
        del self._replies[:size]
        return data


class ExperimentalSerialFollowupTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bridge = _load_bridge()
        cls.directory = cls.bridge.load_chirp(
            str(SOURCE),
            str(VENDOR),
            str(ROOT / "drivers"),
        )

    def test_tm_d710gp_regional_identity_is_accepted(self):
        from chirp import errors
        from chirp.drivers import tmd710
        newchirp_tmd710 = importlib.import_module(
            "newchirp.drivers.newchirp_tmd710"
        )

        radio = object.__new__(tmd710.KenwoodTMD710GRadio)
        with mock.patch.object(
            newchirp_tmd710,
            "_original_connect_radio",
            side_effect=errors.RadioError(
                "Radio responded as D710GP, not D710G."
            ),
        ):
            self.assertIsNone(
                newchirp_tmd710._connect_radio_accepting_regional_identity(
                    radio
                )
            )

    def test_tdh8_fourth_generation_identities_are_detected(self):
        from chirp.drivers import tdh8

        variants = {
            b"TDH84GEN": "TIDRadioTDH8FourthGen",
            b"TDH84GEH": "TIDRadioTDH8FourthGenHAM",
            b"TDH84GEG": "TIDRadioTDH8FourthGenGMRS",
        }
        for identity, class_name in variants.items():
            with self.subTest(identity=identity):
                with mock.patch.object(
                    tdh8,
                    "_do_ident",
                    return_value=identity,
                ):
                    radio_class = tdh8.TDH8.detect_from_serial(object())
                self.assertEqual(radio_class.__name__, class_name)
                self.assertEqual(radio_class.ident_mode, identity)
                self.assertEqual(radio_class.VARIANT, "G4")

    @staticmethod
    def _radio(radio_class, pipe, image):
        from chirp import memmap

        return SimpleNamespace(
            ident_mode=radio_class.ident_mode,
            _memsize=radio_class._memsize,
            pipe=pipe,
            get_mmap=lambda: memmap.MemoryMapBytes(image),
            status_fn=lambda _status: None,
        )

    def test_tdh8_fourth_generation_write_uses_only_official_pages(self):
        newchirp_tdh8 = importlib.import_module(
            "newchirp.drivers.newchirp_tdh8_serial"
        )
        radio_class = newchirp_tdh8.TIDRadioTDH8FourthGenHAM
        image = bytes(range(256)) * (newchirp_tdh8.TDH8_G4_IMAGE_SIZE // 256)
        image += bytes(
            range(newchirp_tdh8.TDH8_G4_IMAGE_SIZE - len(image))
        )
        pipe = FakeTDH8G4Serial(radio_class.ident_mode)

        radio_class.sync_out(self._radio(radio_class, pipe, image))

        self.assertEqual(
            pipe.writes[:3],
            [newchirp_tdh8.TDH8_G4_WRITE_MAGIC, b"\x02", b"\x06"],
        )
        expected_addresses = [
            address
            for start, end in newchirp_tdh8.TDH8_G4_WRITE_RANGES
            for address in range(start, end, newchirp_tdh8.TDH8_G4_BLOCK_SIZE)
        ]
        self.assertEqual(len(expected_addresses), 170)
        self.assertEqual(len(pipe.frames), len(expected_addresses))

        for address, frame in zip(expected_addresses, pipe.frames):
            self.assertEqual(
                frame[:4],
                b"W"
                + address.to_bytes(2, "big")
                + bytes([newchirp_tdh8.TDH8_G4_BLOCK_SIZE]),
            )
            expected = image[
                address + newchirp_tdh8.TDH8_G4_IMAGE_PREFIX:
                address
                + newchirp_tdh8.TDH8_G4_IMAGE_PREFIX
                + newchirp_tdh8.TDH8_G4_BLOCK_SIZE
            ]
            self.assertEqual(frame[4:-1], expected)
            self.assertEqual(frame[-1], sum(expected) & 0xFF)

    def test_tdh8_fourth_generation_write_stops_on_bad_ack(self):
        from chirp import errors

        newchirp_tdh8 = importlib.import_module(
            "newchirp.drivers.newchirp_tdh8_serial"
        )
        radio_class = newchirp_tdh8.TIDRadioTDH8FourthGen
        image = b"\x00" * newchirp_tdh8.TDH8_G4_IMAGE_SIZE
        pipe = FakeTDH8G4Serial(radio_class.ident_mode, bad_ack_at=1)

        with self.assertRaisesRegex(errors.RadioError, "page 0x0020"):
            radio_class.sync_out(self._radio(radio_class, pipe, image))
        self.assertEqual(len(pipe.frames), 2)

    def test_tdh8_fourth_generation_write_rejects_wrong_identity(self):
        from chirp import errors

        newchirp_tdh8 = importlib.import_module(
            "newchirp.drivers.newchirp_tdh8_serial"
        )
        radio_class = newchirp_tdh8.TIDRadioTDH8FourthGenGMRS
        image = b"\x00" * newchirp_tdh8.TDH8_G4_IMAGE_SIZE
        pipe = FakeTDH8G4Serial(b"TDH84GEN")

        with self.assertRaisesRegex(errors.RadioError, "model mismatch"):
            radio_class.sync_out(self._radio(radio_class, pipe, image))
        self.assertEqual(pipe.frames, [])

    def test_tdh8_fourth_generation_write_rejects_incomplete_image(self):
        from chirp import errors

        newchirp_tdh8 = importlib.import_module(
            "newchirp.drivers.newchirp_tdh8_serial"
        )
        radio_class = newchirp_tdh8.TIDRadioTDH8FourthGen
        pipe = FakeTDH8G4Serial(radio_class.ident_mode)

        with self.assertRaisesRegex(errors.RadioError, "image is incomplete"):
            radio_class.sync_out(
                self._radio(
                    radio_class,
                    pipe,
                    b"\x00"
                    * (newchirp_tdh8.TDH8_G4_IMAGE_SIZE - 1),
                )
            )
        self.assertEqual(pipe.writes, [])
