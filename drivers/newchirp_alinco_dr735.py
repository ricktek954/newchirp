# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Alinco DR-735 driver rebuilt from Alinco DR-735 Memory Editor 0.06.

This module replaces the methods of CHIRP's stock ``AlincoDR735T`` class in
place, so the ``Alinco_DR735T`` driver ID and existing 64,000-byte images
keep working. Every rule below comes from the decompiled OEM editor (see
docs/ALINCO_DR735_PROTOCOL.md):

* The ERW-7 cable is a single wire on the rear LEFT speaker jack, so every
  command is echoed back. A missing echo means a cable or port problem. An
  echo with no reply means the radio did not answer.
* A read starts with ``AL~`` -> ``OK`` and then ``AL~WHO`` with a 100 ms
  budget. Blocks use ``AL~EEPEL<addr>R`` for common channels and
  ``AL~EEPDL<addr>R`` for everything else, with 500 ms per block.
* Nine model identities exist. EN and RN radios are limited to
  144-146/144-148 and 430-440 MHz with no airband.
* Writes send ``AL~DR735J`` -> ``OK``, then one ``AL~EEPEL`` write per
  common channel, then ``AL~RESET`` -> ``OK``.

Extended channels (L/R, program scan, call and dual memories), VFOs,
colors, settings and DTMF are read and kept in the image. They are shown
read-only and never written until a physical radio validates the OEM
EEPDL write path with this driver.
"""

import logging
import time

from chirp import bitwise, chirp_common, errors, memmap
from chirp.drivers import alinco_dr735t as stock
from chirp.settings import (
    RadioSetting,
    RadioSettingGroup,
    RadioSettingValueBoolean,
    RadioSettingValueList,
)


LOG = logging.getLogger(__name__)

RECORD = 64
COMMON = 1000
COMMON_SIZE = COMMON * RECORD

# Tones and DCS codes in OEM order (Module1.arTone / arDcs).
TONES = [
    67.0, 69.3, 71.9, 74.4, 77.0, 79.7, 82.5, 85.4, 88.5, 91.5, 94.8, 97.4,
    100.0, 103.5, 107.2, 110.9, 114.8, 118.8, 123.0, 127.3, 131.8, 136.5,
    141.3, 146.2, 151.4, 156.7, 162.2, 167.9, 173.8, 179.9, 186.2, 192.8,
    203.5, 210.7, 218.1, 225.7, 233.6, 241.8, 250.3,
]
DCS_CODES = [
    23, 25, 26, 31, 32, 36, 43, 47, 51, 53, 54, 65, 71, 72, 73, 74, 114,
    115, 116, 122, 125, 131, 132, 134, 143, 145, 152, 155, 156, 162, 165,
    172, 174, 205, 212, 223, 225, 226, 243, 244, 245, 246, 251, 252, 255,
    261, 263, 265, 266, 271, 274, 306, 311, 315, 325, 331, 332, 343, 346,
    351, 356, 364, 365, 371, 411, 412, 413, 423, 431, 432, 445, 446, 452,
    454, 455, 462, 464, 465, 466, 503, 506, 516, 523, 526, 532, 546, 565,
    606, 612, 624, 627, 631, 632, 654, 662, 664, 703, 712, 723, 731, 732,
    734, 743, 754,
]
# Module1.strName: byte value - 0x30 indexes this table.
NAME_CHARSET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ *#+-/\\=()$_"
NAME_SPACE = 0x30 + NAME_CHARSET.index(" ")
SUBTONE_NONE, SUBTONE_TONE, SUBTONE_TSQL, SUBTONE_DCS = 0x00, 0x01, 0x03, 0x0C
MODES = {0x00: "FM", 0x01: "NFM", 0x02: "AM", 0x03: "NAM", 0x80: "Auto"}
DUPLEXES = ["", "-", "+"]
COLORS = ["CL%X" % n for n in range(16)]
HETERODYNE = ["Normal", "Reverse"]
NUM_BANKS = 10

AIR = (108000000, 136000000)
VHF = (136000000, 174000000)
UHF = (400000000, 480000000)
# btRead_Click / Module1.CheckFreq: every other identity keeps all three.
NARROW_BANDS = {
    "DR735EN": [(144000000, 146000000), (430000000, 440000000)],
    "DR735RN": [(144000000, 148000000), (430000000, 440000000)],
}
MODEL_IDS = (
    "DR735J", "DR735EN", "DR735EE", "DR735GN", "DR735GE",
    "DR735TN", "DR735TE", "DR735RN", "DR735RE",
)

# Extended channels, numbered exactly like the OEM grid rows.
CH_LEFT, CH_RIGHT, CH_PROGRAM = 1000, 1100, 1200
CH_APL, CH_APH, CH_CALL_V, CH_CALL_U, CH_DUAL = 1210, 1211, 1212, 1213, 1214
LAST_CHANNEL = 1413


def extended_address(number):
    """EEPDL address of an extended channel (btRead_Click order)."""
    if CH_LEFT <= number < CH_RIGHT:
        return 0xC000 + (number - CH_LEFT) * RECORD
    if CH_RIGHT <= number < CH_PROGRAM:
        return 0xE000 + (number - CH_RIGHT) * RECORD
    if CH_PROGRAM <= number < CH_APL:
        pair, side = divmod(number - CH_PROGRAM, 2)
        return (0x1200 if side else 0x1000) + pair * RECORD
    fixed = {CH_APL: 0x1180, CH_APH: 0x1380,
             CH_CALL_V: 0x1400, CH_CALL_U: 0x1480}
    if number in fixed:
        return fixed[number]
    if CH_DUAL <= number <= LAST_CHANNEL:
        return 0x2000 + (number - CH_DUAL) * RECORD
    raise IndexError("DR-735 has no extended channel %s" % number)


def channel_label(number):
    if number < CH_LEFT:
        return "%03i" % number
    if number < CH_RIGHT:
        return "L%02i" % (number - CH_LEFT)
    if number < CH_PROGRAM:
        return "R%02i" % (number - CH_RIGHT)
    if number < CH_APL:
        pair, side = divmod(number - CH_PROGRAM, 2)
        return "P%i%s" % (pair + 1, "B" if side else "A")
    labels = {CH_APL: "APL", CH_APH: "APH", CH_CALL_V: "CAV",
              CH_CALL_U: "CAU"}
    if number in labels:
        return labels[number]
    pair, side = divmod(number - CH_DUAL, 2)
    return "d%02i%s" % (pair, "R" if side else "L")


EXTENDED = list(range(CH_LEFT, LAST_CHANNEL + 1))
# VFO L-VHF, L-UHF, L-AIR, R-UHF, R-VHF, R-AIR; colors; settings; DTMF.
TRAILER_ADDRESSES = [
    0x0100, 0x0180, 0x1500, 0x0140, 0x01C0, 0x1540,
    0x0080, 0x0000, 0x0040, 0x1700, 0x1740, 0x1780,
]
EXTENDED_SIZE = (len(EXTENDED) + len(TRAILER_ADDRESSES)) * RECORD
FULL_SIZE = COMMON_SIZE + EXTENDED_SIZE

MEM_FORMAT = """
struct dr735_mem {
  u8 used;
  u8 skip;
  u8 favorite;
  u8 step;
  ul32 frequency;
  ul32 shift;
  u8 shift_direction;
  u8 subtone_selection;
  u8 tx_tone_index;
  u8 rx_tone_index;
  u8 dcs_index;
  u8 dcs_index_2;
  u8 power_index;
  u8 busy_channel_lockout;
  u8 mode;
  u8 heterodyne_mode;
  u8 unknown22;
  u8 bell;
  u8 name[6];
  u8 dcs_off;
  u8 unknown31;
  u8 standby_screen_color;
  u8 rx_screen_color;
  u8 tx_screen_color;
  u8 unknown35[21];
  ul16 banks;
  ul16 pch;
  u8 unknown60[4];
};
struct dr735_mem memory[%i];
""" % COMMON

EXTENDED_FORMAT = MEM_FORMAT.replace(
    "memory[%i];" % COMMON, "memory[%i];" % (COMMON + len(EXTENDED))
)

EMPTY_RECORD = b"\xFF" * RECORD
CHANNEL_TIMEOUT = 0.5   # SioSendData(..., 500)
COMMAND_TIMEOUT = 0.1   # SioSendData(..., 100)


class DR735Error(errors.RadioError):
    pass


def _read_reply(pipe, command, timeout):
    """Return the reply line after the cable echo of ``command``."""
    deadline = time.monotonic() + timeout
    data = b""
    old_timeout = pipe.timeout
    pipe.timeout = 0.02
    try:
        while time.monotonic() < deadline:
            chunk = pipe.read(256)
            if chunk:
                data += chunk
                lines = data.count(b"\r\n")
                if lines >= 2:
                    break
                if lines == 1 and not data.startswith(command + b"\r\n"):
                    break   # cable without echo: this line is the reply
    finally:
        pipe.timeout = old_timeout
    echo, sep, rest = data.partition(b"\r\n")
    if not sep:
        if not data:
            raise DR735Error(
                "No echo from the programming cable after %s. Check that "
                "the selected port is the ERW-7 (or compatible) cable."
                % command.decode()
            )
        raise DR735Error(
            "Incomplete reply to %s: %r." % (command.decode(), data[:40])
        )
    if echo != command:
        # The ERW-7 is a single-wire cable and always echoes. Separate
        # TX/RX leads do not, so the first line is already the reply.
        LOG.debug("DR-735 cable did not echo %s", command[:12])
        return echo
    reply, sep, _ = rest.partition(b"\r\n")
    if not sep:
        if not rest:
            raise errors.RadioNoResponse(
                "The radio did not answer %s. Plug the cable into the "
                "rear LEFT speaker jack, make sure the radio is on and not "
                "in Clone mode, then try again." % command.decode()
            )
        raise DR735Error(
            "Incomplete reply to %s (%i bytes)." % (command.decode(),
                                                   len(rest))
        )
    return reply


def send_command(pipe, text, timeout=COMMAND_TIMEOUT):
    command = text.encode("ascii")
    pipe.write(command + b"\r\n")
    return _read_reply(pipe, command, timeout).decode("ascii", "replace")


def expect_ok(pipe, text, timeout=COMMAND_TIMEOUT):
    reply = send_command(pipe, text, timeout)
    if reply != "OK":
        raise DR735Error("The radio answered %r to %s." % (reply, text))


def identify(pipe):
    """btRead_Click: wake with AL~, then AL~WHO against the OEM list."""
    reset = getattr(pipe, "reset_input_buffer", None)
    if reset is not None:
        reset()
    reply = send_command(pipe, "AL~")
    if reply != "OK":
        raise DR735Error("The radio answered %r to AL~." % reply)
    model = send_command(pipe, "AL~WHO")
    if model not in MODEL_IDS:
        raise DR735Error(
            "The radio identified as %r, which is not a DR-735 model the "
            "Alinco editor accepts." % model
        )
    LOG.info("DR-735 identity %s", model)
    return model


def read_record(pipe, family, address):
    reply = send_command(
        pipe, "AL~%s%04XR" % (family, address), CHANNEL_TIMEOUT
    )
    if len(reply) != RECORD * 2:
        raise DR735Error(
            "Block %s %04X: expected 128 hex digits, received %i."
            % (family, address, len(reply))
        )
    try:
        return bytes.fromhex(reply)
    except ValueError as exc:
        raise DR735Error(
            "Block %s %04X was not hexadecimal." % (family, address)
        ) from exc


def write_record(pipe, family, address, data):
    if len(data) != RECORD:
        raise ValueError("DR-735 records are 64 bytes")
    expect_ok(
        pipe,
        "AL~%s%04XW%s" % (family, address, data.hex().upper()),
        CHANNEL_TIMEOUT,
    )


def bands_for(model):
    return list(NARROW_BANDS.get(model, [AIR, VHF, UHF]))


def _status(radio, cur, total, msg):
    if radio.status_fn:
        status = chirp_common.Status()
        status.cur, status.max, status.msg = cur, total, msg
        radio.status_fn(status)


def _do_download(self):
    model = identify(self.pipe)
    self._dr735_model = model
    self._metadata["dr735_model"] = model
    total = COMMON + len(EXTENDED) + len(TRAILER_ADDRESSES)
    data = bytearray()
    for number in range(COMMON):
        data += read_record(self.pipe, "EEPEL", number * RECORD)
        _status(self, number + 1, total, "Reading channel %03i" % number)
    extended = bytearray()
    try:
        for index, number in enumerate(EXTENDED):
            extended += read_record(
                self.pipe, "EEPDL", extended_address(number)
            )
            _status(self, COMMON + index + 1, total,
                    "Reading %s" % channel_label(number))
        for index, address in enumerate(TRAILER_ADDRESSES):
            extended += read_record(self.pipe, "EEPDL", address)
            _status(self, COMMON + len(EXTENDED) + index + 1, total,
                    "Reading settings")
    except errors.RadioError as exc:
        # The common channels are complete and useful on their own.
        LOG.warning("DR-735 extended read stopped: %s", exc)
        extended = bytearray()
    return memmap.MemoryMapBytes(bytes(data + extended))


def _sync_in(self):
    try:
        self._mmap = _do_download(self)
    except errors.RadioError:
        raise
    except Exception as exc:
        LOG.exception("Unexpected DR-735 download error")
        raise errors.RadioError(
            "Unexpected error reading the DR-735: %s" % exc
        ) from exc
    self.process_mmap()


def _validate_for_upload(self):
    bands = bands_for(self._dr735_model)
    for number in range(COMMON):
        record = self._memobj.memory[number]
        if int(record.used) != 0x55:
            continue
        freq = int(record.frequency)
        if not any(lo <= freq < hi for lo, hi in bands):
            raise DR735Error(
                "Channel %03i (%s MHz) is outside the %s's range. The radio "
                "was not changed." % (number, freq / 1e6, self._dr735_model)
            )


def _do_upload(self):
    model = identify(self.pipe)
    stored = self._metadata.get("dr735_model")
    if stored and stored != model:
        raise DR735Error(
            "This image was read from a %s, but the connected radio is a "
            "%s. Read this radio first. The radio was not changed."
            % (stored, model)
        )
    self._dr735_model = model
    _validate_for_upload(self)
    expect_ok(self.pipe, "AL~DR735J")
    raw = self.get_mmap().get_packed()
    for number in range(COMMON):
        write_record(self.pipe, "EEPEL", number * RECORD,
                     raw[number * RECORD:(number + 1) * RECORD])
        _status(self, number + 1, COMMON, "Writing channel %03i" % number)
    expect_ok(self.pipe, "AL~RESET")


def _sync_out(self):
    try:
        _do_upload(self)
    except errors.RadioError:
        raise
    except Exception as exc:
        LOG.exception("Unexpected DR-735 upload error")
        raise errors.RadioError(
            "Unexpected error writing the DR-735: %s" % exc
        ) from exc


def _process_mmap(self):
    size = len(self._mmap.get_packed())
    if size >= FULL_SIZE:
        self._memobj = bitwise.parse(EXTENDED_FORMAT, self._mmap)
        self._dr735_has_extended = True
    else:
        self._memobj = bitwise.parse(MEM_FORMAT, self._mmap)
        self._dr735_has_extended = False
    if not getattr(self, "_dr735_model", None):
        self._dr735_model = self._metadata.get("dr735_model")


def _get_features(self):
    rf = chirp_common.RadioFeatures()
    rf.has_bank = True
    rf.has_ctone = True
    rf.has_cross = True
    rf.has_dtcs_polarity = False
    rf.has_rx_dtcs = False
    rf.has_tuning_step = False
    rf.can_delete = True
    rf.valid_tmodes = ["", "Tone", "TSQL", "DTCS", "Cross"]
    rf.valid_cross_modes = ["Tone->Tone"]
    rf.valid_modes = list(MODES.values())
    rf.valid_duplexes = list(DUPLEXES)
    rf.valid_skips = ["", "S"]
    rf.valid_bands = bands_for(getattr(self, "_dr735_model", None))
    rf.valid_tuning_steps = [5.0, 6.25, 8.33, 10.0, 12.5, 15.0, 20.0,
                             25.0, 30.0, 50.0, 100.0]
    rf.valid_name_length = 6
    rf.valid_characters = NAME_CHARSET
    rf.valid_power_levels = stock.AlincoDR735T.POWER_MAP
    rf.valid_dtcs_codes = list(DCS_CODES)
    rf.memory_bounds = (0, LAST_CHANNEL)
    return rf


def _decode_name(raw):
    return "".join(
        NAME_CHARSET[b - 0x30] for b in raw if 0x30 <= b < 0x30 + 48
    ).rstrip()


def _encode_name(name):
    out = [0] * 6
    for i, char in enumerate(name[:6].upper()):
        out[i] = (0x30 + NAME_CHARSET.index(char)
                  if char in NAME_CHARSET else NAME_SPACE)
    return out


def _record_valid(rec):
    """Mirror ExpandMem: any out-of-table value hides the record."""
    try:
        return (
            int(rec.skip) in (0, 1)
            and int(rec.favorite) in (0, 1)
            and int(rec.shift_direction) < 3
            and int(rec.subtone_selection) in (0, 1, 3, 0x0C)
            and int(rec.tx_tone_index) < len(TONES)
            and int(rec.rx_tone_index) < len(TONES)
            and int(rec.dcs_index) < len(DCS_CODES)
            and int(rec.power_index) < 3
            and int(rec.busy_channel_lockout) in (0, 1)
            and int(rec.mode) in MODES
            and int(rec.heterodyne_mode) in (0, 1)
            and int(rec.bell) in (0, 1)
            and int(rec.dcs_off) in (0, 1)
            and int(rec.standby_screen_color) < 16
            and int(rec.rx_screen_color) < 16
            and int(rec.tx_screen_color) < 16
            and int(rec.banks) < (1 << NUM_BANKS)
        )
    except (TypeError, ValueError):
        return False


def _extra_settings(rec):
    group = RadioSettingGroup("extra", "Extra")
    pch = int(rec.pch) if rec is not None else 0
    pch_choices = ["None"] + ["%03i" % n for n in range(COMMON)]
    pch_index = (pch & 0x7FFF) + 1 if pch & 0x8000 and \
        (pch & 0x7FFF) < COMMON else 0

    def color(value):
        return int(value) if rec is not None and int(value) < 16 else 0

    entries = [
        ("heterodyne_mode", "Heterodyne Mode", RadioSettingValueList(
            HETERODYNE, current_index=int(rec.heterodyne_mode) & 1
            if rec is not None else 0)),
        ("bcl", "Busy Channel Lockout", RadioSettingValueBoolean(
            bool(rec is not None and rec.busy_channel_lockout))),
        ("fav", "Favorite", RadioSettingValueBoolean(
            bool(rec is not None and rec.favorite))),
        ("bell", "Bell", RadioSettingValueBoolean(
            bool(rec is not None and rec.bell))),
        ("dcs_off", "DCS Off", RadioSettingValueBoolean(
            bool(rec is not None and rec.dcs_off))),
        ("stby_screen", "Standby Screen Color", RadioSettingValueList(
            COLORS, current_index=color(rec.standby_screen_color)
            if rec is not None else 0)),
        ("rx_screen", "RX Screen Color", RadioSettingValueList(
            COLORS, current_index=color(rec.rx_screen_color)
            if rec is not None else 0)),
        ("tx_screen", "TX Screen Color", RadioSettingValueList(
            COLORS, current_index=color(rec.tx_screen_color)
            if rec is not None else 0)),
        ("pch", "Linked Channel (pch)", RadioSettingValueList(
            pch_choices, current_index=pch_index)),
    ]
    for name, label, value in entries:
        group.append(RadioSetting(name, label, value))
    return group


def _blank_memory(number):
    mem = chirp_common.Memory()
    mem.number = number
    mem.empty = True
    mem.freq = 0
    mem.name = ""
    mem.extra = _extra_settings(None)
    return mem


def _get_memory(self, number):
    extended = number >= COMMON
    if extended and not self._dr735_has_extended:
        mem = _blank_memory(number)
        mem.comment = "%s (read from the radio to load)" % channel_label(
            number)
        mem.immutable = ["empty"]
        return mem
    rec = self._memobj.memory[number]
    if int(rec.used) != 0x55 or not _record_valid(rec):
        if int(rec.used) == 0x55:
            LOG.warning("DR-735 channel %s has values outside the OEM "
                        "tables; shown as empty", number)
        mem = _blank_memory(number)
    else:
        mem = chirp_common.Memory()
        mem.number = number
        mem.freq = int(rec.frequency)
        mem.offset = int(rec.shift)
        mem.duplex = DUPLEXES[int(rec.shift_direction)]
        mem.name = _decode_name(rec.name)
        mem.mode = MODES[int(rec.mode)]
        mem.power = stock.AlincoDR735T.POWER_MAP[int(rec.power_index)]
        mem.skip = "S" if int(rec.skip) else ""
        mem.rtone = TONES[int(rec.tx_tone_index)]
        mem.ctone = TONES[int(rec.rx_tone_index)]
        mem.dtcs = DCS_CODES[int(rec.dcs_index)]
        subtone = int(rec.subtone_selection)
        if subtone == SUBTONE_TONE:
            mem.tmode = "Tone"
        elif subtone == SUBTONE_TSQL:
            if mem.rtone == mem.ctone:
                mem.tmode = "TSQL"
            else:
                mem.tmode = "Cross"
                mem.cross_mode = "Tone->Tone"
        elif subtone == SUBTONE_DCS:
            mem.tmode = "DTCS"
        mem.extra = _extra_settings(rec)
    if extended:
        mem.comment = "%s (read-only)" % channel_label(number)
        mem.immutable = [
            "empty", "freq", "offset", "duplex", "name", "mode", "power",
            "skip", "rtone", "ctone", "dtcs", "tmode", "cross_mode",
            "comment",
        ]
        for setting in mem.extra:
            setting.value.set_mutable(False)
    return mem


def _apply_extra(rec, mem):
    for setting in mem.extra:
        name = setting.get_name()
        value = setting.value
        if name == "heterodyne_mode":
            rec.heterodyne_mode = HETERODYNE.index(str(value))
        elif name == "bcl":
            rec.busy_channel_lockout = int(bool(value))
        elif name == "fav":
            rec.favorite = int(bool(value))
        elif name == "bell":
            rec.bell = int(bool(value))
        elif name == "dcs_off":
            rec.dcs_off = int(bool(value))
        elif name == "stby_screen":
            rec.standby_screen_color = COLORS.index(str(value))
        elif name == "rx_screen":
            rec.rx_screen_color = COLORS.index(str(value))
        elif name == "tx_screen":
            rec.tx_screen_color = COLORS.index(str(value))
        elif name == "pch":
            rec.pch = 0 if str(value) == "None" else 0x8000 | int(str(value))


def _set_memory(self, mem):
    if mem.number >= COMMON:
        # Extended channels stay as read until the EEPDL write path is
        # validated on a physical radio.
        return
    rec = self._memobj.memory[mem.number]
    if mem.empty:
        if int(rec.used) == 0x55:
            rec.set_raw(EMPTY_RECORD)   # Form1 delete: 64 bytes of 0xFF
        return
    if int(rec.used) != 0x55:
        rec.set_raw(b"\x00" * RECORD)
        rec.mode = 0x80
    try:
        tx_tone = TONES.index(mem.rtone)
        rx_tone = TONES.index(mem.ctone)
    except ValueError:
        raise errors.UnsupportedToneError(
            "The DR-735 does not support tone %.1f Hz"
            % (mem.rtone if mem.rtone not in TONES else mem.ctone))
    rec.used = 0x55
    rec.step = 0                # OEM forces AUTO on memory channels
    rec.frequency = mem.freq
    rec.shift = mem.offset
    rec.shift_direction = DUPLEXES.index(mem.duplex or "")
    if mem.tmode == "Tone":
        rec.subtone_selection = SUBTONE_TONE
        rec.tx_tone_index = tx_tone
    elif mem.tmode == "TSQL":
        rec.subtone_selection = SUBTONE_TSQL
        rec.tx_tone_index = rx_tone
        rec.rx_tone_index = rx_tone
    elif mem.tmode == "Cross":
        rec.subtone_selection = SUBTONE_TSQL
        rec.tx_tone_index = tx_tone
        rec.rx_tone_index = rx_tone
    elif mem.tmode == "DTCS":
        rec.subtone_selection = SUBTONE_DCS
    else:
        rec.subtone_selection = SUBTONE_NONE
    dcs = DCS_CODES.index(mem.dtcs) if mem.dtcs in DCS_CODES else 0
    rec.dcs_index = dcs
    rec.dcs_index_2 = dcs       # Memory.btnOK_Click writes both bytes
    power = stock.AlincoDR735T.POWER_MAP
    rec.power_index = power.index(mem.power) if mem.power in power else 0
    rec.mode = {v: k for k, v in MODES.items()}.get(mem.mode, 0x00)
    rec.skip = 1 if mem.skip == "S" else 0
    rec.name = _encode_name(mem.name)
    _apply_extra(rec, mem)


def _get_raw_memory(self, number):
    return repr(self._memobj.memory[number])


class DR735Bank(chirp_common.Bank):
    pass


class DR735BankModel(chirp_common.MTOBankModel):
    """Ten banks stored as a u16 bit mask at record offset 56."""

    def get_num_mappings(self):
        return NUM_BANKS

    def get_mappings(self):
        return [DR735Bank(self, i, "Bank %i" % (i + 1))
                for i in range(NUM_BANKS)]

    def _record(self, memory):
        if memory.number >= COMMON:
            raise errors.RadioError(
                "Extended DR-735 channels are read-only.")
        return self._radio._memobj.memory[memory.number]

    def add_memory_to_mapping(self, memory, bank):
        rec = self._record(memory)
        rec.banks = int(rec.banks) | (1 << bank.get_index())

    def remove_memory_from_mapping(self, memory, bank):
        rec = self._record(memory)
        bit = 1 << bank.get_index()
        if not int(rec.banks) & bit:
            raise Exception("Memory %i is not in bank %s"
                            % (memory.number, bank.get_name()))
        rec.banks = int(rec.banks) & ~bit

    def get_mapping_memories(self, bank):
        bit = 1 << bank.get_index()
        return [
            self._radio.get_memory(n) for n in range(COMMON)
            if int(self._radio._memobj.memory[n].used) == 0x55
            and int(self._radio._memobj.memory[n].banks) & bit
        ]

    def get_memory_mappings(self, memory):
        if memory.number >= COMMON:
            return []
        mask = int(self._radio._memobj.memory[memory.number].banks)
        return [bank for bank in self.get_mappings()
                if mask & (1 << bank.get_index())]


def _get_bank_model(self):
    return DR735BankModel(self)


def _get_prompts(cls):
    rp = chirp_common.RadioPrompts()
    rp.pre_download = (
        "Plug the ERW-7 (or compatible) cable into the LEFT speaker jack "
        "on the rear panel and turn the radio on normally. Do not enter "
        "Clone mode; the Alinco editor does not use it."
    )
    rp.pre_upload = rp.pre_download + (
        " Writing replaces all 1000 common channels. The radio restarts "
        "when the write finishes."
    )
    return rp


if not getattr(stock.AlincoDR735T, "newchirp_oem_editor_transport", False):
    cls = stock.AlincoDR735T
    cls.newchirp_oem_editor_transport = True
    cls._dr735_model = None
    cls._dr735_has_extended = False
    cls.do_download = _do_download
    cls.do_upload = _do_upload
    cls.sync_in = _sync_in
    cls.sync_out = _sync_out
    cls.process_mmap = _process_mmap
    cls.get_features = _get_features
    cls.get_memory = _get_memory
    cls.set_memory = _set_memory
    cls.get_raw_memory = _get_raw_memory
    cls.get_bank_model = _get_bank_model
    cls.get_prompts = classmethod(_get_prompts)
