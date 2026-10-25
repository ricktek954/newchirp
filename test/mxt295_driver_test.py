"""Round-trip tests for the experimental Midland MXT295 driver."""

from __future__ import annotations

import importlib.util
import struct
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
VENDOR = ROOT / "assets/python/pyserial-3.5-py2.py3-none-any.whl"
CAPTURES = Path("/Users/randybrown/Downloads/mxt295")


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
    "newchirp_chirp_bridge", ROOT / "scripts/chirp_bridge.py"
)
bridge = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = bridge
spec.loader.exec_module(bridge)
directory = bridge.load_chirp(str(SOURCE), str(VENDOR), str(ROOT / "drivers"))

from chirp import chirp_common  # noqa: E402
from chirp import errors  # noqa: E402
from chirp import memmap  # noqa: E402

mxt = sys.modules["newchirp.drivers.newchirp_mxt295"]


class FakePort:
    def __init__(self, replies):
        self.timeout = 0.25
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


def settings_radio(block):
    radio = blank_radio()
    packed = bytearray(radio._mmap.get_packed())
    packed[mxt.SETTINGS_ADDR:mxt.SETTINGS_ADDR + 32] = block
    return mxt.MXT295Radio(memmap.MemoryMapBytes(bytes(packed)))


def setting_by_name(radio, name):
    for group in radio.get_settings():
        for item in group:
            if item.get_name() == name:
                return item
    raise AssertionError(name)


def setting_values(radio):
    return {
        item.get_name(): str(item.value)
        for group in radio.get_settings()
        for item in group
    }


def choose(tree, name, value):
    for group in tree:
        for item in group:
            if item.get_name() == name:
                item.value = value
                return
    raise AssertionError(name)


def blank_radio():
    """An image shaped like a download: empty slots, FF padding, flag bits 0."""
    data = bytearray(b"\xff" * mxt.MEM_SIZE)
    for index in range(mxt.SLOT_COUNT):
        start = index * mxt.SLOT_SIZE
        data[start:start + 12] = b"\x00" * 12
        data[start + 12:start + 14] = b"\xff\xff"
        data[start + 14:start + 18] = b"\x00" * 4
        data[start + 18:start + 20] = b"\xff\xff"
        data[start + 20] = 0
    return mxt.MXT295Radio(memmap.MemoryMapBytes(bytes(data)))


def channel(number, **fields):
    mem = chirp_common.Memory()
    mem.number = number
    mem.freq = 462562500
    mem.duplex = ""
    mem.offset = 0
    mem.mode = "FM"
    mem.power = mxt.POWER_LOW
    mem.skip = ""
    mem.tmode = ""
    mem.tuning_step = 12.5
    for name, value in fields.items():
        setattr(mem, name, value)
    return mem


class MXT295DriverTest(unittest.TestCase):
    def test_radio_is_registered(self):
        radio_cls = directory.get_radio("Midland_MXT295")
        self.assertIs(radio_cls, mxt.MXT295Radio)
        prompts = radio_cls.get_prompts()
        self.assertEqual(prompts.experimental, "")
        self.assertIsNone(prompts.info)
        self.assertIn(
            "This driver for Midland radios is experimental.",
            prompts.pre_download,
        )
        self.assertIn(
            "keep a backup of your radio from the Midland program.",
            prompts.pre_download,
        )
        self.assertIn("1. Power the radio with 12 volts.", prompts.pre_download)
        self.assertIn("Turn the Bluetooth mic off.", prompts.pre_download)
        self.assertIn(
            "Plug the MXPG15 cable into the radio base.",
            prompts.pre_download,
        )
        self.assertIn("Click OK to download.", prompts.pre_download)
        self.assertEqual(
            prompts.pre_upload,
            "This Midland driver is experimental.  Make a backup of "
            "your radio before using this experimental driver to make "
            "any changes.",
        )

    def test_simplex_channel_round_trip(self):
        radio = blank_radio()
        radio.set_memory(channel(1, name="GMRS 1"))
        raw = bytes(radio._mmap[0:32])
        self.assertEqual(
            raw[:21],
            bytes.fromhex("474d5253203100001b9224c4ffff1b9224c4ffff18"),
        )
        self.assertEqual(raw[21:], b"\xff" * 11)

        mem = radio.get_memory(1)
        self.assertEqual(mem.name, "GMRS 1")
        self.assertEqual(mem.freq, 462562500)
        self.assertEqual(mem.duplex, "")
        self.assertEqual(mem.mode, "FM")
        self.assertEqual(mem.power, mxt.POWER_LOW)
        self.assertEqual(mem.skip, "")
        self.assertFalse(mem.empty)

    def test_repeater_and_receive_only(self):
        radio = blank_radio()
        radio.set_memory(channel(
            16,
            name="HIDESERT",
            freq=462550000,
            duplex="+",
            offset=5000000,
            tmode="DTCS",
            dtcs=423,
            power=mxt.POWER_HIGH,
            skip="S",
        ))
        raw = bytes(radio._mmap[15 * 32:16 * 32])
        self.assertEqual(
            raw[:21],
            bytes.fromhex("48494445534552541b91f3f029131bde3f3029130b"),
        )
        mem = radio.get_memory(16)
        self.assertEqual(mem.name, "HIDESERT")
        self.assertEqual(mem.duplex, "+")
        self.assertEqual(mem.offset, 5000000)
        self.assertEqual(mem.tmode, "DTCS")
        self.assertEqual(mem.dtcs, 423)
        self.assertEqual(mem.power, mxt.POWER_HIGH)
        self.assertEqual(mem.skip, "S")

        radio.set_memory(channel(8, freq=467562500, duplex="off", mode="NFM"))
        narrow = bytes(radio._mmap[7 * 32:8 * 32])
        self.assertEqual(narrow[8:12], bytes.fromhex("1bde7004"))
        self.assertEqual(narrow[12:20], bytes.fromhex("ffff00000000ffff"))
        self.assertEqual(narrow[20], 0x10)
        mem = radio.get_memory(8)
        self.assertEqual(mem.duplex, "off")
        self.assertEqual(mem.mode, "NFM")

    def test_split_privacy_codes(self):
        radio = blank_radio()
        radio.set_memory(channel(
            31,
            name="SANJCNTO",
            freq=462550000,
            duplex="+",
            offset=5000000,
            tmode="Cross",
            cross_mode="DTCS->DTCS",
            dtcs=606,
            rx_dtcs=306,
            power=mxt.POWER_HIGH,
            skip="S",
        ))
        mem = radio.get_memory(31)
        self.assertEqual(mem.tmode, "Cross")
        self.assertEqual(mem.cross_mode, "DTCS->DTCS")
        self.assertEqual(mem.dtcs, 606)
        self.assertEqual(mem.rx_dtcs, 306)

    def test_default_step_and_off_grid_frequency(self):
        radio = blank_radio()
        mem = channel(1, name="GMRS 1")
        mem.tuning_step = 5.0
        self.assertEqual(radio.validate_memory(mem), [])

        before = bytes(radio._mmap[0:32])
        off_grid = channel(1, name="GMRS 1", freq=462552500)
        self.assertTrue(radio.validate_memory(off_grid))
        with self.assertRaises(errors.InvalidValueError):
            radio.set_memory(off_grid)
        self.assertEqual(bytes(radio._mmap[0:32]), before)

    def test_clearing_a_repeater_row_puts_the_plain_frequency_back(self):
        radio = blank_radio()
        radio.set_memory(channel(
            30,
            name="CALICO",
            freq=462725000,
            duplex="+",
            offset=5000000,
            tmode="TSQL",
            ctone=77.0,
            skip="S",
            power=mxt.POWER_HIGH,
        ))
        programmed = radio.get_memory(30)
        programmed.empty = True
        radio.set_memory(programmed)
        restored = radio.get_memory(30)
        self.assertFalse(restored.empty)
        self.assertEqual(restored.name, "")
        self.assertEqual(restored.freq, 462725000)
        self.assertEqual(restored.duplex, "+")
        self.assertEqual(restored.offset, 5000000)
        self.assertEqual(restored.tmode, "")
        self.assertEqual(restored.skip, "S")
        self.assertEqual(restored.mode, "FM")
        self.assertEqual(restored.power, mxt.POWER_HIGH)

        radio.set_memory(channel(17, name="4X4", freq=462575000))
        normal = radio.get_memory(17)
        normal.empty = True
        radio.set_memory(normal)
        self.assertTrue(radio.get_memory(17).empty)

        for slot, rx_freq in mxt.PLAIN_REPEATER_RX.items():
            mem = radio.get_memory(slot)
            mem.empty = True
            radio.set_memory(mem)
            kept = radio.get_memory(slot)
            self.assertEqual(kept.freq, rx_freq)
            self.assertEqual(kept.duplex, "+")
            self.assertEqual(kept.offset, 5000000)
            self.assertFalse(kept.empty)

    def test_empty_slot_keeps_radio_padding_until_deleted(self):
        radio = blank_radio()
        before = bytes(radio._mmap[0:32])
        radio.set_memory(radio.get_memory(1))
        self.assertEqual(bytes(radio._mmap[0:32]), before)

        radio.set_memory(channel(1, name="GMRS 1"))
        mem = radio.get_memory(1)
        mem.empty = True
        radio.set_memory(mem)
        raw = bytes(radio._mmap[0:32])
        self.assertEqual(raw[:12], b"\x00" * 12)
        self.assertEqual(raw[12:14], b"\xff\xff")
        self.assertEqual(raw[20], 0)
        self.assertEqual(raw[21:], b"\x00" * 11)

    def test_gmrs_channels_reject_illegal_values(self):
        radio = blank_radio()
        features = radio.get_features()
        self.assertEqual(features.valid_duplexes, ["", "+", "off"])
        self.assertFalse(features.can_odd_split)
        self.assertEqual(radio.validate_memory(channel(1, name="GMRS 1")), [])

        wrong_channel = channel(1, freq=462550000)
        self.assertTrue(radio.validate_memory(wrong_channel))
        with self.assertRaises(errors.InvalidValueError) as caught:
            radio.set_memory(wrong_channel)
        self.assertIn("462.562500", str(caught.exception))

        with self.assertRaises(errors.InvalidValueError) as caught:
            radio.set_memory(channel(
                1, duplex="+", offset=5000000,
            ))
        self.assertIn("stay simplex", str(caught.exception))

        with self.assertRaises(errors.InvalidValueError) as caught:
            radio.set_memory(channel(1, duplex="off"))
        self.assertIn("stay simplex", str(caught.exception))

        with self.assertRaises(errors.InvalidValueError) as caught:
            radio.set_memory(channel(38, duplex="off"))
        self.assertIn("stay simplex", str(caught.exception))

        with self.assertRaises(errors.InvalidValueError) as caught:
            radio.set_memory(channel(8, freq=467562500, duplex=""))
        self.assertIn("receive only", str(caught.exception))

        with self.assertRaises(errors.InvalidValueError) as caught:
            radio.set_memory(channel(16, freq=462550000, duplex=""))
        self.assertIn("+5", str(caught.exception))

        with self.assertRaises(errors.InvalidValueError) as caught:
            radio.set_memory(channel(
                17, freq=462575000, duplex="+", offset=600000,
            ))
        self.assertIn("+5 MHz", str(caught.exception))

        with self.assertRaises(errors.InvalidValueError) as caught:
            radio.set_memory(channel(
                15, freq=462550000, duplex="-", offset=5000000,
            ))
        self.assertIn("only allows simplex", str(caught.exception))

        radio.set_memory(channel(
            17, freq=462575000, duplex="+", offset=5000000,
        ))
        stored = radio.get_memory(17)
        self.assertEqual(stored.duplex, "+")
        self.assertEqual(stored.offset, 5000000)

        radio.set_memory(channel(38, freq=462612500))
        extra = radio.get_memory(38)
        self.assertEqual(extra.freq, 462612500)
        self.assertEqual(extra.duplex, "")

        with self.assertRaises(errors.InvalidValueError) as caught:
            radio.set_memory(channel(
                38, freq=462612500, duplex="+", offset=5000000,
            ))
        self.assertIn("stay simplex", str(caught.exception))

    def test_rejected_edit_does_not_change_the_slot(self):
        radio = blank_radio()
        radio.set_memory(channel(1, name="GMRS 1"))
        before = bytes(radio._mmap[0:32])
        with self.assertRaises(errors.InvalidValueError):
            radio.set_memory(channel(1, name="GMRS 1", freq=146000000))
        with self.assertRaises(errors.InvalidValueError):
            radio.set_memory(channel(
                1, name="GMRS 1", tmode="DTCS", dtcs=23,
                dtcs_polarity="RR",
            ))
        with self.assertRaises(errors.InvalidValueError):
            radio.set_memory(channel(1, name="gmrs 1"))
        self.assertEqual(bytes(radio._mmap[0:32]), before)

    def test_download_and_upload_use_only_known_blocks(self):
        image = bytearray(b"\xff" * mxt.MEM_SIZE)
        image[0:21] = bytes.fromhex(
            "474d5253203100001b9224c4ffff1b9224c4ffff18"
        )
        image[mxt.SETTINGS_ADDR:mxt.SETTINGS_ADDR + 8] = bytes.fromhex(
            "0000010304001308"
        )
        replies = [b"\x06", b"SMP558\xff\xff", b"\x06"]
        for addr in mxt._block_addresses():
            command = bytes([
                0x52, (addr >> 8) & 0xFF, addr & 0xFF, 0x20,
            ])
            replies.append(command + bytes(image[addr:addr + 32]))
        port = FakePort(replies)
        radio = mxt.MXT295Radio(port)
        radio.sync_in()
        self.assertEqual(bytes(radio._mmap.get_packed()), bytes(image))
        self.assertEqual(port.writes[-1], b"\x62")

        port.writes.clear()
        port._replies = [b"\x06", b"SMP558\xff\xff", b"\x06"]
        port._replies.extend([b"\x06"] * len(mxt._block_addresses()))
        radio.sync_out()
        written = [
            item for item in port.writes
            if len(item) > 1 and item[0] == 0x57
        ]
        self.assertEqual(len(written), 108)
        addresses = [
            (item[1] << 8) | item[2] for item in written
        ]
        self.assertEqual(addresses, mxt._block_addresses())
        self.assertNotIn(0xD60, addresses)
        self.assertEqual(written[0][4:25], image[0:21])
        self.assertEqual(port.writes[-1], b"\x62")

    def test_unknown_radio_leaves_program_mode(self):
        port = FakePort([b"\x06", b"NOPE!!!!"])
        radio = mxt.MXT295Radio(port)
        with self.assertRaises(errors.RadioError):
            radio.sync_in()
        self.assertEqual(port.writes[-1], b"\x62")

    def test_no_answer_does_not_send_exit(self):
        port = FakePort([b"\x15"])
        radio = mxt.MXT295Radio(port)
        with self.assertRaises(errors.RadioError):
            radio.sync_in()
        self.assertNotIn(b"\x62", port.writes)

    def test_upload_requires_a_download(self):
        port = FakePort([])
        radio = mxt.MXT295Radio(port)
        with self.assertRaises(errors.RadioError):
            radio.sync_out()
        self.assertEqual(port.writes, [])

    def test_radio_settings_match_the_captured_bytes(self):
        block = bytes.fromhex("00000103040013080000") + (b"\xa5" * 22)
        radio = settings_radio(block)
        self.assertTrue(radio.get_features().has_settings)
        self.assertEqual(setting_values(radio), {
            "vox": "Off",
            "rogerbeep": "Off",
            "calltone": "1",
            "backlight": "3 Brightest",
            "backlightcolor": "5 Cyan",
            "repeat": "Disabled",
            "dw": "20",
            "sq": "8",
            "beep": "Off",
            "micgain": "1",
        })
        self.assertEqual(
            [mxt._midland_channel_label(index) for index in (
                0, 14, 15, 16, 29, 30, 106,
            )],
            ["1", "15", "RPTR 15", "16", "RPTR 22", "23", "99"],
        )

    def test_one_setting_changes_only_its_byte(self):
        block = bytes.fromhex("00000103040013080000") + (b"\xa5" * 22)
        radio = settings_radio(block)
        before = bytes(radio._mmap.get_packed())
        tree = radio.get_settings()
        choose(tree, "sq", "4")
        radio.set_settings(tree)
        after = bytearray(radio._mmap.get_packed())
        self.assertEqual(after[mxt.SETTINGS_ADDR + 7], 4)
        after[mxt.SETTINGS_ADDR + 7] = before[mxt.SETTINGS_ADDR + 7]
        self.assertEqual(bytes(after), before)

    def test_enabling_repeater_keeps_the_dual_watch_position(self):
        block = bytes.fromhex("00000103040013080000") + (b"\xa5" * 22)
        radio = settings_radio(block)
        tree = radio.get_settings()
        choose(tree, "repeat", "Enabled")
        radio.set_settings(tree)
        raw = bytes(radio._mmap.get_packed())
        self.assertEqual(raw[mxt.SETTINGS_ADDR + 5], 1)
        self.assertEqual(raw[mxt.SETTINGS_ADDR + 6], 0x13)
        self.assertEqual(setting_values(radio)["dw"], "RPTR 17")
        self.assertEqual(setting_values(radio)["repeat"], "Enabled")

    def test_unknown_setting_byte_is_not_rewritten(self):
        block = bytearray(bytes.fromhex("00000103040013080000") + (b"\xa5" * 22))
        block[9] = 9
        radio = settings_radio(bytes(block))
        mic = setting_by_name(radio, "micgain")
        self.assertFalse(mic.value.get_mutable())
        self.assertEqual(str(mic.value), "Stored value 9")
        tree = radio.get_settings()
        choose(tree, "beep", "On")
        radio.set_settings(tree)
        raw = bytes(radio._mmap.get_packed())
        self.assertEqual(raw[mxt.SETTINGS_ADDR + 8], 1)
        self.assertEqual(raw[mxt.SETTINGS_ADDR + 9], 9)
        self.assertEqual(raw[mxt.SETTINGS_ADDR + 10:mxt.SETTINGS_ADDR + 32], b"\xa5" * 22)


def _usb_payloads(path, endpoint, submit):
    data = path.read_bytes()
    offset = 24
    payloads = []
    while offset + 16 <= len(data):
        _ts, _usec, incl, _orig = struct.unpack_from("<IIII", data, offset)
        offset += 16
        packet = data[offset:offset + incl]
        offset += incl
        if len(packet) < 27:
            continue
        header_len = struct.unpack_from("<H", packet, 0)[0]
        info = packet[16]
        device = struct.unpack_from("<H", packet, 19)[0]
        ep = packet[21]
        data_len = struct.unpack_from("<I", packet, 23)[0]
        payload = packet[header_len:header_len + data_len]
        if device != 1 or ep != endpoint or not payload:
            continue
        if bool(info & 1) != submit:
            continue
        payloads.append(payload)
    return payloads


def _captured_read_image(path):
    image = bytearray(b"\xff" * mxt.MEM_SIZE)
    pending = None
    for payload in _usb_payloads(path, 0x82, True):
        if len(payload) == 32 and payload[0] == 0x52:
            pending = payload
        elif payload == b"\xff\xff\xff\xff" and pending is not None:
            addr = (pending[1] << 8) | pending[2]
            image[addr:addr + 32] = pending[4:] + payload
            pending = None
    return bytes(image)


def _captured_write_blocks(path):
    blocks = {}
    for payload in _usb_payloads(path, 0x02, False):
        if payload[:1] == b"\x57" and len(payload) == 36:
            addr = (payload[1] << 8) | payload[2]
            blocks[addr] = payload[4:]
    return blocks


@unittest.skipUnless(
    (CAPTURES / "295-read.pcap").is_file()
    and (CAPTURES / "295-write.pcap").is_file(),
    "MXT295 capture files are not on this Mac",
)
class MXT295CaptureTest(unittest.TestCase):
    def test_recording_round_trip(self):
        image = _captured_read_image(CAPTURES / "295-read.pcap")
        radio = mxt.MXT295Radio(memmap.MemoryMapBytes(image))
        first = radio.get_memory(1)
        self.assertEqual(first.name, "GMRS 1")
        self.assertEqual(first.freq, 462562500)
        self.assertEqual(first.duplex, "")

        hdesert = radio.get_memory(16)
        self.assertEqual(hdesert.name, "HIDESERT")
        self.assertEqual(hdesert.tmode, "DTCS")
        self.assertEqual(hdesert.dtcs, 423)
        self.assertEqual(hdesert.duplex, "+")

        before = bytes(radio._mmap.get_packed())
        for number in range(1, mxt.SLOT_COUNT + 1):
            radio.set_memory(radio.get_memory(number))
        self.assertEqual(bytes(radio._mmap.get_packed()), before)

        renamed = radio.get_memory(1)
        renamed.name = "GMRS1"
        radio.set_memory(renamed)
        written = _captured_write_blocks(CAPTURES / "295-write.pcap")
        self.assertEqual(bytes(radio._mmap[0:21]), written[0][:21])
        self.assertEqual(
            bytes(radio._mmap[mxt.SETTINGS_ADDR:mxt.SETTINGS_ADDR + 8]),
            image[mxt.SETTINGS_ADDR:mxt.SETTINGS_ADDR + 8],
        )


if __name__ == "__main__":
    unittest.main()
