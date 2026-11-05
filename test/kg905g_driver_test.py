"""Offline tests for the Wouxun KG-905G Plus driver."""

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
        "newchirp_chirp_bridge_kg905g",
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

kg = sys.modules["newchirp.drivers.newchirp_kg905g"]
kg.time.sleep = lambda *_args, **_kwargs: None


def _image():
    image = bytearray(kg.MEM_SIZE)
    image[kg.MODEL_OFFSET:kg.MODEL_OFFSET + len(kg.IDENT)] = kg.IDENT
    return image


def _memory(number, **fields):
    mem = chirp_common.Memory()
    mem.number = number
    mem.freq = 462562500
    mem.duplex = ""
    mem.offset = 0
    mem.mode = "FM"
    mem.power = kg.POWER_HIGH
    mem.skip = ""
    mem.tmode = ""
    mem.tuning_step = 12.5
    for name, value in fields.items():
        setattr(mem, name, value)
    return mem


class FakeKG905Serial:
    def __init__(self, image):
        self.image = bytearray(image)
        self.baudrate = 0
        self.timeout = 0
        self.dtr = False
        self.rts = False
        self.writes = []
        self.read_addresses = []
        self.write_addresses = []
        self._responses = bytearray()

    def _enqueue(self, frame):
        self._responses.extend(frame)

    def write(self, data):
        data = bytes(data)
        self.writes.append(data)
        if len(data) < 5 or data[0] != 0x7C:
            return len(data)
        plain = kg.decrypt(data[4:])
        payload, passed_check = plain[:-1], plain[-1]
        expected_check = kg.checksum(
            data[1], data[2], data[3], payload
        )
        if passed_check != expected_check:
            raise AssertionError("host frame has a bad checksum")
        if data[1] == 0x82:
            address = struct.unpack_from(">H", payload, 0)[0]
            size = payload[2]
            self.read_addresses.append(address)
            block = bytes(self.image[address:address + size])
            self._enqueue(
                kg.build_frame(
                    0x82,
                    0x00,
                    struct.pack(">H", address) + block,
                )
            )
        elif data[1] == 0x83:
            address = struct.unpack_from(">H", payload, 0)[0]
            block = payload[2:]
            self.write_addresses.append(address)
            self.image[address:address + len(block)] = block
            self._enqueue(kg.build_frame(0x83, 0x00, payload[:2]))
        return len(data)

    def read(self, count):
        data = bytes(self._responses[:count])
        del self._responses[:count]
        return data

    def reset_input_buffer(self):
        self._responses.clear()


class KG905GPlusDriverTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.radio_class = directory.get_radio("Wouxun_KG-905G_Plus")

    def _radio(self, image=None):
        data = bytes(image) if image is not None else bytes(_image())
        radio = self.radio_class(memmap.MemoryMapBytes(data))
        radio.status_fn = lambda _status: None
        return radio

    def test_radio_is_registered_with_all_cps_ranges(self):
        self.assertEqual(
            self.radio_class.__name__,
            kg.KG905GPlusRadio.__name__,
        )
        features = self.radio_class(None).get_features()
        self.assertEqual(features.memory_bounds, (1, 400))
        self.assertEqual(features.valid_name_length, 8)
        self.assertEqual(features.valid_duplexes, ["", "+"])
        self.assertEqual(self.radio_class.BAUD_RATE, 19200)
        self.assertTrue(self.radio_class.WANTS_DTR)
        self.assertTrue(self.radio_class.WANTS_RTS)
        self.assertFalse(self.radio_class.NEEDS_COMPAT_SERIAL)
        self.assertEqual(
            kg.READ_RANGES,
            (
                kg.SERIAL_DATA,
                (0x0440, 0x04C0),
                (0x0540, 0x0550),
                (0x05E0, 0x1EF0),
                (0x1F00, 0x2B88),
                (0x3000, 0x3191),
                (0x3700, 0x3728),
                (0x3360, 0x33DE),
                (0x35C0, 0x3668),
            ),
        )
        self.assertNotIn(kg.SERIAL_DATA, kg.WRITE_RANGES)

    def test_cps_probe_and_end_frame(self):
        probe = kg.build_frame(0x82, 0xFF, struct.pack(">HB", 0x0040, 64))
        self.assertEqual(probe.hex(), "7c82ff0354145453")
        self.assertEqual(kg.build_frame(0x81, 0xFF, b"").hex(), "7c81ff00d7")

    def test_download_uses_official_cps_order_and_identity(self):
        source = _image()
        serial = FakeKG905Serial(source)
        radio = self.radio_class(serial)
        radio.status_fn = lambda _status: None

        radio.sync_in()

        expected = []
        for start, end in kg.READ_RANGES:
            expected.extend(range(start, end, kg.BLOCK_SIZE))
        self.assertEqual(serial.read_addresses, expected)
        self.assertEqual(len(radio._packed()), kg.MEM_SIZE)
        self.assertTrue(radio._packed().startswith(kg.IDENT, kg.MODEL_OFFSET))
        self.assertEqual(serial.writes[-1].hex(), "7c81ff00d7")
        self.assertTrue(serial.dtr)
        self.assertTrue(serial.rts)

    def test_download_accepts_capture_identity_fallback(self):
        source = _image()
        source[kg.MODEL_OFFSET:kg.MODEL_OFFSET + 16] = bytes(16)
        source[kg.CAPTURE_MODEL_OFFSET:kg.CAPTURE_MODEL_OFFSET + len(
            kg.CAPTURE_IDENT
        )] = kg.CAPTURE_IDENT
        serial = FakeKG905Serial(source)
        radio = self.radio_class(serial)
        radio.status_fn = lambda _status: None

        radio.sync_in()

        self.assertEqual(serial.read_addresses[4], 0x0040)
        self.assertEqual(
            bytes(radio._packed()[
                kg.CAPTURE_MODEL_OFFSET:
                kg.CAPTURE_MODEL_OFFSET + len(kg.CAPTURE_IDENT)
            ]),
            kg.CAPTURE_IDENT,
        )

    def test_channel_map_and_400th_slot(self):
        radio = self._radio()
        radio.set_memory(_memory(1, name="GMRS-01", power=kg.POWER_LOW))
        radio.set_memory(_memory(
            400,
            freq=462550000,
            duplex="+",
            offset=5_000_000,
            mode="NFM",
            name="RPT-22",
            skip="S",
        ))
        raw = radio._packed()
        first = raw[kg.CHANNEL_BASE + 16:kg.CHANNEL_BASE + 32]
        last = raw[kg.CHANNEL_BASE + 400 * 16:kg.CHANNEL_BASE + 401 * 16]
        self.assertEqual(
            struct.unpack_from("<II", first),
            (46256250, 46256250),
        )
        self.assertEqual(raw[kg.VALID_BASE + 1], kg.VALID_FLAG)
        self.assertEqual(raw[kg.VALID_BASE + 400], kg.VALID_FLAG)
        self.assertEqual(
            raw[kg.NAME_BASE + 8:kg.NAME_BASE + 16],
            b"GMRS-01\x00",
        )
        self.assertEqual(
            raw[kg.NAME_BASE + 400 * 8:kg.NAME_BASE + 401 * 8],
            b"RPT-22\x00\x00",
        )
        self.assertEqual(struct.unpack_from("<I", last, 4)[0], 46755000)
        self.assertEqual(radio.get_memory(1).name, "GMRS-01")
        self.assertEqual(radio.get_memory(400).name, "RPT-22")

    def test_tones_modes_and_unknown_bits_are_preserved(self):
        image = _image()
        offset = kg.CHANNEL_BASE + 17 * 16
        image[offset:offset + 16] = struct.pack(
            "<IIHH", 46260000, 46760000, 0x83E8, 0x40E3
        ) + bytes.fromhex("ACFE0100")
        image[kg.NAME_BASE + 17 * 8:kg.NAME_BASE + 18 * 8] = b"TONE-17 "
        image[kg.VALID_BASE + 17] = kg.VALID_FLAG
        radio = self._radio(image)
        mem = radio.get_memory(17)
        self.assertEqual(mem.tmode, "Cross")
        self.assertEqual(mem.cross_mode, "DTCS->Tone")
        self.assertEqual(mem.dtcs, 343)
        self.assertEqual(mem.ctone, 100.0)
        self.assertEqual(mem.mode, "NAM")
        radio.set_memory(mem)
        changed = radio._packed()[offset:offset + 16]
        self.assertEqual(changed[12] & 0x0C, 0x0C)
        self.assertEqual(changed[12] & 0xF0, 0xA0)
        self.assertEqual(changed[13:16], b"\xFE\x01\x00")

    def test_rejects_non_gmrs_uploads_and_unknown_duplexes(self):
        radio = self._radio()
        with self.assertRaises(errors.InvalidValueError):
            radio.set_memory(_memory(1, freq=146520000))
        with self.assertRaises(errors.InvalidValueError):
            radio.set_memory(_memory(1, freq=440000000))
        with self.assertRaises(errors.InvalidValueError):
            radio.set_memory(_memory(1, duplex="+", offset=600000))
        with self.assertRaises(errors.InvalidValueError):
            radio.set_memory(_memory(
                1,
                freq=467550000,
                duplex="+",
                offset=5000000,
            ))
        with self.assertRaises(errors.InvalidValueError):
            radio.set_memory(_memory(401))
        with self.assertRaises(errors.InvalidValueError):
            radio.set_memory(_memory(1, name="TOO-LONG!"))

    def test_empty_channel_clears_record_name_and_valid_flag(self):
        radio = self._radio()
        radio.set_memory(_memory(31, name="DELETE"))
        radio.set_memory(_memory(31, empty=True))
        raw = radio._packed()
        offset = kg.CHANNEL_BASE + 31 * 16
        self.assertEqual(raw[offset:offset + 16], bytes(16))
        self.assertEqual(
            raw[kg.NAME_BASE + 31 * 8:kg.NAME_BASE + 32 * 8],
            bytes(8),
        )
        self.assertEqual(raw[kg.VALID_BASE + 31], 0)

    def test_upload_writes_only_official_program_ranges(self):
        image = _image()
        image[0x0440:0x04C0] = b"\x11" * 128
        image[0x3700:0x3728] = b"\x22" * 40
        serial = FakeKG905Serial(image)
        radio = self.radio_class(memmap.MemoryMapBytes(bytes(image)))
        radio.status_fn = lambda _status: None
        radio.pipe = serial

        radio.sync_out()

        expected = []
        for start, end in kg.WRITE_RANGES:
            expected.extend(range(start, end, kg.BLOCK_SIZE))
        self.assertEqual(serial.write_addresses, expected)
        self.assertEqual(serial.read_addresses, [0x0340, 0x0380, 0x03C0, 0x0400])
        self.assertNotIn(kg.SERIAL_DATA[0], serial.write_addresses)
        self.assertEqual(serial.writes[-1].hex(), "7c81ff00d7")
        self.assertEqual(bytes(serial.image[0x0440:0x04C0]), b"\x11" * 128)
        self.assertEqual(bytes(serial.image[0x3700:0x3728]), b"\x22" * 40)

    def test_truncated_or_foreign_image_cannot_write(self):
        radio = self._radio()
        serial = FakeKG905Serial(_image())
        radio.pipe = serial
        radio._mmap = memmap.MemoryMapBytes(bytes(_image()[:0x80]))
        with self.assertRaises(errors.InvalidDataError):
            radio.sync_out()
        self.assertEqual(serial.writes, [])

        foreign = _image()
        foreign[kg.MODEL_OFFSET:kg.MODEL_OFFSET + 16] = b"NOT-A-KG905G"
        radio._mmap = memmap.MemoryMapBytes(bytes(foreign))
        with self.assertRaises(errors.InvalidDataError):
            radio.sync_out()
        self.assertEqual(serial.writes, [])

    def test_match_model_requires_complete_supported_image(self):
        self.assertTrue(self.radio_class.match_model(bytes(_image()), "test.img"))
        self.assertFalse(
            self.radio_class.match_model(bytes(_image()[:0x100]), "test.img")
        )
        foreign = _image()
        foreign[kg.MODEL_OFFSET:kg.MODEL_OFFSET + 16] = b"NOT-A-KG905G"
        self.assertFalse(
            self.radio_class.match_model(bytes(foreign), "test.img")
        )


if __name__ == "__main__":
    unittest.main()
