# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Experimental AnyTone AT-D578UVIII Plus serial driver.

This driver was reconstructed from the official AnyTone D578UV CPS 1.21 and
the documented QDMR D578UV I/II codeplug implementation.  It reads and writes
conventional channels and zones.  Analog tone, DMR color-code and time-slot,
TX contact index, and RX-group index fields are retained.  Contacts, scan
lists, optional signalling and radio-wide settings are left untouched.
"""

import logging
import time

from chirp import chirp_common, directory, errors, memmap
from chirp.settings import RadioSetting, RadioSettingGroup
from chirp.settings import RadioSettingValueBoolean
from chirp.settings import RadioSettingValueInteger
from chirp.settings import RadioSettingValueList


LOG = logging.getLogger(__name__)

ACK = b"\x06"
PROGRAM_RESPONSE = b"QX\x06"
MODEL_IDS = ("D578UV", "D578UV2", "D578UV3", "D578UVIII")

CHANNEL_COUNT = 4000
CHANNELS_PER_BANK = 1000
CHANNEL_SIZE = 0x40
CHANNEL_BANKS_ADDRESS = 0x00800000
BETWEEN_CHANNEL_BANKS = 0x00040000
CHANNEL_BITMAP_ADDRESS = 0x024C1500
CHANNEL_BITMAP_SIZE = 0x0200

ZONE_COUNT = 250
ZONE_CHANNELS = 250
ZONE_CHANNELS_ADDRESS = 0x01000000
BETWEEN_ZONE_CHANNELS = 0x00000200
ZONE_NAMES_ADDRESS = 0x02540000
BETWEEN_ZONE_NAMES = 0x00000020
ZONE_BITMAP_ADDRESS = 0x024C1300
ZONE_BITMAP_SIZE = 0x20

CTCSS_CODES = (
    62.5, 67.0, 69.3, 71.9, 74.4, 77.0, 79.7, 82.5,
    85.4, 88.5, 91.5, 94.8, 97.4, 100.0, 103.5, 107.2,
    110.9, 114.8, 118.8, 123.0, 127.3, 131.8, 136.5, 141.3,
    146.2, 151.4, 156.7, 159.8, 162.2, 165.5, 167.9, 171.3,
    173.8, 177.3, 179.9, 183.5, 186.2, 189.9, 192.8, 196.6,
    199.5, 203.5, 206.5, 210.7, 218.1, 225.7, 229.1, 233.6,
    241.8, 250.3, 254.1,
)
CTCSS_CUSTOM_INDEX = 51

POWER_LEVELS = [
    chirp_common.PowerLevel("Low", watts=5),
    chirp_common.PowerLevel("Mid", watts=25),
    chirp_common.PowerLevel("High", watts=50),
    chirp_common.PowerLevel("Turbo", watts=50),
]


def _read_exact(pipe, count, context):
    data = bytearray()
    deadline = time.monotonic() + 1.5
    while len(data) < count and time.monotonic() < deadline:
        chunk = pipe.read(count - len(data))
        if chunk:
            data.extend(chunk)
        elif not data:
            time.sleep(0.005)
    if len(data) != count:
        raise errors.RadioNoResponse(
            "Radio returned %i of %i bytes while %s"
            % (len(data), count, context)
        )
    return bytes(data)


def _bcd_decode(raw):
    value = 0
    for byte in raw:
        for nibble in (byte >> 4, byte & 0x0F):
            if nibble > 9:
                return None
            value = value * 10 + nibble
    return value


def _bcd_encode(value, width=4):
    digits = "%08i" % int(value)
    if len(digits) > width * 2:
        raise errors.RadioError("Frequency value is too large")
    return bytes.fromhex(digits)


def _ascii(raw):
    return raw.split(b"\x00", 1)[0].rstrip(b"\xff ").decode(
        "ascii", errors="replace"
    ).strip()


def _ctcss_decode(index):
    if 0 <= index < len(CTCSS_CODES):
        return CTCSS_CODES[index]
    return None


def _ctcss_encode(tone):
    try:
        index = min(
            range(len(CTCSS_CODES)),
            key=lambda pos: abs(CTCSS_CODES[pos] - float(tone)),
        )
    except (TypeError, ValueError):
        return None
    if abs(CTCSS_CODES[index] - float(tone)) > 0.05:
        return None
    return index


def _dcs_decode(raw):
    value = int.from_bytes(raw, "little")
    inverted = value >= 512
    binary = value - 512 if inverted else value
    if not binary:
        return None, inverted
    return int(format(binary, "o")), inverted


def _dcs_encode(code):
    try:
        binary = int(str(int(code)), 8)
    except ValueError:
        return 0
    return binary


def _bit(value, offset, width=1):
    return (value >> offset) & ((1 << width) - 1)


def _set_bits(original, offset, width, value):
    mask = ((1 << width) - 1) << offset
    return (original & ~mask) | ((int(value) << offset) & mask)


class _SparseImage:
    """Map the small codeplug sections used by the UI into a compact image."""

    BLOCKS = (
        ("channel_bitmap", CHANNEL_BITMAP_SIZE),
        ("channels", CHANNEL_COUNT * CHANNEL_SIZE),
        ("zone_bitmap", ZONE_BITMAP_SIZE),
        ("zone_channels", ZONE_COUNT * BETWEEN_ZONE_CHANNELS),
        ("zone_names", ZONE_COUNT * BETWEEN_ZONE_NAMES),
    )

    def __init__(self):
        offset = 0
        self.offsets = {}
        for name, size in self.BLOCKS:
            self.offsets[name] = (offset, size)
            offset += size
        self.data = bytearray(b"\xff" * offset)
        self._zero("zone_names")

    def _zero(self, name):
        offset, size = self.offsets[name]
        self.data[offset:offset + size] = b"\x00" * size

    def get(self, name, offset, size=None):
        base, length = self.offsets[name]
        if size is None:
            size = length - offset
        return bytes(self.data[base + offset:base + offset + size])

    def set(self, name, offset, value):
        base, _length = self.offsets[name]
        value = bytes(value)
        self.data[base + offset:base + offset + len(value)] = value

    def packed(self):
        return bytes(self.data)


class D578UVZone(chirp_common.NamedBank):
    def _zone_index(self):
        return self.index

    def get_name(self):
        name = self._model._radio._zone_name(self._zone_index())
        if not name:
            return "New zone"
        return name

    def set_name(self, name):
        self._model._radio._set_zone_name(
            self._zone_index(), str(name)[:16]
        )


class D578UVZoneModel(chirp_common.MTOBankModel):
    def __init__(self, radio):
        super().__init__(radio, "Zones")

    def get_num_mappings(self):
        return ZONE_COUNT

    def get_mappings(self):
        mappings = []
        for index in range(ZONE_COUNT):
            bank = D578UVZone(self, "%i" % (index + 1), "Zone %i" % (index + 1))
            bank.index = index
            mappings.append(bank)
        return mappings

    def add_memory_to_mapping(self, memory, bank):
        members = self._radio._zone_members(bank.index)
        if memory.number in members:
            return
        if len(members) >= ZONE_CHANNELS:
            raise errors.RadioError("Zone %s is full" % bank.get_name())
        self._radio._set_zone_members(bank.index, members + [memory.number])

    def remove_memory_from_mapping(self, memory, bank):
        members = self._radio._zone_members(bank.index)
        if memory.number not in members:
            raise Exception("Memory %i is not in zone %s"
                            % (memory.number, bank.get_name()))
        self._radio._set_zone_members(
            bank.index, [number for number in members
                         if number != memory.number]
        )

    def get_mapping_memories(self, bank):
        return [
            self._radio.get_memory(number)
            for number in self._radio._zone_members(bank.index)
            if 1 <= number <= CHANNEL_COUNT
        ]

    def get_memory_mappings(self, memory):
        mappings = []
        for index in self._radio._zone_index().get(memory.number, []):
            bank = D578UVZone(self, "%i" % (index + 1),
                              "Zone %i" % (index + 1))
            bank.index = index
            mappings.append(bank)
        return mappings


@directory.register
class AnyToneD578UVIIIPlusRadio(
    chirp_common.CloneModeRadio,
    chirp_common.ExperimentalRadio,
):
    """AnyTone AT-D578UVIII Plus tri-band DMR mobile."""

    VENDOR = "AnyTone"
    MODEL = "AT-D578UVIII Plus"
    BAUD_RATE = 115200
    HARDWARE_FLOW = False
    WANTS_RTS = False
    WANTS_DTR = False
    _model = "D578UV"
    _memsize = 1

    @classmethod
    def get_prompts(cls):
        prompts = chirp_common.RadioPrompts()
        prompts.experimental = (
            "The AnyTone AT-D578UVIII Plus driver is experimental. It uses "
            "the D578UV CPS serial protocol recovered from the official CPS "
            "1.21 and QDMR's tested D578UV I/II implementation. Conventional "
            "channels and zones are read and written. Radio-wide settings, "
            "contacts, scan lists, and optional signalling are preserved but "
            "are not edited here. Save a complete image before uploading."
        )
        prompts.pre_download = (
            "1. Connect the radio's USB programming cable and power it on.\n"
            "2. Close any AnyTone CPS instance using the serial port.\n"
            "3. Start the download and leave the radio powered on."
        )
        prompts.pre_upload = (
            "Confirm the CPS and firmware generations match the radio. "
            "NewChirp writes only conventional channel and zone records; "
            "settings, contacts, scan lists, and optional signalling are "
            "left unchanged."
        )
        return prompts

    def __init__(self, pipe):
        super().__init__(pipe)
        self._sparse = None
        self._model_name = ""
        self._firmware = ""
        self._bands = 0

    def get_features(self):
        rf = chirp_common.RadioFeatures()
        rf.has_name = True
        rf.has_settings = False
        rf.has_bank = True
        rf.has_tuning_step = False
        rf.has_cross = False
        rf.can_odd_split = False
        rf.valid_name_length = 16
        rf.valid_modes = ["FM", "NFM", "DMR"]
        rf.valid_tmodes = ["", "Tone", "TSQL", "DTCS"]
        rf.valid_power_levels = list(POWER_LEVELS)
        rf.valid_duplexes = ["", "+", "-"]
        rf.valid_bands = [
            (136000000, 174000000),
            (220000000, 225000000),
            (400000000, 520000000),
        ]
        rf.memory_bounds = (1, CHANNEL_COUNT)
        return rf

    def get_bank_model(self):
        return D578UVZoneModel(self)

    def _command(self, data, length, context):
        self.pipe.write(data)
        return _read_exact(self.pipe, length, context)

    def _begin(self):
        self.pipe.timeout = 1
        response = self._command(b"PROGRAM", 3, "entering program mode")
        if response != PROGRAM_RESPONSE:
            raise errors.RadioError(
                "The AnyTone CPS did not enter programming mode; expected "
                "QX06, received %s" % response.hex()
            )
        identity = self._command(b"\x02", 16, "reading radio identity")
        if identity[:1] != b"I" or identity[-1:] != ACK:
            raise errors.RadioError(
                "Invalid AnyTone identity response: %s" % identity.hex()
            )
        self._model_name = _ascii(identity[1:8])
        self._bands = identity[8]
        self._firmware = _ascii(identity[9:15])
        if self._model_name not in MODEL_IDS:
            raise errors.RadioError(
                "Unsupported AnyTone model %r; expected D578UV family"
                % self._model_name
            )
        LOG.info(
            "AnyTone D578UV identity: model=%s bands=0x%02x firmware=%s",
            self._model_name,
            self._bands,
            self._firmware,
        )

    def _end(self):
        try:
            self.pipe.write(b"END")
            _read_exact(self.pipe, 1, "leaving program mode")
        except errors.RadioError:
            LOG.debug("AnyTone did not acknowledge END")

    def _read(self, address, length):
        data = bytearray()
        for offset in range(0, length, 16):
            request = (
                b"R" + (address + offset).to_bytes(4, "big") + b"\x10"
            )
            response = self._command(
                request, 24, "reading memory at 0x%08X" % (address + offset)
            )
            if (
                response[:1] != b"W"
                or int.from_bytes(response[1:5], "big") != address + offset
                or response[5] != 16
                or response[23:] != ACK
            ):
                raise errors.RadioError(
                    "Invalid AnyTone read response at 0x%08X: %s"
                    % ((address + offset), response.hex())
                )
            checksum = sum(response[1:22]) & 0xFF
            if checksum != response[22]:
                raise errors.RadioError(
                    "AnyTone read checksum mismatch at 0x%08X"
                    % (address + offset)
                )
            data.extend(response[6:22])
        return bytes(data)

    def _write(self, address, data):
        data = bytes(data)
        for offset in range(0, len(data), 16):
            chunk = data[offset:offset + 16]
            if len(chunk) != 16:
                raise errors.RadioError("AnyTone writes must be 16-byte aligned")
            body = (
                (address + offset).to_bytes(4, "big") + b"\x10" + chunk
            )
            checksum = sum(body) & 0xFF
            response = self._command(
                b"W" + body + bytes((checksum,)) + ACK,
                1,
                "writing memory at 0x%08X" % (address + offset),
            )
            if response != ACK:
                raise errors.RadioError(
                    "AnyTone rejected write at 0x%08X: %s"
                    % (address + offset, response.hex())
                )

    def _bitmap(self, name, index):
        bitmap = self._sparse.get(name, 0, self._sparse.offsets[name][1])
        return bool(bitmap[index // 8] & (1 << (index % 8)))

    def _set_bitmap(self, name, index, enabled):
        bitmap = bytearray(
            self._sparse.get(name, 0, self._sparse.offsets[name][1])
        )
        mask = 1 << (index % 8)
        if enabled:
            bitmap[index // 8] |= mask
        else:
            bitmap[index // 8] &= ~mask
        self._sparse.set(name, 0, bitmap)

    def _channel_address(self, number):
        index = number - 1
        bank, within = divmod(index, CHANNELS_PER_BANK)
        return (
            CHANNEL_BANKS_ADDRESS
            + bank * BETWEEN_CHANNEL_BANKS
            + within * CHANNEL_SIZE
        )

    def _channel_record(self, number):
        index = number - 1
        return self._sparse.get("channels", index * CHANNEL_SIZE, CHANNEL_SIZE)

    def _set_channel_record(self, number, record):
        self._sparse.set(
            "channels", (number - 1) * CHANNEL_SIZE, bytes(record)
        )

    def _zone_name(self, index):
        return _ascii(
            self._sparse.get("zone_names", index * BETWEEN_ZONE_NAMES, 32)
        )

    def _set_zone_name(self, index, name):
        raw = name.encode("ascii", errors="replace")[:16].ljust(32, b"\x00")
        self._sparse.set("zone_names", index * BETWEEN_ZONE_NAMES, raw)

    def _zone_members(self, index):
        raw = self._sparse.get(
            "zone_channels", index * BETWEEN_ZONE_CHANNELS,
            BETWEEN_ZONE_CHANNELS
        )
        members = []
        for offset in range(0, len(raw), 2):
            stored = int.from_bytes(raw[offset:offset + 2], "little")
            if stored == 0xFFFF:
                break
            members.append(stored + 1)
        return members

    def _set_zone_members(self, index, members):
        raw = bytearray(b"\xff" * BETWEEN_ZONE_CHANNELS)
        for offset, number in enumerate(members[:ZONE_CHANNELS]):
            raw[offset * 2:offset * 2 + 2] = (number - 1).to_bytes(2, "little")
        self._sparse.set("zone_channels", index * BETWEEN_ZONE_CHANNELS, raw)
        self._set_bitmap("zone_bitmap", index, bool(members))

    def _zone_index(self):
        result = {}
        for index in range(ZONE_COUNT):
            if not self._bitmap("zone_bitmap", index):
                continue
            for number in self._zone_members(index):
                result.setdefault(number, []).append(index)
        return result

    def process_mmap(self):
        data = self._mmap.get_packed()
        expected = sum(size for _name, size in _SparseImage.BLOCKS)
        if len(data) != expected:
            raise errors.RadioError(
                "Unsupported AnyTone NewChirp image size %i; expected %i"
                % (len(data), expected)
            )
        self._sparse = _SparseImage()
        self._sparse.data = bytearray(data)

    def sync_in(self):
        self._sparse = _SparseImage()
        try:
            self._begin()
            self._sparse.set(
                "channel_bitmap", 0,
                self._read(CHANNEL_BITMAP_ADDRESS, CHANNEL_BITMAP_SIZE)
            )
            self._sparse.set(
                "zone_bitmap", 0,
                self._read(ZONE_BITMAP_ADDRESS, ZONE_BITMAP_SIZE)
            )

            used = [
                number for number in range(1, CHANNEL_COUNT + 1)
                if self._bitmap("channel_bitmap", number - 1)
            ]
            status = chirp_common.Status()
            status.max = max(len(used), 1)
            status.msg = "Reading D578UV channels"
            for position, number in enumerate(used, 1):
                record = self._read(self._channel_address(number), CHANNEL_SIZE)
                self._set_channel_record(number, record)
                if self.status_fn:
                    status.cur = position
                    self.status_fn(status)

            used_zones = [
                index for index in range(ZONE_COUNT)
                if self._bitmap("zone_bitmap", index)
            ]
            for index in used_zones:
                self._sparse.set(
                    "zone_channels", index * BETWEEN_ZONE_CHANNELS,
                    self._read(
                        ZONE_CHANNELS_ADDRESS + index * BETWEEN_ZONE_CHANNELS,
                        BETWEEN_ZONE_CHANNELS,
                    )
                )
                self._sparse.set(
                    "zone_names", index * BETWEEN_ZONE_NAMES,
                    self._read(
                        ZONE_NAMES_ADDRESS + index * BETWEEN_ZONE_NAMES,
                        BETWEEN_ZONE_NAMES,
                    )
                )
        finally:
            self._end()
        self._mmap = memmap.MemoryMapBytes(self._sparse.packed())

    def sync_out(self):
        if self._sparse is None:
            raise errors.RadioError("No AnyTone codeplug data loaded")
        self._begin()
        try:
            self._write(
                CHANNEL_BITMAP_ADDRESS,
                self._sparse.get(
                    "channel_bitmap", 0, CHANNEL_BITMAP_SIZE
                ),
            )
            for number in range(1, CHANNEL_COUNT + 1):
                if self._bitmap("channel_bitmap", number - 1):
                    self._write(
                        self._channel_address(number),
                        self._channel_record(number),
                    )

            self._write(
                ZONE_BITMAP_ADDRESS,
                self._sparse.get("zone_bitmap", 0, ZONE_BITMAP_SIZE),
            )
            for index in range(ZONE_COUNT):
                if not self._bitmap("zone_bitmap", index):
                    continue
                self._write(
                    ZONE_CHANNELS_ADDRESS + index * BETWEEN_ZONE_CHANNELS,
                    self._sparse.get(
                        "zone_channels", index * BETWEEN_ZONE_CHANNELS,
                        BETWEEN_ZONE_CHANNELS,
                    ),
                )
                self._write(
                    ZONE_NAMES_ADDRESS + index * BETWEEN_ZONE_NAMES,
                    self._sparse.get(
                        "zone_names", index * BETWEEN_ZONE_NAMES,
                        BETWEEN_ZONE_NAMES,
                    ),
                )
        finally:
            self._end()

    def get_raw_memory(self, number):
        if self._sparse is None:
            raise errors.InvalidMemoryLocation("No image loaded")
        return self._channel_record(number).hex()

    def get_memory(self, number):
        if not 1 <= number <= CHANNEL_COUNT:
            raise errors.InvalidMemoryLocation(
                "Channel number must be between 1 and %i" % CHANNEL_COUNT
            )
        memory = chirp_common.Memory(number)
        if self._sparse is None or not self._bitmap(
                "channel_bitmap", number - 1):
            memory.empty = True
            return memory
        record = bytearray(self._channel_record(number))
        frequency = _bcd_decode(record[0:4])
        if not frequency:
            memory.empty = True
            return memory
        memory.freq = frequency * 10
        offset = (_bcd_decode(record[4:8]) or 0) * 10
        repeater = _bit(record[8], 6, 2)
        if repeater == 0 or not offset:
            memory.duplex = ""
            memory.offset = 0
        else:
            memory.duplex = "+" if repeater == 1 else "-"
            memory.offset = offset

        mode = _bit(record[8], 0, 2)
        memory.mode = "DMR" if mode in (1, 3) else (
            "FM" if _bit(record[8], 4) else "NFM"
        )
        memory.power = POWER_LEVELS[min(_bit(record[8], 2, 2), 3)]
        memory.name = _ascii(record[0x23:0x33])

        rx_signaling = _bit(record[9], 0, 2)
        tx_signaling = _bit(record[9], 2, 2)
        if rx_signaling == 1 and tx_signaling == 1:
            memory.tmode = "TSQL"
            memory.ctone = _ctcss_decode(record[0x0B]) or 88.5
            memory.rtone = _ctcss_decode(record[0x0A]) or memory.ctone
        elif tx_signaling == 1:
            memory.tmode = "Tone"
            memory.rtone = _ctcss_decode(record[0x0A]) or 88.5
        elif rx_signaling == 2 and tx_signaling == 2:
            tx_code, tx_inv = _dcs_decode(record[0x0C:0x0E])
            rx_code, rx_inv = _dcs_decode(record[0x0E:0x10])
            memory.tmode = "DTCS"
            memory.dtcs = tx_code or rx_code or 23
            memory.dtcs_polarity = (
                ("R" if rx_inv else "N") + ("R" if tx_inv else "N")
            )

        extra = RadioSettingGroup("extra", "Extra")
        extra.append(RadioSetting(
            "color_code", "Color code (DMR)",
            RadioSettingValueInteger(
                0, 15, record[0x20]
            ),
        ))
        extra.append(RadioSetting(
            "time_slot", "Time slot (DMR)",
            RadioSettingValueList(
                ["1", "2"], current_index=_bit(record[0x21], 0)
            ),
        ))
        extra.append(RadioSetting(
            "tx_contact", "TX contact index (DMR)",
            RadioSettingValueInteger(
                0, 9999, int.from_bytes(record[0x14:0x18], "little")
            ),
        ))
        extra.append(RadioSetting(
            "rx_group", "RX group-list index (DMR)",
            RadioSettingValueInteger(
                0, 255, record[0x1C]
            ),
        ))
        extra.append(RadioSetting(
            "rx_only", "Receive only",
            RadioSettingValueBoolean(
                bool(_bit(record[9], 5))
            ),
        ))
        extra.append(RadioSetting(
            "talkaround", "Talkaround",
            RadioSettingValueBoolean(
                bool(_bit(record[9], 7))
            ),
        ))
        memory.extra = extra
        return memory

    @staticmethod
    def _extra(memory, name, default):
        try:
            return memory.extra[name].value
        except (AttributeError, KeyError, TypeError):
            return default

    def set_memory(self, memory):
        if self._sparse is None:
            raise errors.RadioError("No AnyTone codeplug data loaded")
        number = memory.number
        if not 1 <= number <= CHANNEL_COUNT:
            raise errors.InvalidMemoryLocation(
                "Channel number must be between 1 and %i" % CHANNEL_COUNT
            )
        if memory.empty:
            self._set_bitmap("channel_bitmap", number - 1, False)
            self._set_channel_record(number, b"\xff" * CHANNEL_SIZE)
            for index in range(ZONE_COUNT):
                members = self._zone_members(index)
                if number in members:
                    self._set_zone_members(
                        index, [item for item in members if item != number]
                    )
            return

        record = bytearray(self._channel_record(number))
        if record == b"\xff" * CHANNEL_SIZE:
            record = bytearray(CHANNEL_SIZE)

        frequency = int(memory.freq)
        record[0:4] = _bcd_encode(frequency // 10)
        if memory.duplex in ("+", "-"):
            offset = abs(int(memory.offset))
            record[4:8] = _bcd_encode(offset // 10)
            repeater = 1 if memory.duplex == "+" else 2
        else:
            record[4:8] = _bcd_encode(0)
            repeater = 0

        record[8] = _set_bits(record[8], 6, 2, repeater)
        mode = 1 if memory.mode == "DMR" else 0
        record[8] = _set_bits(record[8], 0, 2, mode)
        record[8] = _set_bits(
            record[8], 4, 1, int(memory.mode == "FM")
        )
        try:
            power = POWER_LEVELS.index(memory.power)
        except ValueError:
            power = 0
        record[8] = _set_bits(record[8], 2, 2, power)

        record[9] = _set_bits(record[9], 0, 2, 0)
        record[9] = _set_bits(record[9], 2, 2, 0)
        record[0x0A] = 0
        record[0x0B] = 0
        record[0x0C:0x0E] = b"\x00\x00"
        record[0x0E:0x10] = b"\x00\x00"
        if memory.tmode == "Tone":
            record[9] = _set_bits(record[9], 2, 2, 1)
            index = _ctcss_encode(memory.rtone)
            record[0x0A] = 0 if index is None else index
        elif memory.tmode == "TSQL":
            record[9] = _set_bits(record[9], 0, 2, 1)
            record[9] = _set_bits(record[9], 2, 2, 1)
            rx_index = _ctcss_encode(
                getattr(memory, "ctone", memory.rtone)
            )
            tx_index = _ctcss_encode(memory.rtone)
            record[0x0A] = 0 if tx_index is None else tx_index
            record[0x0B] = 0 if rx_index is None else rx_index
        elif memory.tmode == "DTCS":
            record[9] = _set_bits(record[9], 0, 2, 2)
            record[9] = _set_bits(record[9], 2, 2, 2)
            polarity = str(memory.dtcs_polarity)
            binary = _dcs_encode(memory.dtcs)
            tx_inv = polarity[-1:] == "R"
            rx_inv = polarity[:1] == "R"
            record[0x0C:0x0E] = (
                binary + (512 if tx_inv else 0)
            ).to_bytes(2, "little")
            record[0x0E:0x10] = (
                binary + (512 if rx_inv else 0)
            ).to_bytes(2, "little")

        record[0x14:0x18] = int(
            self._extra(memory, "tx_contact", 0)
        ).to_bytes(4, "little")
        record[0x1C] = min(
            255, int(self._extra(memory, "rx_group", 255))
        )
        record[0x20] = min(
            15, int(self._extra(memory, "color_code", 0))
        )
        record[0x21] = _set_bits(
            record[0x21], 0, 1, int(self._extra(memory, "time_slot", 0))
        )
        record[9] = _set_bits(
            record[9], 5, 1,
            int(bool(self._extra(memory, "rx_only", False)))
        )
        record[9] = _set_bits(
            record[9], 7, 1,
            int(bool(self._extra(memory, "talkaround", False)))
        )
        name = str(memory.name).encode(
            "ascii", errors="replace"
        )[:16].ljust(16, b"\x00")
        record[0x23:0x33] = name

        self._set_channel_record(number, record)
        self._set_bitmap("channel_bitmap", number - 1, True)

    @classmethod
    def match_model(cls, filedata, filename):
        return False
