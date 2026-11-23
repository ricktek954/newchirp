"""Offline checks for the FT-70D clone alignment and ID-5100 tone overrides."""

import importlib
import importlib.util
from pathlib import Path
import sys
import unittest


from chirp_test_source import chirp_source


ROOT = Path(__file__).resolve().parent.parent
SOURCE = chirp_source()
PYTHON_VENDOR = ROOT / "assets/python/pyserial-3.5-py2.py3-none-any.whl"
IMAGES = SOURCE / "tests/images"


def _load_bridge():
    spec = importlib.util.spec_from_file_location(
        "newchirp_chirp_bridge_ft70_id5100",
        ROOT / "scripts/chirp_bridge.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load chirp_bridge.py")
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


class _ClonePipe:
    """Serve a radio byte stream; the body is released only after the ACK."""

    def __init__(self, ident_stream, body, stale=b""):
        self.pending = bytearray(stale)
        self.ident = bytes(ident_stream)
        self.body = bytes(body)
        self.sent_ident = False
        self.writes = []
        self.resets = 0

    def reset_input_buffer(self):
        self.resets += 1
        self.pending.clear()

    def read(self, size):
        if not self.pending and not self.sent_ident:
            self.pending.extend(self.ident)
            self.sent_ident = True
        out = bytes(self.pending[:size])
        del self.pending[:size]
        return out

    def write(self, data):
        self.writes.append(bytes(data))
        if data == b"\x06" and self.body:
            self.pending.extend(self.body)
            self.body = b""


class FT70AlignmentTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        bridge = _load_bridge()
        cls.directory = bridge.load_chirp(
            str(SOURCE), str(PYTHON_VENDOR), str(ROOT / "drivers")
        )
        cls.module = importlib.import_module(
            "newchirp.drivers.newchirp_ft70_compat"
        )
        cls.image = (IMAGES / "Yaesu_FT-70D.img").read_bytes()[:65227]
        cls.radio_class = cls.directory.get_radio("Yaesu_FT-70D")

    def _radio(self, pipe):
        radio = self.radio_class(None)
        radio.pipe = pipe
        radio.status_fn = lambda _status: None
        return radio

    def test_override_is_installed(self):
        self.assertTrue(
            getattr(self.radio_class.sync_in, "newchirp_ft70_aligned", False)
        )

    def test_stray_bytes_before_id_are_discarded(self):
        pipe = _ClonePipe(b"\x00\xff" + self.image[:10], self.image[10:])
        radio = self._radio(pipe)

        radio.sync_in()

        self.assertEqual(radio.get_mmap().get_packed(), self.image)
        self.assertEqual(pipe.writes, [b"\x06"])

    def test_stale_input_is_cleared_before_reading(self):
        pipe = _ClonePipe(
            self.image[:10], self.image[10:], stale=b"leftover"
        )
        radio = self._radio(pipe)

        radio.sync_in()

        self.assertEqual(pipe.resets, 1)
        self.assertEqual(radio.get_mmap().get_packed(), self.image)

    def test_checksum_failure_explains_recovery(self):
        body = bytearray(self.image[10:])
        body[100] ^= 0x01
        radio = self._radio(_ClonePipe(self.image[:10], bytes(body)))

        with self.assertRaisesRegex(Exception, "ADMS mode from cold") as ctx:
            radio.sync_in()

        self.assertIn("Checksum Failed", str(ctx.exception))
        self.assertIn("Nothing was written", str(ctx.exception))

    def test_non_ft70_stream_is_rejected(self):
        radio = self._radio(_ClonePipe(b"\x55" * 200, b""))

        with self.assertRaisesRegex(Exception, "identification block"):
            radio.sync_in()


class ID5100ToneTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        bridge = _load_bridge()
        cls.directory = bridge.load_chirp(
            str(SOURCE), str(PYTHON_VENDOR), str(ROOT / "drivers")
        )
        importlib.import_module(
            "newchirp.drivers.newchirp_icom_id5100_tone_compat"
        )

    def _radio(self, model="Icom_ID-5100", image="Icom_ID-5100.img"):
        radio_class = self.directory.get_radio(model)
        return radio_class(str(IMAGES / image))

    def _first_used(self, radio):
        for number in range(0, 1000):
            if not radio.get_memory(number).empty:
                return number
        self.fail("test image has no channels")

    def test_dtcs_transmit_only_reads_as_cross_dtcs(self):
        radio = self._radio()
        number = self._first_used(radio)
        radio._memobj.memory[number].tmode = 8

        mem = radio.get_memory(number)

        self.assertEqual(mem.tmode, "Cross")
        self.assertEqual(mem.cross_mode, "DTCS->")
        radio.set_memory(mem)
        self.assertEqual(int(radio._memobj.memory[number].tmode), 8)
        self.assertIn("DTCS->", radio.get_features().valid_cross_modes)

    def test_pocket_beep_modes_read_and_round_trip(self):
        radio = self._radio()
        number = self._first_used(radio)
        for raw, shown in ((2, "TSQL"), (4, "DTCS")):
            radio._memobj.memory[number].tmode = raw
            mem = radio.get_memory(number)
            self.assertEqual(mem.tmode, shown)
            radio.set_memory(mem)
            self.assertEqual(int(radio._memobj.memory[number].tmode), raw)

    def test_changed_mode_does_not_keep_pocket_beep(self):
        radio = self._radio()
        number = self._first_used(radio)
        radio._memobj.memory[number].tmode = 2
        mem = radio.get_memory(number)
        mem.tmode = "DTCS"

        radio.set_memory(mem)

        self.assertEqual(int(radio._memobj.memory[number].tmode), 5)

    def test_every_stored_value_decodes_on_both_models(self):
        for model, image in (
            ("Icom_ID-5100", "Icom_ID-5100.img"),
            ("Icom_ID-4100", "Icom_ID-4100.img"),
        ):
            radio = self._radio(model, image)
            number = self._first_used(radio)
            for raw in range(16):
                radio._memobj.memory[number].tmode = raw
                radio.get_memory(number)
            features = radio.get_features()
            self.assertIn("TSQL-R", features.valid_tmodes)
            self.assertIn("DTCS-R", features.valid_tmodes)

    def test_reading_does_not_change_image_bytes(self):
        radio = self._radio()
        number = self._first_used(radio)
        radio._memobj.memory[number].tmode = 14
        before = radio.get_mmap().get_packed()

        mem = radio.get_memory(number)

        self.assertEqual(mem.tmode, "")
        self.assertEqual(radio.get_mmap().get_packed(), before)


if __name__ == "__main__":
    unittest.main()
