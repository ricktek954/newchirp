# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Wouxun KG-905G Plus experimental clone driver.

The radio answers as KG-905G+ at 19200 8N1. Frames use the Wouxun
rolling-XOR link with seed 0x54 and the four-step checksum adjustment.
Reads are 64-byte blocks, with a few shorter tails. Writes use the same
blocks except the factory identity and one overlapping read. Two write
blocks cover the same addresses and return different bytes; the extra
trailer keeps the earlier read so a channel name is not copied into it.

This capture proves memory slots 1 through 31. The radio offers 400
slots. Slots 32 through 400 are not mapped here, because their bytes
were not in a pattern that could be checked against the read.
"""

import struct
import time

from chirp import chirp_common
from chirp import directory
from chirp import errors
from chirp import memmap

IDENT = b"KG-905G+"
MEM_SIZE = 0x3700
SLOT_COUNT = 31
NAME_BASE = 0x1C08
NAME_LEN = 8
VALID_BASE = 0x3301
VALID_SET = 0x9E
SEED = 0x54
RECORD = 16
REPEATER_OFFSET = 5_000_000

# Factory identity is read so the model can be checked. It is never written.
# 0x0700 overlaps the 0x06E0 write, so the extra read is not written back.
WRITE_SKIP = (0x0040, 0x0080, 0x00C0, 0x0700)

# Address, byte count. Order matches the Wouxun program's read.
READ_BLOCKS = (
    (0x0040, 64), (0x0080, 64), (0x00C0, 64), (0x0700, 64), (0x0740, 64),
    (0x0780, 64), (0x0640, 16), (0x06E0, 64), (0x0520, 64), (0x0560, 64),
    (0x05A0, 64), (0x05E0, 64), (0x0420, 64), (0x0460, 64), (0x04A0, 64),
    (0x04E0, 64), (0x0B20, 64), (0x0B60, 64), (0x0BA0, 64), (0x0BE0, 64),
    (0x0A20, 64), (0x0A60, 64), (0x0AA0, 64), (0x0AE0, 64), (0x0920, 64),
    (0x0960, 64), (0x09A0, 64), (0x09E0, 64), (0x0820, 64), (0x0860, 64),
    (0x08A0, 64), (0x08E0, 64), (0x0F20, 64), (0x0F60, 64), (0x0FA0, 64),
    (0x0FE0, 64), (0x0E20, 64), (0x0E60, 64), (0x0EA0, 64), (0x0EE0, 64),
    (0x0D20, 64), (0x0D60, 64), (0x0DA0, 64), (0x0DE0, 64), (0x0C20, 64),
    (0x0C60, 64), (0x0CA0, 64), (0x0CE0, 64), (0x1320, 64), (0x1360, 64),
    (0x13A0, 64), (0x13E0, 64), (0x1220, 64), (0x1260, 64), (0x12A0, 64),
    (0x12E0, 64), (0x1120, 64), (0x1160, 64), (0x11A0, 64), (0x11E0, 64),
    (0x1020, 64), (0x1060, 64), (0x10A0, 64), (0x10E0, 64), (0x1720, 64),
    (0x1760, 64), (0x17A0, 64), (0x17E0, 64), (0x1620, 64), (0x1660, 64),
    (0x16A0, 64), (0x16E0, 64), (0x1520, 64), (0x1560, 64), (0x15A0, 64),
    (0x15E0, 64), (0x1420, 64), (0x1460, 64), (0x14A0, 64), (0x14E0, 64),
    (0x1B20, 64), (0x1B60, 64), (0x1BA0, 64), (0x1BE0, 64), (0x1A20, 64),
    (0x1A60, 64), (0x1AA0, 64), (0x1AE0, 64), (0x1920, 64), (0x1960, 64),
    (0x19A0, 64), (0x19E0, 64), (0x1820, 64), (0x1860, 64), (0x18A0, 64),
    (0x18E0, 64), (0x1F20, 64), (0x1F60, 64), (0x1FA0, 64), (0x1FE0, 64),
    (0x1E20, 64), (0x1E60, 64), (0x1EA0, 64), (0x1EE0, 64), (0x1D20, 64),
    (0x1D60, 64), (0x1DA0, 64), (0x1DE0, 16), (0x1C00, 64), (0x1C40, 64),
    (0x1C80, 64), (0x1CC0, 64), (0x2300, 64), (0x2340, 64), (0x2380, 64),
    (0x23C0, 64), (0x2200, 64), (0x2240, 64), (0x2280, 64), (0x22C0, 64),
    (0x2100, 64), (0x2140, 64), (0x2180, 64), (0x21C0, 64), (0x2000, 64),
    (0x2040, 64), (0x2080, 64), (0x20C0, 64), (0x2700, 64), (0x2740, 64),
    (0x2780, 64), (0x27C0, 64), (0x2600, 64), (0x2640, 64), (0x2680, 64),
    (0x26C0, 64), (0x2500, 64), (0x2540, 64), (0x2580, 64), (0x25C0, 64),
    (0x2400, 64), (0x2440, 64), (0x2480, 64), (0x24C0, 64), (0x2B00, 64),
    (0x2B40, 64), (0x2B80, 64), (0x2BC0, 64), (0x2A00, 64), (0x2A40, 64),
    (0x2A80, 64), (0x2AC0, 64), (0x2900, 64), (0x2940, 64), (0x2980, 64),
    (0x29C0, 64), (0x2800, 64), (0x2840, 64), (0x2880, 8), (0x3300, 64),
    (0x3340, 64), (0x3380, 64), (0x33C0, 64), (0x3200, 64), (0x3240, 64),
    (0x3280, 17), (0x3400, 40), (0x3060, 64), (0x30A0, 62), (0x36C0, 64),
    (0x3500, 64), (0x3540, 40),
)
WRITE_BLOCKS = tuple(block for block in READ_BLOCKS if block[0] not in WRITE_SKIP)
# Two captured reads can cover the same addresses and still return different
# bytes. The image keeps the later read. A write of the earlier block must
# send that earlier read, which is stored after the image.
TRAILER_MAGIC = b"KG905OVL"

POWER_LOW = chirp_common.PowerLevel("Low", watts=0.5)
POWER_HIGH = chirp_common.PowerLevel("High", watts=5.0)
POWER_LEVELS = [POWER_LOW, POWER_HIGH]
CHARSET = (
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789- "
)

# GMRS simplex: channels 1-7, 15-22, and the seven 467 MHz interstitial
# channels. Values are Hertz.
SIMPLEX_HZ = (
    462562500, 462587500, 462612500, 462637500, 462662500, 462687500,
    462712500, 462550000, 462575000, 462600000, 462625000, 462650000,
    462675000, 462700000, 462725000, 467562500, 467587500, 467612500,
    467637500, 467662500, 467687500, 467712500,
)
REPEATER_RX_HZ = (
    462550000, 462575000, 462600000, 462625000, 462650000, 462675000,
    462700000, 462725000,
)
INTERSTITIAL_HZ = (
    467562500, 467587500, 467612500, 467637500, 467662500, 467687500,
    467712500,
)


def shadowed_slices(addr, size):
    """Parts of a write block that a later write block also covers."""
    end = addr + size
    found = []
    for other, other_size in WRITE_BLOCKS:
        if other <= addr or other >= end:
            continue
        overlap_end = min(end, other + other_size)
        found.append((other - addr, overlap_end - other))
    return tuple(found)


def trailer_for(blocks):
    """Remember the earlier read where two write blocks overlap."""
    chunks = []
    for addr, size in WRITE_BLOCKS:
        data = blocks.get(addr)
        if data is None:
            continue
        for offset, length in shadowed_slices(addr, size):
            chunks.append(struct.pack("<HHH", addr, offset, length))
            chunks.append(data[offset:offset + length])
    if not chunks:
        return b""
    return TRAILER_MAGIC + struct.pack("<H", len(chunks) // 2) + b"".join(chunks)


def parse_trailer(image):
    """Return the image body and any saved overlap slices."""
    if len(image) < MEM_SIZE or image[MEM_SIZE:MEM_SIZE + len(TRAILER_MAGIC)] != TRAILER_MAGIC:
        return image[:MEM_SIZE], {}
    pos = MEM_SIZE + len(TRAILER_MAGIC)
    if pos + 2 > len(image):
        raise errors.RadioError("KG-905G Plus image trailer is truncated")
    count = struct.unpack_from("<H", image, pos)[0]
    pos += 2
    saved = {}
    for _ in range(count):
        if pos + 6 > len(image):
            raise errors.RadioError("KG-905G Plus image trailer is truncated")
        addr, offset, length = struct.unpack_from("<HHH", image, pos)
        pos += 6
        if pos + length > len(image):
            raise errors.RadioError("KG-905G Plus image trailer is truncated")
        saved.setdefault(addr, []).append((offset, image[pos:pos + length]))
        pos += length
    return image[:MEM_SIZE], saved


def write_payload(image, addr, size, saved):
    """Bytes to send for one write block.

    Where a later block covers the same addresses, keep the earlier read.
    A captured radio returned zeros there, and the Wouxun program wrote
    those zeros back. Filling from the flat image would copy channel names
    into that other block.
    """
    data = bytearray(image[addr:addr + size])
    if len(data) < size:
        data.extend(bytes(size - len(data)))
    slices = saved.get(addr)
    if slices is None:
        slices = [(offset, bytes(length)) for offset, length in shadowed_slices(addr, size)]
    for offset, original in slices:
        if offset < 0 or offset + len(original) > size:
            raise errors.RadioError("KG-905G Plus image trailer is invalid")
        data[offset:offset + len(original)] = original
    return bytes(data)


def channel_address(index):
    """Physical address of one 16-byte channel record.

    Slot 1 starts 13 records into the first 16-channel block. Each
    following block sits 256 bytes lower.
    """
    if not 0 <= index < SLOT_COUNT:
        raise IndexError(index)
    adjusted = index + 13
    slot = adjusted % 16
    block = adjusted // 16
    return 0x620 + (slot * RECORD) - (block * 0x100)


def encrypt(plain, seed=SEED):
    if not plain:
        return b""
    out = bytearray(len(plain))
    out[0] = seed ^ plain[0]
    for i in range(1, len(plain)):
        out[i] = out[i - 1] ^ plain[i]
    return bytes(out)


def decrypt(encoded, seed=SEED):
    if not encoded:
        return b""
    out = bytearray(len(encoded))
    out[0] = seed ^ encoded[0]
    for i in range(1, len(encoded)):
        out[i] = encoded[i - 1] ^ encoded[i]
    return bytes(out)


def checksum(cmd, direction, length, payload):
    total = (cmd + direction + length + sum(payload)) & 0xFF
    adjust = {0: 3, 1: 1, 2: -1, 3: -3}[(payload[0] if payload else 0) & 0x03]
    return (total + adjust) & 0xFF


def build_frame(cmd, direction, payload):
    check = checksum(cmd, direction, len(payload), payload)
    return bytes([0x7C, cmd, direction, len(payload)]) + encrypt(payload + bytes([check]))


def _decode_tone(word):
    kind = (word >> 12) & 0x0F
    low = word & 0x0FFF
    if kind == 0 or word == 0:
        return "", None, None
    if kind == 8:
        return "Tone", low / 10.0, None
    if kind in (4, 6):
        for code in chirp_common.DTCS_CODES:
            if int(str(code), 8) == low:
                return "DTCS", code, "N" if kind == 4 else "R"
    return "", None, None


def _encode_tone(mode, value, polarity):
    if not mode:
        return 0
    if mode == "Tone":
        tenths = int(round(float(value) * 10))
        if tenths <= 0 or tenths > 0x0FFF:
            raise errors.InvalidValueError("That CTCSS tone is out of range")
        return 0x8000 + tenths
    if mode == "DTCS":
        if int(value) not in chirp_common.DTCS_CODES:
            raise errors.InvalidValueError("DCS code %s is not supported" % value)
        base = 0x6000 if polarity == "R" else 0x4000
        return base + int(str(int(value)), 8)
    raise errors.InvalidValueError("Tone mode %s is not supported" % mode)


def _tones_from_memory(mem):
    tx_mode, tx_val, tx_pol = "", None, "N"
    rx_mode, rx_val, rx_pol = "", None, "N"
    if mem.tmode == "Tone":
        tx_mode, tx_val = "Tone", mem.rtone
    elif mem.tmode == "TSQL":
        tx_mode, tx_val = "Tone", mem.ctone
        rx_mode, rx_val = "Tone", mem.ctone
    elif mem.tmode == "DTCS":
        tx_pol = mem.dtcs_polarity[0] if mem.dtcs_polarity else "N"
        rx_pol = mem.dtcs_polarity[1] if mem.dtcs_polarity else "N"
        tx_mode, tx_val, tx_pol = "DTCS", mem.dtcs, tx_pol
        rx_mode, rx_val, rx_pol = "DTCS", mem.rx_dtcs or mem.dtcs, rx_pol
    elif mem.tmode == "Cross":
        left, right = (mem.cross_mode or "->").split("->")
        if left == "Tone":
            tx_mode, tx_val = "Tone", mem.rtone
        elif left == "DTCS":
            tx_pol = mem.dtcs_polarity[0] if mem.dtcs_polarity else "N"
            tx_mode, tx_val, tx_pol = "DTCS", mem.dtcs, tx_pol
        if right == "Tone":
            rx_mode, rx_val = "Tone", mem.ctone
        elif right == "DTCS":
            rx_pol = mem.dtcs_polarity[1] if mem.dtcs_polarity else "N"
            rx_mode, rx_val, rx_pol = "DTCS", mem.rx_dtcs or mem.dtcs, rx_pol
    elif mem.tmode:
        raise errors.InvalidValueError("Tone mode %s is not supported" % mem.tmode)
    return (
        _encode_tone(tx_mode, tx_val, tx_pol),
        _encode_tone(rx_mode, rx_val, rx_pol),
    )


def _apply_tones(mem, rx_word, tx_word):
    rx_mode, rx_val, rx_pol = _decode_tone(rx_word)
    tx_mode, tx_val, tx_pol = _decode_tone(tx_word)
    mem.tmode = ""
    mem.cross_mode = "Tone->Tone"
    mem.dtcs_polarity = "NN"
    if tx_mode == "Tone" and not rx_mode:
        mem.tmode = "Tone"
        mem.rtone = tx_val
    elif tx_mode == "Tone" and rx_mode == "Tone" and tx_val == rx_val:
        mem.tmode = "TSQL"
        mem.rtone = tx_val
        mem.ctone = rx_val
    elif tx_mode == "DTCS" and rx_mode == "DTCS" and tx_val == rx_val and tx_pol == rx_pol:
        mem.tmode = "DTCS"
        mem.dtcs = tx_val
        mem.rx_dtcs = rx_val
        mem.dtcs_polarity = tx_pol + rx_pol
    elif tx_mode or rx_mode:
        mem.tmode = "Cross"
        left = tx_mode if tx_mode else ""
        right = rx_mode if rx_mode else ""
        mem.cross_mode = "%s->%s" % (left, right)
        if tx_mode == "Tone":
            mem.rtone = tx_val
        if rx_mode == "Tone":
            mem.ctone = rx_val
        if tx_mode == "DTCS":
            mem.dtcs = tx_val
        if rx_mode == "DTCS":
            mem.rx_dtcs = rx_val
        mem.dtcs_polarity = (tx_pol or "N") + (rx_pol or "N")


def _tx_hz(mem):
    freq = int(mem.freq)
    if mem.duplex in ("", " "):
        if freq not in SIMPLEX_HZ:
            raise errors.InvalidValueError(
                "Simplex must be a GMRS channel frequency"
            )
        if int(mem.offset or 0) not in (0,):
            raise errors.InvalidValueError("Simplex offset must be 0")
        return freq
    if mem.duplex == "+":
        if freq not in REPEATER_RX_HZ:
            raise errors.InvalidValueError(
                "A repeater must use a GMRS repeater output"
            )
        if int(mem.offset) != REPEATER_OFFSET:
            raise errors.InvalidValueError("Repeater offset must be +5 MHz")
        return freq + REPEATER_OFFSET
    raise errors.InvalidValueError(
        "This radio accepts simplex or a +5 MHz GMRS repeater"
    )


@directory.register
class KG905GPlusRadio(chirp_common.CloneModeRadio,
                      chirp_common.ExperimentalRadio):
    """Wouxun KG-905G Plus"""

    VENDOR = "Wouxun"
    MODEL = "KG-905G Plus"
    BAUD_RATE = 19200
    NEEDS_COMPAT_SERIAL = False
    WANTS_DTR = True
    WANTS_RTS = True
    _memsize = MEM_SIZE

    @classmethod
    def get_prompts(cls):
        prompts = chirp_common.RadioPrompts()
        prompts.experimental = (
            "The KG-905G Plus driver is experimental. A read and one "
            "channel-name write were tested on a radio. Keep a backup from "
            "the Wouxun program before you upload."
        )
        prompts.info = (
            "Use a Wouxun K-plug programming cable. The link is 19200 "
            "baud, 8 data bits, no parity, and one stop bit. Memories "
            "1 through 31 can be edited. Memories 32 through 400 are not "
            "mapped yet."
        )
        prompts.pre_download = (
            "1. Power on the KG-905G Plus.\n"
            "2. Plug in the programming cable.\n"
            "3. Close the Wouxun program so it releases the port.\n"
            "4. Click OK to download."
        )
        prompts.pre_upload = (
            "Uploading replaces the channels in the radio. Make a backup "
            "with the Wouxun program first. Memories 32 through 400 are "
            "left as they were read."
        )
        return prompts

    def get_features(self):
        rf = chirp_common.RadioFeatures()
        rf.has_bank = False
        rf.has_settings = False
        rf.has_name = True
        rf.has_tuning_step = False
        rf.has_nostep_tuning = True
        rf.has_rx_dtcs = True
        rf.has_ctone = True
        rf.has_cross = True
        rf.can_odd_split = False
        rf.memory_bounds = (1, SLOT_COUNT)
        # The upper value is exclusive. 462.725 MHz is a real GMRS channel,
        # and its repeater input is 467.725 MHz.
        rf.valid_bands = [
            (462550000, 462725001),
            (467550000, 467725001),
        ]
        rf.valid_modes = ["FM", "NFM"]
        rf.valid_power_levels = list(POWER_LEVELS)
        rf.valid_tuning_steps = [12.5]
        rf.valid_duplexes = ["", "+"]
        rf.valid_tmodes = ["", "Tone", "TSQL", "DTCS", "Cross"]
        rf.valid_cross_modes = list(chirp_common.CROSS_MODES)
        rf.valid_skips = ["", "S"]
        rf.valid_dtcs_codes = list(chirp_common.DTCS_CODES)
        rf.valid_dtcs_pols = ["NN", "NR", "RN", "RR"]
        rf.valid_characters = CHARSET
        rf.valid_name_length = NAME_LEN
        return rf

    def process_mmap(self):
        return

    def sync_in(self):
        try:
            self._prepare_port()
            self._mmap = memmap.MemoryMapBytes(bytes(self._download()))
        except errors.RadioError:
            raise
        except Exception as exc:
            raise errors.RadioError(
                "Failed to communicate with radio: %s" % exc
            ) from exc
        self.process_mmap()

    def sync_out(self):
        try:
            self._prepare_port()
            self._upload()
        except errors.RadioError:
            raise
        except Exception as exc:
            raise errors.RadioError(
                "Failed to communicate with radio: %s" % exc
            ) from exc

    def get_memory(self, number):
        index = self._index(number)
        raw = self._packed()
        addr = channel_address(index)
        record = raw[addr:addr + RECORD]
        rx, tx, rx_tone, tx_tone = struct.unpack_from("<IIHH", record)
        mem = chirp_common.Memory()
        mem.number = number
        name = raw[NAME_BASE + index * NAME_LEN:NAME_BASE + (index + 1) * NAME_LEN]
        mem.name = name.split(b"\x00", 1)[0].decode("ascii", "replace").rstrip()
        if rx == 0 or raw[VALID_BASE + index] == 0:
            mem.empty = True
            return mem
        mem.freq = rx * 10
        if tx == rx:
            mem.duplex = ""
            mem.offset = 0
        elif tx == rx + (REPEATER_OFFSET // 10) and mem.freq in REPEATER_RX_HZ:
            mem.duplex = "+"
            mem.offset = REPEATER_OFFSET
        else:
            # The capture has no odd split. Leave the bytes untouched until
            # this channel is edited. An edit stores simplex or +5 MHz only.
            mem.duplex = ""
            mem.offset = 0
            mem.freq = rx * 10
        power = record[12] & 0x03
        mem.power = POWER_LOW if power == 0 else POWER_HIGH
        wide = record[13] & 0x01
        mem.mode = "FM" if wide else "NFM"
        mem.skip = "" if (record[13] & 0x20) else "S"
        _apply_tones(mem, rx_tone, tx_tone)
        return mem

    def set_memory(self, mem):
        index = self._index(mem.number)
        raw = bytearray(self._packed())
        addr = channel_address(index)
        if mem.empty or not mem.freq:
            raw[addr:addr + RECORD] = bytes(RECORD)
            raw[NAME_BASE + index * NAME_LEN:NAME_BASE + (index + 1) * NAME_LEN] = bytes(NAME_LEN)
            raw[VALID_BASE + index] = 0
            self._mmap = memmap.MemoryMapBytes(bytes(raw))
            return
        tx_hz = _tx_hz(mem)
        rx_hz = int(mem.freq)
        if mem.mode not in ("FM", "NFM", None, ""):
            raise errors.InvalidValueError("Mode must be FM or NFM")
        wide = mem.mode != "NFM"
        power = 0 if mem.power == POWER_LOW else 1
        if rx_hz in INTERSTITIAL_HZ:
            wide = False
            power = 0
        scan = mem.skip != "S"
        tx_tone, rx_tone = _tones_from_memory(mem)
        current = bytearray(raw[addr:addr + RECORD])
        if current == bytes(RECORD):
            current = bytearray(bytes.fromhex("00000000000000000000000001210100"))
        struct.pack_into("<IIHH", current, 0, rx_hz // 10, tx_hz // 10, rx_tone, tx_tone)
        current[12] = (current[12] & 0xFC) | power
        flags = current[13] & 0xDE
        if wide:
            flags |= 0x01
        if scan:
            flags |= 0x20
        current[13] = flags
        if current[14] == 0:
            current[14] = 1
        raw[addr:addr + RECORD] = current
        name_at = NAME_BASE + index * NAME_LEN
        raw[name_at:name_at + NAME_LEN] = self._name_bytes(
            mem.name, bytes(raw[name_at:name_at + NAME_LEN])
        )
        raw[VALID_BASE + index] = VALID_SET
        self._mmap = memmap.MemoryMapBytes(bytes(raw))

    def _index(self, number):
        if not 1 <= int(number) <= SLOT_COUNT:
            raise errors.InvalidValueError(
                "Memory %s is outside 1-%s" % (number, SLOT_COUNT)
            )
        return int(number) - 1

    def _packed(self):
        if self._mmap is None:
            raise errors.RadioError("Download from the radio before editing")
        return self._mmap.get_packed()

    def _name_bytes(self, name, previous):
        text = "" if name is None else str(name)
        try:
            raw = text.encode("ascii")
        except UnicodeEncodeError as exc:
            raise errors.InvalidValueError("Channel name must be plain text") from exc
        if len(raw) > NAME_LEN:
            raise errors.InvalidValueError("Channel name is limited to 8 characters")
        if any(chr(byte) not in CHARSET for byte in raw):
            raise errors.InvalidValueError("Channel name has a character this radio does not store")
        stored = previous.split(b"\x00", 1)[0].decode("ascii", "replace").rstrip()
        if stored == text:
            return previous
        return raw.ljust(NAME_LEN, b"\x00")

    def _prepare_port(self):
        self.pipe.baudrate = self.BAUD_RATE
        self.pipe.timeout = 2
        try:
            self.pipe.dtr = True
            self.pipe.rts = True
        except Exception:
            pass
        reset = getattr(self.pipe, "reset_input_buffer", None)
        if reset:
            reset()
        time.sleep(0.2)

    def _status(self, message, current, total):
        if not self.status_fn:
            return
        status = chirp_common.Status()
        status.msg = message
        status.cur = current
        status.max = total
        self.status_fn(status)

    def _read_exact(self, size):
        data = bytearray()
        deadline = time.monotonic() + 2
        while len(data) < size:
            chunk = self.pipe.read(size - len(data))
            if chunk:
                data.extend(chunk)
                continue
            if time.monotonic() > deadline:
                raise errors.RadioNoResponse()
        return bytes(data)

    def _read_frame(self):
        header = self._read_exact(4)
        if header[0] != 0x7C:
            raise errors.RadioError("Radio sent an unexpected reply")
        payload_len = header[3]
        encoded = self._read_exact(payload_len + 1)
        plain = decrypt(encoded)
        payload, check = plain[:-1], plain[-1]
        expect = checksum(header[1], header[2], payload_len, payload)
        if check != expect:
            raise errors.RadioError("Radio reply failed its checksum")
        return header[1], payload

    def _write_frame(self, frame, repeats):
        for _ in range(repeats):
            self.pipe.write(frame)

    def _command(self, cmd, payload, repeats=1):
        self._write_frame(build_frame(cmd, 0xFF, payload), repeats)
        return self._read_frame()

    def _read_block(self, addr, size, repeats):
        cmd, payload = self._command(
            0x82, struct.pack(">HB", addr, size), repeats
        )
        if cmd != 0x82 or len(payload) < 2:
            raise errors.RadioError("Short read at %04X" % addr)
        got = (payload[0] << 8) | payload[1]
        data = payload[2:]
        if got != addr or len(data) != size:
            raise errors.RadioError("Bad read block at %04X" % addr)
        return data

    def _download(self):
        image = bytearray(MEM_SIZE)
        blocks = {}
        total = len(READ_BLOCKS)
        for pos, (addr, size) in enumerate(READ_BLOCKS):
            self._status("Cloning from radio", pos, total)
            repeats = 3 if pos == 0 else 2
            data = self._read_block(addr, size, repeats)
            if pos == 0 and not data.startswith(IDENT):
                raise errors.RadioError("Radio did not identify as KG-905G Plus")
            blocks[addr] = data
            image[addr:addr + size] = data
        self.pipe.write(build_frame(0x81, 0xFF, b""))
        self._status("Cloning from radio", total, total)
        return bytes(image) + trailer_for(blocks)

    def _upload(self):
        ident = self._read_block(0x0040, 64, 3)
        if not ident.startswith(IDENT):
            raise errors.RadioError("Radio did not identify as KG-905G Plus")
        for addr, size in ((0x0080, 64), (0x00C0, 64), (0x0700, 64)):
            self._read_block(addr, size, 2)
        body, saved = parse_trailer(self._packed())
        if not bytes(body[0x40:0x48]).startswith(IDENT):
            raise errors.RadioError("This image is not a KG-905G Plus")
        total = len(WRITE_BLOCKS)
        for pos, (addr, size) in enumerate(WRITE_BLOCKS):
            self._status("Cloning to radio", pos, total)
            cmd, payload = self._command(
                0x83,
                struct.pack(">H", addr) + write_payload(body, addr, size, saved),
                1,
            )
            if cmd != 0x83 or payload != struct.pack(">H", addr):
                raise errors.RadioError("Radio did not accept the block at %04X" % addr)
        self.pipe.write(build_frame(0x81, 0xFF, b""))
        self._status("Cloning to radio", total, total)
