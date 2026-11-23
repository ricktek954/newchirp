"""Offline tests for the read-only UV-K5 Robzyl RO-KO 512K profile.

Channel records are built with the encoding in the RO-KO firmware's
SETTINGS_SaveChannel (settings.c, commit a4ab1a0b).
"""

import importlib.util
from pathlib import Path
import struct
import sys
import unittest

from chirp_test_source import chirp_source


ROOT = Path(__file__).resolve().parent.parent
SOURCE = chirp_source()
PYTHON_VENDOR = ROOT / "assets/python/pyserial-3.5-py2.py3-none-any.whl"
MEM_SIZE = 0xA100


def _record(freq_hz, offset_hz=0, direction=0, rx=(0, 0), tx=(0, 0),
            modulation=0, bandwidth=0, power=2, step=4, scrambler=0):
    data = bytearray(16)
    struct.pack_into("<II", data, 0, freq_hz // 10, offset_hz // 10)
    data[8], data[9] = rx[1], tx[1]
    data[10] = (tx[0] << 4) | rx[0]
    data[11] = (modulation << 4) | direction
    data[12] = (power << 2) | ((bandwidth != 0) << 1)
    if bandwidth:
        data[12] |= (bandwidth - 1) << 5
    data[14], data[15] = step, scrambler
    return bytes(data)


def _image(eeprom_8k=False):
    image = bytearray(b"\xff" * MEM_SIZE)
    image[:0x2000] = bytes(range(256)) * 32

    def put(index, record, name, band, scanlist=0):
        image[0x2000 + index * 16:0x2010 + index * 16] = record
        image[0x5E80 + index] = (scanlist << 4) | band
        raw = name.encode().ljust(16, b"\x00")
        image[0x6280 + index * 16:0x6290 + index * 16] = raw

    # 146.520 FM wide, TSQL 100.0 (index 12), high power
    put(0, _record(146_520_000, rx=(1, 12), tx=(1, 12)), "SIMPLEX", 2, 1)
    # 442.100 +5 MHz, tone 55.0 (non-standard index 50), DCS 023N rx, NFM
    put(1, _record(442_100_000, 5_000_000, 1, rx=(2, 0), tx=(1, 50),
                   bandwidth=1, power=0, step=5), "RPT TEN 12", 5)
    # 118.000 AM narrow aviation; codes are ignored off FM
    put(2, _record(118_000_000, rx=(1, 3), modulation=1, bandwidth=2,
                   power=1, step=6), "TOWER", 1)
    # 14.200 SSB
    put(3, _record(14_200_000, modulation=2, step=7), "20M", 0)
    # band nibble 0x0F marks an unused slot even with data present
    put(4, _record(145_000_000), "GHOST", 0x0F)
    if eeprom_8k:
        for start in range(0x2000, MEM_SIZE, 0x2000):
            chunk = image[:0x2000][:MEM_SIZE - start]
            image[start:start + len(chunk)] = chunk
    return bytes(image)


class FakeRoKoSerial:
    def __init__(self, firmware=b"RO-KO V6.11", eeprom_8k=False):
        from chirp.drivers import uvk5
        self.uvk5 = uvk5
        self.firmware = firmware
        self.image = _image(eeprom_8k)
        self.rx = bytearray()
        self.writes = []
        self.timeout = 0.5

    def _reply(self, body):
        return (b"\xab\xcd" + bytes([len(body) & 0xFF, len(body) >> 8])
                + self.uvk5.xorarr(body) + b"\x00\x00\xdc\xba")

    def write(self, data):
        data = bytes(data)
        body = self.uvk5.xorarr(data[4:-4])
        self.writes.append(body)
        if body[:2] == b"\x14\x05":
            self.rx.extend(self._reply(
                b"\x15\x05\x24\x00" + self.firmware.ljust(32, b"\x00")))
        elif body[:2] == b"\x1b\x05":
            offset, length = struct.unpack("<HB", body[4:7])
            payload = self.image[offset:offset + length].ljust(length, b"\xff")
            self.rx.extend(self._reply(
                b"\x1c\x05" + bytes([length + 4, 0])
                + struct.pack("<HBB", offset, length, 0) + payload))
        return len(data)

    def read(self, size):
        chunk, self.rx = bytes(self.rx[:size]), self.rx[size:]
        return chunk

    def log(self, _message):
        pass


class UVK5RoKo512KTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location(
            "newchirp_chirp_bridge_roko", ROOT / "scripts/chirp_bridge.py")
        bridge = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = bridge
        spec.loader.exec_module(bridge)
        cls.directory = bridge.load_chirp(
            str(SOURCE), str(PYTHON_VENDOR), str(ROOT / "drivers"))
        cls.radio_class = cls.directory.get_radio(
            "Quansheng_UV-K5_RO-KO_512K")

    def _read(self, serial):
        radio = self.radio_class(serial)
        radio.status_fn = None
        radio.sync_in()
        return radio

    def test_registered_read_only(self):
        self.assertTrue(self.radio_class.NEWCHIRP_WRITE_DISABLED)
        features = self.radio_class(None).get_features()
        self.assertEqual(features.memory_bounds, (1, 999))
        self.assertEqual(features.valid_name_length, 10)

    def test_decodes_channels_per_firmware(self):
        radio = self._read(FakeRoKoSerial())
        first = radio.get_memory(1)
        self.assertEqual((first.freq, first.name, first.mode, first.tmode,
                          first.ctone, str(first.power)),
                         (146_520_000, "SIMPLEX", "FM", "TSQL", 100.0, "High"))
        self.assertEqual(str(first.extra["scanlist"].value), "1")

        rpt = radio.get_memory(2)
        self.assertEqual((rpt.freq, rpt.duplex, rpt.offset, rpt.mode,
                          rpt.tuning_step, rpt.name, str(rpt.power)),
                         (442_100_000, "+", 5_000_000, "NFM", 25.0,
                          "RPT TEN 12", "Low"))
        self.assertEqual((rpt.tmode, rpt.cross_mode, rpt.rtone, rpt.rx_dtcs),
                         ("Cross", "Tone->DTCS", 55.0, 23))

        tower = radio.get_memory(3)
        self.assertEqual((tower.mode, tower.tmode, tower.tuning_step),
                         ("NAM", "", 8.33))
        self.assertEqual(str(tower.extra["bandwidth"].value),
                         "Narrow aviation")
        ssb = radio.get_memory(4)
        self.assertEqual((ssb.freq, ssb.mode, ssb.tuning_step),
                         (14_200_000, "USB", 0.01))
        self.assertTrue(radio.get_memory(5).empty)
        self.assertTrue(radio.get_memory(999).empty)

    def test_reads_whole_512k_map_and_never_writes(self):
        serial = FakeRoKoSerial()
        radio = self._read(serial)
        reads = [body for body in serial.writes if body[:2] == b"\x1b\x05"]
        self.assertEqual(len(reads), MEM_SIZE // 0x80)
        self.assertFalse([b for b in serial.writes if b[:2] == b"\x1d\x05"])
        count = len(serial.writes)
        with self.assertRaisesRegex(Exception, "not enabled"):
            radio.sync_out()
        self.assertEqual(len(serial.writes), count)

    def test_refuses_other_firmware(self):
        with self.assertRaisesRegex(Exception, "RO-KO 512K firmware"):
            self._read(FakeRoKoSerial(firmware=b"F4HWN v4.3"))

    def test_refuses_8k_eeprom_that_wraps(self):
        with self.assertRaisesRegex(Exception, "repeats every 8 KB"):
            self._read(FakeRoKoSerial(eeprom_8k=True))


if __name__ == "__main__":
    unittest.main()
