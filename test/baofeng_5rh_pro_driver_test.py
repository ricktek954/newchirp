"""Offline protocol and image tests for the Baofeng 5RH Pro v2 driver."""

from collections import deque
import importlib
import importlib.util
from pathlib import Path
import sys
import unittest


from chirp_test_source import chirp_source


ROOT = Path(__file__).resolve().parent.parent
SOURCE = chirp_source()
PYTHON_VENDOR = ROOT / "assets/python/pyserial-3.5-py2.py3-none-any.whl"


def _load_bridge():
    spec = importlib.util.spec_from_file_location(
        "newchirp_chirp_bridge_baofeng_5rh_pro",
        ROOT / "scripts/chirp_bridge.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load chirp_bridge.py")
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


class FakeSessionSerial:
    def __init__(self, announce_baud=19200, plain_sync=False):
        self.announce_baud = announce_baud
        # UV-5RM Pro (CPS 5RH Pro v1.12): only a plain-text "PROGRAM" works.
        self.plain_sync = plain_sync
        self.baudrate = 115200
        self.timeout = 0.25
        self.seed = None
        self.responses = deque()
        self.writes = []
        self.baudrates = []
        self.resets = 0

    def reset_input_buffer(self):
        self.resets += 1

    def write(self, data):
        data = bytes(data)
        self.writes.append(data)
        self.baudrates.append(self.baudrate)

        if data == self.module.T_INFO:
            if self.baudrate == self.announce_baud:
                self.responses.append(b"A")
            return

        if len(data) == 8 and data[:-1] == b"PROGRAM" and self.plain_sync:
            self.seed = data[-1]
            self.responses.append(bytes([self.seed ^ 0x41]))
            return

        if (
            len(data) == 8
            and data[:-1] == self.module._xor_seed(b"PROGRAM", data[-1])
        ):
            if self.plain_sync:
                self.responses.append(b"N")   # 2026-11-24 UV-5RM Pro trace
                return
            self.seed = data[-1]
            self.responses.append(bytes([self.seed ^ 0x41]))
            return

        if data == bytes([self.seed ^ 0xFF]) * 8:
            self.responses.append(bytes([self.seed ^ 0x41]))
            return

        if data == self.module._xor_seed(b"INFORMATION", self.seed):
            model = b"BF-K6".ljust(16, b"\xFF")
            self.responses.append(
                self.module._xor_seed(model, self.seed)
            )
            return

        if len(data) == 1 and data[0] in (
            self.seed ^ 0x52,
            self.seed ^ 0x57,
        ):
            self.responses.append(bytes([self.seed ^ 0x41]))
            return

        if (
            len(data) == 4
            and data[0] ^ self.seed == 0x52
        ):
            offset = ((data[1] ^ self.seed) << 8) | (
                data[2] ^ self.seed
            )
            payload = bytes(
                (offset + index) & 0xFF
                for index in range(self.module.BLOCK_SIZE)
            )
            self.responses.append(
                data + self.module._xor_seed(payload, self.seed)
            )
            return

        if (
            len(data) == self.module.BLOCK_SIZE + 4
            and data[0] ^ self.seed == 0x57
        ):
            self.responses.append(bytes([self.seed ^ 0x41]))
            return

        if data == self.module._xor_seed(self.module.END_INFO, self.seed):
            self.responses.append(bytes([self.seed ^ 0x41]))
            return

        raise AssertionError("Unexpected write: %r" % data[:16])

    def read(self, size):
        result = bytearray()
        while self.responses and len(result) < size:
            chunk = self.responses[0]
            take = min(size - len(result), len(chunk))
            result.extend(chunk[:take])
            if take == len(chunk):
                self.responses.popleft()
            else:
                self.responses[0] = chunk[take:]
        return bytes(result)


class Baofeng5RHProDriverTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        bridge = _load_bridge()
        cls.directory = bridge.load_chirp(
            str(SOURCE),
            str(PYTHON_VENDOR),
            str(ROOT / "drivers"),
        )
        cls.radio_class = cls.directory.get_radio("Baofeng_UV-5RH_Pro")
        cls.driver = importlib.import_module(cls.radio_class.__module__)
        FakeSessionSerial.module = cls.driver

    def _empty_radio(self):
        from chirp import memmap

        image = bytearray(b"\xFF" * self.driver.DATA_LEN)
        image[0x50:0x58] = b"v2_0_09\xff"
        image[0x58:0x60] = b"v1_0_4\xff\xff\xff"
        return self.radio_class(memmap.MemoryMapBytes(bytes(image)))

    def test_model_family_and_features(self):
        for model in (
            "Baofeng_5RH_Pro",
            "Baofeng_UV-5RH_Pro",
            "Baofeng_UV-5RH_Plus",
            "Baofeng_UV-5RM_Plus_v2",
        ):
            self.assertTrue(
                issubclass(
                    self.directory.get_radio(model),
                    self.driver.Baofeng5RHPro,
                )
            )

        features = self.radio_class(None).get_features()
        self.assertEqual(features.memory_bounds, (1, 640))
        self.assertTrue(features.has_sub_devices)
        self.assertEqual(features.valid_name_length, 16)
        self.assertIn("AM", features.valid_modes)

    def test_handshake_falls_back_to_19200_and_uses_cps_seed(self):
        serial = FakeSessionSerial(announce_baud=19200)
        radio = self.radio_class(serial)

        seed = self.driver._handshake(radio, seed=0x5A)

        self.assertEqual(seed, 0x5A)
        self.assertEqual(serial.baudrates[:2], [115200, 19200])
        self.assertEqual(serial.resets, 2)
        self.assertEqual(
            serial.writes[2],
            self.driver._xor_seed(b"PROGRAM", seed) + bytes([seed]),
        )
        self.assertEqual(serial.writes[3], bytes([seed ^ 0xFF]) * 8)
        self.assertEqual(
            serial.writes[4],
            self.driver._xor_seed(b"INFORMATION", seed),
        )
        self.assertEqual(serial.writes[5], bytes([seed ^ 0x52]))

    def test_uv5rm_pro_plain_sync_fallback_like_cps_v112(self):
        serial = FakeSessionSerial(announce_baud=19200, plain_sync=True)
        radio = self.radio_class(serial)

        seed = self.driver._handshake(radio, seed=0x5A)

        syncs = [w for w in serial.writes if len(w) == 8 and w[-1] == seed]
        self.assertEqual(syncs[0], self.driver._xor_seed(b"PROGRAM", seed) + b"\x5a")
        self.assertEqual(syncs[1], b"PROGRAM\x5a")
        self.assertTrue(radio._plain_sync)
        self.assertEqual(serial.writes[-1], bytes([seed ^ 0x52]))

        # The write in the same session goes straight to the plain sync.
        serial.writes.clear()
        self.driver._handshake(radio, is_write=True, seed=0x33)
        syncs = [w for w in serial.writes if len(w) == 8 and w[-1] == 0x33]
        self.assertEqual(syncs, [b"PROGRAM\x33"])

    def test_stray_byte_before_the_sync_ack_is_skipped_like_cps_v112(self):
        """CPS v1.12 keeps reading after a byte that is not seed ^ 'A'; a
        UV-5RM Pro answers the sync with "N" first (2026-11-26, UID 1046)."""

        class NThenAck(FakeSessionSerial):
            def write(self, data):
                data = bytes(data)
                if len(data) == 8 and data[:-1] == self.module._xor_seed(
                        b"PROGRAM", data[-1]):
                    self.writes.append(data)
                    self.seed = data[-1]
                    self.responses.append(b"N" + bytes([self.seed ^ 0x41]))
                    return
                return super().write(data)

        serial = NThenAck(announce_baud=19200)
        radio = self.radio_class(serial)
        seed = self.driver._handshake(radio, seed=0x5A)
        self.assertEqual(seed, 0x5A)
        syncs = [w for w in serial.writes if len(w) == 8 and w[-1] == seed]
        self.assertEqual(len(syncs), 1, "no second sync form needed")
        self.assertFalse(radio._plain_sync)

    def test_xored_sync_radios_never_see_the_plain_form(self):
        serial = FakeSessionSerial(announce_baud=115200)
        radio = self.radio_class(serial)
        self.driver._handshake(radio, seed=0x21)
        self.assertNotIn(b"PROGRAM!", serial.writes)
        self.assertFalse(radio._plain_sync)

    def test_uv5rm_pro_announces_at_19200_first_like_cps_v112(self):
        """CPS v1.12 ships Setting.ini baudrate=19200 and starts there."""
        pro = self.directory.get_radio("Baofeng_UV-5RM_Pro")
        serial = FakeSessionSerial(announce_baud=19200, plain_sync=True)
        radio = pro(serial)
        self.driver._handshake(radio, seed=0x5A)
        self.assertEqual(serial.baudrates[0], 19200)
        self.assertNotIn(115200, serial.baudrates[:2])

    def test_uv5rm_pro_is_listed(self):
        self.assertIsNotNone(self.directory.get_radio("Baofeng_UV-5RM_Pro"))

    def test_uv5rm_pro_graduated_without_experimental_prompt(self):
        """2026-11-27 owner write + read-back (mailbox UID 1080)."""
        pro = self.directory.get_radio("Baofeng_UV-5RM_Pro")
        self.assertIsNone(pro.get_prompts().experimental)
        self.assertIsNotNone(pro.get_prompts().pre_download)
        sibling = self.directory.get_radio("Baofeng_UV-5RH_Pro")
        self.assertIsNotNone(sibling.get_prompts().experimental)

    def test_stray_announce_reply_advises_a_power_cycle(self):
        """2026-11-19 report: after failed attempts with the older profile
        the radio sent a stray byte until it was power-cycled."""
        from chirp import errors

        class Stray(FakeSessionSerial):
            def write(self, data):
                if bytes(data) == self.module.T_INFO:
                    self.writes.append(bytes(data))
                    if self.baudrate == 19200:
                        self.responses.append(b"\x03")
                    return
                return super().write(data)

        radio = self.radio_class(Stray(announce_baud=None))
        with self.assertRaisesRegex(errors.RadioError,
                                    r"0x03.*turn the radio off and on"):
            self.driver._handshake(radio, seed=0x5A)

    def test_silent_radio_points_to_cable_and_port(self):
        from chirp import errors
        radio = self.radio_class(FakeSessionSerial(announce_baud=None))
        with self.assertRaisesRegex(errors.RadioNoResponse,
                                    "cable is fully inserted"):
            self.driver._handshake(radio, seed=0x5A)

    def test_read_uses_twelve_encrypted_4096_byte_blocks(self):
        serial = FakeSessionSerial(announce_baud=115200)
        radio = self.radio_class(serial)
        serial.seed = 0x33

        data = self.driver._read_blocks(radio, serial.seed)

        self.assertEqual(len(data), 49152)
        self.assertEqual(data[:4], b"\x00\x01\x02\x03")
        self.assertEqual(
            data[4092:4096],
            bytes(value & 0xFF for value in (4092, 4093, 4094, 4095)),
        )
        self.assertEqual(
            serial.writes[-1],
            self.driver._xor_seed(b"END\x00", serial.seed),
        )
        self.assertEqual(len(serial.writes), 13)

    def test_write_uses_twelve_encrypted_4096_byte_blocks(self):
        serial = FakeSessionSerial(announce_baud=115200)
        radio = self.radio_class(serial)
        serial.seed = 0x44
        image = bytes(index & 0xFF for index in range(self.driver.DATA_LEN))

        self.driver._write_blocks(radio, image, serial.seed)

        self.assertEqual(len(serial.writes), 13)
        for block, packet in enumerate(serial.writes[:12]):
            self.assertEqual(len(packet), self.driver.BLOCK_SIZE + 4)
            decoded = self.driver._xor_seed(packet, serial.seed)
            offset = block * self.driver.BLOCK_SIZE
            self.assertEqual(
                decoded[:4],
                bytes((0x57, offset >> 8, offset & 0xFF, 0)),
            )
            self.assertEqual(
                decoded[4:],
                image[offset:offset + self.driver.BLOCK_SIZE],
            )
        self.assertEqual(
            serial.writes[-1],
            self.driver._xor_seed(b"END\x00", serial.seed),
        )

    def test_channel_and_zone_round_trip(self):
        from chirp import chirp_common

        radio = self._empty_radio()
        radio._memobj.chn_unused[0] = 0
        channel = chirp_common.Memory()
        channel.number = 1
        channel.name = "LOW CASE"
        channel.freq = 462_562_500
        channel.duplex = "+"
        channel.offset = 5_000_000
        channel.mode = "NFM"
        channel.power = radio.get_features().valid_power_levels[1]
        channel.tmode = "Tone"
        channel.rtone = 100.0

        radio.set_memory(channel)
        decoded = radio.get_memory(1)

        self.assertEqual(decoded.name, "LOW CASE")
        self.assertEqual(decoded.freq, 462_562_500)
        self.assertEqual(decoded.duplex, "+")
        self.assertEqual(decoded.offset, 5_000_000)
        self.assertEqual(decoded.mode, "NFM")
        self.assertEqual(str(decoded.power), "High")
        self.assertEqual(decoded.tmode, "Tone")
        self.assertEqual(decoded.rtone, 100.0)

        radio._rebuild_zones()
        self.assertEqual(int(radio._memobj.zones[0].count), 1)
        self.assertEqual(int(radio._memobj.zones[0].channels[0]), 0)
        self.assertEqual(radio.get_sub_devices()[0].VARIANT, "Zone 1")


    def test_zone_feature_bit_limits_zones_like_the_cps(self):
        from chirp import memmap

        radio = self._empty_radio()
        self.assertTrue(radio.zones_enabled())
        self.assertEqual(len(radio.get_sub_devices()), 10)

        data = bytearray(radio._mmap.get_packed())
        data[self.driver.DEVICE_FEATURES_OFFSET] &= ~0x04
        radio = self.radio_class(memmap.MemoryMapBytes(bytes(data)))
        self.assertFalse(radio.zones_enabled())
        zones = radio.get_sub_devices()
        self.assertEqual(len(zones), 1)
        self.assertEqual(zones[0].get_features().memory_bounds, (1, 64))

    def test_zone_two_edit_lands_in_zone_two(self):
        # 2026-11-19 report: writes made in zone 2 or 3 appeared in zone 1.
        from chirp import chirp_common

        radio = self._empty_radio()
        zone2 = radio.get_sub_devices()[1]
        channel = chirp_common.Memory()
        channel.number = 1
        channel.freq = 146_520_000
        channel.name = "ZONE2"
        zone2.set_memory(channel)
        radio._rebuild_zones()

        self.assertTrue(radio.get_memory(1).empty)
        self.assertEqual(radio.get_memory(65).name, "ZONE2")
        self.assertEqual(int(radio._memobj.zones[0].count), 0)
        self.assertEqual(int(radio._memobj.zones[1].count), 1)
        self.assertEqual(int(radio._memobj.zones[1].channels[0]), 64)
        self.assertEqual(int(radio._memobj.zones_used), 1)

if __name__ == "__main__":
    unittest.main()
