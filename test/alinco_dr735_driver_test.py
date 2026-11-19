"""Alinco DR-735 driver rebuilt from DR-735 Memory Editor 0.06.

2026-11-19 forum report (MX Linux, DR-735T): the read failed after about
one second. The stock CHIRP driver skipped the OEM ``AL~`` wake, accepted
only two of nine identities, used the bridge's 0.25 s read timeout (OEM
500 ms) and called ``exit(1)`` on a short block.
"""

from pathlib import Path
import importlib.util
import sys
import unittest

from chirp_test_source import chirp_source


ROOT = Path(__file__).resolve().parent.parent
SOURCE = chirp_source()
VENDOR = ROOT / "assets/python/pyserial-3.5-py2.py3-none-any.whl"
STOCK_IMAGE = SOURCE / "tests/images/Alinco_DR735T.img"


def _load_bridge():
    spec = importlib.util.spec_from_file_location(
        "newchirp_chirp_bridge_dr735", ROOT / "scripts/chirp_bridge.py"
    )
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


def _record(freq, used=0x55, name=b"", **fields):
    rec = bytearray(64)
    rec[0] = used
    rec[4:8] = freq.to_bytes(4, "little")
    rec[13] = fields.get("subtone", 0)
    rec[14] = fields.get("enc", 8)
    rec[15] = fields.get("dec", 8)
    rec[20] = fields.get("mode", 0)
    for i, value in enumerate(name):
        rec[24 + i] = value
    rec[56:58] = fields.get("banks", 0).to_bytes(2, "little")
    return bytes(rec)


class FakeDR735:
    """Answers like the radio behind a single-wire (echoing) ERW-7."""

    def __init__(self, model="DR735TN", echo=True, eepdl=True,
                 answer=True):
        self.model = model
        self.echo = echo
        self.eepdl = eepdl
        self.answer = answer
        self.eepel = {}
        self.eepdl_mem = {}
        self.sent = []
        self._pending = b""
        self.timeout = 0.25

    def reset_input_buffer(self):
        self._pending = b""

    def write(self, data):
        assert data.endswith(b"\r\n"), data
        command = data[:-2].decode("ascii")
        self.sent.append(command)
        if self.echo:
            self._pending += data
        reply = self._reply(command)
        if reply is not None and self.answer:
            self._pending += reply.encode("ascii") + b"\r\n"

    def _reply(self, command):
        if command in ("AL~", "AL~DR735J", "AL~RESET"):
            return "OK"
        if command == "AL~WHO":
            return self.model
        for family, store in (("EEPEL", self.eepel),
                              ("EEPDL", self.eepdl_mem)):
            prefix = "AL~" + family
            if command.startswith(prefix):
                if family == "EEPDL" and not self.eepdl:
                    return None
                address = int(command[len(prefix):len(prefix) + 4], 16)
                op = command[len(prefix) + 4]
                if op == "R":
                    return store.get(address, b"\xFF" * 64).hex().upper()
                store[address] = bytes.fromhex(command[len(prefix) + 5:])
                return "OK"
        return "NG"

    def read(self, size):
        chunk, self._pending = self._pending[:size], self._pending[size:]
        return chunk


class AlincoDR735DriverTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bridge = _load_bridge()
        cls.bridge.load_chirp(str(SOURCE), str(VENDOR), str(ROOT / "drivers"))
        from chirp.drivers import alinco_dr735t
        cls.stock = alinco_dr735t
        cls.mod = sys.modules["newchirp.drivers.newchirp_alinco_dr735"]

    def _radio(self, pipe=None):
        radio = self.stock.AlincoDR735T(pipe)
        radio.status_fn = lambda status: None
        return radio

    def _download(self, fake):
        radio = self._radio(fake)
        radio.sync_in()
        return radio

    def test_override_installed_on_stock_driver_id(self):
        from chirp import directory
        cls = directory.get_radio("Alinco_DR735T")
        self.assertIs(cls, self.stock.AlincoDR735T)
        self.assertTrue(cls.newchirp_oem_editor_transport)

    def test_read_wakes_radio_and_accepts_every_oem_identity(self):
        for model in self.mod.MODEL_IDS:
            fake = FakeDR735(model=model, eepdl=False)
            fake.eepel[0] = _record(146520000, name=b"\x3a")
            radio = self._download(fake)
            self.assertEqual(fake.sent[:2], ["AL~", "AL~WHO"], model)
            self.assertEqual(radio.metadata["dr735_model"], model)
            self.assertEqual(radio.get_memory(0).freq, 146520000)

    def test_unknown_identity_is_refused(self):
        from chirp import errors
        fake = FakeDR735(model="DR635T")
        with self.assertRaisesRegex(errors.RadioError, "DR635T"):
            self._download(fake)

    def test_full_read_uses_oem_addresses_for_extended_channels(self):
        fake = FakeDR735()
        fake.eepdl_mem[0xC000 + 5 * 64] = _record(145500000,
                                                   name=b"\x3b\x3a")
        fake.eepdl_mem[0x1400] = _record(144000000)
        fake.eepdl_mem[0x2000 + 3 * 64] = _record(433000000)
        radio = self._download(fake)
        self.assertEqual(len(radio.get_mmap().get_packed()),
                         self.mod.FULL_SIZE)
        eepel = [c for c in fake.sent if c.startswith("AL~EEPEL")]
        self.assertEqual(len(eepel), 1000)
        self.assertEqual(eepel[-1], "AL~EEPELF9C0R")
        eepdl = [c[8:12] for c in fake.sent if c.startswith("AL~EEPDL")]
        self.assertEqual(eepdl[:2], ["C000", "C040"])
        self.assertIn("E000", eepdl)
        self.assertEqual(eepdl[-3:], ["1700", "1740", "1780"])
        self.assertEqual(len(eepdl), len(self.mod.EXTENDED) + 12)

        left = radio.get_memory(1005)
        self.assertEqual((left.freq, left.name), (145500000, "BA"))
        self.assertIn("L05", left.comment)
        self.assertIn("freq", left.immutable)
        self.assertEqual(radio.get_memory(1212).freq, 144000000)
        self.assertEqual(radio.get_memory(1214 + 3).freq, 433000000)

    def test_extended_timeout_keeps_common_channels(self):
        fake = FakeDR735(eepdl=False)
        fake.eepel[7 * 64] = _record(147000000)
        radio = self._download(fake)
        self.assertEqual(len(radio.get_mmap().get_packed()),
                         self.mod.COMMON_SIZE)
        self.assertEqual(radio.get_memory(7).freq, 147000000)
        self.assertTrue(radio.get_memory(1000).empty)

    def test_cable_without_echo_still_reads(self):
        fake = FakeDR735(echo=False, eepdl=False)
        fake.eepel[1 * 64] = _record(146000000)
        radio = self._download(fake)
        self.assertEqual(radio.get_memory(1).freq, 146000000)

    def test_missing_echo_and_missing_reply_explain_the_fault(self):
        from chirp import errors
        silent = FakeDR735(echo=False, answer=False)
        with self.assertRaisesRegex(errors.RadioError, "No echo"):
            self._download(silent)
        mute = FakeDR735(answer=False)
        with self.assertRaisesRegex(errors.RadioError,
                                    "LEFT speaker jack"):
            self._download(mute)

    def test_short_block_raises_radio_error_not_system_exit(self):
        from chirp import errors

        class Short(FakeDR735):
            def _reply(self, command):
                if command.startswith("AL~EEPEL"):
                    return "55"
                return super()._reply(command)

        with self.assertRaisesRegex(errors.RadioError, "128 hex digits"):
            self._download(Short())

    def test_stock_image_decodes_and_round_trips(self):
        from chirp import chirp_common
        radio = self._radio()
        radio.load_mmap(str(STOCK_IMAGE))
        first = radio.get_memory(0)
        self.assertFalse(first.empty)
        self.assertEqual(first.duplex, "-")
        self.assertTrue(radio.get_memory(1000).empty)
        used = [n for n in range(1000)
                if radio._memobj.memory[n].used == 0x55]
        self.assertEqual(len(used), 19)
        for number in used:
            before = radio.get_memory(number)
            radio.set_memory(before)
            after = radio.get_memory(number)
            for field in ("freq", "offset", "duplex", "name", "tmode",
                          "rtone", "ctone", "dtcs", "power", "mode",
                          "skip"):
                self.assertEqual(getattr(before, field),
                                 getattr(after, field),
                                 "%s %s" % (number, field))
        self.assertIsInstance(radio.get_bank_model(),
                              chirp_common.MTOBankModel)

    def test_tone_modes_follow_the_oem_editor(self):
        from chirp import chirp_common
        radio = self._radio()
        radio._mmap = __import__("chirp").memmap.MemoryMapBytes(
            b"\x00" * self.mod.COMMON_SIZE)
        radio.process_mmap()
        mem = chirp_common.Memory()
        mem.number = 3
        mem.freq = 146520000
        mem.tmode = "TSQL"
        mem.rtone = 67.0
        mem.ctone = 100.0
        radio.set_memory(mem)
        rec = radio._memobj.memory[3]
        self.assertEqual((rec.subtone_selection, rec.tx_tone_index,
                          rec.rx_tone_index), (3, 12, 12))
        self.assertEqual(rec.step, 0)

        mem.tmode = "Cross"
        mem.cross_mode = "Tone->Tone"
        radio.set_memory(mem)
        self.assertEqual((rec.tx_tone_index, rec.rx_tone_index), (0, 12))
        self.assertEqual(radio.get_memory(3).tmode, "Cross")

        mem.tmode = "DTCS"
        mem.dtcs = 754
        radio.set_memory(mem)
        self.assertEqual((rec.subtone_selection, rec.dcs_index,
                          rec.dcs_index_2), (0x0C, 103, 103))

        mem.name = "A*B=1$"
        radio.set_memory(mem)
        self.assertEqual(radio.get_memory(3).name, "A*B=1$")

    def test_delete_writes_oem_blank_record(self):
        radio = self._radio()
        radio.load_mmap(str(STOCK_IMAGE))
        self.assertTrue(radio.get_features().can_delete)
        mem = radio.get_memory(0)
        mem.empty = True
        radio.set_memory(mem)
        raw = radio.get_mmap().get_packed()[:64]
        self.assertEqual(raw, b"\xFF" * 64)
        self.assertTrue(radio.get_memory(0).empty)

    def test_banks_use_the_record_mask(self):
        radio = self._radio()
        radio.load_mmap(str(STOCK_IMAGE))
        model = radio.get_bank_model()
        banks = model.get_mappings()
        self.assertEqual(len(banks), 10)
        mem = radio.get_memory(0)
        model.add_memory_to_mapping(mem, banks[9])
        self.assertEqual(radio._memobj.memory[0].banks, 0x200)
        self.assertEqual(model.get_memory_mappings(mem), [banks[9]])
        model.remove_memory_from_mapping(mem, banks[9])
        self.assertEqual(radio._memobj.memory[0].banks, 0)

    def test_upload_sequence_writes_only_common_channels(self):
        fake = FakeDR735()
        fake.eepel[0] = _record(146520000)
        radio = self._download(fake)
        fake.sent.clear()
        radio.sync_out()
        self.assertEqual(fake.sent[:3], ["AL~", "AL~WHO", "AL~DR735J"])
        self.assertEqual(fake.sent[-1], "AL~RESET")
        writes = [c for c in fake.sent if c.startswith("AL~EEP")]
        self.assertEqual(len(writes), 1000)
        self.assertTrue(all(c.startswith("AL~EEPEL") for c in writes))
        self.assertEqual(fake.eepel[0][4:8],
                         (146520000).to_bytes(4, "little"))

    def test_upload_refuses_out_of_band_and_model_mismatch(self):
        from chirp import errors
        fake = FakeDR735(model="DR735EN", eepdl=False)
        fake.eepel[2 * 64] = _record(118000000, mode=2)  # airband AM
        radio = self._download(fake)
        self.assertEqual(radio.get_features().valid_bands,
                         self.mod.NARROW_BANDS["DR735EN"])
        fake.sent.clear()
        with self.assertRaisesRegex(errors.RadioError, "outside"):
            radio.sync_out()
        self.assertNotIn("AL~DR735J", fake.sent)

        other = FakeDR735(model="DR735TE", eepdl=False)
        radio.pipe = other
        with self.assertRaisesRegex(errors.RadioError, "DR735EN"):
            radio.sync_out()
        self.assertNotIn("AL~DR735J", other.sent)

    def test_extended_channels_are_not_written(self):
        fake = FakeDR735()
        radio = self._download(fake)
        from chirp import chirp_common
        self.assertIn("freq", radio.get_memory(1100).immutable)
        before = radio.get_mmap().get_packed()
        mem = chirp_common.Memory()
        mem.number = 1100
        mem.freq = 146000000
        radio.set_memory(mem)
        self.assertEqual(radio.get_mmap().get_packed(), before)

    def test_forum_report_echo_only_trace_and_message(self):
        """Reporter trace: 'AL~WHO | response complete | 0.01s', then
        'No response from radio'. The 10 ms reply was the cable echo."""
        from chirp import errors
        trace = self.bridge.RadioCommunicationTrace()
        fake = FakeDR735(answer=False)
        radio = self._radio(self.bridge.TracedSerial(fake, trace))
        with self.assertRaises(errors.RadioNoResponse) as caught:
            radio.sync_in()
        self.assertIn("LEFT speaker jack", str(caught.exception))
        self.assertIn("Clone mode", str(caught.exception))
        message = self.bridge.bridge_error_message(
            caught.exception, command="download", model="Alinco_DR735T")
        self.assertIn("LEFT speaker jack", message)
        rendered = trace.format()
        self.assertIn("cable echo only; radio did not answer", rendered)
        self.assertNotIn("response complete", rendered)

    def test_trace_shows_identity_and_blocks(self):
        trace = self.bridge.RadioCommunicationTrace(max_entries=2000)
        fake = FakeDR735(eepdl=False)
        radio = self._radio(self.bridge.TracedSerial(fake, trace))
        radio.sync_in()
        trace.format()   # the bridge finishes the pending entry here
        entries = [(e["command"], e["result"]) for e in trace._entries]
        self.assertIn(("AL~WHO", "radio id=DR735TN"), entries)
        self.assertIn(("AL~EEPEL F9C0 R", "block (64 bytes)"), entries)
        self.assertEqual(entries[-1], ("AL~EEPDL C000 R",
                                       "cable echo only; radio did not answer"))

    def test_oem_tables_match_chirp_constants(self):
        from chirp import chirp_common
        from chirp.drivers.alinco import ALINCO_TONES
        self.assertEqual(self.mod.TONES, ALINCO_TONES)
        self.assertEqual(self.mod.DCS_CODES, list(chirp_common.DTCS_CODES))
        self.assertEqual(len(self.mod.NAME_CHARSET), 48)


if __name__ == "__main__":
    unittest.main()
