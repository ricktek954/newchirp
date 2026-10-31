"""Radioddity DB35-G GMRS mobile driver.

Protocol and memory layout recovered from the official DB-35G Programming
Software 20251029V3 ``model.xml`` file.
"""

import logging
import struct

from chirp import bandplan_na
from chirp import bitwise
from chirp import chirp_common
from chirp import directory
from chirp import errors
from chirp import memmap
from chirp import util
from chirp.settings import (
    MemSetting,
    RadioSetting,
    RadioSettingGroup,
    RadioSettingValueBoolean,
    RadioSettingValueInteger,
    RadioSettingValueList,
    RadioSettings,
)

LOG = logging.getLogger(__name__)

CMD_ACK = b"\x06"
CMD_PROGRAM = b"\x02PROGRAM"
CMD_EXIT = b"\x62"
IDENT_PREFIX = b"SMP558"

NUM_CHANNELS = 80
PAGE_SIZE = 16
CH_START_ADDR = 0x0000
SETTINGS_ADDR = 0xE000
SETTINGS_OFFSET = NUM_CHANNELS * PAGE_SIZE
MEM_SIZE = SETTINGS_OFFSET + PAGE_SIZE

POWER_LEVELS = [
    chirp_common.PowerLevel("Low", watts=5),
    chirp_common.PowerLevel("High", watts=35),
]

TONE_OFF = 0xFFFF
TONE_DCS_FLAG = 0x2000
TONE_INV_FLAG = 0x8000
TONE_DCS_MASK = 0x07FF

TOT_OPTIONS = ["Off", "60 sec", "120 sec", "180 sec"]
NRC_LEVELS = ["L1", "L2", "L3", "L4", "L5"]

MEM_FORMAT = """
struct channel {
    u32 rxfreq;
    u32 txfreq;
    u16 rxtone;
    u16 txtone;
    u8 txpower:2,
       bandwidth:1,
       unknown0:1,
       scanadd:1,
       busylock:1,
       unknown1:2;
    u8 unknown2[3];
};

struct settings {
    u8 sqlevel:4,
       nrclevel:4;
    u8 totlevel:3,
       keybeep:1,
       rogerbeep:1,
       priwatch:1,
       unknown:2;
    u8 unknown2[14];
};

#seekto 0x0000;
struct channel memory[%d];

#seekto 0x%04X;
struct settings settings;
"""


def _enter_programming(radio):
    serial = radio.pipe
    try:
        serial.write(CMD_PROGRAM)
        ack = serial.read(1)
    except Exception:
        raise errors.RadioError("Error communicating with radio")
    if ack != CMD_ACK:
        raise errors.RadioError("Radio did not respond to program mode request")

    try:
        serial.write(b"\x02")
        ident = serial.read(8)
    except Exception:
        raise errors.RadioError("Error communicating with radio")
    LOG.debug("Ident: %s", util.hexprint(ident))
    if not ident.startswith(IDENT_PREFIX):
        raise errors.RadioError(
            "Unsupported radio (ident %s)" % ident.hex()
        )

    try:
        serial.write(CMD_ACK)
        ack = serial.read(1)
    except Exception:
        raise errors.RadioError("Error communicating with radio")
    if ack != CMD_ACK:
        raise errors.RadioError("Radio refused programming mode")


def _exit_programming(radio):
    try:
        radio.pipe.write(CMD_EXIT)
    except Exception:
        raise errors.RadioError("Failed to exit programming mode")


def _read_page(radio, address):
    command = struct.pack(">cHB", b"R", address, PAGE_SIZE)
    try:
        radio.pipe.write(command)
        response = radio.pipe.read(4 + PAGE_SIZE)
    except Exception:
        raise errors.RadioError(
            "Failed to read from radio at 0x%04X" % address
        )
    if len(response) != 4 + PAGE_SIZE:
        raise errors.RadioError(
            "Short read at 0x%04X (%d bytes)" % (address, len(response))
        )
    if response[:4] != command:
        raise errors.RadioError("Bad read response at 0x%04X" % address)
    return response[4:]


def _write_page(radio, address, data):
    if len(data) != PAGE_SIZE:
        raise errors.RadioError(
            "Invalid page length for 0x%04X" % address
        )
    command = struct.pack(">cHB", b"W", address, PAGE_SIZE)
    try:
        radio.pipe.write(command + data)
        ack = radio.pipe.read(1)
    except Exception:
        raise errors.RadioError(
            "Failed to write to radio at 0x%04X" % address
        )
    if ack != CMD_ACK:
        raise errors.RadioError("No ACK after write at 0x%04X" % address)


def do_download(radio):
    _enter_programming(radio)
    data = bytearray(b"\xFF" * MEM_SIZE)
    status = chirp_common.Status()
    status.msg = "Cloning from radio"
    status.max = NUM_CHANNELS + 1

    for index in range(NUM_CHANNELS):
        address = CH_START_ADDR + index * PAGE_SIZE
        offset = index * PAGE_SIZE
        data[offset:offset + PAGE_SIZE] = _read_page(radio, address)
        status.cur = index + 1
        radio.status_fn(status)

    data[SETTINGS_OFFSET:SETTINGS_OFFSET + PAGE_SIZE] = _read_page(
        radio, SETTINGS_ADDR
    )
    status.cur = status.max
    radio.status_fn(status)
    _exit_programming(radio)
    return memmap.MemoryMapBytes(bytes(data))


def do_upload(radio):
    _enter_programming(radio)
    status = chirp_common.Status()
    status.msg = "Uploading to radio"
    status.max = NUM_CHANNELS + 1
    raw = radio.get_mmap().get_packed()

    for index in range(NUM_CHANNELS):
        address = CH_START_ADDR + index * PAGE_SIZE
        offset = index * PAGE_SIZE
        _write_page(radio, address, raw[offset:offset + PAGE_SIZE])
        status.cur = index + 1
        radio.status_fn(status)

    _write_page(
        radio,
        SETTINGS_ADDR,
        raw[SETTINGS_OFFSET:SETTINGS_OFFSET + PAGE_SIZE],
    )
    status.cur = status.max
    radio.status_fn(status)
    _exit_programming(radio)


def _decode_tone(value):
    value = int(value)
    if value == TONE_OFF:
        return "", None, None
    if value & TONE_DCS_FLAG:
        code = int(oct(value & TONE_DCS_MASK)[2:])
        polarity = "R" if value & TONE_INV_FLAG else "N"
        return "DTCS", code, polarity
    return "Tone", value / 10.0, None


def _encode_tone(mode, value, polarity):
    if not mode:
        return TONE_OFF
    if mode == "Tone":
        return int(value * 10)
    if mode == "DTCS":
        result = TONE_DCS_FLAG | 0x0800 | int(str(value), 8)
        if polarity == "R":
            result |= TONE_INV_FLAG
        return result
    raise errors.RadioError("Unsupported tone mode: %s" % mode)


@directory.register
class RadioddityDB35G(chirp_common.CloneModeRadio):
    """Radioddity DB35-G"""

    VENDOR = "Radioddity"
    MODEL = "DB35-G"
    BAUD_RATE = 115200
    _memsize = MEM_SIZE

    @classmethod
    def get_prompts(cls):
        prompts = chirp_common.RadioPrompts()
        prompts.experimental = (
            "This DB35-G driver is experimental and has not yet been "
            "validated with a physical radio. Reading is enabled; writing "
            "is disabled until a physical read and controlled write are "
            "verified.\n"
        )
        prompts.pre_download = (
            "Connect the programming cable to the rear microphone port. "
            "Turn on the radio, close Radioddity CPS, then start the read."
        )
        prompts.pre_upload = (
            "Connect the programming cable to the rear microphone port. "
            "Writing is currently disabled for this experimental driver."
        )
        return prompts

    def get_features(self):
        rf = chirp_common.RadioFeatures()
        rf.has_settings = True
        rf.has_bank = False
        rf.has_tuning_step = False
        rf.has_name = False
        rf.has_ctone = True
        rf.has_dtcs = True
        rf.has_rx_dtcs = True
        rf.has_cross = True
        rf.can_odd_split = True
        rf.valid_modes = ["FM", "NFM"]
        rf.valid_tmodes = ["", "Tone", "TSQL", "DTCS", "Cross"]
        rf.valid_cross_modes = list(chirp_common.CROSS_MODES)
        rf.valid_duplexes = ["", "-", "+", "split", "off"]
        rf.valid_skips = ["", "S"]
        rf.valid_power_levels = POWER_LEVELS
        rf.valid_bands = [
            (136000000, 175000000),
            (400000000, 470000000),
        ]
        rf.memory_bounds = (1, NUM_CHANNELS)
        rf.valid_tuning_steps = [5.0, 6.25, 12.5, 25.0]
        rf.valid_characters = ""
        rf.valid_name_length = 0
        return rf

    def process_mmap(self):
        self._memobj = bitwise.parse(
            MEM_FORMAT % (NUM_CHANNELS, SETTINGS_OFFSET),
            self._mmap,
        )

    def sync_in(self):
        self._mmap = do_download(self)
        self.process_mmap()

    def sync_out(self):
        raise errors.RadioError(
            "DB35-G write support is disabled until physical validation is "
            "complete."
        )

    def get_raw_memory(self, number):
        return repr(self._memobj.memory[number - 1])

    def get_memory(self, number):
        raw = self._memobj.memory[number - 1]
        mem = chirp_common.Memory()
        mem.number = number

        rxfreq = int(raw.rxfreq)
        if rxfreq in (0, 0xFFFFFFFF):
            mem.empty = True
            return mem

        mem.freq = rxfreq
        txfreq = int(raw.txfreq)
        if txfreq in (0, 0xFFFFFFFF):
            mem.duplex = "off"
            mem.offset = 0
        elif txfreq == rxfreq:
            mem.duplex = ""
            mem.offset = 0
        elif txfreq > rxfreq:
            mem.duplex = "+"
            mem.offset = txfreq - rxfreq
        else:
            mem.duplex = "-"
            mem.offset = rxfreq - txfreq

        mem.mode = "FM" if int(raw.bandwidth) else "NFM"
        power_index = int(raw.txpower)
        mem.power = (
            POWER_LEVELS[power_index]
            if power_index < len(POWER_LEVELS)
            else POWER_LEVELS[0]
        )
        mem.skip = "" if int(raw.scanadd) else "S"
        chirp_common.split_tone_decode(
            mem,
            _decode_tone(raw.txtone),
            _decode_tone(raw.rxtone),
        )

        mem.extra = RadioSettingGroup("extra", "Extra")
        mem.extra.append(
            RadioSetting(
                "busylock",
                "Busy Lock",
                RadioSettingValueBoolean(bool(int(raw.busylock))),
            )
        )
        return mem

    def validate_memory(self, mem):
        messages = super().validate_memory(mem)
        if mem.empty:
            return messages

        if mem.duplex == "split":
            tx_freq = int(mem.offset)
        elif mem.duplex == "+":
            tx_freq = int(mem.freq + mem.offset)
        elif mem.duplex == "-":
            tx_freq = int(mem.freq - mem.offset)
        elif mem.duplex == "off":
            tx_freq = 0
        else:
            tx_freq = int(mem.freq)
        if not tx_freq:
            return messages

        repeater_tx = [
            freq + 5000000 for freq in bandplan_na.GMRS_HIRPT
        ]
        allowed = list(bandplan_na.ALL_GMRS_FREQS) + repeater_tx
        if tx_freq not in allowed:
            messages.append(
                chirp_common.ValidationWarning(
                    "TX frequency %s is not a standard GMRS frequency"
                    % chirp_common.format_freq(tx_freq)
                )
            )
        if tx_freq in bandplan_na.GMRS_HHONLY:
            if mem.power != POWER_LEVELS[0]:
                messages.append(
                    chirp_common.ValidationWarning(
                        "GMRS 467 MHz channels require low power"
                    )
                )
            if mem.mode != "NFM":
                messages.append(
                    chirp_common.ValidationWarning(
                        "GMRS 467 MHz channels require narrowband"
                    )
                )
        return messages

    def set_memory(self, mem):
        raw = self._memobj.memory[mem.number - 1]
        if mem.empty:
            raw.set_raw(b"\xFF" * PAGE_SIZE)
            return

        raw.rxfreq = mem.freq
        if mem.duplex == "off":
            raw.txfreq = 0
        elif mem.duplex == "+":
            raw.txfreq = mem.freq + mem.offset
        elif mem.duplex == "-":
            raw.txfreq = mem.freq - mem.offset
        elif mem.duplex == "split":
            raw.txfreq = mem.offset
        else:
            raw.txfreq = mem.freq

        raw.bandwidth = 1 if mem.mode == "FM" else 0
        try:
            raw.txpower = POWER_LEVELS.index(mem.power)
        except ValueError:
            raw.txpower = 0
        raw.scanadd = mem.skip != "S"

        (txmode, txval, txpol), (rxmode, rxval, rxpol) = (
            chirp_common.split_tone_encode(mem)
        )
        raw.txtone = _encode_tone(txmode, txval, txpol)
        raw.rxtone = _encode_tone(rxmode, rxval, rxpol)

        for setting in mem.extra:
            if setting.get_name() == "busylock":
                raw.busylock = bool(setting.value)

    def get_settings(self):
        raw = self._memobj.settings
        basic = RadioSettingGroup("basic", "Basic Settings")

        basic.append(
            MemSetting(
                "settings.sqlevel",
                "Squelch Level",
                RadioSettingValueInteger(0, 9, min(int(raw.sqlevel), 9)),
            )
        )
        basic.append(
            MemSetting(
                "settings.nrclevel",
                "NRC Level",
                RadioSettingValueList(
                    NRC_LEVELS,
                    current_index=min(int(raw.nrclevel), len(NRC_LEVELS) - 1),
                ),
            )
        )
        basic.append(
            MemSetting(
                "settings.totlevel",
                "TX Time-out Timer",
                RadioSettingValueList(
                    TOT_OPTIONS,
                    current_index=min(
                        int(raw.totlevel), len(TOT_OPTIONS) - 1
                    ),
                ),
            )
        )
        basic.append(
            MemSetting(
                "settings.keybeep",
                "Key Beep",
                RadioSettingValueBoolean(bool(int(raw.keybeep))),
            )
        )
        basic.append(
            MemSetting(
                "settings.rogerbeep",
                "Roger Beep",
                RadioSettingValueBoolean(bool(int(raw.rogerbeep))),
            )
        )
        basic.append(
            MemSetting(
                "settings.priwatch",
                "Priority Watch",
                RadioSettingValueBoolean(bool(int(raw.priwatch))),
            )
        )
        return RadioSettings(basic)

    def set_settings(self, settings):
        settings.apply_to(self._memobj)
