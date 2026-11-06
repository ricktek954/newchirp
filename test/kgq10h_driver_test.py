"""Offline tests for the CPS-derived Wouxun KG-Q10H driver."""

import importlib.util
from pathlib import Path
import struct
import sys
import unittest

from chirp_test_source import chirp_source


ROOT = Path(__file__).resolve().parent.parent
SOURCE = chirp_source()
VENDOR = ROOT / "assets/python/pyserial-3.5-py2.py3-none-any.whl"


def _load_bridge():
    spec = importlib.util.spec_from_file_location(
        "newchirp_chirp_bridge_kgq10h",
        ROOT / "scripts/chirp_bridge.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load chirp_bridge.py")
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


bridge = _load_bridge()
directory = bridge.load_chirp(
    str(SOURCE), str(VENDOR), str(ROOT / "drivers")
)

from chirp import chirp_common  # noqa: E402
from chirp import errors  # noqa: E402
from chirp import memmap  # noqa: E402

kg = sys.modules["newchirp.drivers.newchirp_kgq10h"]


def _image():
    image = bytearray(b"\xFF" * kg.MEM_SIZE)
    image[kg.IDENT_OFFSET:kg.IDENT_OFFSET + len(b"KG-Q10H")] = b"KG-Q10H"
    image[
        kg.INTERNAL_MODEL_OFFSET:
        kg.INTERNAL_MODEL_OFFSET + len(kg.INTERNAL_MODEL)
    ] = kg.INTERNAL_MODEL
    image[
        kg.SOFTWARE_OFFSET:
        kg.SOFTWARE_OFFSET + len(kg.SOFTWARE_PREFIX)
    ] = kg.SOFTWARE_PREFIX
    return image


def _memory(number, **fields):
    mem = chirp_common.Memory()
    mem.number = number
    mem.freq = 146_520_000
    mem.duplex = ""
    mem.offset = 0
    mem.mode = "FM"
    mem.power = kg.POWER_LEVELS[2]
    mem.skip = ""
    mem.tmode = ""
    for name, value in fields.items():
        setattr(mem, name, value)
    return mem


def _response(command, payload):
    check = kg.checksum(command, 0x00, payload)
    plain = payload + bytes((check,))
    return (
        bytes((0x7C, command, 0x00, len(payload)))
        + kg.encrypt(plain)
    )


class FakeKGQ10Serial:
    def __init__(self, image, split_responses=False):
        self.image = bytearray(image)
        self.baudrate = 0
        self.timeout = 0
        self.write_timeout = 0
        self.dtr = False
        self.rts = False
        self.writes = []
        self.read_addresses = []
        self.write_addresses = []
        self._responses = bytearray()
        self.split_responses = split_responses

    def _queue(self, frame):
        self._responses.extend(frame)

    def write(self, data):
        data = bytes(data)
        self.writes.append(data)
        if len(data) < 5 or data[0] != 0x7C:
            return len(data)
        plain = kg.decrypt(data[4:])
        payload, received_check = plain[:-1], plain[-1]
        if len(payload) != data[3]:
            raise AssertionError("host frame length is inconsistent")
        expected_check = kg.checksum(data[1], data[2], payload)
        if received_check != expected_check:
            raise AssertionError("host frame has a bad checksum")

        if data[1] == kg.CMD_READ:
            address, size = struct.unpack_from(">HB", payload)
            self.read_addresses.append(address)
            block = bytes(self.image[address:address + size])
            self._queue(
                _response(kg.CMD_READ, struct.pack(">H", address) + block)
            )
        elif data[1] == kg.CMD_WRITE:
            address = struct.unpack_from(">H", payload)[0]
            block = payload[2:]
            self.write_addresses.append(address)
            self.image[address:address + len(block)] = block
            self._queue(_response(kg.CMD_WRITE, payload[:2]))
        return len(data)

    def read(self, count):
        if not self._responses:
            return b""
        take = min(count, 1 if self.split_responses else count)
        data = bytes(self._responses[:take])
        del self._responses[:take]
        return data

    def reset_input_buffer(self):
        self._responses.clear()


class KGQ10HDriverTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.radio_class = directory.get_radio("Wouxun_KG-Q10H")

    def _radio(self, image=None):
        data = bytes(image) if image is not None else bytes(_image())
        radio = self.radio_class(memmap.MemoryMapBytes(data))
        radio.status_fn = lambda _status: None
        return radio

    def test_registration_and_cps_features(self):
        self.assertEqual(
            self.radio_class.__name__,
            kg.KGQ10HRadio.__name__,
        )
        features = self.radio_class(None).get_features()
        self.assertEqual(features.memory_bounds, (1, 999))
        self.assertEqual(features.valid_name_length, 12)
        self.assertEqual(features.valid_modes, ["FM", "NFM", "AM"])
        self.assertEqual(self.radio_class.BAUD_RATE, 115200)
        self.assertTrue(self.radio_class.WANTS_DTR)
        self.assertTrue(self.radio_class.WANTS_RTS)
        self.assertFalse(self.radio_class.NEEDS_COMPAT_SERIAL)
        self.assertEqual(
            kg.PROGRAM_RANGES,
            (
                (0x0440, 0x0508),
                (0x0540, 0x05C0),
                (0x05E0, 0x4460),
                (0x4460, 0x7340),
                (0x7340, 0x7728),
                (0x7740, 0x78A8),
                (0x78B0, 0x78D8),
                (0x78E0, 0x7B38),
                (0x7B40, 0x8000),
            ),
        )

    def test_official_cps_frame_vectors(self):
        self.assertEqual(kg.ENCRYPT_SEED, 0x57)
        self.assertEqual(
            kg.build_frame(
                kg.CMD_READ, struct.pack(">HB", 0x0340, 64)
            ).hex(),
            "7c82ff0354145453",
        )
        self.assertEqual(kg.end_frame().hex(), "7c81ff00d7")

    def test_download_reads_cps_regions_and_identity(self):
        image = _image()
        image[0x05F0:0x0600] = struct.pack(
            "<IIHH", 14_652_000, 14_652_000, 0, 0
        ) + bytes.fromhex("0201200001010000")
        image[0x446C:0x4478] = b"2m Calling\x00\x00"
        image[0x7341] = kg.VALID_FLAG
        serial = FakeKGQ10Serial(image, split_responses=True)
        radio = self.radio_class(serial)
        radio.status_fn = lambda _status: None

        radio.sync_in()

        expected = []
        for start, end in kg.READ_RANGES:
            expected.extend(range(start, end, kg.READ_BLOCK_SIZE))
        self.assertEqual(serial.read_addresses, expected)
        self.assertEqual(len(radio._packed()), kg.MEM_SIZE)
        self.assertEqual(radio.get_memory(1).name, "2m Calling")
        self.assertEqual(serial.writes[-1], kg.end_frame())
        self.assertTrue(serial.dtr)
        self.assertTrue(serial.rts)

    def test_channel_fields_names_and_tones(self):
        image = _image()
        number = 17
        record_offset = kg.CHANNEL_BASE + number * kg.RECORD_SIZE
        tone_words = (
            0x4000 | int("023", 8),  # RX D023N
            0x8000 | 885,             # TX 88.5 Hz
        )
        image[record_offset:record_offset + 16] = struct.pack(
            "<IIHH",
            146_520_000 // 10,
            147_000_000 // 10,
            tone_words[0],
            tone_words[1],
        ) + bytes.fromhex("A2A20180")
        name_offset = kg.NAME_BASE + number * kg.NAME_SIZE
        image[name_offset:name_offset + 12] = b"CROSS-17\x00\x00\x00\x00"
        image[kg.VALID_BASE + number] = kg.VALID_FLAG
        radio = self._radio(image)

        mem = radio.get_memory(number)
        self.assertEqual(mem.freq, 146_520_000)
        self.assertEqual(mem.duplex, "+")
        self.assertEqual(mem.offset, 480_000)
        self.assertEqual(mem.name, "CROSS-17")
        self.assertEqual(mem.tmode, "Cross")
        self.assertEqual(mem.cross_mode, "Tone->DTCS")
        self.assertEqual(mem.rtone, 88.5)
        self.assertEqual(mem.rx_dtcs, 23)
        self.assertEqual(mem.dtcs_polarity, "NN")

        mem.skip = "S"
        radio.set_memory(mem)
        changed = radio._packed()
        self.assertEqual(changed[record_offset + 13] & 0x80, 0x80)
        self.assertEqual(changed[record_offset + 15], 0x80)
        self.assertEqual(changed[record_offset + 13] & 0x20, 0)

    def test_empty_channel_clears_all_channel_storage(self):
        radio = self._radio()
        radio.set_memory(_memory(31, name="DELETE"))
        radio.set_memory(_memory(31, empty=True))
        raw = radio._packed()
        offset = kg.CHANNEL_BASE + 31 * kg.RECORD_SIZE
        name_offset = kg.NAME_BASE + 31 * kg.NAME_SIZE
        self.assertEqual(raw[offset:offset + kg.RECORD_SIZE], bytes(16))
        self.assertEqual(raw[name_offset:name_offset + kg.NAME_SIZE], bytes(12))
        self.assertEqual(raw[kg.VALID_BASE + 31], 0)

    def test_decoded_channel_round_trips_without_byte_changes(self):
        image = _image()
        record_offset = kg.CHANNEL_BASE + 23 * kg.RECORD_SIZE
        image[record_offset:record_offset + 16] = struct.pack(
            "<IIHH",
            146_520_000 // 10,
            146_520_000 // 10,
            0,
            0,
        ) + bytes.fromhex("02AD0100")
        name_offset = kg.NAME_BASE + 23 * kg.NAME_SIZE
        image[name_offset:name_offset + 12] = b"ROUNDTRIP\x00\x00\x00"
        image[kg.VALID_BASE + 23] = kg.VALID_FLAG
        radio = self._radio(image)

        radio.set_memory(radio.get_memory(23))

        self.assertEqual(radio._packed(), bytes(image))

    def test_upload_writes_only_official_program_ranges(self):
        image = _image()
        image[0x0440:0x0508] = b"\x11" * 200
        image[0x78B0:0x78D8] = b"\x22" * 40
        serial = FakeKGQ10Serial(image)
        radio = self.radio_class(memmap.MemoryMapBytes(bytes(image)))
        radio.status_fn = lambda _status: None
        radio.pipe = serial

        radio.sync_out()

        expected = []
        for start, end in kg.PROGRAM_RANGES:
            expected.extend(range(start, end, kg.WRITE_BLOCK_SIZE))
        self.assertEqual(serial.write_addresses, expected)
        self.assertEqual(
            serial.read_addresses,
            list(range(0x0340, 0x0440, kg.READ_BLOCK_SIZE)),
        )
        self.assertNotIn(0x0340, serial.write_addresses)
        self.assertEqual(bytes(serial.image[0x0440:0x0508]), b"\x11" * 200)
        self.assertEqual(bytes(serial.image[0x78B0:0x78D8]), b"\x22" * 40)
        self.assertEqual(serial.writes[-1], kg.end_frame())

    def test_invalid_images_cannot_write(self):
        radio = self._radio()
        serial = FakeKGQ10Serial(_image())
        radio.pipe = serial
        radio._mmap = memmap.MemoryMapBytes(bytes(_image()[:0x80]))
        with self.assertRaises(errors.InvalidDataError):
            radio.sync_out()
        self.assertEqual(serial.writes, [])

        foreign = _image()
        foreign[
            kg.INTERNAL_MODEL_OFFSET:
            kg.INTERNAL_MODEL_OFFSET + len(kg.INTERNAL_MODEL)
        ] = b"NOT-A-Q10"
        radio._mmap = memmap.MemoryMapBytes(bytes(foreign))
        with self.assertRaises(errors.InvalidDataError):
            radio.sync_out()
        self.assertEqual(serial.writes, [])

    def test_match_model_requires_complete_supported_image(self):
        self.assertTrue(
            self.radio_class.match_model(bytes(_image()), "test.img")
        )
        self.assertFalse(
            self.radio_class.match_model(
                bytes(_image()[:0x100]), "test.img"
            )
        )
        foreign = _image()
        foreign[
            kg.IDENT_OFFSET:kg.IDENT_OFFSET + len(b"KG-Q10H")
        ] = b"NOT-A-10"
        self.assertFalse(
            self.radio_class.match_model(bytes(foreign), "test.img")
        )

    def test_rejects_unsafe_channel_values(self):
        radio = self._radio()
        with self.assertRaises(errors.InvalidValueError):
            radio.set_memory(_memory(1, freq=146_520_001))
        with self.assertRaises(errors.InvalidValueError):
            radio.set_memory(_memory(1, freq=146_520_000, duplex="+",
                                    offset=3_000_000))
        with self.assertRaises(errors.InvalidValueError):
            radio.set_memory(_memory(1, freq=135_000_000, duplex="off",
                                    mode="FM"))
        with self.assertRaises(errors.InvalidValueError):
            radio.set_memory(_memory(1, name="TOO-LONG-NAME"))
        with self.assertRaises(errors.InvalidValueError):
            radio.set_memory(_memory(1000))


if __name__ == "__main__":
    unittest.main()
