# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Read-only Baofeng K67 Pro driver recovered from the official K6 CPS."""

import logging
import struct
import time

from chirp import chirp_common, directory, errors, memmap


LOG = logging.getLogger(__name__)

MEM_SIZE = 0x0D040
CHANNEL_SIZE = 32
CHANNEL_COUNT = 1000
PROGRAM = b"PROGRAMBF-K6PROU"
IDENTITY_BYTES = (16, 15)
READ_ACK = 0x06
READ_COMMAND = b"R"
END_COMMAND = b"E"

READ_RANGES = (
    (0x0000, 0x7D00),
    (0x7D00, 0x7D40),
    (0x9000, 0x9080),
    (0xA000, 0xA2C0),
    (0xC000, 0xC040),
    (0xD000, 0xD040),
)

CTCSS_VALUES = (
    670, 693, 719, 744, 770, 797, 825, 854, 885, 915,
    948, 974, 1000, 1035, 1072, 1109, 1148, 1188, 1230,
    1273, 1318, 1365, 1413, 1462, 1514, 1567, 1598, 1622,
    1655, 1679, 1713, 1738, 1773, 1799, 1835, 1862, 1899,
    1928, 1966, 1995, 2035, 2065, 2107, 2181, 2257, 2291,
    2336, 2418, 2503, 2541,
)

DCS_VALUES = (
    23, 25, 26, 31, 32, 36, 43, 47, 51, 53, 54, 65, 71, 72,
    73, 74, 114, 115, 116, 122, 125, 131, 132, 134, 143, 145,
    152, 155, 156, 162, 165, 172, 174, 205, 212, 223, 225,
    226, 243, 244, 245, 246, 251, 252, 255, 261, 263, 265,
    266, 271, 274, 306, 311, 315, 325, 331, 332, 343, 346,
    351, 356, 364, 365, 371, 411, 412, 413, 423, 431, 432,
    445, 446, 452, 454, 455, 462, 464, 465, 466, 503, 506,
    516, 523, 526, 532, 546, 565, 606, 612, 624, 627, 631,
    632, 645, 654, 662, 664, 703, 712, 723, 731, 732, 734,
    743, 754,
)

POWER_LEVELS = (
    chirp_common.PowerLevel("High"),
    chirp_common.PowerLevel("Low"),
)


def _decode_frequency(raw):
    raw = bytes(raw)
    if len(raw) != 4 or any(byte == 0xFF for byte in raw):
        return None
    digits = "".join("%02x" % byte for byte in reversed(raw))
    try:
        return int(digits, 10) * 100
    except ValueError:
        return None


def _encode_frequency(frequency):
    value = int(frequency // 100)
    digits = "%08d" % value
    return bytes(
        int(digits[index:index + 2], 16)
        for index in range(6, -1, -2)
    )


def _decode_tone(raw):
    low, high = bytes(raw)
    if low == 0 and high == 0:
        return "", None, None, "N"
    if high == 0:
        if 1 <= low <= len(DCS_VALUES):
            return "DTCS", DCS_VALUES[low - 1], None, "N"
        if 1 <= low <= len(DCS_VALUES) * 2:
            return "DTCS", DCS_VALUES[low - len(DCS_VALUES) - 1], None, "R"
        return "", None, None, "N"
    ctcss = (high << 8 | low) / 10.0
    if ctcss not in chirp_common.TONES:
        return "", None, None, "N"
    return "Tone", None, ctcss, "N"


def _encode_tone(mode, code, polarity, tone):
    if mode == "DTCS" and code in DCS_VALUES:
        index = DCS_VALUES.index(code)
        if polarity == "R":
            index += len(DCS_VALUES)
        return bytes((index + 1, 0))
    if mode == "Tone" and tone:
        value = int(round(tone * 10))
        return bytes((value & 0xFF, value >> 8))
    return b"\x00\x00"


def _decode_name(raw):
    raw = bytes(raw)
    raw = raw.split(b"\x00", 1)[0].rstrip(b"\xff ")
    if not raw:
        return ""
    try:
        return raw.decode("gb2312").strip()
    except UnicodeDecodeError:
        return raw.decode("latin-1", "replace").strip()


@directory.register
class BaofengK67ProRadio(chirp_common.CloneModeRadio,
                        chirp_common.ExperimentalRadio):
    """Baofeng K67 Pro, CPS-derived read-only profile."""

    VENDOR = "Baofeng"
    MODEL = "K67 Pro"
    VARIANT = "CPS V1.1.2"
    BAUD_RATE = 115200
    WANTS_DTR = True
    WANTS_RTS = True
    _file_ident = b"K67PRO"
    _memsize = MEM_SIZE

    @classmethod
    def get_prompts(cls):
        prompts = chirp_common.RadioPrompts()
        prompts.experimental = (
            "The Baofeng K67 Pro driver is experimental and read-only. "
            "It is derived from the official Baofeng K6 CPS V1.1.2. Uploads "
            "remain disabled until a physical read and controlled write/read-"
            "back are verified."
        )
        prompts.pre_download = (
            "Connect the K67 Pro programming cable, turn the radio on to a "
            "normal channel, close Baofeng CPS, and select the cable's COM "
            "port."
        )
        return prompts

    def get_features(self):
        rf = chirp_common.RadioFeatures()
        rf.memory_bounds = (1, 1000)
        rf.has_settings = False
        rf.has_ctone = True
        rf.has_rx_dtcs = True
        rf.has_cross = True
        rf.can_odd_split = True
        rf.valid_tmodes = ["", "Tone", "TSQL", "DTCS", "Cross"]
        rf.valid_cross_modes = [
            "Tone->Tone",
            "Tone->DTCS",
            "DTCS->Tone",
            "DTCS->",
            "->Tone",
            "->DTCS",
            "DTCS->DTCS",
        ]
        rf.valid_duplexes = ["", "-", "+", "split", "off"]
        rf.valid_modes = ["FM", "NFM", "AM"]
        rf.valid_power_levels = list(POWER_LEVELS)
        rf.valid_skips = ["", "S"]
        rf.valid_name_length = 12
        rf.valid_characters = chirp_common.CHARSET_ASCII
        rf.valid_bands = [(65_000_000, 600_000_000)]
        return rf

    def _read_count(self, count, timeout=2.0):
        deadline = time.monotonic() + timeout
        result = b""
        while len(result) < count and time.monotonic() < deadline:
            chunk = self.pipe.read(count - len(result))
            if chunk:
                result += chunk
        if len(result) != count:
            raise errors.RadioError(
                "K67 Pro returned %i of %i expected bytes"
                % (len(result), count)
            )
        return result

    def _identify(self):
        self.pipe.reset_input_buffer()
        self.pipe.write(PROGRAM)
        ack = self._read_count(1)
        if ack != bytes((READ_ACK,)):
            raise errors.RadioError(
                "The K67 Pro rejected the programming handshake: %r" % ack
            )
        self.pipe.write(b"F")
        identity = self._read_count(sum(IDENTITY_BYTES))
        LOG.debug("K67 Pro identity: %s", identity.hex())
        if b"K6PROU" not in identity:
            raise errors.RadioError(
                "The K67 Pro returned an unexpected CPS identity: %s"
                % identity.hex()
            )

    def _read_block(self, address):
        request = READ_COMMAND + struct.pack(">HB", address, 0x40)
        self.pipe.write(request)
        response = self._read_count(0x44)
        if response[0:1] != READ_COMMAND:
            raise errors.RadioError(
                "Unexpected K67 Pro read response %r" % response[:4]
            )
        returned_address, length = struct.unpack(">HB", response[1:4])
        if returned_address != address or length != 0x40:
            raise errors.RadioError(
                "K67 Pro returned block %#06x/%i for %#06x/64"
                % (returned_address, length, address)
            )
        return response[4:]

    def _download(self):
        image = bytearray(b"\xff" * MEM_SIZE)
        total = sum(end - start for start, end in READ_RANGES)
        current = 0
        self._identify()
        try:
            for start, end in READ_RANGES:
                for address in range(start, end, 0x40):
                    image[address:address + 0x40] = self._read_block(address)
                    current += 0x40
                    if self.status_fn:
                        status = chirp_common.Status()
                        status.msg = "Cloning from K67 Pro"
                        status.cur = current
                        status.max = total
                        self.status_fn(status)
        finally:
            self.pipe.write(END_COMMAND)
        return memmap.MemoryMapBytes(bytes(image))

    def sync_in(self):
        try:
            self._mmap = self._download()
        except errors.RadioError:
            raise
        except Exception as exc:
            raise errors.RadioError(
                "Failed to communicate with the K67 Pro: %s" % exc
            ) from exc

    def sync_out(self):
        raise errors.RadioError(
            "K67 Pro uploads are disabled until physical write/read-back "
            "validation is complete."
        )

    def _record(self, number):
        if number < 1 or number > CHANNEL_COUNT:
            raise errors.InvalidMemoryLocation(
                "K67 Pro channel %s is outside 1-%i"
                % (number, CHANNEL_COUNT)
            )
        offset = (number - 1) * CHANNEL_SIZE
        return bytes(self._mmap.get_packed()[offset:offset + CHANNEL_SIZE])

    def get_raw_memory(self, number):
        return self._record(number).hex()

    def get_memory(self, number):
        raw = self._record(number)
        memory = chirp_common.Memory()
        memory.number = number
        if len(raw) != CHANNEL_SIZE or raw[0] == 0xFF or raw[1] == 0xFF:
            memory.empty = True
            return memory

        memory.empty = False
        memory.freq = _decode_frequency(raw[0:4])
        tx_frequency = _decode_frequency(raw[4:8])
        if not memory.freq:
            memory.empty = True
            return memory
        if tx_frequency == memory.freq:
            memory.duplex = ""
            memory.offset = 0
        elif tx_frequency is None:
            memory.duplex = "off"
            memory.offset = 0
        elif abs(tx_frequency - memory.freq) > 70_000_000:
            memory.duplex = "split"
            memory.offset = tx_frequency
        else:
            memory.duplex = "+" if tx_frequency > memory.freq else "-"
            memory.offset = abs(tx_frequency - memory.freq)

        rx_mode, rx_dtcs, rx_ctcss, rx_pol = _decode_tone(raw[8:10])
        tx_mode, tx_dtcs, tx_ctcss, tx_pol = _decode_tone(raw[10:12])
        memory.rtone = tx_ctcss or 88.5
        memory.ctone = rx_ctcss or 88.5
        memory.dtcs = tx_dtcs or 23
        memory.rx_dtcs = rx_dtcs or 23
        memory.dtcs_polarity = "%s%s" % (tx_pol, rx_pol)
        if tx_mode == "Tone" and not rx_mode:
            memory.tmode = "Tone"
        elif tx_mode == rx_mode == "Tone" and tx_ctcss == rx_ctcss:
            memory.tmode = "TSQL"
        elif (
            tx_mode == rx_mode == "DTCS"
            and tx_dtcs == rx_dtcs
            and tx_pol == rx_pol
        ):
            memory.tmode = "DTCS"
        elif tx_mode or rx_mode:
            memory.tmode = "Cross"
            memory.cross_mode = "%s->%s" % (tx_mode, rx_mode)
        else:
            memory.tmode = ""

        memory.name = _decode_name(raw[20:32])
        memory.skip = "" if raw[15] & 0x04 else "S"
        memory.mode = (
            "AM"
            if 108_000_000 <= memory.freq < 136_000_000
            else "FM"
            if raw[15] & 0x40
            else "NFM"
        )
        memory.power = POWER_LEVELS[0 if (raw[14] & 0x0F) == 0 else 1]
        return memory

    def set_memory(self, memory):
        offset = (memory.number - 1) * CHANNEL_SIZE
        image = bytearray(self._mmap.get_packed())
        raw = bytearray(image[offset:offset + CHANNEL_SIZE])
        if memory.empty:
            image[offset:offset + CHANNEL_SIZE] = b"\xff" * CHANNEL_SIZE
            self._mmap = memmap.MemoryMapBytes(bytes(image))
            return
        if not memory.freq:
            raise errors.InvalidDataError("A receive frequency is required")
        raw[0:4] = _encode_frequency(memory.freq)
        if memory.duplex == "off":
            raw[4:8] = b"\xff" * 4
        elif memory.duplex == "split":
            raw[4:8] = _encode_frequency(memory.offset)
        elif memory.duplex == "+":
            raw[4:8] = _encode_frequency(memory.freq + memory.offset)
        elif memory.duplex == "-":
            raw[4:8] = _encode_frequency(memory.freq - memory.offset)
        else:
            raw[4:8] = raw[0:4]

        if memory.tmode == "DTCS":
            rx = _encode_tone("DTCS", memory.dtcs,
                              memory.dtcs_polarity[1], None)
            tx = _encode_tone("DTCS", memory.dtcs,
                              memory.dtcs_polarity[0], None)
        elif memory.tmode == "TSQL":
            rx = tx = _encode_tone("Tone", None, "N", memory.ctone)
        elif memory.tmode == "Tone":
            rx = _encode_tone("", None, "N", None)
            tx = _encode_tone("Tone", None, "N", memory.rtone)
        elif memory.tmode == "Cross":
            tx_mode, rx_mode = memory.cross_mode.split("->")
            tx = (
                _encode_tone("DTCS", memory.dtcs,
                             memory.dtcs_polarity[0], None)
                if tx_mode == "DTCS"
                else _encode_tone("Tone", None, "N", memory.rtone)
                if tx_mode == "Tone"
                else _encode_tone("", None, "N", None)
            )
            rx = (
                _encode_tone("DTCS", memory.rx_dtcs,
                             memory.dtcs_polarity[1], None)
                if rx_mode == "DTCS"
                else _encode_tone("Tone", None, "N", memory.ctone)
                if rx_mode == "Tone"
                else _encode_tone("", None, "N", None)
            )
        else:
            rx = tx = b"\x00\x00"
        raw[8:10] = rx
        raw[10:12] = tx
        raw[14] = (raw[14] & 0xF0) | (
            0 if memory.power == POWER_LEVELS[0] else 1
        )
        raw[15] &= ~(0x44)
        raw[15] |= 0x40 if memory.mode == "FM" else 0
        raw[15] |= 0 if memory.skip == "S" else 0x04
        name = memory.name.encode("gb2312", "replace")[:12]
        raw[20:32] = name.ljust(12, b"\xff")
        image[offset:offset + CHANNEL_SIZE] = raw
        self._mmap = memmap.MemoryMapBytes(bytes(image))
