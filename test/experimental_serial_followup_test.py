"""Offline regressions for reported regional and generation identities."""

import importlib.util
import importlib
from pathlib import Path
import sys
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

    def test_tdh8_fourth_generation_ham_is_read_only(self):
        from chirp import errors
        from chirp.drivers import tdh8

        with mock.patch.object(
            tdh8,
            "_do_ident",
            return_value=b"TDH84GEH",
        ):
            radio_class = tdh8.TDH8.detect_from_serial(object())
        self.assertEqual(
            radio_class.__name__,
            "TIDRadioTDH8FourthGenHAM",
        )
        self.assertEqual(radio_class.ident_mode, b"TDH84GEH")
        radio = object.__new__(radio_class)
        with self.assertRaisesRegex(errors.RadioError, "writes are disabled"):
            radio.sync_out()
