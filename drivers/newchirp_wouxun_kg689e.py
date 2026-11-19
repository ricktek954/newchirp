# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Experimental Wouxun KG-689E / KG-699E clone-mode driver.

Recovered from Wouxun's "KG-699E 689E" programming software (MFC, the only
programmer Wouxun publishes for these radios). See
docs/WOUXUN_KG689E_PROTOCOL.md for the call paths and evidence.

Transport (CPS serial wrapper at 0x40b5ae, protocol at 0x40b722-0x40ba4c):

* 9600 8N1, DTR on, 1 s reads.
* Wake: "HiWOUXUN\\x02" answered by 06, retried up to 20 times.
* Identify: 02 answered by 06 "KG669V" F8, then 06 answered by 06.
* Read: "R" hi lo 40 answered by "W" hi lo 40 + 64 data bytes, then 06/06.
* Write: "W" hi lo 10 + 16 data bytes answered by 06.

The CPS reads 67 64-byte blocks: channels 0x0010-0x080F, names
0x1010-0x180F and settings blocks 0x0810, 0x0E20 and 0x1810. It writes the
channel and name areas back in full, but only the first 32 bytes of 0x0810
and 0x1810 and all of 0x0E20. Before any write it reads block 0x0970, which
holds the radio's own RX/TX limits, and refuses channels outside them.
"""

import logging
import time

from chirp import bitwise, chirp_common, directory, errors, memmap
from chirp.settings import (
    RadioSetting,
    RadioSettingGroup,
    RadioSettingValueBoolean,
    RadioSettingValueList,
)


LOG = logging.getLogger(__name__)

MEM_SIZE = 0x2000
CHANNELS = 128
READ_SIZE = 0x40
WRITE_SIZE = 0x10
ACK = b"\x06"
WAKE = b"HiWOUXUN\x02"
IDENT_REPLY = b"\x06KG669V\xf8"
WAKE_ATTEMPTS = 20
LIMITS_BLOCK = 0x0970

CHANNEL_BLOCKS = tuple(0x0010 + index * READ_SIZE for index in range(32))
NAME_BLOCKS = tuple(0x1010 + index * READ_SIZE for index in range(32))
SETTINGS_BLOCKS = (0x0810, 0x0E20, 0x1810)
READ_BLOCKS = CHANNEL_BLOCKS + NAME_BLOCKS + SETTINGS_BLOCKS

# (address, bytes) the CPS writes back, in its order (thread 0x41e1e2).
WRITE_SPANS = (
    tuple((address, READ_SIZE) for address in CHANNEL_BLOCKS)
    + tuple((address, READ_SIZE) for address in NAME_BLOCKS)
    + ((0x0810, 0x20), (0x0E20, 0x40), (0x1810, 0x20))
)

# CPS name codec (0x404a06): 0-9, A-Z, then ?, +, -. Anything else ends it.
CHARSET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ?+-"
POWER_LEVELS = [
    chirp_common.PowerLevel("High", watts=5.0),
    chirp_common.PowerLevel("Low", watts=1.0),
]
MUTE_MODES = ["QT", "QT+DTMF", "QT*DTMF"]
# The CPS allows up to the reported upper limit plus 0.995 MHz.
LIMIT_TOLERANCE_HZ = 995000

MEM_FORMAT = """
#seekto 0x0010;
struct {
  lbcd rx_freq[4];
  lbcd tx_freq[4];
  ul16 rx_tone;
  ul16 tx_tone;
  u8 unknown_b7:1,
     mute_mode:2,
     unknown_b4:1,
     busy_lock:1,
     unknown_b2:1,
     optional_dtmf:1,
     unknown_b0:1;
  u8 unknown_b15:1,
     scan_add:1,
     high_power:1,
     wide:1,
     unknown_b8:4;
  u8 unknown[2];
} memory[128];

#seekto 0x0970;
struct {
  u8 unknown0[4];
  bbcd rx_low[2];
  bbcd rx_high[2];
  u8 unknown1[4];
  bbcd tx_low[2];
  bbcd tx_high[2];
} limits;

#seekto 0x1010;
struct {
  u8 chars[6];
  u8 unknown[10];
} names[128];
"""


def _exchange(radio, data, length):
    radio.pipe.write(data)
    reply = radio.pipe.read(length)
    return reply


def _wake_and_identify(radio):
    reply = b""
    for attempt in range(WAKE_ATTEMPTS):
        if attempt:
            time.sleep(0.2)
        try:
            radio.pipe.reset_input_buffer()
        except Exception:
            pass
        reply = _exchange(radio, WAKE, 1)
        if reply == ACK:
            break
    else:
        if not reply:
            raise errors.RadioNoResponse(
                "The radio did not answer. Check that the programming cable "
                "is fully inserted, the radio is on, and the right serial "
                "port is selected."
            )
        raise errors.RadioError(
            "The radio answered %s instead of the Wouxun acknowledgement. "
            "Turn the radio off and on, then try again." % reply.hex()
        )

    ident = _exchange(radio, b"\x02", 8)
    if ident != IDENT_REPLY:
        raise errors.RadioError(
            "This radio did not identify as a KG-689E/KG-699E "
            "(expected KG669V, got %s)." % (ident.hex() or "no reply")
        )
    if _exchange(radio, ACK, 1) != ACK:
        raise errors.RadioError("The radio refused programming mode.")


def _read_block(radio, address):
    command = bytes((0x52, address >> 8, address & 0xFF, READ_SIZE))
    reply = _exchange(radio, command, 4 + READ_SIZE)
    expected = bytes((0x57, address >> 8, address & 0xFF, READ_SIZE))
    if len(reply) != 4 + READ_SIZE or reply[:4] != expected:
        raise errors.RadioError(
            "Bad reply reading block %04X (%i bytes)" % (address, len(reply))
        )
    if _exchange(radio, ACK, 1) != ACK:
        raise errors.RadioError(
            "No acknowledgement after block %04X" % address
        )
    return reply[4:]


def _write_block(radio, address, data):
    command = bytes((0x57, address >> 8, address & 0xFF, WRITE_SIZE)) + data
    reply = _exchange(radio, command, 1)
    if reply != ACK:
        raise errors.RadioError(
            "The radio did not accept block %04X (%s)"
            % (address, reply.hex() or "no reply")
        )


def _status(radio, done, total, message):
    status = chirp_common.Status()
    status.cur = done
    status.max = total
    status.msg = message
    radio.status_fn(status)


def _bcd_mhz(value):
    return int(value) * 1000000


def _limits_hz(limits):
    """Return ((rx_low, rx_high), (tx_low, tx_high)) in Hz, or None."""
    raw = limits.get_raw(asbytes=True)
    if raw[4:8] in (b"\xff" * 4, b"\x00" * 4):
        return None
    try:
        rx = (_bcd_mhz(limits.rx_low),
              _bcd_mhz(limits.rx_high) + LIMIT_TOLERANCE_HZ)
        tx = (_bcd_mhz(limits.tx_low),
              _bcd_mhz(limits.tx_high) + LIMIT_TOLERANCE_HZ)
    except Exception:
        return None
    if not (0 < rx[0] < rx[1] and 0 < tx[0] < tx[1]):
        return None
    return rx, tx


def _bcd_programmed(raw):
    """CPS 0x41d5a0: the low four BCD digits must all be 0-9."""
    for byte in raw[:2]:
        if (byte & 0x0F) > 9 or (byte >> 4) > 9:
            return False
    return True


def _decode_tone(value):
    if value in (0x0000, 0xFFFF):
        return "", None, None
    high = value >> 8
    if high < 0x28:
        return "Tone", value / 10.0, None
    code = int("%o" % (value & 0x1FF))
    return "DTCS", code, "R" if high >= 0x80 else "N"


def _encode_tone(mode, value, polarity):
    if mode == "Tone":
        return int(round(value * 10))
    if mode == "DTCS":
        encoded = int(str(value), 8) | 0x2800
        if polarity == "R":
            encoded |= 0x8000
        return encoded
    return 0xFFFF


class KG689EBase(chirp_common.CloneModeRadio, chirp_common.ExperimentalRadio):
    """Wouxun KG-689E family, transport and map from the OEM CPS."""

    VENDOR = "Wouxun"
    BAUD_RATE = 9600
    WANTS_DTR = True
    WANTS_RTS = True
    NEEDS_COMPAT_SERIAL = False
    FALLBACK_BANDS = [(136000000, 174000000)]

    @classmethod
    def get_prompts(cls):
        prompts = chirp_common.RadioPrompts()
        prompts.experimental = (
            "Wouxun %s support is experimental. NewChirp follows Wouxun's "
            "own programming software: it writes only the areas that "
            "software writes, and it refuses a write when a channel is "
            "outside the radio's own frequency limits. Save the image after "
            "reading so you can restore it." % cls.MODEL
        )
        prompts.pre_download = (
            "1. Turn the radio off.\n"
            "2. Connect the programming cable to the speaker/mic jack.\n"
            "3. Turn the radio on.\n"
            "4. Click OK to read.\n"
        )
        prompts.pre_upload = prompts.pre_download.replace("read", "write")
        return prompts

    def get_features(self):
        rf = chirp_common.RadioFeatures()
        rf.memory_bounds = (1, CHANNELS)
        rf.has_bank = False
        rf.has_ctone = True
        rf.has_cross = True
        rf.has_rx_dtcs = True
        rf.has_dtcs_polarity = True
        rf.has_tuning_step = False
        rf.has_settings = False
        rf.valid_tmodes = ["", "Tone", "TSQL", "DTCS", "Cross"]
        rf.valid_cross_modes = [
            "Tone->Tone", "Tone->DTCS", "DTCS->Tone", "DTCS->",
            "->Tone", "->DTCS", "DTCS->DTCS",
        ]
        rf.valid_duplexes = ["", "+", "-", "split", "off"]
        rf.valid_modes = ["FM", "NFM"]
        rf.valid_power_levels = POWER_LEVELS
        rf.valid_characters = CHARSET
        rf.valid_name_length = 6
        rf.valid_skips = ["", "S"]
        rf.can_odd_split = True
        rf.valid_bands = self._valid_bands()
        return rf

    def _valid_bands(self):
        if self._memobj is not None:
            limits = _limits_hz(self._memobj.limits)
            if limits:
                low = min(limits[0][0], limits[1][0])
                high = max(limits[0][1], limits[1][1])
                return [(low, high + 1)]
        return list(self.FALLBACK_BANDS)

    @classmethod
    def match_model(cls, filedata, filename):
        # Same 8 KiB size as CHIRP's KG-UVD1P images; only metadata
        # identifies a KG-689E image.
        return False

    def process_mmap(self):
        self._memobj = bitwise.parse(MEM_FORMAT, self._mmap)

    def sync_in(self):
        data = bytearray(b"\xff" * MEM_SIZE)
        blocks = READ_BLOCKS + (LIMITS_BLOCK,)
        try:
            _wake_and_identify(self)
            for index, address in enumerate(blocks):
                data[address:address + READ_SIZE] = _read_block(self, address)
                _status(self, index + 1, len(blocks), "Cloning from radio")
        except errors.RadioError:
            raise
        except Exception as exc:
            raise errors.RadioError("Failed to read the radio: %s" % exc)
        self._mmap = memmap.MemoryMapBytes(bytes(data))
        self.process_mmap()

    def _check_limits(self, limits):
        """Mirror CPS 0x416799: every programmed channel within limits."""
        (rx_low, rx_high), (tx_low, tx_high) = limits
        for index in range(CHANNELS):
            channel = self._memobj.memory[index]
            raw = channel.get_raw(asbytes=True)
            if not _bcd_programmed(raw[0:4]):
                continue
            rx = int(channel.rx_freq) * 10
            if not rx_low <= rx <= rx_high:
                raise errors.RadioError(
                    "Channel %i receives on %.5f MHz, outside this radio's "
                    "%.3f-%.3f MHz range. Nothing was written."
                    % (index + 1, rx / 1e6, rx_low / 1e6, rx_high / 1e6)
                )
            if _bcd_programmed(raw[4:8]):
                tx = int(channel.tx_freq) * 10
                if not tx_low <= tx <= tx_high:
                    raise errors.RadioError(
                        "Channel %i transmits on %.5f MHz, outside this "
                        "radio's %.3f-%.3f MHz range. Nothing was written."
                        % (index + 1, tx / 1e6, tx_low / 1e6, tx_high / 1e6)
                    )

    def sync_out(self):
        image = self._mmap.get_packed()
        try:
            _wake_and_identify(self)
            limits_raw = _read_block(self, LIMITS_BLOCK)
            probe = bitwise.parse(
                "struct { u8 unknown0[4]; bbcd rx_low[2]; bbcd rx_high[2]; "
                "u8 unknown1[4]; bbcd tx_low[2]; bbcd tx_high[2]; } limits;",
                memmap.MemoryMapBytes(limits_raw),
            )
            limits = _limits_hz(probe.limits)
            if limits is None:
                raise errors.RadioError(
                    "The radio did not report its frequency limits, so "
                    "NewChirp stopped before writing."
                )
            self._check_limits(limits)
            total = sum(length // WRITE_SIZE for _address, length in WRITE_SPANS)
            done = 0
            for address, length in WRITE_SPANS:
                for offset in range(0, length, WRITE_SIZE):
                    start = address + offset
                    _write_block(self, start, image[start:start + WRITE_SIZE])
                    done += 1
                    _status(self, done, total, "Cloning to radio")
        except errors.RadioError:
            raise
        except Exception as exc:
            raise errors.RadioError("Failed to write the radio: %s" % exc)

    def get_raw_memory(self, number):
        return repr(self._memobj.memory[number - 1])

    def _name(self, index):
        chars = []
        for value in self._memobj.names[index].chars:
            value = int(value)
            if value >= len(CHARSET):
                break
            chars.append(CHARSET[value])
        return "".join(chars)

    def get_memory(self, number):
        channel = self._memobj.memory[number - 1]
        mem = chirp_common.Memory()
        mem.number = number
        raw = channel.get_raw(asbytes=True)
        if not _bcd_programmed(raw[0:4]):
            mem.empty = True
            return mem

        mem.freq = int(channel.rx_freq) * 10
        if _bcd_programmed(raw[4:8]):
            chirp_common.split_to_offset(mem, mem.freq,
                                         int(channel.tx_freq) * 10)
        else:
            mem.duplex = "off"
            mem.offset = 0

        tx = _decode_tone(int(channel.tx_tone))
        rx = _decode_tone(int(channel.rx_tone))
        chirp_common.split_tone_decode(mem, tx, rx)

        mem.mode = "FM" if channel.wide else "NFM"
        mem.power = POWER_LEVELS[0] if channel.high_power else POWER_LEVELS[1]
        mem.skip = "" if channel.scan_add else "S"
        mem.name = self._name(number - 1)

        mem.extra = RadioSettingGroup("extra", "Extra")
        mem.extra.append(RadioSetting(
            "busy_lock", "Busy lock (carrier)",
            RadioSettingValueBoolean(bool(channel.busy_lock))))
        mem.extra.append(RadioSetting(
            "optional_dtmf", "Optional signal (DTMF)",
            RadioSettingValueBoolean(bool(channel.optional_dtmf))))
        mute = int(channel.mute_mode)
        if mute < len(MUTE_MODES):
            mem.extra.append(RadioSetting(
                "mute_mode", "Mute mode",
                RadioSettingValueList(MUTE_MODES, current_index=mute)))
        return mem

    def set_memory(self, mem):
        index = mem.number - 1
        channel = self._memobj.memory[index]
        name = self._memobj.names[index]
        if mem.empty:
            channel.set_raw(b"\xff" * 16)
            name.chars.set_raw(b"\xff" * 6)
            return

        if not _bcd_programmed(channel.get_raw(asbytes=True)[0:4]):
            # A fresh slot: wide, high power, scan add, every option off.
            # Bytes 14-15 keep the erased value (their meaning is unknown).
            channel.set_raw(b"\x00" * 12 + bytes((0x00, 0x70)) + b"\xff\xff")

        channel.rx_freq = mem.freq // 10
        if mem.duplex == "off":
            channel.tx_freq.set_raw(b"\xff" * 4)
        else:
            channel.tx_freq = _tx_frequency(mem) // 10

        tx, rx = chirp_common.split_tone_encode(mem)
        channel.tx_tone = _encode_tone(*tx)
        channel.rx_tone = _encode_tone(*rx)

        channel.wide = mem.mode != "NFM"
        channel.high_power = mem.power != POWER_LEVELS[1]
        channel.scan_add = mem.skip != "S"

        for setting in mem.extra:
            key = setting.get_name()
            if key == "busy_lock":
                channel.busy_lock = bool(setting.value)
            elif key == "optional_dtmf":
                channel.optional_dtmf = bool(setting.value)
            elif key == "mute_mode":
                channel.mute_mode = MUTE_MODES.index(str(setting.value))

        codes = []
        for char in mem.name.upper()[:6]:
            position = CHARSET.find(char)
            if position < 0:
                break
            codes.append(position)
        name.chars.set_raw(bytes(codes) + b"\xff" * (6 - len(codes)))


def _tx_frequency(mem):
    if mem.duplex == "+":
        return mem.freq + mem.offset
    if mem.duplex == "-":
        return mem.freq - mem.offset
    if mem.duplex == "split":
        return mem.offset
    return mem.freq


@directory.register
class WouxunKG689E(KG689EBase):
    MODEL = "KG-689E"


@directory.register
class WouxunKG699E(KG689EBase):
    """The 66-88 MHz package; same CPS, transport and identity."""

    MODEL = "KG-699E"
    FALLBACK_BANDS = [(66000000, 88000000)]
