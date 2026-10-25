# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Experimental read-only driver for the Radtel RT-950.

The transport, block map, and channel record layout were recovered from the
RT-950 CPS v1.3.0 with static managed-IL analysis. This initial driver exposes
channel reads only. Uploads remain disabled until the write framing, encryption
path, and all settings blocks have been independently validated.
"""

import logging
import time

from chirp import chirp_common, directory, errors, memmap
from chirp.settings import (
    RadioSetting,
    RadioSettingGroup,
    RadioSettingValueBoolean,
    RadioSettingValueInteger,
    RadioSettingValueList,
    RadioSettingValueString,
)


LOG = logging.getLogger(__name__)

MEM_SIZE = 0xC100
CHANNEL_COUNT = 960
CHANNEL_RECORD_SIZE = 0x20
BLOCK_SIZE = 0x80

ACK = b"\x06"
HANDSHAKE = b"PROGRAMBT9000U"
MODEL_CODE = b"BT-9000"

# The CPS deliberately skips the unused regions between these ranges.
READ_RANGES = (
    (0x0000, 0x7800),
    (0x8000, 0x8080),
    (0x9000, 0x9080),
    (0xA000, 0xA180),
    (0xB000, 0xB080),
    (0xC000, 0xC100),
)

POWER_LEVELS = ["High", "Middle", "Low"]
# These are the 105 codes in the CPS DCS table. Reversed codes follow the
# normal codes in the same order.
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

SCRAMBLE_OPTIONS = (
    "Off",
    "Scramble 1",
    "Scramble 2",
    "Scramble 3",
    "Scramble 4",
    "Scramble 5",
    "Scramble 6",
    "Scramble 7",
    "Scramble 8",
)

ENCRYPTION_OPTIONS = (
    "Off",
    "Encryption 1",
    "Encryption 2",
    "Encryption 3",
)

PTT_ID_OPTIONS = ("Off", "PTT ID 1", "PTT ID 2", "PTT ID 3")


def _read_blocks():
    for start, end in READ_RANGES:
        for address in range(start, end, BLOCK_SIZE):
            yield address


def _decode_frequency(raw):
    """Decode the CPS two-digits-per-byte decimal frequency format."""
    transformed = []
    for value in raw:
        high, low = value >> 4, value & 0x0F
        if high > 9 or low > 9:
            raise errors.InvalidDataError(
                "Invalid packed frequency 0x%02x" % value
            )
        transformed.append(high * 10 + low)

    value = 0
    for part in transformed:
        value = value * 100 + part
    # Channel frequencies are stored in 10 Hz units.
    return value * 10


def _decode_tone(raw):
    word = int.from_bytes(raw, "little")
    if word in (0x0000, 0xFFFF):
        return None, None, None

    # DCS uses a one-based index in byte zero and leaves byte one clear.
    if raw[1] == 0:
        index = raw[0] - 1
        if 0 <= index < len(DCS_CODES) * 2:
            code = DCS_CODES[index % len(DCS_CODES)]
            polarity = "N" if index < len(DCS_CODES) else "R"
            return "DTCS", code, polarity
        return None, None, None

    return "Tone", word / 10.0, None


def _extra(name, label, value, doc):
    setting = RadioSetting(name, label, value)
    setting.set_doc(doc)
    return setting


@directory.register
class RT950Radio(chirp_common.CloneModeRadio,
                 chirp_common.ExperimentalRadio):
    """Radtel RT-950 experimental read-only driver."""

    VENDOR = "Radtel"
    MODEL = "RT-950"
    BAUD_RATE = 115200
    HARDWARE_FLOW = True
    XON_XOFF = True
    WANTS_DTR = True
    WANTS_RTS = True

    _memsize = MEM_SIZE

    @classmethod
    def get_prompts(cls):
        prompts = chirp_common.RadioPrompts()
        prompts.experimental = (
            "The Radtel RT-950 driver is experimental and read-only. It "
            "downloads and decodes channel memories, but uploads are "
            "disabled until the CPS write protocol and settings blocks have "
            "been independently verified with hardware."
        )
        prompts.info = (
            "Connect the radio with its USB programming cable, turn the "
            "radio on, and start the download. The interface uses 115200 "
            "baud, 8 data bits, no parity, one stop bit, and hardware flow "
            "control with XON/XOFF."
        )
        prompts.pre_download = (
            "1. Turn the radio on and connect its USB programming cable.\n"
            "2. Close the Radtel CPS so it does not hold the serial port.\n"
            "3. Start the download and leave the radio powered on.\n\n"
            "This driver is read-only. Do not attempt an upload."
        )
        return prompts

    def get_features(self):
        rf = chirp_common.RadioFeatures()
        rf.has_rx_dtcs = True
        rf.has_name = True
        rf.has_settings = False
        rf.has_tuning_step = False
        rf.has_cross = True
        rf.can_odd_split = True
        rf.memory_bounds = (1, CHANNEL_COUNT)
        rf.valid_bands = [(18000000, 1000000000)]
        rf.valid_modes = ["FM", "NFM", "AM", "NAM"]
        rf.valid_duplexes = ["", "+", "-", "split"]
        rf.valid_tmodes = ["", "Tone", "TSQL", "DTCS", "Cross"]
        rf.valid_cross_modes = list(chirp_common.CROSS_MODES)
        rf.valid_tuning_steps = [5.0]
        rf.valid_power_levels = list(POWER_LEVELS)
        rf.valid_dtcs_codes = list(DCS_CODES)
        rf.valid_dtcs_pols = ["NN", "NR", "RN", "RR"]
        rf.valid_name_length = 12
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
                "Expected %i bytes from the RT-950, received %i"
                % (size, len(data))
            )
        return bytes(data)

    def _handshake_once(self):
        if hasattr(self.pipe, "reset_input_buffer"):
            self.pipe.reset_input_buffer()

        self.pipe.write(HANDSHAKE)
        if self._read_exact(1, timeout=1.5) != ACK:
            raise errors.RadioNoResponse(
                "The RT-950 did not acknowledge programming mode"
            )

        # The CPS discards this 16-byte response. Requiring it avoids treating
        # unrelated serial traffic as a valid programming session.
        self.pipe.write(b"F")
        self._read_exact(16)

        self.pipe.write(b"M")
        model = self._read_exact(12).replace(b"\x00", b"").strip()
        if model != MODEL_CODE:
            raise errors.RadioError(
                "RT-950 driver expected model %s, radio reported %r"
                % (MODEL_CODE.decode("ascii"), model)
            )

    def _handshake(self):
        last_error = None
        for _attempt in range(3):
            try:
                self._handshake_once()
                return
            except errors.RadioError as exc:
                last_error = exc
        raise last_error

    def _read_block(self, address):
        command = bytes((ord("R"), address >> 8, address & 0xFF, BLOCK_SIZE))
        self.pipe.write(command)
        reply = self._read_exact(4 + BLOCK_SIZE)
        # The CPS confirms only the echoed address. It does not require a
        # particular response command byte or re-check the requested length.
        if reply[1:3] != command[1:3]:
            raise errors.RadioError(
                "RT-950 returned the wrong block address for 0x%04x: %r"
                % (address, reply[1:3])
            )
        return reply[4:]

    def sync_in(self):
        session_started = False
        try:
            self._handshake()
            session_started = True

            memory = memmap.MemoryMapBytes(b"\xff" * MEM_SIZE)
            addresses = tuple(_read_blocks())
            for current, address in enumerate(addresses, 1):
                status = chirp_common.Status()
                status.cur = current
                status.max = len(addresses)
                status.msg = "Reading channel memory"
                self.status_fn(status)
                memory.set(address, self._read_block(address))
        except errors.RadioError:
            raise
        except Exception as exc:
            raise errors.RadioError(
                "Failed to communicate with the RT-950: %s" % exc
            ) from exc
        finally:
            if session_started:
                try:
                    self.pipe.write(b"E")
                except Exception:
                    pass

        self._mmap = memory
        self.process_mmap()

    def sync_out(self):
        raise errors.RadioError(
            "The experimental RT-950 driver is read-only; radio uploads are "
            "disabled until write framing and checksums are verified."
        )

    def process_mmap(self):
        return

    def get_raw_memory(self, number):
        offset = (number - 1) * CHANNEL_RECORD_SIZE
        return repr(self._mmap.get(offset, CHANNEL_RECORD_SIZE))

    @staticmethod
    def _decode_name(raw):
        raw = raw.split(b"\x00", 1)[0].replace(b"\xff", b"")
        return raw.decode("gb2312", errors="replace").strip()

    def get_memory(self, number):
        if not 1 <= number <= CHANNEL_COUNT:
            raise errors.InvalidMemoryLocation(
                "Channel number must be between 1 and %i" % CHANNEL_COUNT
            )

        offset = (number - 1) * CHANNEL_RECORD_SIZE
        raw = self._mmap.get(offset, CHANNEL_RECORD_SIZE)
        mem = chirp_common.Memory()
        mem.number = number
        mem.empty = raw[:4] in (b"\x00" * 4, b"\xff" * 4)

        bcl = tx_enabled = hopping = False
        signalling_group = ptt_id = scramble = encryption = 0
        fhss_code = ""
        if not mem.empty:
            mem.freq = _decode_frequency(raw[0:4])
            tx_freq = _decode_frequency(raw[4:8])
            offset_hz = tx_freq - mem.freq
            if offset_hz == 0:
                mem.duplex = ""
                mem.offset = 0
            elif abs(offset_hz) < 10_000_000:
                mem.duplex = "+" if offset_hz > 0 else "-"
                mem.offset = abs(offset_hz)
            else:
                mem.duplex = "split"
                mem.offset = tx_freq

            rx_tone = _decode_tone(raw[8:10])
            tx_tone = _decode_tone(raw[10:12])
            chirp_common.split_tone_decode(mem, tx_tone, rx_tone)

            am = bool(raw[15] & 0x01)
            narrow = bool(raw[15] & 0x40)
            if am:
                mem.mode = "NAM" if narrow else "AM"
            else:
                mem.mode = "NFM" if narrow else "FM"
            mem.power = POWER_LEVELS[min(raw[14] & 0x0F, 2)]
            mem.skip = "" if raw[15] & 0x04 else "S"
            mem.name = self._decode_name(raw[20:32])

            bcl = bool(raw[15] & 0x08)
            tx_enabled = not bool(raw[15] & 0x02)
            heading = (raw[14] >> 4) & 0x0F
            scramble = heading if heading < len(SCRAMBLE_OPTIONS) else 0
            encryption = min((raw[15] >> 4) & 0x03, 3)
            hopping = bool(raw[15] & 0x80)
            signalling_group = raw[12] & 0x0F
            ptt_id = min(raw[13] & 0x03, 3)
            if raw[19] == 0xA0:
                nibbles = (
                    (raw[16] >> 4) & 0x0F,
                    raw[16] & 0x0F,
                    (raw[17] >> 4) & 0x0F,
                    raw[17] & 0x0F,
                    (raw[18] >> 4) & 0x0F,
                    raw[18] & 0x0F,
                )
                fhss_code = "".join("0123456789ABCDEF"[value]
                                    for value in nibbles)

        mem.extra = RadioSettingGroup("Extra", "extra")
        extras = (
            _extra(
                "bcl", "Busy channel lockout",
                RadioSettingValueBoolean(bcl),
                "Prevents transmitting while the channel is already busy.",
            ),
            _extra(
                "tx_enabled", "Transmit enabled",
                RadioSettingValueBoolean(tx_enabled),
                "Shows whether the CPS permits transmission on this channel.",
            ),
            _extra(
                "scramble", "Voice inversion",
                RadioSettingValueList(
                    SCRAMBLE_OPTIONS, current_index=scramble
                ),
                "Selects the analog voice-inversion key used by the channel.",
            ),
            _extra(
                "encryption", "Encryption",
                RadioSettingValueList(
                    ENCRYPTION_OPTIONS, current_index=encryption
                ),
                "Selects the digital encryption key reported by the radio.",
            ),
            _extra(
                "hopping", "Frequency hopping",
                RadioSettingValueBoolean(hopping),
                "Shows whether frequency-hopping mode is enabled.",
            ),
            _extra(
                "signalling_group", "Signalling group",
                RadioSettingValueInteger(0, 15, signalling_group),
                "Selects the channel's signalling or remote-control group.",
            ),
            _extra(
                "ptt_id", "PTT ID",
                RadioSettingValueList(
                    PTT_ID_OPTIONS, current_index=ptt_id
                ),
                "Selects the identifier sent when the transmitter is keyed.",
            ),
        )
        for setting in extras:
            mem.extra.append(setting)

        fhss = _extra(
            "fhss_code", "FHSS code",
            RadioSettingValueString(0, 6, fhss_code, autopad=False),
            "Six-digit code used by frequency-hopping mode.",
        )
        fhss.value.set_mutable(False)
        mem.extra.append(fhss)
        return mem

    def set_memory(self, memory):
        raise errors.RadioError(
            "The experimental RT-950 driver is read-only; channel writes are "
            "not enabled."
        )
