# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Experimental Yaesu FT-991A live CAT memory driver.

Yaesu documents the memory format through its CAT command manual. The public
FT-991A NVRAM work by Gil Kloepfer supplies the undocumented two-byte SPR/SPW
access contract and the channel-record offsets. This driver treats memory
channels as live records and preserves every byte outside the fields it
validates and edits.
"""

import logging
import struct
import time

from chirp import chirp_common, directory, errors


LOG = logging.getLogger(__name__)

IDENTIFICATION = "0670"
CAT_BAUD_RATES = (38400, 19200, 9600, 4800)
VISIBLE_BITMAP = 0x3229
FILLED_BITMAP = 0x3239
MEMORY_START = 0x3249
DCS_POLARITY_ADDRESS = 0x01E4
MEMORY_RECORD_SIZE = 96
MEMORY_COUNT = 117

CTCSS_TONES = (
    67.0, 69.3, 71.9, 74.4, 77.0, 79.7, 82.5, 85.4,
    88.5, 91.5, 94.8, 97.4, 100.0, 103.5, 107.2, 110.9,
    114.8, 118.8, 123.0, 127.3, 131.8, 136.5, 141.3, 146.2,
    151.4, 156.7, 159.8, 162.2, 165.5, 167.9, 171.3, 173.8,
    177.3, 179.9, 183.5, 186.2, 189.9, 192.8, 196.6, 199.5,
    203.5, 206.5, 210.7, 218.1, 225.7, 229.1, 233.6, 241.8,
    250.3, 254.1,
)
DCS_CODES = (
    23, 25, 26, 31, 32, 36, 43, 47, 51, 53, 54, 65, 71, 72,
    73, 74, 114, 115, 116, 122, 125, 131, 132, 134, 143, 145,
    152, 155, 156, 162, 165, 172, 174, 205, 212, 223, 225, 226,
    243, 244, 245, 246, 251, 252, 255, 261, 263, 265, 266, 271,
    274, 306, 311, 315, 325, 331, 332, 343, 346, 351, 356, 364,
    365, 371, 411, 412, 413, 423, 431, 432, 445, 446, 452, 454,
    455, 462, 464, 465, 466, 503, 506, 516, 523, 526, 532, 546,
    565, 606, 612, 624, 627, 631, 632, 654, 662, 664, 703, 712,
    723, 731, 732, 734, 743, 754,
)

MODE_TO_RADIO = {
    "LSB": 0x00,
    "USB": 0x01,
    "CW-USB": 0x02,
    "CW-LSB": 0x03,
    "AM": 0x04,
    "FM": 0x05,
    "NFM": 0x05,
    "RTTY-LSB": 0x06,
    "RTTY-USB": 0x07,
    "DATA-LSB": 0x08,
    "DATA-USB": 0x09,
    "DATA-FM": 0x0A,
    "C4FM": 0x0B,
}
RADIO_TO_MODE = {
    0x00: "LSB",
    0x01: "USB",
    0x02: "CW-USB",
    0x03: "CW-LSB",
    0x04: "AM",
    0x05: "FM",
    0x06: "RTTY-LSB",
    0x07: "RTTY-USB",
    0x08: "DATA-LSB",
    0x09: "DATA-USB",
    0x0A: "DATA-FM",
    0x0B: "C4FM",
}
TONE_MODE_TO_RADIO = {
    "": 0,
    "Tone": 2,
    "TSQL": 1,
    "DTCS": 4,
}
RADIO_TO_TONE_MODE = {
    0: "",
    1: "TSQL",
    2: "Tone",
    3: "Tone",
    4: "DTCS",
}


def _cat_checksum(data):
    return sum(data) & 0xFF


def _read_exact(pipe, size, timeout=1.0):
    deadline = time.monotonic() + timeout
    data = bytearray()
    while len(data) < size and time.monotonic() < deadline:
        chunk = pipe.read(size - len(data))
        if chunk:
            data.extend(chunk)
        else:
            time.sleep(0.005)
    return bytes(data)


def _read_until_semicolon(pipe, timeout=1.0):
    deadline = time.monotonic() + timeout
    data = bytearray()
    while time.monotonic() < deadline:
        chunk = pipe.read(1)
        if chunk:
            data.extend(chunk)
            if chunk == b";":
                break
        else:
            time.sleep(0.005)
    return bytes(data)


def _command(pipe, command, timeout=1.0):
    pipe.write(command.encode("ascii"))
    response = _read_until_semicolon(pipe, timeout=timeout)
    if not response:
        raise errors.RadioNoResponse(
            "No response to FT-991A CAT command %s" % command
        )
    if not response.endswith(b";"):
        raise errors.RadioNoResponse(
            "Incomplete FT-991A CAT response to %s: %s"
            % (command, response.decode("ascii", errors="replace"))
        )
    text = response.decode("ascii", errors="replace")
    return "" if text == "?;" else text[:-1]


def _read_pair(pipe, address):
    body = b"SPR" + struct.pack(">H", address)
    frame = body + bytes((_cat_checksum(body),)) + b";"
    pipe.write(frame)
    response = _read_exact(pipe, 9)
    if (
        len(response) != 9
        or response[:5] != body
        or response[-1:] != b";"
    ):
        raise errors.RadioError(
            "Invalid FT-991A SPR response at 0x%04X: %s"
            % (address, response.hex())
        )
    expected = (
        _cat_checksum(body) + response[5] + response[6]
    ) & 0xFF
    if response[7] != expected:
        raise errors.RadioError(
            "FT-991A SPR checksum mismatch at 0x%04X: got %02X, "
            "expected %02X" % (address, response[7], expected)
        )
    return response[5], response[6]


def _write_pair(pipe, address, first, second):
    body = b"SPW" + struct.pack(">HBB", address, first, second)
    frame = body + bytes((_cat_checksum(body),)) + b";"
    pipe.write(frame)
    response = _read_exact(pipe, 2)
    if response != b"A;":
        raise errors.RadioError(
            "FT-991A rejected SPW at 0x%04X (response %s)"
            % (address, response.hex())
        )


def _read_record(pipe, number, offsets):
    base = MEMORY_START + (number - 1) * MEMORY_RECORD_SIZE
    record = {}
    for offset in sorted(set(offset & ~1 for offset in offsets)):
        first, second = _read_pair(pipe, base + offset)
        record[offset] = first
        record[offset + 1] = second
    return record


def _write_changed_pairs(pipe, number, before, after):
    base = MEMORY_START + (number - 1) * MEMORY_RECORD_SIZE
    for offset in sorted(before):
        if offset & 1:
            continue
        first = before[offset]
        second = before[offset + 1]
        new_first = after.get(offset, first)
        new_second = after.get(offset + 1, second)
        if (new_first, new_second) != (first, second):
            _write_pair(pipe, base + offset, new_first, new_second)


@directory.register
class YaesuFT991ARadio(
    chirp_common.LiveRadio,
    chirp_common.ExperimentalRadio,
):
    """Yaesu FT-991A CAT channel programmer."""

    VENDOR = "Yaesu"
    MODEL = "FT-991A"
    BAUD_RATE = 38400
    HARDWARE_FLOW = False
    WANTS_RTS = True
    WANTS_DTR = False
    _detected_baud = None

    @classmethod
    def get_prompts(cls):
        prompts = chirp_common.RadioPrompts()
        prompts.experimental = (
            "Yaesu FT-991A support is experimental and uses the radio's "
            "live CAT interface. NewChirp reads and writes only documented "
            "channel fields and preserves unknown channel bytes. Back up "
            "the current channels with RT Systems or another programmer "
            "before the first write."
        )
        prompts.info = (
            "Use the radio's USB CAT port at 38400, 19200, 9600, or 4800 "
            "baud. Close other CAT applications and confirm menu 033 CAT RTS "
            "is enabled. NewChirp identifies the radio as FT-991A (CAT ID "
            "0670) and disables automatic information output."
        )
        return prompts

    @classmethod
    def detect_from_serial(cls, pipe):
        pipe.timeout = 0.35
        for baud in CAT_BAUD_RATES:
            pipe.baudrate = baud
            try:
                identity = _command(pipe, "ID;", timeout=0.5)
            except errors.RadioError:
                continue
            if identity.endswith(IDENTIFICATION):
                cls._detected_baud = baud
                return cls
        raise errors.RadioNoResponse(
            "FT-991A CAT identification was not received at any supported "
            "baud rate"
        )

    def __init__(self, pipe):
        super().__init__(pipe)
        if self._detected_baud:
            pipe.baudrate = self._detected_baud
        pipe.timeout = 0.35
        identity = self._command("ID;")
        if not identity.endswith(IDENTIFICATION):
            raise errors.RadioError(
                "Unsupported Yaesu CAT identity %r; expected FT-991A (%s)"
                % (identity, IDENTIFICATION)
            )
        try:
            self._command("AI0;")
        except errors.RadioError:
            LOG.debug("FT-991A did not acknowledge AI0")
        self._visible = None
        self._dcs_polarity = None

    def _command(self, command, timeout=1.0):
        return _command(self.pipe, command, timeout=timeout)

    def get_features(self):
        rf = chirp_common.RadioFeatures()
        rf.has_name = True
        rf.has_settings = False
        rf.has_bank = False
        rf.has_tuning_step = False
        rf.has_cross = False
        rf.can_odd_split = False
        rf.has_ctone = True
        rf.has_offset = True
        rf.valid_name_length = 12
        rf.valid_modes = list(MODE_TO_RADIO)
        rf.valid_tmodes = ["", "Tone", "TSQL", "DTCS"]
        rf.valid_duplexes = ["", "+", "-"]
        rf.valid_bands = [
            (1_800_000, 54_000_000),
            (144_000_000, 148_000_000),
            (430_000_000, 450_000_000),
        ]
        rf.memory_bounds = (1, MEMORY_COUNT)
        return rf

    def _read_bitmap(self, base):
        values = {}
        for offset in range(0, 16, 2):
            values[offset], values[offset + 1] = _read_pair(
                self.pipe, base + offset
            )
        return values

    def _ensure_visible(self, refresh=False):
        if self._visible is None or refresh:
            self._visible = self._read_bitmap(VISIBLE_BITMAP)
        return self._visible

    def _ensure_dcs_polarity(self):
        if self._dcs_polarity is None:
            first, _second = _read_pair(self.pipe, DCS_POLARITY_ADDRESS)
            self._dcs_polarity = ("NN", "NR", "RN", "RR")[
                (first >> 6) & 0x03
            ]
        return self._dcs_polarity

    def _is_visible(self, number):
        bitmap = self._ensure_visible()
        index = number - 1
        return bool(bitmap[index // 8] & (1 << (index % 8)))

    def _set_bitmap_bit(self, base, number, enabled):
        index = number - 1
        byte_index = index // 8
        pair_offset = byte_index & ~1
        if base == VISIBLE_BITMAP:
            bitmap = self._ensure_visible()
            current = bitmap[byte_index]
        else:
            first, second = _read_pair(self.pipe, base + pair_offset)
            current = first if byte_index == pair_offset else second
        mask = 1 << (index % 8)
        wanted = current | mask if enabled else current & ~mask
        if wanted == current:
            return
        first, second = _read_pair(self.pipe, base + pair_offset)
        pair = bytearray((first, second))
        local = byte_index - pair_offset
        pair[local] = wanted
        _write_pair(
            self.pipe,
            base + pair_offset,
            pair[0],
            pair[1],
        )
        if base == VISIBLE_BITMAP:
            bitmap[byte_index] = wanted

    def get_memory(self, number):
        if not 1 <= number <= MEMORY_COUNT:
            raise errors.InvalidMemoryLocation(
                "FT-991A memory number must be between 1 and %i"
                % MEMORY_COUNT
            )
        memory = chirp_common.Memory(number)
        if not self._is_visible(number):
            memory.empty = True
            return memory

        offsets = (0, 2, 4, 70, 72, 76, 78, 80, 82, 84, 86, 88, 90, 92, 94)
        record = _read_record(self.pipe, number, offsets)
        mode = record[0]
        memory.mode = RADIO_TO_MODE.get(mode, "FM")
        if mode == 0x05 and record[4] & 0x10:
            memory.mode = "NFM"
        memory.skip = "S" if record[1] & 0x01 else ""

        if record[2] & 0x02:
            shift = (record[2] >> 4) & 0x03
            memory.duplex = "+" if shift == 2 else "-"
        else:
            memory.duplex = ""
        memory.freq = int.from_bytes(
            bytes((record[76], record[77], record[78], record[79])),
            "big",
        )
        memory.offset = int.from_bytes(
            bytes((record[80], record[81], record[82], record[83])),
            "big",
        )
        if not memory.freq:
            memory.empty = True
            return memory
        if not memory.duplex:
            memory.offset = 0

        name = bytes(record[offset] for offset in range(84, 96))
        memory.name = name.split(b"\x00", 1)[0].decode(
            "ascii", errors="replace"
        ).rstrip()

        tone_mode = RADIO_TO_TONE_MODE.get((record[3] >> 2) & 0x07, "")
        memory.tmode = tone_mode
        if tone_mode in ("Tone", "TSQL"):
            tone_index = record[70]
            if tone_index < len(CTCSS_TONES):
                memory.rtone = CTCSS_TONES[tone_index]
                if tone_mode == "TSQL":
                    memory.ctone = CTCSS_TONES[tone_index]
        elif tone_mode == "DTCS":
            dcs_index = record[71]
            if dcs_index < len(DCS_CODES):
                memory.dtcs = DCS_CODES[dcs_index]
                memory.dtcs_polarity = self._ensure_dcs_polarity()
        return memory

    def set_memory(self, memory):
        number = int(memory.number)
        if not 1 <= number <= MEMORY_COUNT:
            raise errors.InvalidMemoryLocation(
                "FT-991A memory number must be between 1 and %i"
                % MEMORY_COUNT
            )
        if memory.empty:
            self.erase_memory(number)
            return
        validation_errors = self.validate_memory(memory)
        if validation_errors:
            raise errors.RadioError(validation_errors[0])

        offsets = (0, 2, 4, 70, 72, 76, 78, 80, 82, 84, 86, 88, 90, 92, 94)
        before = _read_record(self.pipe, number, offsets)
        after = dict(before)
        after[0] = MODE_TO_RADIO.get(memory.mode, 0x05)
        if memory.skip == "S":
            after[1] |= 0x01
        else:
            after[1] &= ~0x01

        after[2] &= ~((1 << 1) | (0x03 << 4))
        if memory.duplex in ("+", "-"):
            after[2] |= 1 << 1
            after[2] |= (2 if memory.duplex == "+" else 0) << 4
        if memory.mode == "NFM":
            after[4] |= 0x10
        elif memory.mode == "FM":
            after[4] &= ~0x10

        tone_mode = TONE_MODE_TO_RADIO.get(memory.tmode, 0)
        after[3] = (after[3] & ~(0x07 << 2)) | (tone_mode << 2)
        if memory.tmode in ("Tone", "TSQL"):
            try:
                index = min(
                    range(len(CTCSS_TONES)),
                    key=lambda pos: abs(CTCSS_TONES[pos] - float(memory.rtone)),
                )
            except (TypeError, ValueError) as exc:
                raise errors.RadioError(
                    "FT-991A does not support CTCSS %r" % memory.rtone
                ) from exc
            if abs(CTCSS_TONES[index] - float(memory.rtone)) > 0.05:
                raise errors.RadioError(
                    "FT-991A does not support CTCSS %.1f Hz" % memory.rtone
                )
            after[70] = index
        elif memory.tmode == "DTCS":
            if memory.dtcs_polarity != self._ensure_dcs_polarity():
                raise errors.RadioError(
                    "FT-991A DCS polarity %s is radio-wide; change it in "
                    "the radio menu before writing this channel"
                    % self._ensure_dcs_polarity()
                )
            try:
                after[71] = DCS_CODES.index(int(memory.dtcs))
            except (TypeError, ValueError) as exc:
                raise errors.RadioError(
                    "FT-991A does not support DCS %r" % memory.dtcs
                ) from exc

        frequency = int(memory.freq)
        offset = int(memory.offset) if memory.duplex in ("+", "-") else 0
        after.update({
            76: (frequency >> 24) & 0xFF,
            77: (frequency >> 16) & 0xFF,
            78: (frequency >> 8) & 0xFF,
            79: frequency & 0xFF,
            80: (offset >> 24) & 0xFF,
            81: (offset >> 16) & 0xFF,
            82: (offset >> 8) & 0xFF,
            83: offset & 0xFF,
        })
        name = str(memory.name or "")[:12].encode(
            "ascii", errors="replace"
        ).ljust(12, b" ")
        for index, value in enumerate(name):
            after[84 + index] = value

        _write_changed_pairs(self.pipe, number, before, after)
        self._set_bitmap_bit(VISIBLE_BITMAP, number, True)
        self._set_bitmap_bit(FILLED_BITMAP, number, True)

    def erase_memory(self, number):
        if not 1 <= number <= MEMORY_COUNT:
            raise errors.InvalidMemoryLocation(
                "FT-991A memory number must be between 1 and %i"
                % MEMORY_COUNT
            )
        if not self._is_visible(number):
            return
        self._set_bitmap_bit(VISIBLE_BITMAP, number, False)
