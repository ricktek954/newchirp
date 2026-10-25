# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Experimental read-only driver for the Retevis RT97L repeater.

The serial framing comes from independent analysis of the Windows RT97L
programmer. The 256-byte channel layout is still provisional and must be
confirmed against a capture from physical hardware. Uploads are intentionally
disabled until that validation is complete.
"""

import struct
import time

from chirp import chirp_common, directory, errors, memmap
from chirp.settings import (
    RadioSetting,
    RadioSettingGroup,
    RadioSettingValueBoolean,
    RadioSettingValueList,
)


MEM_SIZE = 0x100
CHANNEL_COUNT = 16
CHANNEL_SIZE = 0x10
READ_BLOCK_SIZE = 0x20
ACK = b"\x06"
STX = b"\x02"
END = b"E"
DEVICE_ID_PREFIX = b"P3"

POWER_LEVELS = [
    chirp_common.PowerLevel("High", watts=10),
    chirp_common.PowerLevel("Low", watts=5),
]

CTCSS_TONES = (
    "67.0", "69.3", "71.9", "74.4", "77.0", "79.7", "82.5", "85.4",
    "88.5", "91.5", "94.8", "97.4", "100.0", "103.5", "107.2", "110.9",
    "114.8", "118.8", "123.0", "127.3", "131.8", "136.5", "141.3", "146.2",
    "151.4", "156.7", "159.8", "162.2", "165.5", "167.9", "171.3", "173.8",
    "177.3", "179.9", "183.5", "186.2", "189.9", "192.8", "196.6", "199.5",
    "203.5", "206.5", "210.7", "218.1", "225.7", "229.1", "233.6", "241.8",
    "250.3", "254.1",
)

DCS_CODES = (
    23, 25, 26, 31, 32, 36, 43, 47, 51, 53, 54, 65, 71, 72, 73, 74,
    114, 115, 116, 122, 125, 131, 132, 134, 143, 145, 152, 155, 156,
    162, 165, 172, 174, 205, 212, 223, 225, 226, 243, 244, 245, 246,
    251, 252, 255, 261, 263, 265, 266, 271, 274, 306, 311, 315, 325,
    331, 332, 343, 346, 351, 356, 364, 365, 371, 411, 412, 413, 423,
    431, 432, 445, 446, 452, 454, 455, 462, 464, 465, 466, 503, 506,
    516, 523, 526, 532, 546, 565, 606, 612, 624, 627, 631, 632, 645,
    654, 662, 664, 703, 712, 723, 731, 732, 734, 743, 754,
)

SQUELCH_OPTIONS = ("Off",) + tuple(str(level) for level in range(10))
CHANNEL_MODE_OPTIONS = ("Frequency", "CH+Frequency")
COMPAND_OPTIONS = ("Wide", "Narrow")


def _setting(name, label, value, documentation):
    setting = RadioSetting(name, label, value)
    setting.set_doc(documentation)
    return setting


def _decode_frequency(raw):
    """Decode the RT97L's eight-digit BCD frequency, in 10 Hz units."""
    if len(raw) != 4 or raw in (b"\x00" * 4, b"\xff" * 4):
        return None

    digits = []
    for value in raw:
        high, low = value >> 4, value & 0x0F
        if high > 9 or low > 9:
            return None
        digits.extend((high, low))

    decimal = 0
    for digit in digits:
        decimal = decimal * 10 + digit
    frequency = decimal * 10
    if not 400_000_000 <= frequency <= 520_000_000:
        return None
    return frequency


def _decode_tone(index):
    """Return a CHIRP tone tuple for an RT97L combined tone-table index."""
    if 1 <= index <= len(CTCSS_TONES):
        return "Tone", float(CTCSS_TONES[index - 1]), None

    dcs_index = index - len(CTCSS_TONES) - 1
    if 0 <= dcs_index < len(DCS_CODES) * 2:
        code = DCS_CODES[dcs_index % len(DCS_CODES)]
        polarity = "N" if dcs_index < len(DCS_CODES) else "R"
        return "DTCS", code, polarity
    return "", None, None


@directory.register
class RT97LRadio(chirp_common.CloneModeRadio,
                 chirp_common.ExperimentalRadio):
    """Retevis RT97L experimental read-only driver."""

    VENDOR = "Retevis"
    MODEL = "RT97L"
    BAUD_RATE = 9600
    WANTS_DTR = True
    WANTS_RTS = True
    _memsize = MEM_SIZE

    @classmethod
    def get_prompts(cls):
        prompts = chirp_common.RadioPrompts()
        prompts.experimental = (
            "The Retevis RT97L driver is experimental and read-only. The "
            "download framing is known, but the 16-channel byte map still "
            "needs validation against physical hardware. Uploads are disabled."
        )
        prompts.info = (
            "Connect the RT97L using its stock USB programming cable, power "
            "the repeater, and start the download. The interface uses 9600 "
            "baud, 8 data bits, no parity, and one stop bit."
        )
        prompts.pre_download = (
            "1. Connect the stock programming cable and power on the RT97L.\n"
            "2. Close the Retevis programmer so it releases the serial port.\n"
            "3. Start the download and leave the repeater powered on.\n\n"
            "This first driver version is read-only. Please save the downloaded "
            "image and report channel, tone, power, or squelch differences to "
            "help validate the layout."
        )
        return prompts

    def get_features(self):
        rf = chirp_common.RadioFeatures()
        rf.has_settings = False
        rf.has_name = False
        rf.has_tuning_step = False
        rf.has_nostep_tuning = True
        rf.has_rx_dtcs = True
        rf.has_ctone = True
        rf.has_cross = True
        rf.can_odd_split = True
        rf.valid_modes = ["NFM"]
        rf.valid_duplexes = ["", "+", "-", "split"]
        rf.valid_tmodes = ["", "Tone", "TSQL", "DTCS", "Cross"]
        rf.valid_cross_modes = list(chirp_common.CROSS_MODES)
        rf.valid_power_levels = list(POWER_LEVELS)
        rf.valid_dtcs_codes = list(DCS_CODES)
        rf.valid_dtcs_pols = ["NN", "NR", "RN", "RR"]
        rf.valid_bands = [(400_000_000, 520_000_000)]
        rf.memory_bounds = (1, CHANNEL_COUNT)
        return rf

    def _read_exact(self, size, timeout=2.0):
        data = bytearray()
        deadline = time.monotonic() + timeout
        while len(data) < size:
            chunk = self.pipe.read(size - len(data))
            if chunk:
                data.extend(chunk)
            if time.monotonic() >= deadline:
                break
        if len(data) != size:
            raise errors.RadioNoResponse(
                "Expected %i bytes from the RT97L, received %i"
                % (size, len(data))
            )
        return bytes(data)

    def _enter_programming_mode(self):
        self.pipe.timeout = 2

        # Unlike request/response CHIRP drivers, the RT97L announces itself
        # before the host transmits anything. Do not flush the input buffer
        # here or the initial ACK can be discarded.
        if self._read_exact(1, timeout=2.0) != ACK:
            raise errors.RadioNoResponse(
                "The RT97L did not announce programming mode"
            )
        self.pipe.write(STX)
        identity = self._read_exact(8)
        if identity[:2] != DEVICE_ID_PREFIX or identity[7:] != b"\xff":
            raise errors.RadioError(
                "RT97L identification failed: %r" % identity
            )
        self.pipe.write(ACK)
        if self._read_exact(1) != ACK:
            raise errors.RadioError(
                "RT97L refused programming mode after identification"
            )

    def _read_block(self, address):
        command = struct.pack(">cHB", b"R", address, READ_BLOCK_SIZE)
        self.pipe.write(command)
        reply = self._read_exact(4 + READ_BLOCK_SIZE)
        if reply[:4] != struct.pack(">cHB", b"W", address, READ_BLOCK_SIZE):
            raise errors.RadioError(
                "RT97L returned an invalid block header at 0x%04x" % address
            )
        self.pipe.write(ACK)
        if self._read_exact(1) != ACK:
            raise errors.RadioError(
                "RT97L did not acknowledge block 0x%04x" % address
            )
        return reply[4:]

    def sync_in(self):
        session_started = False
        try:
            self._enter_programming_mode()
            session_started = True
            memory = memmap.MemoryMapBytes(b"\xff" * MEM_SIZE)
            addresses = range(0, MEM_SIZE, READ_BLOCK_SIZE)
            for current, address in enumerate(addresses, 1):
                status = chirp_common.Status()
                status.cur = current
                status.max = MEM_SIZE // READ_BLOCK_SIZE
                status.msg = "Reading RT97L configuration"
                self.status_fn(status)
                memory.set(address, self._read_block(address))
            self._mmap = memory
            self.process_mmap()
        except errors.RadioError:
            raise
        except Exception as exc:
            raise errors.RadioError(
                "Failed to communicate with the RT97L: %s" % exc
            ) from exc
        finally:
            if session_started:
                try:
                    self.pipe.write(END)
                except Exception:
                    pass

    def sync_out(self):
        raise errors.RadioError(
            "The experimental RT97L driver is read-only; uploads are disabled "
            "until the channel byte map and password write sequence are "
            "validated with physical hardware."
        )

    def process_mmap(self):
        return

    def get_raw_memory(self, number):
        offset = (number - 1) * CHANNEL_SIZE
        return repr(self._mmap.get(offset, CHANNEL_SIZE))

    def get_memory(self, number):
        if not 1 <= number <= CHANNEL_COUNT:
            raise errors.InvalidMemoryLocation(
                "Channel number must be between 1 and %i" % CHANNEL_COUNT
            )

        offset = (number - 1) * CHANNEL_SIZE
        raw = self._mmap.get(offset, CHANNEL_SIZE)
        mem = chirp_common.Memory()
        mem.number = number

        receive_frequency = _decode_frequency(raw[0:4])
        transmit_frequency = _decode_frequency(raw[4:8])
        if receive_frequency is None or transmit_frequency is None:
            mem.empty = True
        else:
            mem.freq = receive_frequency
            difference = transmit_frequency - receive_frequency
            if difference == 0:
                mem.duplex = ""
                mem.offset = 0
            elif abs(difference) <= 100_000_000:
                mem.duplex = "+" if difference > 0 else "-"
                mem.offset = abs(difference)
            else:
                mem.duplex = "split"
                mem.offset = transmit_frequency

            transmit_tone = _decode_tone(raw[8])
            receive_tone = _decode_tone(raw[9])
            chirp_common.split_tone_decode(
                mem,
                transmit_tone,
                receive_tone,
            )
            mem.mode = "NFM"
            flags1 = raw[10]
            mem.power = POWER_LEVELS[1 if flags1 & 0x01 else 0]
            flags2 = raw[12]
            mem.skip = "" if flags2 & 0x01 else "S"

        squelch = raw[11]
        squelch_index = 0 if squelch == 0xFF or squelch > 9 else squelch + 1
        flags1 = raw[10]
        flags2 = raw[12]
        mem.extra = RadioSettingGroup("Extra", "extra")
        extras = (
            _setting(
                "squelch",
                "Squelch",
                RadioSettingValueList(
                    SQUELCH_OPTIONS,
                    current_index=squelch_index,
                ),
                "Per-channel squelch level. Off means carrier squelch.",
            ),
            _setting(
                "channel_mode",
                "Channel mode",
                RadioSettingValueList(
                    CHANNEL_MODE_OPTIONS,
                    current_index=1 if flags1 & 0x04 else 0,
                ),
                "Shows whether the display uses a frequency or "
                "channel-plus-frequency mode.",
            ),
            _setting(
                "compand",
                "Compand",
                RadioSettingValueList(
                    COMPAND_OPTIONS,
                    current_index=1 if flags1 & 0x08 else 0,
                ),
                "Per-channel compander setting reported by the RT97L.",
            ),
            _setting(
                "scan_add",
                "Scan add",
                RadioSettingValueBoolean(bool(flags2 & 0x01)),
                "Includes the channel when the repeater scans its channel list.",
            ),
            _setting(
                "channel_lock",
                "Channel lock",
                RadioSettingValueBoolean(bool(flags2 & 0x02)),
                "Prevents changing this channel at the repeater controls.",
            ),
        )
        for setting in extras:
            setting.value.set_mutable(False)
            mem.extra.append(setting)
        return mem

    def set_memory(self, memory):
        raise errors.RadioError(
            "The experimental RT97L driver is read-only; channel writes are "
            "not enabled."
        )
