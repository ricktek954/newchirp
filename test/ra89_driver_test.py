"""Offline replay tests for the CPS-derived Retevis RA89 driver."""

import importlib.util
from pathlib import Path
import struct
import sys
import unittest
from unittest import mock

from chirp_test_source import chirp_source


ROOT = Path(__file__).resolve().parent.parent
SOURCE = chirp_source()
VENDOR = ROOT / "assets/python/pyserial-3.5-py2.py3-none-any.whl"


def _load_bridge():
    spec = importlib.util.spec_from_file_location(
        "newchirp_chirp_bridge_ra89",
        ROOT / "scripts/chirp_bridge.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load chirp_bridge.py")
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


bridge = _load_bridge()
directory = bridge.load_chirp(str(SOURCE), str(VENDOR), str(ROOT / "drivers"))

from chirp import chirp_common  # noqa: E402
from chirp import errors  # noqa: E402
from chirp import memmap  # noqa: E402

ra89 = sys.modules["newchirp.drivers.newchirp_ra89"]
ra89.time.sleep = lambda *_args, **_kwargs: None


def _image():
    image = bytearray(b"\xFF" * ra89.MEM_SIZE)
    image[ra89.INTRO_BASE:ra89.INTRO_BASE + 16] = b"Retevis".ljust(16, b" ")
    image[
        ra89.INTRO_BASE + 16:ra89.INTRO_BASE + 32
    ] = b"RA89".ljust(16, b" ")
    return image


def _handshake_response():
    response = bytearray(36)
    response[:9] = ra89.HANDSHAKE_RESPONSE
    response[-14:-10] = ra89.AUTH_RESPONSE_CODE
    response[-1] = 0xFD
    return bytes(response)


def _memory(number, **fields):
    mem = chirp_common.Memory()
    mem.number = number
    mem.freq = 146_520_000
    mem.duplex = ""
    mem.offset = 0
    mem.mode = "FM"
    mem.power = ra89.POWER_LEVELS[0]
    mem.skip = ""
    mem.tmode = ""
    mem.name = ""
    for name, value in fields.items():
        setattr(mem, name, value)
    return mem


class FakeRA89Serial:
    def __init__(self, image, split_reads=False):
        self.image = bytearray(image)
        self.baudrate = 57600
        self.timeout = 0.25
        self.dtr = True
        self.rts = True
        self.writes = []
        self.read_addresses = []
        self.write_addresses = []
        self._responses = bytearray()
        self.split_reads = split_reads
        self.corrupt_marker = False
        self.wrong_address = False
        self.bad_terminator = False

    def _queue(self, data):
        self._responses.extend(data)

    def write(self, data):
        data = bytes(data)
        self.writes.append(data)
        if data == ra89.HANDSHAKE:
            self._queue(_handshake_response())
        elif data in (
            ra89.AUTH_COMMAND + ra89.OPEN_PASSWORD + b"\xFD",
            ra89.SET_BAUD,
            ra89.ENTER_READ,
            ra89.ENTER_WRITE,
            ra89.EXIT_SESSION,
        ):
            self._queue(ra89.COMMAND_ACK)
        elif data.startswith(ra89.READ_COMMAND):
            if len(data) != 12 or data[-1:] != b"\xFD":
                raise AssertionError("Malformed RA89 read request")
            address = int.from_bytes(data[5:9], "big")
            length = int.from_bytes(data[9:11], "big")
            self.read_addresses.append(address)
            payload = bytes(self.image[address:address + length])
            echoed_address = address ^ 1 if self.wrong_address else address
            marker = b"\x00\x00\x00\x00\x00" if self.corrupt_marker else (
                ra89.READ_RESPONSE
            )
            tail = b"\x00" if self.bad_terminator else b"\xFD"
            check = ra89._checksum(
                struct.pack(">I", echoed_address)
                + struct.pack(">H", len(payload))
                + payload
            )
            self._queue(
                marker
                + struct.pack(">I", echoed_address)
                + struct.pack(">H", len(payload))
                + payload
                + bytes((check,))
                + tail
            )
        elif data.startswith(ra89.WRITE_COMMAND):
            if len(data) != 45 or data[-1:] != b"\xFD":
                raise AssertionError("Malformed RA89 write request")
            address = int.from_bytes(data[5:9], "big")
            length = int.from_bytes(data[9:11], "big")
            payload = data[11:11 + length]
            returned_check = data[11 + length]
            expected_check = ra89._checksum(
                struct.pack(">I", address)
                + struct.pack(">H", length)
                + payload
            )
            if returned_check != expected_check:
                raise AssertionError("Host write checksum is invalid")
            self.write_addresses.append(address)
            self.image[address:address + length] = payload
            self._queue(ra89.COMMAND_ACK)
        else:
            raise AssertionError("Unexpected RA89 write: %s" % data.hex())
        return len(data)

    def read(self, count):
        if not self._responses:
            return b""
        take = min(count, 1 if self.split_reads else count)
        result = bytes(self._responses[:take])
        del self._responses[:take]
        return result

    def reset_input_buffer(self):
        self._responses.clear()


class RA89DriverTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.radio_class = directory.get_radio("Retevis_RA89")

    def _radio(self, image=None, pipe=None):
        data = bytes(image) if image is not None else bytes(_image())
        radio = self.radio_class(memmap.MemoryMapBytes(data))
        if pipe is not None:
            radio.pipe = pipe
        radio.status_fn = lambda _status: None
        return radio

    def test_registration_transport_and_frame_vectors(self):
        self.assertEqual(
            self.radio_class.__name__,
            ra89.NewChirpRA89Radio.__name__,
        )
        self.assertEqual(self.radio_class.BAUD_RATE, 57600)
        self.assertTrue(self.radio_class.WANTS_DTR)
        self.assertTrue(self.radio_class.WANTS_RTS)
        self.assertFalse(self.radio_class.HARDWARE_FLOW)
        self.assertFalse(self.radio_class.XON_XOFF)
        self.assertEqual(
            ra89.HANDSHAKE.hex(),
            "fefeeeefe055563939fd",
        )
        self.assertEqual(
            ra89.make_read_frame(0, 32).hex(),
            "fefeeeefeb000000000020fd",
        )
        write_frame = ra89.make_write_frame(0, bytes(range(32)))
        self.assertEqual(len(write_frame), 45)
        self.assertEqual(write_frame[-2], 0xF0)
        self.assertEqual(write_frame[-1], 0xFD)

    def test_open_serial_matches_cps_control_lines(self):
        import serial

        handle = mock.MagicMock()
        with mock.patch.object(
            serial,
            "Serial",
            return_value=handle,
        ) as serial_class:
            self.assertIs(
                bridge.open_serial(
                    self.radio_class,
                    "/dev/fake-ra89",
                ),
                handle,
            )

        self.assertEqual(serial_class.call_args.kwargs["baudrate"], 57600)
        self.assertFalse(serial_class.call_args.kwargs["rtscts"])
        self.assertFalse(serial_class.call_args.kwargs["xonxoff"])
        self.assertTrue(handle.dtr)
        self.assertTrue(handle.rts)

    def test_download_uses_oem_session_and_fragment_safe_reads(self):
        source = _image()
        source[0:4] = struct.pack("<I", 435_230_000 // 10)
        source[4:8] = source[0:4]
        source[8:12] = bytes.fromhex("FF0FFF0F")
        source[12:15] = bytes.fromhex("000004")
        serial = FakeRA89Serial(source, split_reads=True)
        radio = self.radio_class(serial)
        radio.status_fn = lambda _status: None

        radio.sync_in()

        expected = list(range(0, ra89.MEM_SIZE, ra89.BLOCK_SIZE))
        self.assertEqual(serial.read_addresses, expected)
        self.assertEqual(len(radio._packed()), ra89.MEM_SIZE)
        self.assertEqual(radio.get_memory(1).freq, 435_230_000)
        self.assertEqual(serial.writes[0], ra89.HANDSHAKE)
        self.assertEqual(
            serial.writes[1],
            ra89.AUTH_COMMAND + ra89.OPEN_PASSWORD + b"\xFD",
        )
        self.assertEqual(serial.writes[2], ra89.SET_BAUD)
        self.assertEqual(serial.writes[3], ra89.ENTER_READ)
        self.assertEqual(serial.writes[-1], ra89.EXIT_SESSION)

    def test_channel_fields_names_and_tones_round_trip(self):
        image = _image()
        number = 17
        record_offset = ra89._channel_offset(number)
        image[record_offset:record_offset + 21] = (
            struct.pack(
                "<II",
                462_562_500 // 10,
                467_562_500 // 10,
            )
            + struct.pack(
                ">HH",
                (0 << 12) | int("023", 8),
                (0 << 13) | 885,
            )
            + bytes.fromhex("060204")
            + b"CROSS-"
        )
        image[
            ra89._name_offset(number):
            ra89._name_offset(number) + 10
        ] = b"17        "
        radio = self._radio(image)

        mem = radio.get_memory(number)
        self.assertEqual(mem.freq, 462_562_500)
        self.assertEqual(mem.duplex, "+")
        self.assertEqual(mem.offset, 5_000_000)
        self.assertEqual(mem.name, "CROSS-17")
        self.assertEqual(mem.tmode, "Cross")
        self.assertEqual(mem.cross_mode, "Tone->DTCS")
        self.assertEqual(mem.rtone, 88.5)
        self.assertEqual(mem.rx_dtcs, 23)
        self.assertEqual(mem.dtcs_polarity, "NN")
        self.assertEqual(mem.mode, "FM")
        self.assertEqual(mem.power, ra89.POWER_LEVELS[2])

        radio.set_memory(mem)
        changed = radio.get_memory(number)
        self.assertEqual(changed.freq, mem.freq)
        self.assertEqual(changed.duplex, mem.duplex)
        self.assertEqual(changed.offset, mem.offset)
        self.assertEqual(changed.name, mem.name)
        self.assertEqual(changed.tmode, mem.tmode)
        self.assertEqual(changed.cross_mode, mem.cross_mode)

    def test_upload_skips_oem_protected_region(self):
        serial = FakeRA89Serial(_image())
        radio = self._radio(pipe=serial)

        radio.sync_out()

        self.assertEqual(serial.write_addresses[0], 0)
        self.assertEqual(serial.write_addresses[-1], ra89.MEM_SIZE - 32)
        self.assertTrue(
            all(
                not ra89.WRITE_SKIP_START <= address < ra89.WRITE_SKIP_END
                for address in serial.write_addresses
            )
        )
        self.assertIn(
            ra89.WRITE_SKIP_START - 32,
            serial.write_addresses,
        )
        self.assertIn(ra89.WRITE_SKIP_END, serial.write_addresses)
        self.assertEqual(serial.writes[3], ra89.ENTER_WRITE)
        self.assertEqual(serial.writes[-1], ra89.EXIT_SESSION)

    def test_core_settings_and_startup_text_apply_in_place(self):
        radio = self._radio()
        tree = radio.get_settings()
        basic = next(group for group in tree if group.get_name() == "basic")
        advanced = next(
            group for group in tree if group.get_name() == "advanced"
        )
        beep = next(
            setting
            for setting in basic
            if setting.get_name() == "beep"
        )
        intro = next(
            setting
            for setting in advanced
            if setting.get_name() == "introLine1"
        )

        beep.value = False
        intro.value = "NewChirp RA89"
        radio.set_settings(tree)

        image = radio._packed()
        self.assertEqual(image[ra89.SETTINGS_BASE + 0x0D] & 0x01, 0)
        self.assertEqual(
            image[ra89.INTRO_BASE:ra89.INTRO_BASE + 16],
            b"NewChirp RA89   ",
        )

    def test_malformed_read_responses_fail_closed(self):
        for attribute in (
            "corrupt_marker",
            "wrong_address",
            "bad_terminator",
        ):
            with self.subTest(attribute=attribute):
                serial = FakeRA89Serial(_image())
                setattr(serial, attribute, True)
                radio = self.radio_class(serial)
                with self.assertRaises(errors.RadioError):
                    radio.sync_in()
                self.assertEqual(serial.writes[-1], ra89.EXIT_SESSION)

    def test_saved_image_matching(self):
        image = _image()
        self.assertTrue(self.radio_class.match_model(bytes(image), "RA89.img"))
        broken = bytearray(image)
        broken[ra89.INTRO_BASE + 16:ra89.INTRO_BASE + 20] = b"XXXX"
        self.assertFalse(
            self.radio_class.match_model(bytes(broken), "RA89.img")
        )
        self.assertFalse(
            self.radio_class.match_model(bytes(image[:-1]), "RA89.img")
        )


if __name__ == "__main__":
    unittest.main()
