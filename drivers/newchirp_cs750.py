# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Experimental Connect Systems CS750 codeplug importer.

This driver reads the `.rdb` archive produced by the official CSI CPS. It is
deliberately import-only: the radio's USB mass-storage transport is different
from CHIRP's serial clone transport and has not yet been validated with
hardware.
"""

from chirp import chirp_common, directory, errors, memmap


MAGIC_VERSION = b"CS750"
SUPPORTED_MODEL = b"M100000"
SUPPORTED_SIZE = 0x44010
CHANNEL_LIMIT = 2000
CHANNEL_TABLE = 0x12000
CHANNEL_INDEX = 0x21F60
CHANNEL_NAME_TABLE = 0xA000

ALIAS_ALPHABET = (
    "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz ."
)


def _decode_alias(raw):
    """Decode the CPS 6-bit 16-byte alias format."""
    result = []
    for offset in range(0, 15, 3):
        first, second, third = raw[offset:offset + 3]
        result.extend((
            ALIAS_ALPHABET[(first >> 2) & 0x3F],
            ALIAS_ALPHABET[((second >> 4) & 0x0F) | ((first & 0x03) << 4)],
            ALIAS_ALPHABET[((third >> 6) & 0x03) | ((second & 0x0F) << 2)],
            ALIAS_ALPHABET[third & 0x3F],
        ))
    return "".join(result[:16]).rstrip()


@directory.register
class CS750Radio(chirp_common.CloneModeRadio,
                 chirp_common.ExperimentalRadio):
    """Connect Systems CS750 CPS codeplug importer."""

    VENDOR = "Connect Systems"
    MODEL = "CS750"
    FILE_EXTENSION = "rdb"
    FORMATS = [
        directory.register_format("Connect Systems CS750 CPS", "*.rdb"),
    ]
    NEWCHIRP_TRANSPORT = "scsi_rap"
    _memsize = SUPPORTED_SIZE

    @classmethod
    def match_model(cls, filedata, filename):
        return (
            len(filedata) == SUPPORTED_SIZE
            and filedata[0x2000:0x2005] == MAGIC_VERSION
            and filedata[0x2068:0x206F] == SUPPORTED_MODEL
        )

    @classmethod
    def get_prompts(cls):
        prompts = chirp_common.RadioPrompts()
        prompts.experimental = (
            "The Connect Systems CS750 driver is experimental. It can import "
            "CPS R4.x codeplugs and perform a read-only live download from "
            "M100000/2000-channel radios using NewChirp's own USB "
            "mass-storage transport. Upload is not enabled."
        )
        prompts.info = (
            "On macOS, connect the radio's USB programming interface and "
            "choose the STM microSD Flash interface listed by NewChirp. The "
            "experimental transport is read-only. You can also use the "
            "official CSI CPS to save an '.rdb' archive and open it directly. "
            "Channel tone, color-code, contact, and scan-list details are not "
            "yet decoded."
        )
        prompts.pre_download = (
            "1. Turn the radio on and connect its programming cable.\n"
            "2. Close the CSI CPS so it releases the USB interface.\n"
            "3. Choose the STM microSD Flash interface in NewChirp.\n"
            "4. Start the download and leave the radio connected.\n\n"
            "This transport is read-only. Do not attempt an upload."
        )
        return prompts

    def get_features(self):
        rf = chirp_common.RadioFeatures()
        rf.has_name = True
        rf.has_settings = False
        rf.has_tuning_step = False
        rf.has_cross = False
        rf.can_odd_split = True
        rf.valid_name_length = 16
        rf.valid_modes = ["FM", "DMR"]
        rf.valid_duplexes = ["", "+", "-", "split"]
        rf.valid_bands = [
            (136000000, 174000000),
            (400000000, 470000000),
        ]
        rf.memory_bounds = (1, self._channel_count() or 1)
        return rf

    def _channel_count(self):
        if self._mmap is None or len(self._mmap.get_packed()) < CHANNEL_INDEX + 2:
            return 0
        return int.from_bytes(
            self._mmap.get(CHANNEL_INDEX, 2), "little"
        )

    def _channel_index(self, number):
        offset = CHANNEL_INDEX + 2 + (number - 1) * 2
        return int.from_bytes(self._mmap.get(offset, 2), "little")

    def process_mmap(self):
        data = self._mmap.get_packed()
        if len(data) != SUPPORTED_SIZE:
            raise errors.RadioError(
                "Unsupported CS750 codeplug size 0x%x; expected 0x%x"
                % (len(data), SUPPORTED_SIZE)
            )
        if data[0x2000:0x2005] != MAGIC_VERSION:
            raise errors.RadioError("Not a Connect Systems CS750 codeplug")
        if data[0x2068:0x206F] != SUPPORTED_MODEL:
            raise errors.RadioError(
                "Unsupported CS750 model %r; this importer supports %s"
                % (
                    data[0x2068:0x206F].decode("ascii", errors="replace"),
                    SUPPORTED_MODEL.decode("ascii"),
                )
            )
        if self._channel_count() > CHANNEL_LIMIT:
            raise errors.RadioError(
                "CS750 codeplug reports more than %i channels"
                % CHANNEL_LIMIT
            )

    def sync_in(self):
        from newchirp_mass_storage import CS750Profile

        def progress(current, total):
            status = chirp_common.Status()
            status.cur = current
            status.max = total
            status.msg = "Reading CS750 codeplug"
            self.status_fn(status)

        profile = CS750Profile(self.pipe)
        try:
            image = profile.read_codeplug(progress=progress)
        finally:
            profile.close()
        self._mmap = memmap.MemoryMapBytes(image)
        self.process_mmap()

    def sync_out(self):
        raise errors.RadioError(
            "The experimental CS750 driver is read-only and import-only."
        )

    def get_raw_memory(self, number):
        if not 1 <= number <= self._channel_count():
            raise errors.InvalidMemoryLocation(
                "CS750 channel must be between 1 and %i"
                % self._channel_count()
            )
        index = self._channel_index(number)
        record = self._mmap.get(
            CHANNEL_TABLE + (index - 1) * 0x20, 0x20
        )
        alias = self._mmap.get(
            CHANNEL_NAME_TABLE + (index - 1) * 0x10, 0x10
        )
        return "record=%s alias=%s" % (record.hex(), alias.hex())

    def get_memory(self, number):
        count = self._channel_count()
        if not 1 <= number <= count:
            raise errors.InvalidMemoryLocation(
                "CS750 channel must be between 1 and %i" % count
            )

        index = self._channel_index(number)
        if not 1 <= index <= CHANNEL_LIMIT:
            raise errors.RadioError(
                "CS750 channel %i references invalid record %i"
                % (number, index)
            )

        record = self._mmap.get(
            CHANNEL_TABLE + (index - 1) * 0x20, 0x20
        )
        alias = self._mmap.get(
            CHANNEL_NAME_TABLE + (index - 1) * 0x10, 0x10
        )

        mem = chirp_common.Memory()
        mem.number = number
        mem.freq = int.from_bytes(record[0:4], "little")
        tx_freq = int.from_bytes(record[4:8], "little")
        offset = tx_freq - mem.freq
        if offset == 0:
            mem.duplex = ""
            mem.offset = 0
        elif abs(offset) < 10_000_000:
            mem.duplex = "+" if offset > 0 else "-"
            mem.offset = abs(offset)
        else:
            mem.duplex = "split"
            mem.offset = tx_freq

        # Bit zero is set on the stock analog channel and clear on the stock
        # digital channel. The remaining flag bits are not yet decoded.
        mem.mode = "FM" if record[8] & 0x01 else "DMR"
        mem.name = _decode_alias(alias)
        return mem

    def set_memory(self, memory):
        raise errors.RadioError(
            "The experimental CS750 driver is read-only and import-only."
        )
