"""Offline checks for the UV-5RM Plus OEM handshake retry."""

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
        "newchirp_chirp_bridge_uv5rm_plus",
        ROOT / "scripts/chirp_bridge.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load chirp_bridge.py")
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


class _SequenceSerial:
    def __init__(self, replies):
        self.replies = deque(replies)
        self.timeout = 1.5
        self.writes = []

    def read(self, size):
        if size == 256:
            return b""
        if not self.replies:
            return b""
        return self.replies.popleft()[:size]

    def write(self, data):
        self.writes.append(bytes(data))


class UV5RMPlusHandshakeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        bridge = _load_bridge()
        cls.bridge = bridge
        cls.directory = bridge.load_chirp(
            str(SOURCE),
            str(PYTHON_VENDOR),
            str(ROOT / "drivers"),
        )
        cls.radio_module = importlib.import_module(
            "chirp.drivers.baofeng_uv17Pro"
        )
        cls.compat = importlib.import_module(
            "newchirp.drivers.newchirp_uv5rm_plus"
        )

    def test_retries_stray_byte_like_official_cps(self):
        serial = _SequenceSerial([
            b"\x05",
            b"",
            b"\x06",
            b"F" * 16,
            b"M" * 15,
            b"\x06",
        ])
        radio = self.radio_module.BaofengUV5RMPlus(serial)

        with mock.patch.object(self.compat.time, "sleep") as sleep:
            self.assertTrue(self.radio_module._do_ident(radio))

        sleep.assert_called_once_with(self.compat.RETRY_DELAY)
        self.assertEqual(serial.writes[:2], [
            b"PROGRAMBFNORMALU",
            b"PROGRAMBFNORMALU",
        ])

    def test_retries_stray_byte_for_uv5rh(self):
        serial = _SequenceSerial([
            b"\xE0",
            b"",
            b"\x06",
            b"F" * 16,
            b"M" * 15,
            b"\x06",
        ])
        radio = self.radio_module.UV5RH(serial)

        with mock.patch.object(self.compat.time, "sleep") as sleep:
            self.assertTrue(self.radio_module._do_ident(radio))

        sleep.assert_called_once_with(self.compat.RETRY_DELAY)
        self.assertEqual(serial.writes[:2], [
            b"PROGRAMBFNORMALU",
            b"PROGRAMBFNORMALU",
        ])

    def test_retries_stray_byte_for_uv32_like_its_cps(self):
        # 2026-11-22 UV-32 report: PROGRAMCOLORPROU answered 0x40. The
        # "BF-UVs Pro" CPS v1.4.7 discards a non-ACK byte and resends.
        radio = self.radio_module.UV32(None)
        magic = radio._idents[0]
        replies = [b"\x40", b"", b"\x06"] + [
            reply for _magic, length in radio._magics
            for reply in (b"\x00" * length,)
        ]
        serial = _SequenceSerial(replies)
        radio = self.radio_module.UV32(serial)

        with mock.patch.object(self.compat.time, "sleep") as sleep:
            self.assertTrue(self.radio_module._do_ident(radio))

        sleep.assert_called_once_with(self.compat.RETRY_DELAY)
        self.assertEqual(serial.writes[:2], [magic, magic])

    def test_stray_byte_then_ack_is_accepted_without_resend(self):
        # The CPS keeps reading after a non-ACK byte and accepts a later ACK.
        radio = self.radio_module.UV5RMini(None)
        replies = [b"\x40", b"\x06"] + [
            b"\x00" * length for _magic, length in radio._magics
        ]
        serial = _SequenceSerial(replies)
        radio = self.radio_module.UV5RMini(serial)

        with mock.patch.object(self.compat.time, "sleep") as sleep:
            self.assertTrue(self.radio_module._do_ident(radio))

        sleep.assert_not_called()
        self.assertEqual(serial.writes[0], b"PROGRAMCOLORPROU")
        self.assertEqual(len(serial.writes), 1 + len(radio._magics))

    def test_mini_echo_followed_by_ack_reads(self):
        """2026-11-24 INBOX:948/950: PROGRAMCOLORPROU answered "P"."""
        radio = self.radio_module.UV5RMini(None)
        magic = radio._idents[0]
        replies = [bytes((b,)) for b in magic] + [b"\x06"] + [
            b"\x00" * length for _magic, length in radio._magics
        ]
        serial = _SequenceSerial(replies)
        radio = self.radio_module.UV5RMini(serial)

        with mock.patch.object(self.compat.time, "sleep"):
            self.assertTrue(self.radio_module._do_ident(radio))

        self.assertEqual(serial.writes[0], magic)

    def test_mini_echo_only_explains_the_plug(self):
        from chirp import errors

        radio = self.radio_module.UV5RMini(None)
        magic = radio._idents[0]
        replies = []
        for _attempt in range(self.compat.HANDSHAKE_RETRIES):
            replies += [bytes((b,)) for b in magic] + [b""]
        serial = _SequenceSerial(replies)
        radio = self.radio_module.UV5RMini(serial)

        with mock.patch.object(self.compat.time, "sleep") as sleep:
            with self.assertRaisesRegex(errors.RadioError,
                                        "hearing its own") as caught:
                self.radio_module._do_ident(radio)

        self.assertIn("was not changed", str(caught.exception))
        self.assertEqual(sleep.call_count, self.compat.HANDSHAKE_RETRIES - 1)
        self.assertEqual(serial.writes,
                         [magic] * self.compat.HANDSHAKE_RETRIES)

    def test_uv32_0x41_reply_is_not_called_v2_firmware(self):
        from chirp import errors

        serial = _SequenceSerial([b"\x41"] * 12)
        radio = self.radio_module.UV32(serial)
        with mock.patch.object(self.compat.time, "sleep"):
            with self.assertRaises(errors.RadioError) as caught:
                self.radio_module._do_ident(radio)
        self.assertNotIn("v2", str(caught.exception))

    def test_does_not_retry_other_handshake_failures(self):
        serial = _SequenceSerial([])
        radio = self.radio_module.BaofengUV5RMPlus(serial)

        with self.assertRaisesRegex(Exception, "No response"):
            self.radio_module._do_ident(radio)

        self.assertEqual(serial.writes, [b"PROGRAMBFNORMALU"])

    def test_v2_firmware_reply_names_the_v2_model(self):
        """2026-11-19 Linux report: replies 41, 03, 41, 03 then silence."""
        from chirp import errors
        serial = _SequenceSerial([b"\x41", b"\x03", b"\x41", b"\x03"])
        radio = self.radio_module.BaofengUV5RMPlus(serial)

        with mock.patch.object(self.compat.time, "sleep"):
            with self.assertRaisesRegex(errors.RadioError,
                                        "UV-5RM Plus v2"):
                self.radio_module._do_ident(radio)
        # The recording hook is removed again.
        self.assertNotEqual(self.radio_module._sendmagic.__name__,
                            "recording_sendmagic")

    def test_v2_hint_for_uv5rh(self):
        from chirp import errors
        serial = _SequenceSerial([b"\x41"])
        radio = self.radio_module.UV5RH(serial)
        with mock.patch.object(self.compat.time, "sleep"):
            with self.assertRaisesRegex(errors.RadioError, "UV-5RH Pro"):
                self.radio_module._do_ident(radio)

    def test_unprogrammed_pttid_is_exposed_as_off(self):
        radio = self.bridge.radio_from_image(
            self.directory,
            "Baofeng_UV-5RM_Plus",
            str(SOURCE / "tests/images/Baofeng_UV-5RM_Plus.img"),
        )
        radio._memobj.memory[0].pttid = 0xFF

        memory = radio.get_memory(1)
        pttid = next(
            setting
            for setting in memory.extra
            if setting.get_name() == "pttid"
        )

        self.assertEqual(str(pttid.value), "Off")
        self.assertEqual(int(radio._memobj.memory[0].pttid), 0)


if __name__ == "__main__":
    unittest.main()
