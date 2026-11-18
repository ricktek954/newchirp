"""Offline replay tests for the MCP-2A-derived TM-V71 clone driver."""

from pathlib import Path
import importlib
import importlib.util
import struct
import sys
import unittest

from chirp_test_source import chirp_source


ROOT = Path(__file__).resolve().parent.parent
SOURCE = chirp_source()
VENDOR = ROOT / "assets/python/pyserial-3.5-py2.py3-none-any.whl"
BODY_END = 0x7F00


def _load_bridge():
    spec = importlib.util.spec_from_file_location(
        "newchirp_chirp_bridge_tmv71", ROOT / "scripts/chirp_bridge.py",
    )
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


class FakeTMV71:
    """Answers with the wire format traced from MCP-2A 3.22."""

    def __init__(self, image, model="TM-V71", chunk=None,
                 bad_header_at=None, short_at=None, nak_at=None,
                 refuse_program=False):
        self.image = bytearray(image)
        self.model = model
        self.chunk = chunk
        self.bad_header_at = bad_header_at
        self.short_at = short_at
        self.nak_at = nak_at
        self.refuse_program = refuse_program
        self.timeout = 0.1
        self.baudrate = 9600
        self.out = b""
        self.writes = []
        self.reads_requested = []
        self.program = False
        self._pending_ack = None
        self._line = b""

    def write(self, data):
        data = bytes(data)
        self.writes.append(data)
        if not self.program:
            self._line += data
            while b"\r" in self._line:
                line, self._line = self._line.split(b"\r", 1)
                self._text_command(line.decode("ascii"))
            return
        if data == b"\x06":
            self.out += b"\x15" if self._pending_ack == self.nak_at \
                else b"\x06"
            return
        if data == b"E":
            self.program = False
            self.out += b"\x06"
            return
        if data[:1] == b"R" and len(data) == 4:
            address, length = struct.unpack(">HB", data[1:])
            length = length or 256
            self.reads_requested.append(address)
            header = b"W" + data[1:]
            if address == self.bad_header_at:
                header = b"W\x00\x00\x00"
            payload = bytes(self.image[address:address + length])
            if address == self.short_at:
                payload = payload[:100]
            self._pending_ack = address
            self.out += header + payload
            return
        raise AssertionError("unexpected clone bytes %r" % data)

    def _text_command(self, line):
        if line == "":
            return
        if line == "ID":
            self.out += ("ID %s\r" % self.model).encode()
        elif line == "0M PROGRAM":
            if self.refuse_program:
                self.out += b"N\r\r"
            else:
                self.program = True
                self.out += b"0M\r"
        else:
            self.out += b"?\r"

    def read(self, size):
        if self.chunk:
            size = min(size, self.chunk)
        data, self.out = self.out[:size], self.out[size:]
        return data


class FragmentingPipe:
    """pyserial read(n) keeps collecting until n bytes or timeout."""

    def __init__(self, fake):
        self.fake = fake

    def __getattr__(self, name):
        return getattr(self.fake, name)

    def __setattr__(self, name, value):
        if name == "fake":
            object.__setattr__(self, name, value)
        else:
            setattr(self.fake, name, value)

    def read(self, size):
        data = b""
        while len(data) < size:
            piece = self.fake.read(size - len(data))
            if not piece:
                break
            data += piece
        return data


class KenwoodTMV71DriverTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bridge = _load_bridge()
        cls.directory = cls.bridge.load_chirp(
            str(SOURCE), str(VENDOR), str(ROOT / "drivers"),
        )
        cls.module = importlib.import_module("newchirp.drivers.newchirp_tmv71")
        cls.radio_class = cls.module.KenwoodTMV71CloneRadio

    def _image(self):
        data = bytearray((i * 7 + 3) & 0xFF for i in range(BODY_END))
        return data

    def _radio(self, fake):
        radio = self.radio_class(None)
        radio.pipe = FragmentingPipe(fake)
        radio.status_fn = lambda status: None
        return radio

    def test_registered_with_exact_model(self):
        from chirp import directory
        self.assertIs(
            directory.get_radio("Kenwood_TM-V71_CloneMode"), self.radio_class
        )

    def test_full_download_matches_body_and_stays_in_range(self):
        image = self._image()
        fake = FakeTMV71(image)
        radio = self._radio(fake)
        radio.sync_in()
        self.assertEqual(radio.get_mmap().get_packed(), bytes(image))
        self.assertEqual(fake.reads_requested,
                         list(range(0, BODY_END, 0x100)))
        self.assertTrue(all(a < BODY_END for a in fake.reads_requested))
        self.assertIn(b"0M PROGRAM\r", fake.writes)
        self.assertEqual(fake.writes[-1], b"E")
        self.assertFalse(fake.program)

    def test_fragmented_responses_are_assembled(self):
        image = self._image()
        fake = FakeTMV71(image, chunk=7)
        radio = self._radio(fake)
        radio.sync_in()
        self.assertEqual(radio.get_mmap().get_packed(), bytes(image))

    def test_wrong_echo_header_is_rejected_and_exits(self):
        from chirp import errors
        fake = FakeTMV71(self._image(), bad_header_at=0x1700)
        with self.assertRaisesRegex(errors.RadioError, "0x1700.*header"):
            self._radio(fake).sync_in()
        self.assertEqual(fake.writes[-1], b"E")

    def test_short_block_is_rejected(self):
        from chirp import errors
        fake = FakeTMV71(self._image(), short_at=0x0200)
        with self.assertRaisesRegex(errors.RadioError, "expected 256 bytes"):
            self._radio(fake).sync_in()

    def test_missing_block_ack_is_rejected(self):
        from chirp import errors
        fake = FakeTMV71(self._image(), nak_at=0x0300)
        with self.assertRaisesRegex(errors.RadioError, "instead of ACK"):
            self._radio(fake).sync_in()

    def test_program_mode_refusal_is_reported(self):
        from chirp import errors
        fake = FakeTMV71(self._image(), refuse_program=True)
        with self.assertRaisesRegex(errors.RadioError, "refused clone mode"):
            self._radio(fake).sync_in()
        self.assertEqual(fake.reads_requested, [])

    def test_tm_d710_identity_points_to_correct_driver(self):
        from chirp import errors
        fake = FakeTMV71(self._image(), model="TM-D710")
        with self.assertRaisesRegex(errors.RadioError, "TM-D710 clone-mode"):
            self._radio(fake).sync_in()
        self.assertNotIn(b"0M PROGRAM\r", fake.writes)

    def test_upload_is_disabled(self):
        from chirp import errors
        fake = FakeTMV71(self._image())
        with self.assertRaisesRegex(errors.RadioError, "read-only"):
            self._radio(fake).sync_out()
        self.assertEqual(fake.writes, [])

    def test_channel_round_trip_and_settings_on_body_image(self):
        from chirp import chirp_common, memmap
        radio = self.radio_class(None)
        radio._mmap = memmap.MemoryMapBytes(b"\x00" * BODY_END)
        radio.process_mmap()
        mem = chirp_common.Memory()
        mem.number = 12
        mem.freq = 146940000
        mem.duplex = "-"
        mem.offset = 600000
        mem.tmode = "Tone"
        mem.rtone = 100.0
        mem.name = "W1AW"
        radio.set_memory(mem)
        back = radio.get_memory(12)
        self.assertEqual(back.freq, 146940000)
        self.assertEqual(back.duplex, "-")
        self.assertEqual(back.offset, 600000)
        self.assertEqual(back.tmode, "Tone")
        self.assertEqual(back.rtone, 100.0)
        self.assertEqual(back.name.rstrip(), "W1AW")
        self.assertEqual(len(radio.get_mmap()), BODY_END)

        names = [group.get_name() for group in radio.get_settings()]
        self.assertNotIn("skyk", names)
        self.assertIn("basic", names)

    def test_names_are_uppercase_only(self):
        radio = self.radio_class(None)
        chars = radio.get_features().valid_characters
        self.assertIn("A", chars)
        self.assertNotIn("a", chars)


if __name__ == "__main__":
    unittest.main()
