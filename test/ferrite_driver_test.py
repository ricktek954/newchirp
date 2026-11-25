"""Offline tests for the Ferrite (RT-950 Pro) link-protocol driver.

The fake radio follows FerriteFW/docs appendix G (protocol 1): COBS frames
with CRC-16/CCITT-FALSE, HELLO, READ_MANY, WRITE_MANY, BEGIN and END.
"""

import importlib.util
import struct
import sys
import tempfile
import unittest
from pathlib import Path

from chirp_test_source import chirp_source

ROOT = Path(__file__).resolve().parent.parent
SOURCE = chirp_source()
VENDOR = ROOT / "assets/python/pyserial-3.5-py2.py3-none-any.whl"
MODEL = "Radtel_RT-950_Pro_Ferrite"


def _load_bridge():
    spec = importlib.util.spec_from_file_location(
        "newchirp_chirp_bridge_ferrite", ROOT / "scripts/chirp_bridge.py"
    )
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


def _channel(driver, index, rx_mhz, name, **kw):
    fields = [
        index, kw.get("zone", 0xFFFF), int(round(rx_mhz * 100000)),
        name.encode("ascii"), kw.get("mode", 1), 1,
        kw.get("rx_tone", 0), kw.get("tx_tone", 0), kw.get("offset", 0),
        kw.get("power", 2), 10, kw.get("squelch", 10), 0,
        kw.get("revsplit", 0), kw.get("flags", 0), kw.get("tones", 0x09),
    ]
    return driver.RECORD.pack(*fields)


def _zone(name):
    return name.encode("ascii").ljust(16, b"\x00") + bytes(
        [1, 1, 0, 0, 0, 0]) + b"\xff\xff\xff\xff" + b"\x02\x00"


class FakeFerrite:
    """A radio running Ferrite on the end of the programming cable."""

    def __init__(self, driver, channels, zones, protocol=1, layout=3,
                 may_go_on=1, busy_once=False, invalid_index=None):
        self.d = driver
        self.channels = dict(channels)
        self.zones = dict(zones)
        self.protocol = protocol
        self.layout = layout
        self.may_go_on = may_go_on
        self.busy_once = busy_once
        self.invalid_index = invalid_index
        self.rx = bytearray()
        self.tx = bytearray()
        self.linked = False
        self.requests = []
        self.written = []
        self.baudrate = 0
        self.in_waiting = 0

    def write(self, data):
        for byte in bytes(data):
            if not self.linked:
                if byte == 0:
                    self.linked = True
                continue
            if byte:
                self.rx.append(byte)
                continue
            raw, self.rx = bytes(self.rx), bytearray()
            if raw:
                self._handle(raw)
        return len(data)

    def read(self, count):
        out = bytes(self.tx[:count])
        del self.tx[:len(out)]
        return out

    def _answer(self, kind, seq, status, payload=b""):
        self.tx += self.d.encode_frame(
            kind | 0x80, seq, bytes([status]) + payload)

    def _handle(self, raw):
        frame = self.d.decode_frame(raw)
        if frame is None:
            return  # a stray byte (the 0x03 that ends a terminal session)
        kind, seq, payload = frame
        self.requests.append(kind)
        if kind == self.d.HELLO:
            version = b"0.9.3"
            self._answer(kind, seq, 0, bytes([
                self.protocol, 240, self.may_go_on, len(version)
            ]) + version + bytes([1, 0, 3, self.layout]) + b"\x01\x02\x03\x04")
        elif kind in (self.d.BEGIN, self.d.END):
            self._answer(kind, seq, 0)
        elif kind == self.d.READ_MANY:
            what, first, count = struct.unpack("<BHH", payload)
            table = self.channels if what == 2 else self.zones
            # Appendix G: the count is cut at the last index. Zones are
            # numbered densely ("the next one creates"), so the range ends
            # after the last zone held and an ask past it answers next ==
            # first with no records (2026-11-25 RT-950 Pro report).
            last = 4000 if what == 2 else (max(table) + 1 if table else 0)
            end = max(first, min(first + count, last))
            body, index = b"", first
            while index < end:
                record = table.get(index)
                if record is not None:
                    item = struct.pack("<HB", index, len(record)) + record
                    if len(body) + len(item) > 236:
                        break
                    body += item
                index += 1
            self._answer(kind, seq, 0, struct.pack("<H", index) + body)
        elif kind == self.d.WRITE_MANY:
            what, body = payload[0], payload[1:]
            assert what == 2
            applied = 0
            while body:
                index, length = struct.unpack("<HB", body[:3])
                record = body[3:3 + length]
                body = body[3 + length:]
                if self.busy_once:
                    self.busy_once = False
                    self._answer(kind, seq, 7, bytes([applied]))
                    return
                if index == self.invalid_index:
                    self._answer(kind, seq, 9, bytes([applied])
                                 + b"power: this channel is RX only")
                    return
                self.written.append((index, bytes(record)))
                if length:
                    self.channels[index] = bytes(record)
                else:
                    self.channels.pop(index, None)
                applied += 1
            self._answer(kind, seq, 0, bytes([applied]))
        else:
            self._answer(kind, seq, 2)


class FerriteDriverTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bridge = _load_bridge()
        cls.directory = cls.bridge.load_chirp(
            str(SOURCE), str(VENDOR), str(ROOT / "drivers")
        )
        cls.radio_class = cls.directory.get_radio(MODEL)
        cls.d = sys.modules[cls.radio_class.__module__]

    def setUp(self):
        self.d.time.sleep = lambda _s: None

    def sample(self):
        d = self.d
        channels = {
            0: _channel(d, 0, 146.52, "CALL", mode=0, power=2),
            4: _channel(d, 4, 145.29, "W1AW RPT", offset=-60000,
                        tx_tone=1000, rx_tone=1000, zone=1),
            7: _channel(d, 7, 446.00625, "PMR 1", flags=d.FLAG_SKIP,
                        tx_tone=0x8000 | 0o23, rx_tone=0x8000 | 0o23),
            3999: _channel(d, 3999, 121.5, "GUARD", mode=7,
                           flags=d.FLAG_RX_ONLY),
        }
        zones = {0: _zone("Local nets"), 1: _zone("Repeaters")}
        return channels, zones

    def read_radio(self, fake):
        radio = self.radio_class(None)
        radio.pipe = fake
        radio.status_fn = lambda _s: None
        radio.sync_in()
        return radio

    def test_registered_as_its_own_model(self):
        self.assertEqual(self.radio_class.VARIANT, "Ferrite")
        self.assertNotEqual(
            self.directory.get_radio("Radtel_RT-950_Pro_nicFW950"),
            self.radio_class)
        self.assertIn("Ferrite", self.radio_class.get_prompts().experimental)

    def test_frame_round_trip_and_crc(self):
        d = self.d
        self.assertEqual(d.crc16(b"123456789"), 0x29B1)
        for payload in (b"", b"\x00", b"\x00\x00\x01", bytes(range(240))):
            raw = d.encode_frame(0x17, 9, payload)
            self.assertEqual(raw.count(0), 1)
            self.assertEqual(d.decode_frame(raw[:-1]), (0x17, 9, payload))
        self.assertIsNone(d.decode_frame(b"ferrite> help"))

    def test_read_decodes_channels_tones_and_zones(self):
        channels, zones = self.sample()
        radio = self.read_radio(FakeFerrite(self.d, channels, zones))
        call = radio.get_memory(1)
        self.assertEqual((call.freq, call.name, call.mode, call.duplex),
                         (146520000, "CALL", "FM", ""))
        self.assertEqual(str(call.power), "High")
        rpt = radio.get_memory(5)
        self.assertEqual((rpt.duplex, rpt.offset, rpt.tmode, rpt.ctone),
                         ("-", 600000, "TSQL", 100.0))
        self.assertEqual(str(rpt.extra[0].value), "Repeaters")
        pmr = radio.get_memory(8)
        self.assertEqual((pmr.tmode, pmr.dtcs, pmr.skip),
                         ("DTCS", 23, "S"))
        guard = radio.get_memory(4000)
        self.assertEqual((guard.mode, guard.duplex), ("NAM", "off"))
        self.assertTrue(radio.get_memory(2).empty)

    def test_refuses_other_protocol_pin_lock_and_pending_update(self):
        from chirp import errors
        channels, zones = self.sample()
        for kwargs, text in (
            ({"protocol": 2}, "protocol 2"),
            ({"may_go_on": 0}, "PIN lock"),
            ({"layout": 255}, "Ferrite Console"),
        ):
            with self.assertRaisesRegex(errors.RadioError, text):
                self.read_radio(FakeFerrite(self.d, channels, zones,
                                            **kwargs))

    def test_unchanged_channels_round_trip_byte_for_byte(self):
        channels, zones = self.sample()
        radio = self.read_radio(FakeFerrite(self.d, channels, zones))
        before = radio.get_mmap().get_packed()
        for number in (1, 5, 8, 4000):
            radio.set_memory(radio.get_memory(number))
        self.assertEqual(radio.get_mmap().get_packed(), before)

    def test_write_sends_only_changes_from_a_saved_image(self):
        channels, zones = self.sample()
        radio = self.read_radio(FakeFerrite(self.d, channels, zones))
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "ferrite.img"
            radio.save_mmap(str(path))
            radio = self.directory.get_radio_by_image(str(path))
            radio.load_mmap(str(path))
        edited = radio.get_memory(5)
        edited.name = "W1AW/R*"
        edited.rtone = edited.ctone = 123.0
        radio.set_memory(edited)
        new = radio.get_memory(2)
        new.empty = False
        new.freq = 446006250
        new.name = "NEW"
        new.mode = "NFM"
        radio.set_memory(new)
        gone = radio.get_memory(8)
        gone.empty = True
        radio.set_memory(gone)

        fake = FakeFerrite(self.d, channels, zones, busy_once=True)
        radio.pipe = fake
        radio.status_fn = lambda _s: None
        radio.sync_out()
        self.assertEqual([index for index, _ in fake.written], [1, 4, 7])
        self.assertEqual(fake.written[2], (7, b""))
        self.assertEqual(fake.channels[4][8:24].rstrip(b"\x00"),
                         b"W1AW/R-")
        self.assertEqual(struct.unpack("<HH", fake.channels[4][26:30]),
                         (1230, 1230))
        self.assertIn(self.d.BEGIN, fake.requests)
        self.assertEqual(fake.requests[-1], self.d.READ_MANY)
        self.assertNotIn(7, fake.channels)

    def test_same_saved_image_written_twice_is_safe(self):
        channels, zones = self.sample()
        radio = self.read_radio(FakeFerrite(self.d, channels, zones))
        mem = radio.get_memory(1)
        mem.name = "SIMPLEX"
        radio.set_memory(mem)
        stale = radio.get_mmap().get_packed()
        fake = FakeFerrite(self.d, channels, zones)
        radio.pipe = fake
        radio.status_fn = lambda _s: None
        radio.sync_out()
        self.assertEqual([i for i, _ in fake.written], [0])
        # The baseline moved forward: nothing left to send.
        self.assertEqual(self.d.channel_changes(
            radio.get_mmap().get_packed()), [])
        # A copy saved before the write (stale baseline) is recognised as
        # already on the radio rather than refused or sent again.
        from chirp import memmap
        again = self.radio_class(memmap.MemoryMapBytes(stale))
        again.pipe = fake
        again.status_fn = lambda _s: None
        fake.written.clear()
        again.sync_out()
        self.assertEqual(fake.written, [])
        self.assertNotIn(self.d.BEGIN, fake.requests[-3:])

    def test_write_refuses_when_radio_changed_since_read(self):
        from chirp import errors
        channels, zones = self.sample()
        radio = self.read_radio(FakeFerrite(self.d, channels, zones))
        mem = radio.get_memory(1)
        mem.name = "EDIT"
        radio.set_memory(mem)
        changed = dict(channels)
        changed[0] = _channel(self.d, 0, 146.55, "OTHER")
        fake = FakeFerrite(self.d, changed, zones)
        radio.pipe = fake
        with self.assertRaisesRegex(errors.RadioError, "Channel 1 changed"):
            radio.sync_out()
        self.assertEqual(fake.written, [])
        self.assertNotIn(self.d.WRITE_MANY, fake.requests)

    def test_radio_refusal_names_channel_and_ends_session(self):
        from chirp import errors
        channels, zones = self.sample()
        radio = self.read_radio(FakeFerrite(self.d, channels, zones))
        mem = radio.get_memory(4000)
        mem.power = radio.get_features().valid_power_levels[2]
        mem.name = "AIR"
        radio.set_memory(mem)
        fake = FakeFerrite(self.d, channels, zones, invalid_index=3999)
        radio.pipe = fake
        with self.assertRaisesRegex(errors.RadioError,
                                    "Channel 4000: power: this channel"):
            radio.sync_out()
        self.assertEqual(fake.requests[-1], self.d.END)

    def test_zone_choice_writes_zone_index(self):
        channels, zones = self.sample()
        radio = self.read_radio(FakeFerrite(self.d, channels, zones))
        mem = radio.get_memory(1)
        zone = next(s for s in mem.extra if s.get_name() == "zone")
        zone.value = "Local nets"
        radio.set_memory(mem)
        record = radio._record(1)
        self.assertEqual(struct.unpack("<H", record[2:4])[0], 0)


if __name__ == "__main__":
    unittest.main()
