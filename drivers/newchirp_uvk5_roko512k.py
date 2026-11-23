# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Experimental, read-only Quansheng UV-K5 (V1) Robzyl RO-KO 512K profile.

RO-KO is community firmware for UV-K5 (V1) radios whose EEPROM has been
upgraded to 512 kbit or larger. Its 512K build moves the 999-channel memory
map above the stock 8 KB area. The firmware source is the oracle (repository
K5Quan/Robzyl_512K_RO_KO, commit a4ab1a0b6ff56fbe33c1ea202d0e07d5241fc81a,
Apache-2.0):

- Makefile: AUTHOR_STRING "RO-KO", VERSION_STRING V6.11; compile-KO.bat
  builds robzyl.512k.ko with ENABLE_EEPROM_512K=1 and robzyl.ko without it.
  Both builds report the same version, so the build is told apart from the
  EEPROM itself (see _require_512k_eeprom).
- misc.h (ENABLE_EEPROM_512K): MR_CHANNEL_LAST 998, ADRESS_FREQ_PARAMS
  0x2000 (16-byte records), ADRESS_ATTRIBUTES 0x5E80 (1 byte: band in the
  low nibble, scan list in the high nibble), ADRESS_NAMES 0x6280 (16-byte
  slots, 10 characters used), ADRESS_HISTORY 0xA100.
- radio.c RADIO_ConfigureChannel / RADIO_CheckValidChannel: a channel is in
  use when its band is 0-6; field rules are mirrored in get_memory.
- dcs.c: 55 CTCSS tones (the standard 50 plus 55.0-65.0 Hz) and 104 DCS
  codes; frequencies.c: the 21-entry step table.
- app_uart.c / driver_eeprom.c: the stock UV-K5 0x051B read command with a
  16-bit address; a 24C64 (8 KB) EEPROM ignores the upper address bits and
  wraps every 0x2000 bytes.

A file submitted on the NewChirp forum (512k_CHIRP_UV-K5_V1_ROBZYL-KO.py,
SHA-256 06df9e84...) split the attribute byte 5/3 and used 16-character
names; the firmware uses 4/4 and 10. It also had no firmware or EEPROM-size
check, so it could write 40 KB to an 8 KB radio.

Read-only until a physical read and a controlled write/read-back have been
compared (ledger w-20261123-211e).
"""

import importlib
import struct
import sys

from chirp import bitwise, chirp_common, directory, errors, memmap
from chirp.drivers import uvk5
from chirp.settings import (
    RadioSetting,
    RadioSettingGroup,
    RadioSettingValueString,
)

try:
    _UVK5 = sys.modules["newchirp.drivers.newchirp_uvk5"]
except KeyError:
    try:
        _UVK5 = importlib.import_module("newchirp.drivers.newchirp_uvk5")
    except ModuleNotFoundError:
        _UVK5 = importlib.import_module(".newchirp_uvk5", __package__)


FIRMWARE_PREFIX = "RO-KO"
MEM_SIZE = 0xA100          # ADRESS_HISTORY; the author's CHIRP MEM_SIZE
MEM_BLOCK = 0x80
STOCK_EEPROM_SIZE = 0x2000
CHANNEL_COUNT = 999
VALID_BANDS_MAX = 6        # BAND7_470MHz

MEM_FORMAT = """
#seekto 0x2000;
struct {
  ul32 freq;
  ul32 offset;
  u8 rxcode;
  u8 txcode;
  u8 txcodeflag:4,
     rxcodeflag:4;
  u8 modulation:4,
     offset_dir:4;
  u8 unused1:1,
     bandwidth_ext:2,
     busy_lockout:1,
     txpower:2,
     bandwidth:1,
     freq_reverse:1;
  u8 unused2;
  u8 step;
  u8 scrambler;
} channel[999];

#seekto 0x5E80;
struct {
  u8 scanlist:4,
     band:4;
} attributes[999];

#seekto 0x6280;
struct {
  char name[10];
  u8 unused[6];
} names[999];
"""

# dcs.c CTCSS_Options (Hz * 10), in index order
CTCSS_TONES = [
    67.0, 69.3, 71.9, 74.4, 77.0, 79.7, 82.5, 85.4, 88.5, 91.5,
    94.8, 97.4, 100.0, 103.5, 107.2, 110.9, 114.8, 118.8, 123.0, 127.3,
    131.8, 136.5, 141.3, 146.2, 151.4, 156.7, 159.8, 162.2, 165.5, 167.9,
    171.3, 173.8, 177.3, 179.9, 183.5, 186.2, 189.9, 192.8, 196.6, 199.5,
    203.5, 206.5, 210.7, 218.1, 225.7, 229.1, 233.6, 241.8, 250.3, 254.1,
    55.0, 57.5, 60.0, 62.5, 65.0,
]
# dcs.c DCS_Options are octal digits stored as hex (0x13 = D023N), which is
# the same 104-code list and order as CHIRP's DTCS_CODES.
DTCS_CODES = list(chirp_common.DTCS_CODES)
# frequencies.c gStepFrequencyTable (10 Hz units) in index order, as kHz
STEPS = [2.5, 5.0, 6.25, 10.0, 12.5, 25.0, 8.33, 0.01, 0.05, 0.1, 0.25,
         0.5, 1.0, 1.25, 15.0, 30.0, 50.0, 100.0, 125.0, 250.0, 500.0]
POWER_LEVELS = [
    chirp_common.PowerLevel("Low", watts=1.5),
    chirp_common.PowerLevel("Mid", watts=3.0),
    chirp_common.PowerLevel("High", watts=5.0),
]
# radio.h BK4819 filter bandwidth indexes
BANDWIDTHS = ["Wide", "Narrow", "Narrow aviation", "Narrower", "Narrowest"]
MODULATIONS = ["FM", "AM", "SSB"]
SCRAMBLERS = ["Off", "2600 Hz", "2700 Hz", "2800 Hz", "2900 Hz", "3000 Hz",
              "3100 Hz", "3200 Hz", "3300 Hz", "3400 Hz", "3500 Hz"]
CODE_OFF, CODE_CTCSS, CODE_DCS, CODE_DCS_REVERSE = range(4)


def _read_block(serport, offset, length):
    command = (
        b"\x1b\x05\x08\x00"
        + struct.pack("<HBB", offset, length, 0)
        + b"\x6a\x39\x57\x64"
    )
    uvk5._send_command(serport, command)
    reply = uvk5._receive_reply(serport)
    if len(reply) < 8 + length or reply[:2] != b"\x1c\x05":
        raise errors.RadioError(
            "Bad read reply from the radio at 0x%04x (%i bytes)"
            % (offset, len(reply))
        )
    returned = struct.unpack("<H", reply[4:6])[0]
    if returned != offset:
        raise errors.RadioError(
            "Read address mismatch: asked for 0x%04x, got 0x%04x"
            % (offset, returned)
        )
    return reply[8:8 + length]


def _require_firmware(firmware):
    if not str(firmware).startswith(FIRMWARE_PREFIX):
        raise errors.RadioError(
            "This profile is only for the Robzyl RO-KO 512K firmware; the "
            "radio reports %r. Select the UV-K5 model that matches the "
            "installed firmware." % firmware
        )


def _require_512k_eeprom(image):
    """Refuse the 8K build, or a 512K build on a stock 8 KB EEPROM.

    A 24C64 wraps every 0x2000 bytes, so the 512K channel area would read
    back as copies of the first 8 KB.
    """
    first = image[:STOCK_EEPROM_SIZE]
    copies = [image[start:start + STOCK_EEPROM_SIZE]
              for start in range(STOCK_EEPROM_SIZE, 0x8000, STOCK_EEPROM_SIZE)]
    if all(copy == first for copy in copies):
        raise errors.RadioError(
            "The radio's memory repeats every 8 KB, so it has the stock "
            "8 KB EEPROM or runs the 8K RO-KO build. This profile reads only "
            "the RO-KO 512K build on a radio with an upgraded EEPROM. "
            "Nothing was written to the radio."
        )


def _download(radio):
    serport = radio.pipe
    serport.timeout = 0.5
    status = chirp_common.Status()
    status.cur = 0
    status.max = MEM_SIZE
    status.msg = "Reading RO-KO 512K radio"
    if radio.status_fn:
        radio.status_fn(status)

    firmware = _UVK5._sayhello_with_retry(serport)
    _require_firmware(firmware)
    radio.FIRMWARE_VERSION = firmware
    metadata = dict(radio.metadata)
    metadata["uvk5_firmware"] = firmware
    radio.metadata = metadata

    image = bytearray()
    for address in range(0, MEM_SIZE, MEM_BLOCK):
        image.extend(_read_block(serport, address, MEM_BLOCK))
        status.cur = address + MEM_BLOCK
        if radio.status_fn:
            radio.status_fn(status)
    _require_512k_eeprom(bytes(image))
    return memmap.MemoryMapBytes(bytes(image))


def _tone(code_type, code):
    """(mode, value, polarity) for one direction, as the firmware reads it."""
    if code_type == CODE_CTCSS:
        return "Tone", CTCSS_TONES[code if code < len(CTCSS_TONES) else 0], ""
    if code_type in (CODE_DCS, CODE_DCS_REVERSE):
        value = DTCS_CODES[code if code < len(DTCS_CODES) else 0]
        return "DTCS", value, "R" if code_type == CODE_DCS_REVERSE else "N"
    return "", None, "N"


@directory.register
class QuanshengUVK5RoKo512K(uvk5.UVK5RadioBase):
    """Quansheng UV-K5 (V1) with Robzyl RO-KO 512K firmware (read-only)."""

    VENDOR = "Quansheng"
    MODEL = "UV-K5 (RO-KO 512K)"
    BAUD_RATE = 38400
    FIRMWARE_VERSION = ""
    # Read-only until a physical write/read-back is validated; the app
    # explains this before a write starts.
    NEWCHIRP_WRITE_DISABLED = True

    @classmethod
    def detect_from_serial(cls, pipe):
        _require_firmware(_UVK5._sayhello_with_retry(pipe))
        return cls

    @classmethod
    def match_model(cls, filedata, filename):
        return False

    @classmethod
    def get_prompts(cls):
        prompts = chirp_common.RadioPrompts()
        prompts.experimental = (
            "This read-only profile is for UV-K5 (V1) radios with an "
            "upgraded EEPROM running the Robzyl RO-KO 512K firmware. It reads "
            "999 channels using the layout in the RO-KO firmware source. "
            "Writing is disabled until a read and a write/read-back have "
            "been checked on a real radio."
        )
        prompts.pre_download = (
            "1. Turn the radio on normally (not in flash mode).\n"
            "2. Connect the programming cable firmly.\n"
            "3. Click OK to read the radio."
        )
        prompts.pre_upload = (
            "Writing to the RO-KO 512K profile is not enabled yet."
        )
        return prompts

    def get_features(self):
        rf = chirp_common.RadioFeatures()
        rf.has_bank = False
        rf.has_settings = False
        rf.has_comment = False
        rf.has_ctone = True
        rf.has_rx_dtcs = True
        rf.has_cross = True
        rf.valid_tones = sorted(CTCSS_TONES)
        rf.valid_dtcs_codes = list(DTCS_CODES)
        rf.valid_tmodes = ["", "Tone", "TSQL", "DTCS", "Cross"]
        rf.valid_cross_modes = [
            "Tone->Tone", "Tone->DTCS", "DTCS->Tone",
            "->Tone", "->DTCS", "DTCS->", "DTCS->DTCS",
        ]
        rf.valid_duplexes = ["", "-", "+"]
        rf.valid_modes = ["FM", "NFM", "AM", "NAM", "USB"]
        rf.valid_power_levels = list(POWER_LEVELS)
        rf.valid_tuning_steps = sorted(STEPS)
        rf.valid_name_length = 10
        rf.valid_characters = chirp_common.CHARSET_ASCII
        rf.valid_skips = [""]
        rf.memory_bounds = (1, CHANNEL_COUNT)
        rf.valid_bands = [
            (14_000_000, 630_000_000),
            (760_000_000, 1_300_000_000),
        ]
        return rf

    def sync_in(self):
        self._mmap = _download(self)
        self.process_mmap()

    def sync_out(self):
        raise errors.RadioError(
            "Writing to the UV-K5 RO-KO 512K profile is not enabled yet; "
            "nothing was sent to the radio."
        )

    def process_mmap(self):
        if len(self._mmap.get_packed()) < MEM_SIZE:
            raise errors.RadioError(
                "This image is %i bytes; an RO-KO 512K image is %i bytes."
                % (len(self._mmap.get_packed()), MEM_SIZE)
            )
        self._memobj = bitwise.parse(MEM_FORMAT, self._mmap)

    def get_raw_memory(self, number):
        return repr(self._memobj.channel[number - 1])

    def get_memory(self, number):
        index = number - 1
        _mem = self._memobj.channel[index]
        _att = self._memobj.attributes[index]
        mem = chirp_common.Memory()
        mem.number = number
        mem.immutable = []

        freq = int(_mem.freq)
        if int(_att.band) > VALID_BANDS_MAX or freq in (0, 0xFFFFFFFF):
            mem.empty = True
            return mem

        mem.freq = freq * 10
        name = bytes(int(ch) for ch in self._memobj.names[index].name)
        mem.name = name.split(b"\x00")[0].split(b"\xff")[0].decode(
            "ascii", "replace").rstrip()

        offset = int(_mem.offset)
        if offset >= 100_000_000:
            offset = 1_000_000     # RADIO_ConfigureChannel's default
        mem.offset = offset * 10
        direction = int(_mem.offset_dir)
        mem.duplex = {1: "+", 2: "-"}.get(direction, "")
        if not mem.duplex:
            mem.offset = 0

        raw = self._mmap.get_packed()[0x2000 + index * 16 + 12]
        if raw == 0xFF:
            bandwidth, power, reverse = 0, 0, False
        else:
            reverse = bool(_mem.freq_reverse)
            power = min(int(_mem.txpower), 2)
            bandwidth = int(_mem.bandwidth_ext) + 1 if _mem.bandwidth else 0
        mem.power = POWER_LEVELS[power]

        modulation = int(_mem.modulation)
        if modulation >= len(MODULATIONS):
            modulation = 0
        if modulation == 2:
            mem.mode = "USB"
        elif modulation == 1:
            mem.mode = "AM" if bandwidth == 0 else "NAM"
        else:
            mem.mode = "FM" if bandwidth == 0 else "NFM"

        step = int(_mem.step)
        mem.tuning_step = STEPS[step if step < len(STEPS) else 4]

        rx = _tone(int(_mem.rxcodeflag), int(_mem.rxcode))
        tx = _tone(int(_mem.txcodeflag), int(_mem.txcode))
        if modulation != 0:
            rx = ("", None, "N")   # the firmware ignores codes off FM
        chirp_common.split_tone_decode(mem, tx, rx)

        extra = RadioSettingGroup("extra", "Extra")
        rows = [
            ("modulation", "Modulation", MODULATIONS[modulation]),
            ("bandwidth", "Bandwidth",
             BANDWIDTHS[bandwidth if bandwidth < len(BANDWIDTHS) else 0]),
            ("scanlist", "Scan list", str(int(_att.scanlist))),
            ("scrambler", "Scrambler",
             SCRAMBLERS[int(_mem.scrambler)]
             if int(_mem.scrambler) < len(SCRAMBLERS) else "Off"),
            ("busy_lockout", "Busy channel lockout",
             "On" if _mem.busy_lockout and raw != 0xFF else "Off"),
            ("reverse", "Reverse", "On" if reverse else "Off"),
        ]
        for key, label, value in rows:
            setting = RadioSetting(key, label, RadioSettingValueString(
                0, 32, value, autopad=False))
            setting.value.set_mutable(False)
            extra.append(setting)
        mem.extra = extra
        return mem

    def set_memory(self, memory):
        raise errors.RadioError(
            "The UV-K5 RO-KO 512K profile is read-only."
        )
