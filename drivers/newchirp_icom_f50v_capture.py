# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Read-only capture profile for the Icom IC-F50V / IC-F60V.

No public memory map exists for these land-mobile handhelds, and Icom's
CS-F50V programmer is dealer software. Related Icom land-mobile radios in
CHIRP (``icf520.py``, IC-F621-2) use Icom's standard clone protocol: a
CLONE_ID (0xE0) query answered by a 4-byte model ID, then CLONE_OUT (0xE2)
answered by 16-byte data frames and an "Icom Inc." end frame.

This profile reads with that protocol without knowing the model ID or the
image size in advance. It asks the radio for its ID, clones out everything
the radio sends up to the end frame, and saves it. It decodes no channels
and can never write. Owners' captures are the evidence a real driver needs.
"""

import logging

from chirp import chirp_common, directory, errors, util
from chirp.drivers import icf


LOG = logging.getLogger(__name__)

# Largest image that still uses the 2-byte frame addresses of the related
# IC-F621 family; the image is truncated to what the radio actually sends.
CAPTURE_LIMIT = 0xFFFF
MODEL_KEY = "icom_capture_model_id"


@directory.register
class IcomF50VCapture(icf.IcomCloneModeRadio, chirp_common.ExperimentalRadio):
    """Icom IC-F50V / IC-F60V read-only capture."""

    VENDOR = "Icom"
    MODEL = "IC-F50V/F60V"
    VARIANT = "Capture"
    NEWCHIRP_WRITE_DISABLED = True
    BAUD_RATE = 9600

    _model = "\x00\x00\x00\x00"
    _memsize = CAPTURE_LIMIT
    _endframe = "Icom Inc."
    _ranges = []
    _can_hispeed = False

    @classmethod
    def get_prompts(cls):
        prompts = chirp_common.RadioPrompts()
        prompts.experimental = (
            "This profile only captures the radio's memory so NewChirp can "
            "learn the IC-F50V/F60V layout. It shows no channels and never "
            "writes to the radio. Save the image after reading and send it "
            "to the NewChirp team."
        )
        prompts.pre_download = (
            "1. Turn the radio off.\n"
            "2. Connect the Icom OPC-966 cable.\n"
            "3. Turn the radio on.\n"
            "4. Click OK to read, then save the image (File > Save).\n"
        )
        return prompts

    def get_features(self):
        rf = chirp_common.RadioFeatures()
        rf.memory_bounds = (1, 1)
        rf.has_bank = False
        rf.has_settings = False
        rf.has_name = False
        rf.has_ctone = False
        rf.has_tuning_step = False
        rf.valid_modes = ["FM"]
        rf.valid_tmodes = [""]
        rf.valid_duplexes = [""]
        rf.valid_bands = [(136000000, 470000000)]
        return rf

    @classmethod
    def match_model(cls, filedata, filename):
        # Only images saved by this profile (identified by metadata).
        return False

    def sync_in(self):
        model_data = icf.get_model_data(self)
        model_id = bytes(model_data[0:4])
        if len(model_id) != 4:
            raise errors.RadioError(
                "The radio answered the Icom identity query with %i bytes; "
                "expected a 4-byte model ID." % len(model_id)
            )
        LOG.info("Icom model data: %s", util.hexprint(model_data))
        # Clone out with the radio's own ID. Each bridge command runs in its
        # own process, so setting it on the class affects only this read.
        type(self)._model = model_id.decode("latin1")
        try:
            super().sync_in()
        except errors.RadioError as exc:
            raise errors.RadioError(
                "The radio identified as Icom model %s but the memory read "
                "failed: %s" % (model_id.hex(" ").upper(), exc)
            )
        self._metadata[MODEL_KEY] = model_id.hex(" ").upper()
        self._metadata["icom_capture_model_data"] = bytes(model_data).hex()
        self._metadata["icom_capture_size"] = len(self._mmap.get_packed())
        self.process_mmap()

    def process_mmap(self):
        model_id = self._metadata.get(MODEL_KEY) if self._metadata else None
        size = len(self._mmap.get_packed()) if self._mmap else 0
        self._firmware = (
            "Icom model ID %s, %i-byte capture" % (model_id, size)
            if model_id else "Icom capture, %i bytes" % size
        )

    def get_memory(self, number):
        mem = chirp_common.Memory()
        mem.number = number
        mem.empty = True
        return mem

    def set_memory(self, mem):
        raise errors.RadioError(
            "The IC-F50V/F60V capture profile is read-only."
        )

    def sync_out(self):
        raise errors.RadioError(
            "The IC-F50V/F60V capture profile is read-only."
        )


# --- Read-only channel decode -------------------------------------------
#
# Layout learned from an owner's IC-F60V capture (request INBOX:816, image
# INBOX:842; sha256 f94c00f3...eff3b, kept out of the repository). The image
# ends with a section directory of 10-byte big-endian entries
# (id, record size, count, offset, 0) whose sections tile the image without
# gaps from 0x180 up to the directory itself. Section 2 holds the channels.
# Seven of the owner's eight listed channels matched name and frequency.
#
# Channel record (0x22 bytes), confirmed fields only:
#   0x00  8  name, ASCII, space padded
#   0x08  4  RX frequency, Hz, big-endian (0 = empty)
#   0x0C  4  TX frequency, Hz, big-endian
#   0x10  4  two tone words; 0x8000 = none. Encoding unconfirmed, not shown.
#   0x14 14  flags and options, not decoded.

CHANNEL_SECTION = 2
CHANNEL_RECORD = 0x22
DIRECTORY_ENTRY = 10
MAX_CHANNELS = 512


def _u16(data, offset):
    return data[offset] << 8 | data[offset + 1]


def _u32(data, offset):
    return int.from_bytes(data[offset:offset + 4], "big")


def find_sections(data):
    """Return {section id: (record size, count, offset)} or None.

    The directory is located by requiring a run of at least three entries
    whose sections are contiguous, so random bytes cannot pass for it.
    """
    data = bytes(data)
    for start in range(0, len(data) - 3 * DIRECTORY_ENTRY + 1, 2):
        sections = {}
        position = start
        expected = None
        while position + DIRECTORY_ENTRY <= len(data):
            ident, size, count, offset, pad = (
                _u16(data, position + index)
                for index in range(0, DIRECTORY_ENTRY, 2))
            if pad or not size or not count or ident in sections:
                break
            if expected is not None and offset != expected:
                break
            end = offset + size * count
            if end > len(data):
                break
            sections[ident] = (size, count, offset)
            expected = end
            position += DIRECTORY_ENTRY
        if len(sections) >= 3 and expected == start:
            return sections
    return None


@directory.register
class IcomF60V(IcomF50VCapture):
    """Icom IC-F50V / IC-F60V, read-only channel view."""

    VARIANT = ""

    @classmethod
    def get_prompts(cls):
        prompts = super().get_prompts()
        prompts.experimental = (
            "IC-F50V/F60V support is read-only and new. NewChirp shows each "
            "channel's name and frequencies; tones and other options are "
            "not shown yet, and nothing is ever written to the radio. If a "
            "channel looks wrong, save the image and send it to the "
            "NewChirp team."
        )
        return prompts

    def process_mmap(self):
        super().process_mmap()
        data = self._mmap.get_packed() if self._mmap else b""
        self._sections = find_sections(data)
        channel = (self._sections or {}).get(CHANNEL_SECTION)
        if not channel or channel[0] != CHANNEL_RECORD:
            raise errors.RadioError(
                "NewChirp could not find the channel table in this "
                "IC-F50V/F60V image. Read it with the \"IC-F50V/F60V "
                "Capture\" profile, save it, and send it to the NewChirp "
                "team so this layout can be added."
            )
        self._channel_count = min(channel[1], MAX_CHANNELS)
        self._channel_offset = channel[2]

    def get_features(self):
        rf = super().get_features()
        rf.memory_bounds = (1, getattr(self, "_channel_count", 16))
        rf.has_name = True
        rf.valid_name_length = 8
        rf.valid_characters = chirp_common.CHARSET_ASCII
        rf.valid_duplexes = ["", "+", "-", "split"]
        rf.can_odd_split = True
        rf.valid_bands = [(136000000, 174000000), (400000000, 520000000)]
        return rf

    def get_raw_memory(self, number):
        offset = self._channel_offset + (number - 1) * CHANNEL_RECORD
        return util.hexprint(
            self._mmap.get_packed()[offset:offset + CHANNEL_RECORD])

    def get_memory(self, number):
        mem = chirp_common.Memory()
        mem.number = number
        data = self._mmap.get_packed()
        offset = self._channel_offset + (number - 1) * CHANNEL_RECORD
        record = data[offset:offset + CHANNEL_RECORD]
        rx = _u32(record, 0x08)
        tx = _u32(record, 0x0C)
        if not rx:
            mem.empty = True
            mem.immutable = ["empty"]
            return mem
        mem.freq = rx
        mem.name = record[0:8].decode("ascii", "replace").rstrip()
        if not tx or tx == rx:
            mem.duplex = ""
            mem.offset = 0
        elif abs(tx - rx) < 70000000:
            mem.duplex = "+" if tx > rx else "-"
            mem.offset = abs(tx - rx)
        else:
            mem.duplex = "split"
            mem.offset = tx
        mem.mode = "FM"
        mem.immutable = ["empty", "name", "freq", "duplex", "offset",
                         "tmode", "mode", "power", "skip"]
        return mem

    def set_memory(self, mem):
        raise errors.RadioError("IC-F50V/F60V support is read-only.")

    def sync_out(self):
        raise errors.RadioError("IC-F50V/F60V support is read-only.")

    @classmethod
    def match_model(cls, filedata, filename):
        # Saved capture images carry this or the capture profile's metadata;
        # raw images are only accepted when the section directory is present.
        return (filename.lower().endswith(".img")
                and b"ICOM Inc" in filedata[:0x200]
                and find_sections(filedata[:CAPTURE_LIMIT]) is not None)
