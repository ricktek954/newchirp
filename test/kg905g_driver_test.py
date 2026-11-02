"""Offline tests for the experimental Wouxun KG-905G Plus driver."""

from __future__ import annotations

import importlib.util
import struct
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
VENDOR = ROOT / "assets/python/pyserial-3.5-py2.py3-none-any.whl"
READ_CAPTURE = Path("/Users/randybrown/Downloads/KG_905G_Plus/905GplusREAD.pcap")
WRITE_CAPTURE = Path("/Users/randybrown/Downloads/KG_905G_Plus/905GWRITE.pcap")


def chirp_source():
    for path in (
        ROOT / "build_support/chirp-20261016",
        ROOT / "build_support/chirp-20261023",
        ROOT.parent / "chirp-20260626",
    ):
        if (path / "chirp/chirp_common.py").is_file():
            return path
    raise RuntimeError("CHIRP source was not found")


SOURCE = chirp_source()
spec = importlib.util.spec_from_file_location(
    "newchirp_chirp_bridge_kg905g", ROOT / "scripts/chirp_bridge.py"
)
bridge = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = bridge
spec.loader.exec_module(bridge)
directory = bridge.load_chirp(str(SOURCE), str(VENDOR), str(ROOT / "drivers"))

from chirp import chirp_common  # noqa: E402
from chirp import errors  # noqa: E402
from chirp import memmap  # noqa: E402

kg = sys.modules["newchirp.drivers.newchirp_kg905g"]
kg.time.sleep = lambda *_args, **_kwargs: None


class FakePort:
    def __init__(self, replies):
        self.timeout = 0.25
        self.baudrate = 0
        self.dtr = False
        self.rts = True
        self.writes = []
        self._replies = [bytes(item) for item in replies]
        self._buffer = b""

    def write(self, data):
        self.writes.append(bytes(data))
        return len(data)

    def read(self, count):
        if not self._buffer and self._replies:
            self._buffer = self._replies.pop(0)
        chunk = self._buffer[:count]
        self._buffer = self._buffer[count:]
        return chunk

    def reset_input_buffer(self):
        return None


def radio_with(data, replies=()):
    radio = kg.KG905GPlusRadio(memmap.MemoryMapBytes(bytes(data)))
    radio.status_fn = lambda _status: None
    radio.pipe = FakePort(replies)
    return radio


def blank_image():
    data = bytearray(kg.MEM_SIZE)
    data[0x40:0x48] = kg.IDENT
    return data


def channel(number, **fields):
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


def frames_from(chunks):
    blob = b"".join(chunks)
    pos = 0
    found = []
    while pos + 4 <= len(blob):
        if blob[pos] != 0x7C:
            pos += 1
            continue
        length = blob[pos + 3]
        end = pos + 5 + length
        if end > len(blob):
            break
        found.append(blob[pos:end])
        pos = end
    return found


def usb_payloads(path, endpoint):
    data = Path(path).read_bytes()
    if data[:4] != b"\xd4\xc3\xb2\xa1":
        raise AssertionError("capture is not a little-endian pcap")
    offset = 24
    found = []
    while offset + 16 <= len(data):
        incl = struct.unpack_from("<I", data, offset + 8)[0]
        packet = data[offset + 16:offset + 16 + incl]
        offset += 16 + incl
        if len(packet) < 27:
            continue
        header_len = struct.unpack_from("<H", packet, 0)[0]
        function = struct.unpack_from("<H", packet, 14)[0]
        if function != 9 or packet[21] != endpoint or header_len > len(packet):
            continue
        length = struct.unpack_from("<I", packet, 23)[0]
        found.append(packet[header_len:header_len + length])
    return found


def read_reply(addr, payload):
    return kg.build_frame(0x82, 0x00, struct.pack(">H", addr) + payload)


def write_ack(addr):
    return kg.build_frame(0x83, 0x00, struct.pack(">H", addr))


def block_inside(start, length, blocks):
    end = start + length
    return any(addr <= start and end <= addr + size for addr, size in blocks)


class KG905GPlusDriverTest(unittest.TestCase):
    def test_radio_is_registered(self):
        radio_cls = directory.get_radio("Wouxun_KG-905G_Plus")
        self.assertIs(radio_cls, kg.KG905GPlusRadio)
        self.assertEqual(radio_cls.BAUD_RATE, 19200)
        self.assertTrue(radio_cls.WANTS_DTR)
        self.assertTrue(radio_cls.WANTS_RTS)
        self.assertFalse(radio_cls.NEEDS_COMPAT_SERIAL)
        prompts = radio_cls.get_prompts()
        self.assertIn("experimental", prompts.experimental.lower())
        self.assertIn("tested on a radio", prompts.experimental)
        self.assertIn("1 through 31", prompts.info)
        self.assertIn("32 through 400", prompts.info)
        features = radio_cls(None).get_features()
        self.assertEqual(features.memory_bounds, (1, 31))
        self.assertEqual(features.valid_duplexes, ["", "+"])
        self.assertNotIn("off", features.valid_duplexes)
        for freq in (462550000, 462725000, 467550000, 467725000):
            self.assertTrue(
                any(low <= freq < high for low, high in features.valid_bands),
                freq,
            )

    def test_probe_and_end_frames(self):
        probe = kg.build_frame(0x82, 0xFF, struct.pack(">HB", 0x0040, 64))
        self.assertEqual(probe.hex(), "7c82ff0354145453")
        end = kg.build_frame(0x81, 0xFF, b"")
        self.assertEqual(end.hex(), "7c81ff00d7")
        plain = kg.decrypt(probe[4:])
        self.assertEqual(plain[:3], b"\x00\x40\x40")

    def test_addresses_and_write_coverage(self):
        expected = {
            0: 0x06F0,
            1: 0x0700,
            2: 0x0710,
            3: 0x0520,
            18: 0x0610,
            19: 0x0420,
            30: 0x04D0,
        }
        for index, addr in expected.items():
            self.assertEqual(kg.channel_address(index), addr)
        self.assertEqual(len(kg.READ_BLOCKS), 172)
        self.assertEqual(len(kg.WRITE_BLOCKS), 168)
        skipped = {addr for addr, _size in kg.WRITE_BLOCKS}
        self.assertTrue(set(kg.WRITE_SKIP).isdisjoint(skipped))
        for index in range(kg.SLOT_COUNT):
            self.assertTrue(block_inside(
                kg.channel_address(index), kg.RECORD, kg.WRITE_BLOCKS
            ))
            self.assertTrue(block_inside(
                kg.NAME_BASE + index * kg.NAME_LEN, kg.NAME_LEN, kg.WRITE_BLOCKS
            ))
            self.assertTrue(block_inside(
                kg.VALID_BASE + index, 1, kg.WRITE_BLOCKS
            ))
        with self.assertRaises(IndexError):
            kg.channel_address(31)
        shadows = [
            (addr, kg.shadowed_slices(addr, size))
            for addr, size in kg.WRITE_BLOCKS
            if kg.shadowed_slices(addr, size)
        ]
        self.assertEqual(shadows, [(0x1BE0, ((0x20, 0x20),)), (0x1FE0, ((0x20, 0x20),))])

    def test_simplex_repeater_and_interstitial(self):
        radio = radio_with(blank_image())
        radio.set_memory(channel(1, name="GMRS-01"))
        record = radio._packed()[kg.channel_address(0):kg.channel_address(0) + 16]
        self.assertEqual(record[:8], struct.pack("<II", 46256250, 46256250))
        self.assertEqual(record[8:12], b"\x00\x00\x00\x00")
        self.assertEqual(record[12:16].hex(), "01210100")
        mem = radio.get_memory(1)
        self.assertEqual(mem.freq, 462562500)
        self.assertEqual(mem.duplex, "")
        self.assertEqual(mem.mode, "FM")
        self.assertEqual(mem.power, kg.POWER_HIGH)
        self.assertEqual(mem.skip, "")
        self.assertEqual(mem.name, "GMRS-01")
        self.assertFalse(mem.empty)

        radio.set_memory(channel(
            23,
            freq=462550000,
            duplex="+",
            offset=5000000,
            tmode="Cross",
            cross_mode="DTCS->DTCS",
            dtcs=423,
            rx_dtcs=343,
            dtcs_polarity="NN",
            skip="S",
        ))
        mem = radio.get_memory(23)
        self.assertEqual(mem.duplex, "+")
        self.assertEqual(mem.offset, 5000000)
        self.assertEqual(mem.tmode, "Cross")
        self.assertEqual(mem.cross_mode, "DTCS->DTCS")
        self.assertEqual(mem.dtcs, 423)
        self.assertEqual(mem.rx_dtcs, 343)
        self.assertEqual(mem.skip, "S")
        raw = radio._packed()[kg.channel_address(22):kg.channel_address(22) + 16]
        self.assertEqual(raw.hex(), "98cbc102b86cc902e340134101010100")

        radio.set_memory(channel(
            8,
            freq=467562500,
            mode="FM",
            power=kg.POWER_HIGH,
        ))
        mem = radio.get_memory(8)
        self.assertEqual(mem.freq, 467562500)
        self.assertEqual(mem.mode, "NFM")
        self.assertEqual(mem.power, kg.POWER_LOW)
        raw = radio._packed()[kg.channel_address(7):kg.channel_address(7) + 16]
        self.assertEqual(raw[12:16].hex(), "00200100")

    def test_preserves_unknown_flag_and_name_padding(self):
        data = blank_image()
        addr = kg.channel_address(0)
        data[addr:addr + 16] = struct.pack("<IIHH", 46256250, 46256250, 0, 0) + bytes.fromhex("01210100")
        data[addr + 13] = 0xA1
        data[kg.NAME_BASE:kg.NAME_BASE + 8] = b"GMRS-01 "
        data[kg.VALID_BASE] = kg.VALID_SET
        radio = radio_with(data)
        mem = radio.get_memory(1)
        self.assertEqual(mem.name, "GMRS-01")
        radio.set_memory(mem)
        raw = radio._packed()
        self.assertEqual(raw[addr + 13], 0xA1)
        self.assertEqual(raw[kg.NAME_BASE:kg.NAME_BASE + 8], b"GMRS-01 ")

    def test_rejects_non_gmrs_and_unmapped_slots(self):
        radio = radio_with(blank_image())
        with self.assertRaises(errors.InvalidValueError):
            radio.set_memory(channel(1, freq=146520000))
        with self.assertRaises(errors.InvalidValueError):
            radio.set_memory(channel(1, freq=440000000))
        with self.assertRaises(errors.InvalidValueError):
            radio.set_memory(channel(1, duplex="+", offset=600000))
        with self.assertRaises(errors.InvalidValueError):
            radio.set_memory(channel(1, freq=467550000, duplex="+", offset=5000000))
        with self.assertRaises(errors.InvalidValueError):
            radio.set_memory(channel(32))
        with self.assertRaises(errors.InvalidValueError):
            radio.set_memory(channel(1, name="GMRS 01!"))
        radio.set_memory(channel(31, name="GMRS-31"))
        radio.set_memory(channel(31, empty=True))
        mem = radio.get_memory(31)
        self.assertTrue(mem.empty)
        raw = radio._packed()
        self.assertEqual(raw[kg.channel_address(30):kg.channel_address(30) + 16], bytes(16))
        self.assertEqual(raw[kg.VALID_BASE + 30], 0)

    def test_upload_keeps_shadowed_block_and_skips_factory_bytes(self):
        data = blank_image()
        data[0x1BE0:0x1C20] = b"\xff" * 64
        data[0x1C00:0x1C20] = b"\x00" * 8 + b"GMRS-01 " + b"GMRS-02 "
        replies = [
            read_reply(0x0040, bytes(data[0x0040:0x0080])),
            read_reply(0x0080, bytes(64)),
            read_reply(0x00C0, bytes(64)),
            read_reply(0x0700, bytes(64)),
        ]
        replies.extend(write_ack(addr) for addr, _size in kg.WRITE_BLOCKS)
        radio = radio_with(data, replies)
        radio.sync_out()
        writes = [frame for frame in radio.pipe.writes if frame[1] == 0x83]
        self.assertEqual(len(writes), len(kg.WRITE_BLOCKS))
        for frame, (addr, size) in zip(writes, kg.WRITE_BLOCKS):
            plain = kg.decrypt(frame[4:])[:-1]
            self.assertEqual(((plain[0] << 8) | plain[1]), addr)
            self.assertEqual(len(plain) - 2, size)
            if addr == 0x1BE0:
                self.assertEqual(plain[2 + 0x20:], bytes(32))
            if addr == 0x1C00:
                self.assertEqual(plain[2:2 + 32], data[0x1C00:0x1C20])
        sent_addrs = set()
        for frame in writes:
            plain = kg.decrypt(frame[4:])[:-1]
            sent_addrs.add((plain[0] << 8) | plain[1])
        self.assertTrue(sent_addrs.isdisjoint(kg.WRITE_SKIP))
        self.assertEqual(radio.pipe.writes[-1].hex(), "7c81ff00d7")
        self.assertEqual(radio.pipe.dtr, True)
        self.assertEqual(radio.pipe.rts, True)

    def test_capture_round_trip(self):
        if not READ_CAPTURE.is_file():
            self.skipTest("KG-905G Plus read capture is not on this Mac")
        incoming = frames_from(usb_payloads(READ_CAPTURE, 0x81))
        outgoing = frames_from(usb_payloads(READ_CAPTURE, 0x01))
        self.assertEqual(len(incoming), 172)
        radio = kg.KG905GPlusRadio(FakePort(incoming))
        radio.status_fn = lambda _status: None
        radio.sync_in()
        self.assertEqual(radio.pipe.writes, outgoing)
        body, saved = kg.parse_trailer(radio._packed())
        self.assertTrue(body[0x40:0x48].startswith(kg.IDENT))
        self.assertEqual(saved[0x1BE0], [(0x20, bytes(32))])
        before = radio._packed()
        for number in range(1, 32):
            radio.set_memory(radio.get_memory(number))
        self.assertEqual(radio._packed(), before)

        mem = radio.get_memory(1)
        self.assertEqual(mem.freq, 462562500)
        self.assertEqual(mem.duplex, "")
        self.assertEqual(mem.mode, "FM")
        self.assertEqual(mem.power, kg.POWER_HIGH)
        self.assertEqual(mem.name, "GMRS-01")
        mem = radio.get_memory(3)
        self.assertEqual(mem.freq, 462612500)
        self.assertEqual(mem.tmode, "TSQL")
        self.assertEqual(mem.ctone, 67.0)
        mem = radio.get_memory(8)
        self.assertEqual(mem.freq, 467562500)
        self.assertEqual(mem.mode, "NFM")
        self.assertEqual(mem.power, kg.POWER_LOW)
        mem = radio.get_memory(15)
        self.assertEqual(mem.freq, 462550000)
        self.assertEqual(mem.power, kg.POWER_LOW)
        mem = radio.get_memory(23)
        self.assertEqual(mem.duplex, "+")
        self.assertEqual(mem.offset, 5000000)
        self.assertEqual(mem.cross_mode, "DTCS->DTCS")
        self.assertEqual((mem.dtcs, mem.rx_dtcs, mem.dtcs_polarity), (423, 343, "NN"))
        self.assertTrue(radio.get_memory(31).empty)
        programmed = [
            number for number in range(1, 32)
            if not radio.get_memory(number).empty
        ]
        self.assertEqual(programmed, list(range(1, 31)))

        read_blocks = {}
        for frame in incoming:
            plain = kg.decrypt(frame[4:])[:-1]
            addr = (plain[0] << 8) | plain[1]
            read_blocks[addr] = plain[2:]
        handshake = incoming[:4]
        acks = [write_ack(addr) for addr, _size in kg.WRITE_BLOCKS]
        radio.pipe = FakePort(list(handshake) + acks)
        radio.sync_out()
        uploaded = [frame for frame in radio.pipe.writes if frame[1] == 0x83]
        for frame, (addr, size) in zip(uploaded, kg.WRITE_BLOCKS):
            plain = kg.decrypt(frame[4:])[:-1]
            payload = plain[2:]
            self.assertNotIn(addr, kg.WRITE_SKIP)
            if addr == 0x1BE0:
                self.assertEqual(payload[:0x20], read_blocks[addr][:0x20])
                self.assertEqual(payload[0x20:], bytes(32))
                self.assertNotEqual(payload[0x20:], body[addr + 0x20:addr + size])
            else:
                self.assertEqual(payload, read_blocks[addr])

        if not WRITE_CAPTURE.is_file():
            return
        write_out = frames_from(usb_payloads(WRITE_CAPTURE, 0x01))
        self.assertEqual(write_out[-1].hex(), "7c81ff00d7")
        write_cmds = [frame for frame in write_out if frame[1] == 0x83]
        self.assertEqual(len(write_cmds), 168)
        for frame, (addr, _size) in zip(write_cmds, kg.WRITE_BLOCKS):
            plain = kg.decrypt(frame[4:])[:-1]
            self.assertEqual((plain[0] << 8) | plain[1], addr)


if __name__ == "__main__":
    unittest.main()
