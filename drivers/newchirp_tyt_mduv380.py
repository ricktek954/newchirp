# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Experimental TYT MD-UV380 codeplug driver.

The DfuSe transport and codeplug layout come from the official TYT CPS 2.42,
the editcp/CHIRP MD-380 family documentation, and QDMR's maintained UV390
implementation.  The driver preserves the complete two-segment codeplug and
edits conventional channels and zones.
"""

import logging
import time

from chirp import chirp_common, directory, errors, memmap
from chirp.settings import RadioSetting, RadioSettingGroup
from chirp.settings import RadioSettingValueBoolean
from chirp.settings import RadioSettingValueInteger
from chirp.settings import RadioSettingValueList


LOG = logging.getLogger(__name__)

MODEL_IDS = ("MD-UV380",)
CHANNEL_COUNT = 3000
CHANNEL_SIZE = 0x40
ZONE_COUNT = 250
ZONE_SIZE = 0x40
ZONE_EXT_SIZE = 0xE0

SEGMENT0_ADDRESS = 0x002000
SEGMENT0_SIZE = 0x03E000
SEGMENT1_ADDRESS = 0x110000
SEGMENT1_SIZE = 0x090000
CHANNELS_ADDRESS = 0x110000
ZONES_ADDRESS = 0x0149E0
ZONE_EXT_ADDRESS = 0x031000

FREQUENCY_RANGES = [
    (136000000, 174000000),
    (400000000, 480000000),
]
POWER_LEVELS = [
    chirp_common.PowerLevel("Low", watts=1),
    chirp_common.PowerLevel("Medium", watts=2.5),
    chirp_common.PowerLevel("High", watts=5),
]


def _bcd_le_decode(raw):
    value = int.from_bytes(raw, "little")
    result = 0
    multiplier = 1
    for index in range(8):
        digit = (value >> (index * 4)) & 0xF
        if digit > 9:
            return None
        result += digit * multiplier
        multiplier *= 10
    return result


def _bcd_le_encode(number):
    value = 0
    for index in range(8):
        value |= (int(number) % 10) << (index * 4)
        number = int(number) // 10
    return value.to_bytes(4, "little")


def _unicode_decode(raw):
    value = raw.decode("utf-16le", errors="replace").split("\x00", 1)[0]
    return value.rstrip("\ufffd ")


def _unicode_encode(value):
    return str(value).encode("utf-16le", errors="replace")[:32].ljust(
        32, b"\x00"
    )


def _ctcss_word_decode(word):
    if word == 0xFFFF:
        return None
    tag = word >> 14
    first = (word >> 12) & 0x03
    second = (word >> 8) & 0x0F
    third = (word >> 4) & 0x0F
    fourth = word & 0x0F
    if tag in (2, 3):
        return ("DCS", 100 * second + 10 * third + fourth,
                tag == 3)
    return (
        "CTCSS",
        100.0 * first + 10.0 * second + third + fourth / 10.0,
        False,
    )


def _ctcss_word_encode(tone, kind, inverted=False):
    if kind == "DCS":
        value = int(str(int(tone)), 8)
        return (
            0
            | ((value // 100) % 10) << 8
            | ((value // 10) % 10) << 4
            | (value % 10)
            | ((3 if inverted else 2) << 14)
        )
    value = int(round(float(tone) * 10))
    return (
        ((value // 1000) & 0x03) << 12
        | ((value // 100) % 10) << 8
        | ((value // 10) % 10) << 4
        | (value % 10)
    )


class MDUV380Zone(chirp_common.NamedBank):
    def get_name(self):
        name = self._model._radio._zone_name(self.index)
        return name or "New zone"

    def set_name(self, name):
        self._model._radio._set_zone_name(self.index, str(name)[:16])


class MDUV380ZoneModel(chirp_common.MTOBankModel):
    def __init__(self, radio):
        super().__init__(radio, "Zones")

    def get_num_mappings(self):
        return ZONE_COUNT

    def get_mappings(self):
        banks = []
        for index in range(ZONE_COUNT):
            bank = MDUV380Zone(
                self, "%i" % (index + 1), "Zone %i" % (index + 1)
            )
            bank.index = index
            banks.append(bank)
        return banks

    def add_memory_to_mapping(self, memory, bank):
        members = self._radio._zone_members(bank.index)
        if memory.number in members:
            return
        if len(members) >= 64:
            raise errors.RadioError("Zone %s is full" % bank.get_name())
        self._radio._set_zone_members(
            bank.index, members + [memory.number]
        )

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
        ]

    def get_memory_mappings(self, memory):
        banks = []
        for index in self._radio._zone_index().get(memory.number, []):
            bank = MDUV380Zone(
                self, "%i" % (index + 1), "Zone %i" % (index + 1)
            )
            bank.index = index
            banks.append(bank)
        return banks


@directory.register
class TYTMDUV380Radio(
    chirp_common.CloneModeRadio,
    chirp_common.ExperimentalRadio,
):
    """TYT MD-UV380 dual-band DMR handheld."""

    VENDOR = "TYT"
    MODEL = "MD-UV380"
    NEWCHIRP_TRANSPORT = "usb_dfu"
    BAUD_RATE = 115200
    _model = "MD-UV380"
    _memsize = SEGMENT0_SIZE + SEGMENT1_SIZE

    @classmethod
    def get_prompts(cls):
        prompts = chirp_common.RadioPrompts()
        prompts.experimental = (
            "TYT MD-UV380 support is experimental. NewChirp talks directly "
            "to the radio's ST DfuSe programming interface and edits the "
            "conventional channel and zone tables while preserving the rest "
            "of the codeplug. Contacts, RX groups, scan lists, optional "
            "signalling, APRS, encryption and radio-wide settings are not "
            "edited yet. Save a complete image before uploading."
        )
        prompts.info = (
            "Turn the radio on, connect it with the programming cable, and "
            "choose the TYT/STM32 USB DFU programming interface shown by "
            "NewChirp. Close the TYT CPS before reading or writing."
        )
        prompts.pre_download = (
            "1. Power on the MD-UV380 and connect the programming cable.\n"
            "2. Close the TYT CPS so it releases the USB DFU interface.\n"
            "3. Select the TYT/STM32 USB DFU interface and start the read."
        )
        prompts.pre_upload = (
            "Upload replaces the two supported codeplug segments after "
            "erasing each 64 KiB page. Confirm that a complete image was read "
            "from this radio and keep the radio powered on."
        )
        return prompts

    def __init__(self, pipe):
        super().__init__(pipe)
        self._image = None
        self._identity = b""

    def get_features(self):
        rf = chirp_common.RadioFeatures()
        rf.has_name = True
        rf.has_settings = False
        rf.has_bank = True
        rf.has_tuning_step = False
        rf.has_cross = False
        rf.can_odd_split = True
        rf.valid_name_length = 16
        rf.valid_modes = ["FM", "NFM", "DMR"]
        rf.valid_tmodes = ["", "Tone", "TSQL", "DTCS"]
        rf.valid_power_levels = list(POWER_LEVELS)
        rf.valid_duplexes = ["", "+", "-", "split"]
        rf.valid_bands = list(FREQUENCY_RANGES)
        rf.memory_bounds = (1, CHANNEL_COUNT)
        return rf

    def get_bank_model(self):
        return MDUV380ZoneModel(self)

    def process_mmap(self):
        data = self._mmap.get_packed()
        if len(data) != self._memsize:
            raise errors.RadioError(
                "Unsupported MD-UV380 NewChirp image size %i; expected %i"
                % (len(data), self._memsize)
            )
        self._image = bytearray(data)

    def _begin(self):
        identity = self.pipe.program_mode()
        self._identity = identity
        if not any(model.encode() in identity[:32]
                   for model in MODEL_IDS):
            text = identity[:32].split(b"\x00", 1)[0].decode(
                "ascii", errors="replace"
            )
            raise errors.RadioError(
                "Unsupported TYT DFU model %r; expected MD-UV380" % text
            )

    def _segment0(self):
        return self._image[:SEGMENT0_SIZE]

    def _segment1(self):
        return self._image[SEGMENT0_SIZE:]

    def _set_segment0(self, offset, value):
        self._image[offset:offset + len(value)] = value

    def _set_segment1(self, offset, value):
        base = SEGMENT0_SIZE
        self._image[base + offset:base + offset + len(value)] = value

    def _channel_record(self, number):
        start = (number - 1) * CHANNEL_SIZE
        return self._image[
            SEGMENT0_SIZE + start:SEGMENT0_SIZE + start + CHANNEL_SIZE
        ]

    def _set_channel_record(self, number, record):
        start = (number - 1) * CHANNEL_SIZE
        self._image[
            SEGMENT0_SIZE + start:SEGMENT0_SIZE + start + CHANNEL_SIZE
        ] = bytes(record)

    def _zone_record(self, index):
        offset = ZONES_ADDRESS - SEGMENT0_ADDRESS + index * ZONE_SIZE
        return self._image[offset:offset + ZONE_SIZE]

    def _set_zone_record(self, index, record):
        offset = ZONES_ADDRESS - SEGMENT0_ADDRESS + index * ZONE_SIZE
        self._image[offset:offset + ZONE_SIZE] = bytes(record)

    def _zone_ext_record(self, index):
        offset = (
            ZONE_EXT_ADDRESS - SEGMENT0_ADDRESS + index * ZONE_EXT_SIZE
        )
        return self._image[offset:offset + ZONE_EXT_SIZE]

    def _set_zone_ext_record(self, index, record):
        offset = (
            ZONE_EXT_ADDRESS - SEGMENT0_ADDRESS + index * ZONE_EXT_SIZE
        )
        self._image[offset:offset + ZONE_EXT_SIZE] = bytes(record)

    def _zone_name(self, index):
        return _unicode_decode(self._zone_record(index)[0:32])

    def _set_zone_name(self, index, name):
        record = bytearray(self._zone_record(index))
        record[0:32] = _unicode_encode(name)
        self._set_zone_record(index, record)

    def _zone_members(self, index):
        record = self._zone_record(index)
        extension = self._zone_ext_record(index)
        members = []
        for offset in range(0x20, 0x40, 2):
            stored = int.from_bytes(record[offset:offset + 2], "little")
            if not stored:
                break
            members.append(stored)
        for offset in range(0, 0x60, 2):
            stored = int.from_bytes(extension[offset:offset + 2], "little")
            if not stored:
                break
            members.append(stored)
        return [number for number in dict.fromkeys(members)
                if 1 <= number <= CHANNEL_COUNT]

    def _set_zone_members(self, index, members):
        record = bytearray(self._zone_record(index))
        extension = bytearray(self._zone_ext_record(index))
        record[0x20:0x40] = b"\x00" * 0x20
        extension[0:0x60] = b"\x00" * 0x60
        values = [number for number in members[:64]]
        for position, value in enumerate(values[:16]):
            record[0x20 + position * 2:0x22 + position * 2] = (
                value.to_bytes(2, "little")
            )
        for position, value in enumerate(values[16:64]):
            extension[position * 2:position * 2 + 2] = (
                value.to_bytes(2, "little")
            )
        self._set_zone_record(index, record)
        self._set_zone_ext_record(index, extension)

    def _zone_index(self):
        result = {}
        for index in range(ZONE_COUNT):
            if not self._zone_name(index):
                continue
            for number in self._zone_members(index):
                result.setdefault(number, []).append(index)
        return result

    def sync_in(self):
        self._begin()
        image = bytearray()
        blocks = (
            (SEGMENT0_ADDRESS, SEGMENT0_SIZE),
            (SEGMENT1_ADDRESS, SEGMENT1_SIZE),
        )
        for address, size in blocks:
            for offset in range(0, size, 0x10000):
                length = min(0x10000, size - offset)
                image.extend(self.pipe.read(address + offset, length))
                if self.status_fn:
                    status = chirp_common.Status()
                    status.msg = "Cloning from radio"
                    status.cur = len(image)
                    status.max = SEGMENT0_SIZE + SEGMENT1_SIZE
                    self.status_fn(status)
        if len(image) != self._memsize:
            raise errors.RadioError(
                "MD-UV380 returned %i bytes; expected %i"
                % (len(image), self._memsize)
            )
        self._image = image
        self._mmap = memmap.MemoryMapBytes(bytes(image))

    def sync_out(self):
        if self._image is None:
            raise errors.RadioError("No MD-UV380 image loaded")
        self._begin()
        for address, size, data in (
            (SEGMENT0_ADDRESS, SEGMENT0_SIZE, self._segment0()),
            (SEGMENT1_ADDRESS, SEGMENT1_SIZE, self._segment1()),
        ):
            self.pipe.erase(address, size)
            for offset in range(0, size, 0x10000):
                self.pipe.write(
                    address + offset, data[offset:offset + 0x10000]
                )

    def get_raw_memory(self, number):
        return self._channel_record(number).hex()

    def get_memory(self, number):
        if not 1 <= number <= CHANNEL_COUNT:
            raise errors.InvalidMemoryLocation(
                "Channel number must be between 1 and %i" % CHANNEL_COUNT
            )
        memory = chirp_common.Memory(number)
        record = bytearray(self._channel_record(number))
        rx_code = _bcd_le_decode(record[0x10:0x14])
        if record == b"\xff" * CHANNEL_SIZE or not rx_code:
            memory.empty = True
            return memory
        tx_code = _bcd_le_decode(record[0x14:0x18])
        if not tx_code:
            memory.empty = True
            return memory
        memory.freq = rx_code * 10
        tx_frequency = tx_code * 10
        difference = tx_frequency - memory.freq
        if difference == 0:
            memory.duplex = ""
            memory.offset = 0
        elif abs(difference) < 100_000_000:
            memory.duplex = "+" if difference > 0 else "-"
            memory.offset = abs(difference)
        else:
            memory.duplex = "split"
            memory.offset = tx_frequency

        mode = record[0] & 0x03
        memory.mode = "DMR" if mode == 2 else (
            "NFM" if ((record[0] >> 2) & 0x03) == 0 else "FM"
        )
        power = (record[0x1E] >> 6) & 0x03
        memory.power = POWER_LEVELS[min(power, 2)]
        memory.name = _unicode_decode(record[0x20:0x40])

        rx_tone = _ctcss_word_decode(
            int.from_bytes(record[0x18:0x1A], "little")
        )
        tx_tone = _ctcss_word_decode(
            int.from_bytes(record[0x1A:0x1C], "little")
        )
        if rx_tone and tx_tone:
            if rx_tone[0] == "CTCSS" and tx_tone[0] == "CTCSS":
                memory.tmode = "TSQL"
                memory.ctone = rx_tone[1]
                memory.rtone = tx_tone[1]
            elif rx_tone[0] == "DCS" and tx_tone[0] == "DCS":
                memory.tmode = "DTCS"
                memory.dtcs = tx_tone[1]
                memory.dtcs_polarity = (
                    ("R" if rx_tone[2] else "N")
                    + ("R" if tx_tone[2] else "N")
                )
        elif tx_tone and tx_tone[0] == "CTCSS":
            memory.tmode = "Tone"
            memory.rtone = tx_tone[1]

        extra = RadioSettingGroup("extra", "Extra")
        extra.append(RadioSetting(
            "color_code", "Color code (DMR)",
            RadioSettingValueInteger(
                0, 15, (record[1] >> 4) & 0x0F
            ),
        ))
        extra.append(RadioSetting(
            "time_slot", "Time slot (DMR)",
            RadioSettingValueList(
                ["1", "2"], current_index=max(
                    0, ((record[1] >> 2) & 0x03) - 1
                )
            ),
        ))
        extra.append(RadioSetting(
            "tx_contact", "TX contact index (DMR)",
            RadioSettingValueInteger(
                0, 9999,
                int.from_bytes(record[0x06:0x08], "little"),
            ),
        ))
        extra.append(RadioSetting(
            "rx_group", "RX group-list index (DMR)",
            RadioSettingValueInteger(0, 255, record[0x0C]),
        ))
        extra.append(RadioSetting(
            "rx_only", "Receive only",
            RadioSettingValueBoolean(bool(record[1] & 0x02)),
        ))
        extra.append(RadioSetting(
            "talkaround", "Talkaround",
            RadioSettingValueBoolean(not bool(record[1] & 0x01)),
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
        if self._image is None:
            raise errors.RadioError("No MD-UV380 image loaded")
        number = memory.number
        if not 1 <= number <= CHANNEL_COUNT:
            raise errors.InvalidMemoryLocation(
                "Channel number must be between 1 and %i" % CHANNEL_COUNT
            )
        if memory.empty:
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
            record[0x18:0x1C] = b"\xff" * 4
            record[0x1C:0x1E] = b"\x00\x00"
            record[0x1E:0x20] = b"\x00\x00"
        record[0x10:0x14] = _bcd_le_encode(int(memory.freq) // 10)
        if memory.duplex == "split":
            tx_frequency = int(memory.offset)
        elif memory.duplex in ("+", "-"):
            tx_frequency = int(memory.freq) + (
                int(memory.offset) if memory.duplex == "+"
                else -int(memory.offset)
            )
        else:
            tx_frequency = int(memory.freq)
        record[0x14:0x18] = _bcd_le_encode(tx_frequency // 10)

        record[0] = (record[0] & ~0x03) | (
            2 if memory.mode == "DMR" else 1
        )
        record[0] = (record[0] & ~0x0C) | (
            0 if memory.mode == "NFM" else 0x08
        )
        try:
            power_code = (0, 2, 3)[POWER_LEVELS.index(memory.power)]
        except ValueError:
            power_code = 0
        record[0x1E] = (record[0x1E] & 0x3F) | (power_code << 6)
        record[0x20:0x40] = _unicode_encode(memory.name)

        record[0x18:0x1C] = b"\xff" * 4
        if memory.tmode == "Tone":
            record[0x1A:0x1C] = _ctcss_word_encode(
                memory.rtone, "CTCSS"
            ).to_bytes(2, "little")
        elif memory.tmode == "TSQL":
            record[0x18:0x1A] = _ctcss_word_encode(
                getattr(memory, "ctone", memory.rtone), "CTCSS"
            ).to_bytes(2, "little")
            record[0x1A:0x1C] = _ctcss_word_encode(
                memory.rtone, "CTCSS"
            ).to_bytes(2, "little")
        elif memory.tmode == "DTCS":
            polarity = str(memory.dtcs_polarity)
            record[0x18:0x1A] = _ctcss_word_encode(
                memory.dtcs, "DCS", polarity[:1] == "R"
            ).to_bytes(2, "little")
            record[0x1A:0x1C] = _ctcss_word_encode(
                memory.dtcs, "DCS", polarity[-1:] == "R"
            ).to_bytes(2, "little")

        record[0x06:0x08] = int(
            self._extra(memory, "tx_contact", 0)
        ).to_bytes(2, "little")
        record[0x0C] = min(
            255, int(self._extra(memory, "rx_group", 0))
        )
        record[1] = (record[1] & 0x0F) | (
            min(15, int(self._extra(memory, "color_code", 0))) << 4
        )
        slot = int(self._extra(memory, "time_slot", 0)) + 1
        record[1] = (record[1] & ~0x0C) | ((slot & 0x03) << 2)
        record[1] = (record[1] & ~0x02) | (
            0x02 if bool(self._extra(memory, "rx_only", False)) else 0
        )
        record[1] = (record[1] & ~0x01) | (
            0 if bool(self._extra(memory, "talkaround", False)) else 1
        )
        self._set_channel_record(number, record)

    @classmethod
    def match_model(cls, filedata, filename):
        return False
