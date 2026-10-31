# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Experimental Icom IC-41S UHF CB clone-mode driver.

The transport and image layout were recovered from Icom CS-41S Cloning
Software Rev. 1.3.  The CPS identifies only the IC-41S, never the IC-41W.

Each memory channel is a 22-byte record:

    u32 rx_hz
    u32 tx_hz
    u16 rx_tone
    u16 tx_tone
    char name[8]
    u16 flags

Only the fields proven by the CPS and sample image are exposed.  Tone,
power, scan, and zone values remain byte-for-byte intact but are not edited
until physical radio validation establishes their exact encodings.
"""

import logging
import struct

from chirp import chirp_common, directory, errors, memmap
from chirp.drivers import icf


LOG = logging.getLogger(__name__)

MODEL_ID = b"\x29\x28\x00\x00"
MODEL_FIELD = "\x29\x28\x00\x00"
END_FRAME = "Icom Inc."
MEM_SIZE = 0x7D80
BLOCK_SIZE = 16

# The serialized zone table is 200 bytes when the CPS emits channel data.
SERIALIZED_START = 0x0178
ZONE_TABLE_SIZE = 0x00C8
CHANNEL_START_WITH_ZONES = SERIALIZED_START + ZONE_TABLE_SIZE
CHANNEL_START_WITHOUT_ZONES = SERIALIZED_START
CHANNEL_RECORD_SIZE = 22

# Global settings immediately follow the variable zone/channel section.
# "FEC" is the stable feature marker observed in both the initial image and
# the populated CPS sample.
SETTINGS_SIGNATURE = bytes.fromhex("500f0102464543100000000000000000")
SETTINGS_MAGIC_OFFSET = 4

FLAG_ACTIVE = 0x40
FLAG_DUPLEX = 0x20
TONE_OFF_BYTES = b"\x80\x00"

VALID_BANDS = [(450000000, 520000000)]
TUNING_STEPS = [2.5, 3.125, 12.5, 25.0]


def _flags(raw):
    return struct.unpack("<H", raw[20:22])[0]


def _u32(raw, offset):
    return struct.unpack(">I", raw[offset:offset + 4])[0]


def _pack_flags(value):
    return struct.pack("<H", value)


def _pack_u32(value):
    return struct.pack(">I", value)


def _valid_frequency(freq):
    return any(start <= freq <= stop for start, stop in VALID_BANDS)


def _find_settings_offset(image):
    start = SERIALIZED_START
    while True:
        offset = image.find(SETTINGS_SIGNATURE, start)
        if offset < 0:
            return None
        if image.startswith(b"FEC\x10", offset + SETTINGS_MAGIC_OFFSET):
            return offset
        start = offset + 1


def _find_channel_layout(image):
    """Return (channel_start, channel_count) for a CPS image."""
    settings = _find_settings_offset(image)
    if settings is None:
        raise errors.InvalidDataError(
            "IC-41S settings block not found; this is not a recognizable "
            "CS-41S image"
        )

    body_size = settings - SERIALIZED_START
    if body_size >= 0 and body_size % CHANNEL_RECORD_SIZE == 0:
        return SERIALIZED_START, body_size // CHANNEL_RECORD_SIZE

    body_without_zones = body_size - ZONE_TABLE_SIZE
    if (
        body_size >= ZONE_TABLE_SIZE
        and body_without_zones >= 0
        and body_without_zones % CHANNEL_RECORD_SIZE == 0
    ):
        return (
            CHANNEL_START_WITH_ZONES,
            body_without_zones // CHANNEL_RECORD_SIZE,
        )

    raise errors.InvalidDataError(
        "IC-41S channel table has an unsupported length"
    )


def _decode_name(name):
    return name.rstrip(b"\xff\x00 ").decode("ascii", "replace")


def _encode_name(name):
    return name.encode("ascii", "replace")[:8].ljust(8, b" ")


def _record(image, channel_start, number):
    offset = channel_start + (number - 1) * CHANNEL_RECORD_SIZE
    return offset, bytes(image[offset:offset + CHANNEL_RECORD_SIZE])


@directory.register
class IcomIC41SRadio(icf.IcomCloneModeRadio, chirp_common.ExperimentalRadio):
    """Icom IC-41S UHF CB transceiver."""

    VENDOR = "Icom"
    MODEL = "IC-41S"
    BAUD_RATE = 9600
    _model = MODEL_FIELD
    _memsize = MEM_SIZE
    _endframe = END_FRAME
    _ranges = [(0x0000, MEM_SIZE, BLOCK_SIZE)]
    _can_hispeed = False
    _raw_frames = False
    _highbit_flip = False
    _num_banks = 8
    _icf_data = {
        "MapRev": 1,
        "recordsize": BLOCK_SIZE,
    }

    def __init__(self, pipe):
        super().__init__(pipe)
        self._channel_start = CHANNEL_START_WITHOUT_ZONES
        self._channel_count = 1

    @classmethod
    def get_prompts(cls):
        prompts = chirp_common.RadioPrompts()
        prompts.experimental = (
            "Icom IC-41S support is experimental. The clone transport and "
            "22-byte channel records were recovered from CS-41S Cloning "
            "Software Rev. 1.3, but this driver has not been validated on "
            "physical hardware. Reading and writing are enabled at your own "
            "risk. Download and save an unedited backup first, and do not "
            "upload unless the frequencies, names, duplex/split settings, "
            "and channel order all look correct.\n"
        )
        prompts.info = (
            "Use an Icom OPC-478/U/UC programming cable, turn the radio on, "
            "and close Icom CS-41S before starting a transfer. The radio uses "
            "9600 baud, 8 data bits, no parity, and one stop bit."
        )
        prompts.pre_download = (
            "1. Turn on the IC-41S and connect the OPC-478/U/UC cable.\n"
            "2. Close CS-41S and any other program using the serial port.\n"
            "3. Read the radio and save the unedited image as a backup.\n\n"
            "Verify channel order, RX/TX frequencies, split operation, and "
            "8-character labels before enabling upload."
        )
        prompts.pre_upload = (
            "Experimental IC-41S write. Keep the backup image from your first "
            "unedited download. Do not disconnect the cable or turn off the "
            "radio during the transfer. Read the radio back afterward and "
            "verify every channel before relying on it."
        )
        return prompts

    def get_features(self):
        rf = chirp_common.RadioFeatures()
        rf.memory_bounds = (1, max(1, self._channel_count))
        rf.valid_bands = list(VALID_BANDS)
        rf.valid_modes = ["FM"]
        rf.has_mode = False
        rf.valid_tmodes = [""]
        rf.has_ctone = False
        rf.has_dtcs = False
        rf.has_offset = False
        rf.valid_duplexes = ["", "split"]
        rf.can_odd_split = True
        rf.has_tuning_step = False
        rf.valid_tuning_steps = list(TUNING_STEPS)
        rf.has_bank = False
        rf.has_settings = False
        rf.valid_name_length = 8
        rf.valid_characters = chirp_common.CHARSET_UPPER_NUMERIC + "-./"
        rf.valid_skips = [""]
        return rf

    def process_mmap(self):
        image = self._mmap.get_packed()
        if len(image) != MEM_SIZE:
            raise errors.InvalidDataError(
                "IC-41S image is %i bytes; expected %i"
                % (len(image), MEM_SIZE)
            )
        self._channel_start, self._channel_count = _find_channel_layout(image)
        self._memsize = len(image)
        LOG.info(
            "IC-41S image has %i channels at 0x%04X",
            self._channel_count,
            self._channel_start,
        )

    def load_mmap(self, filename):
        if filename.lower().endswith((".icf", ".ics")):
            self._icf_data, self._mmap = icf.read_file(filename)
            self.process_mmap()
        else:
            super().load_mmap(filename)

    def save_mmap(self, filename):
        if filename.lower().endswith((".icf", ".ics")):
            icf.write_file(self, filename)
        else:
            super().save_mmap(filename)

    @classmethod
    def match_model(cls, filedata, filename):
        if (
            filename.lower().endswith((".icf", ".ics"))
            and filedata[:4] == b"2928"
        ):
            return True
        return super().match_model(filedata, filename)

    def get_raw_memory(self, number):
        _offset, raw = _record(self._mmap, self._channel_start, number)
        return repr(raw)

    def get_memory(self, number):
        mem = chirp_common.Memory()
        mem.number = number

        _offset, raw = _record(self._mmap, self._channel_start, number)
        rx_freq = _u32(raw, 0)
        tx_freq = _u32(raw, 4)
        flags = _flags(raw)

        if not (flags & FLAG_ACTIVE) or not _valid_frequency(rx_freq):
            mem.empty = True
            return mem

        mem.freq = chirp_common.fix_rounded_step(rx_freq)
        mem.name = _decode_name(raw[12:20])
        mem.mode = "FM"

        if (
            flags & FLAG_DUPLEX
            and _valid_frequency(tx_freq)
            and tx_freq != rx_freq
        ):
            mem.duplex = "split"
            mem.offset = tx_freq
        else:
            mem.duplex = ""
            mem.offset = 0

        return mem

    def set_memory(self, mem):
        offset, raw = _record(
            self._mmap, self._channel_start, mem.number
        )
        updated = bytearray(raw)
        flags = _flags(raw)

        if mem.empty:
            updated[0:4] = _pack_u32(0)
            updated[4:8] = _pack_u32(0x80000000)
            updated[8:10] = TONE_OFF_BYTES
            updated[10:12] = TONE_OFF_BYTES
            updated[12:20] = b" " * 8
            flags &= ~(FLAG_ACTIVE | FLAG_DUPLEX)
        else:
            if not _valid_frequency(mem.freq):
                raise errors.RadioError(
                    "IC-41S receive frequency must be between 450 and "
                    "520 MHz"
                )

            flags |= FLAG_ACTIVE
            tx_freq = mem.freq
            if mem.duplex == "split":
                tx_freq = mem.offset
                if not _valid_frequency(tx_freq):
                    raise errors.RadioError(
                        "IC-41S transmit frequency must be between 450 and "
                        "520 MHz"
                    )
                flags |= FLAG_DUPLEX
            else:
                flags &= ~FLAG_DUPLEX

            updated[0:4] = _pack_u32(mem.freq)
            updated[4:8] = _pack_u32(tx_freq)
            updated[12:20] = _encode_name(mem.name or "")

        updated[20:22] = _pack_flags(flags)
        self._mmap.set(offset, bytes(updated))
