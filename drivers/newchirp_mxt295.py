# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Midland MXT295 experimental clone driver.

Built from one MXPG15 read and one write of a single radio. The radio
answers as SMP558 at 115200 8N1. Channel rows are 32 bytes. 107 rows
start at 0x0000. One settings block lives at 0xE000. Its first 10
bytes are the Radio & Modes settings from the Midland program. The
rest of that block is kept as it was read. The gap between the
channels and the settings is never written.
NewChirp shows Midland's channel numbers on top of that order. Slots
16, 18, 20, 22, 24, 26, 28, and 30 are RPTR 15 through RPTR 22. Those
eight rows are never written empty. Clearing one puts the plain GMRS
repeater frequency back. A write puts each row in the same slot.
Channels 1 through 22 stay on their GMRS frequencies. Channels
1 through 7 stay simplex. Channels 8 through 14 stay receive only.
An offset is only allowed on GMRS channels 15 through 22, and that
offset is +5 MHz. Channels 23 through 99 use one of those same
receive channels.
"""

import logging

from chirp import bitwise
from chirp import chirp_common
from chirp import directory
from chirp import errors
from chirp import memmap
from chirp import settings

LOG = logging.getLogger(__name__)

SLOT_COUNT = 107
SLOT_SIZE = 32
SETTINGS_ADDR = 0xE000
MEM_SIZE = SETTINGS_ADDR + SLOT_SIZE

# RPTR 15 through RPTR 22. The radio always keeps these rows. An empty
# one makes channel-down skip channels when repeater channels are off.
PLAIN_REPEATER_RX = {
    16: 462550000,
    18: 462575000,
    20: 462600000,
    22: 462625000,
    24: 462650000,
    26: 462675000,
    28: 462700000,
    30: 462725000,
}
DCS_BASE = 0x2800

POWER_LOW = chirp_common.PowerLevel("Low", watts=5)
POWER_HIGH = chirp_common.PowerLevel("High", watts=15)
POWER_LEVELS = [POWER_LOW, POWER_HIGH]
BANDS = (
    (462550000, 462737500),
    (467550000, 467737500),
)

# CHIRP numbers follow radio order: 1-14 are GMRS 1-14, 15-30 are
# GMRS 15-22 as simplex then repeater, and 31-107 are GMRS 23-99.
MEM_FORMAT = """
struct {
  char name[8];
  u32 rx_freq;
  u16 rx_tone;
  u32 tx_freq;
  u16 tx_tone;
  u8 unknown7:3,
     scan:1,
     wide:1,
     unknown2:1,
     high:1,
     repeater:1;
  u8 pad[11];
} slots[107];

#seekto 0xE000;
struct {
  u8 vox;
  u8 rogerbeep;
  u8 calltone;
  u8 backlight;
  u8 backlightcolor;
  u8 repeat;
  u8 dw;
  u8 sq;
  u8 beep;
  u8 micgain;
  u8 unused[22];
} settings;
"""


def _midland_channel_label(index):
    """Return the Midland label for a 0-based memory slot."""
    location = index + 1
    if location <= 15:
        return str(location)
    if location <= 30:
        offset = location - 15
        channel = 15 + offset // 2
        if offset % 2:
            return "RPTR %d" % channel
        return str(channel)
    return str(location - 8)


def _dual_watch_choices(repeater_on):
    """Repeater off is channels 1-99. On uses the channel-list labels."""
    if repeater_on:
        return [_midland_channel_label(index) for index in range(SLOT_COUNT)]
    return [str(number) for number in range(1, 100)]


# Radio & Modes, in the Midland program's order. Names match the
# settings struct, and that struct's field order is the radio byte
# order. The stored byte is the dropdown position. Dual Watch's list
# depends on Repeater.
_RADIO_MODE_SETTINGS = (
    ("vox", "VOX", ("Off", "1", "2", "3", "4"),
     "Off, or levels 1 through 4. Level 1 is the most sensitive."),
    ("rogerbeep", "Roger Beep", ("Off", "On"),
     "On sends a short tone when you let go of the talk button."),
    ("calltone", "Call Tone", ("Off", "1", "2", "3", "4", "5"),
     "Off, or call tone 1 through 5."),
    ("backlight", "Backlight", ("0 Off", "1", "2", "3 Brightest"),
     "0 is off. 3 is the brightest."),
    ("backlightcolor", "Backlight Color",
     ("1 White", "2 Blue", "3 Green", "4 Red",
      "5 Cyan", "6 Purple", "7 Yellow"),
     "Screen colors in the radio menu order, 1 through 7."),
    ("repeat", "Repeater", ("Disabled", "Enabled"),
     "Enabled shows repeater rows RPTR 15 through RPTR 22."),
    ("dw", "Dual Watch Pro Channel", _dual_watch_choices,
     "With Repeater off, pick channel 1 through 99. With Repeater on, "
     "the list matches the channel screen, including the RPTR rows. "
     "Turning Repeater on keeps the same position, so check this "
     "channel again."),
    ("sq", "SQ Level", tuple(str(number) for number in range(10)),
     "0 through 9. A lower number lets in weaker signals. "
     "The usual starting point is 4."),
    ("beep", "Key Beep", ("Off", "On"),
     "On beeps when a button is pressed."),
    ("micgain", "Mic Gain", ("1", "2", "3"),
     "1 is the most sensitive. The Midland guide says Mic Gain is "
     "only used by the MXT115P. This radio still stores the value."),
)


def _mode_choices(choices, repeater_on):
    if callable(choices):
        return choices(repeater_on)
    return choices


def _choice_value(choices, index):
    """One dropdown. A byte outside the list is shown and left unchanged."""
    options = list(choices)
    if 0 <= index < len(options):
        return settings.RadioSettingValueList(options, current_index=index)
    value = settings.RadioSettingValueList(
        ["Stored value %d" % index],
        current_index=0,
    )
    value.set_mutable(False)
    return value


def _block_addresses():
    addresses = [index * SLOT_SIZE for index in range(SLOT_COUNT)]
    addresses.append(SETTINGS_ADDR)
    return addresses


def _in_band(freq):
    return any(low <= freq < high for low, high in BANDS)


def _require_band(freq, label):
    if not _in_band(freq):
        raise errors.InvalidValueError(
            "%s %s is outside the GMRS channels this radio uses"
            % (label, chirp_common.format_freq(freq))
        )


def _require_step(freq, label):
    if freq % 12500:
        raise errors.InvalidValueError(
            "%s must be on a 12.5 kHz channel" % label
        )


# GMRS repeater outputs, 462.550 through 462.725. The +5 MHz input
# lands on 467.550 through 467.725. Interstitial channels are not
# repeater pairs.
REPEATER_OUTPUTS = tuple(462550000 + (index * 25000) for index in range(8))
REPEATER_OFFSET = 5000000


def _gmrs_rx_hz(channel):
    """Official receive frequency for GMRS channels 1 through 22."""
    if 1 <= channel <= 7:
        return 462562500 + (channel - 1) * 25000
    if 8 <= channel <= 14:
        return 467562500 + (channel - 8) * 25000
    if 15 <= channel <= 22:
        return 462550000 + (channel - 15) * 25000
    return None


def _slot_gmrs_channel(number):
    """Midland channel 1-22 for a memory slot. Slots 31-107 are open."""
    if 1 <= number <= 15:
        return number
    if 16 <= number <= 30:
        return 15 + (number - 15) // 2
    return None


def _mhz_label(hz):
    return "%d.%06d" % (hz // 1000000, hz % 1000000)


def _gmrs_channel_for_hz(hz):
    """GMRS channel 1-22 for a receive frequency, or None."""
    for channel in range(1, 23):
        if _gmrs_rx_hz(channel) == hz:
            return channel
    return None


def _channel_name(number):
    label = _midland_channel_label(int(number) - 1)
    if label.startswith("RPTR"):
        return label
    return "Channel %s" % label


def _gmrs_problem(mem):
    """Why this channel is not legal on the MXT295, or None.

    The editor uses the same rules in lib/models/radio_channel.dart.
    """
    number = int(mem.number)
    rx_freq = int(mem.freq)
    offset = int(mem.offset)
    duplex = mem.duplex
    channel = _slot_gmrs_channel(number)
    fixed = _gmrs_rx_hz(channel) if channel else None
    if fixed is not None and rx_freq != fixed:
        return "%s must stay on %s MHz." % (
            _channel_name(number), _mhz_label(fixed)
        )
    if 8 <= number <= 14:
        if duplex != "off" or offset != 0:
            return (
                "Channels 8 through 14 stay receive only. "
                "Duplex stays off."
            )
        return None
    if number in PLAIN_REPEATER_RX:
        if duplex != "+" or offset != REPEATER_OFFSET:
            return "Repeater rows use a +5 MHz offset."
        return None
    if 1 <= number <= 7:
        if duplex != "" or offset != 0:
            return "Channels 1 through 14 stay simplex."
        return None
    if channel is None:
        picked = _gmrs_channel_for_hz(rx_freq)
        if picked is not None and picked <= 14:
            if duplex != "" or offset != 0:
                return "Channels 1 through 14 stay simplex."
            return None
    if duplex == "+":
        if offset != REPEATER_OFFSET:
            return "Repeater offset must be +5 MHz."
        if rx_freq not in REPEATER_OUTPUTS:
            return (
                "A +5 MHz offset is only for GMRS repeater frequencies "
                "462.550 through 462.725 MHz."
            )
        return None
    if duplex in ("", "off"):
        if offset != 0:
            return "Offset must be 0 unless duplex is +5 MHz."
        return None
    return (
        "This radio only allows simplex, receive only (off), "
        "or a +5 MHz repeater."
    )


def _tone_spec(word):
    """Return the split-tone tuple stored in one 16-bit tone word."""
    if word in (0, 0xFFFF):
        return ("", None, None)
    if word >= DCS_BASE:
        code = int(format(word - DCS_BASE, "o"))
        return ("DTCS", code, "N")
    return ("Tone", word / 10.0, None)


def _encode_tone(mode, value, polarity):
    if not mode:
        return 0xFFFF
    if mode == "Tone":
        tenths = int(round(float(value) * 10))
        if tenths <= 0 or tenths >= DCS_BASE:
            raise errors.InvalidValueError("That tone is out of range")
        return tenths
    if mode == "DTCS":
        if polarity not in (None, "N"):
            raise errors.InvalidValueError(
                "Inverted DCS is not supported on this radio yet"
            )
        if value not in chirp_common.DTCS_CODES:
            raise errors.InvalidValueError(
                "DCS code %s is not supported" % value
            )
        return DCS_BASE + int(str(int(value)), 8)
    raise errors.InvalidValueError("Tone mode %s is not supported" % mode)


def _tx_frequency(mem):
    if mem.duplex == "off":
        return 0
    if mem.duplex == "":
        return int(mem.freq)
    if mem.duplex == "+":
        return int(mem.freq) + int(mem.offset)
    if mem.duplex == "-":
        return int(mem.freq) - int(mem.offset)
    if mem.duplex == "split":
        return int(mem.offset)
    raise errors.InvalidValueError(
        "Duplex %s is not supported" % mem.duplex
    )


@directory.register
class MXT295Radio(chirp_common.CloneModeRadio,
                  chirp_common.ExperimentalRadio):
    """Midland MXT295"""

    VENDOR = "Midland"
    MODEL = "MXT295"
    BAUD_RATE = 115200
    NEEDS_COMPAT_SERIAL = False
    _memsize = MEM_SIZE

    @classmethod
    def get_prompts(cls):
        radio_prompts = chirp_common.RadioPrompts()
        # Read and write use different wording. A blank experimental
        # value stays set so the warning icon still shows.
        radio_prompts.experimental = ""
        radio_prompts.pre_download = (
            "This driver for Midland radios is experimental.  Download "
            "first and check the channels before you upload and keep a "
            "backup of your radio from the Midland program.\n"
            "\n"
            "1. Power the radio with 12 volts.\n"
            "2. Turn the Bluetooth mic off.\n"
            "3. Plug the MXPG15 cable into the radio base.\n"
            "4. Click OK to download."
        )
        radio_prompts.pre_upload = (
            "This Midland driver is experimental.  Make a backup of "
            "your radio before using this experimental driver to make "
            "any changes."
        )
        return radio_prompts

    def get_features(self):
        rf = chirp_common.RadioFeatures()
        rf.has_bank = False
        rf.has_settings = True
        rf.has_tuning_step = False
        # The radio stores an exact Hertz value and does not keep a step.
        # NewChirp's default step is 5 kHz, which would otherwise block
        # every save. The 12.5 kHz grid is checked on the frequency itself.
        rf.has_nostep_tuning = True
        rf.has_rx_dtcs = True
        rf.has_cross = True
        rf.can_odd_split = False
        rf.memory_bounds = (1, SLOT_COUNT)
        rf.valid_bands = list(BANDS)
        rf.valid_modes = ["FM", "NFM"]
        rf.valid_power_levels = list(POWER_LEVELS)
        rf.valid_tuning_steps = [12.5]
        rf.valid_duplexes = ["", "+", "off"]
        rf.valid_tmodes = ["", "Tone", "TSQL", "DTCS", "Cross"]
        rf.valid_cross_modes = list(chirp_common.CROSS_MODES)
        rf.valid_skips = ["", "S"]
        rf.valid_dtcs_pols = ["NN"]
        rf.valid_characters = chirp_common.CHARSET_UPPER_NUMERIC
        rf.valid_name_length = 8
        return rf

    def _require_image(self):
        if getattr(self, "_memobj", None) is None:
            raise errors.RadioError(
                "Download from the radio before changing settings"
            )
        return self._memobj.settings

    def get_settings(self):
        block = self._require_image()
        repeater_on = int(block.repeat) != 0
        group = settings.RadioSettingGroup("radio_modes", "Radio & Modes")
        group.set_doc(
            "These match the Midland program's Radio & Modes tab."
        )
        for name, label, choices, doc in _RADIO_MODE_SETTINGS:
            value = _choice_value(
                _mode_choices(choices, repeater_on),
                int(getattr(block, name)),
            )
            item = settings.RadioSetting(name, label, value)
            item.set_doc(doc)
            group.append(item)
        return settings.RadioSettings(group)

    def set_settings(self, ui_settings):
        block = self._require_image()
        known = {spec[0] for spec in _RADIO_MODE_SETTINGS}
        for element in ui_settings:
            self._apply_setting_element(block, known, element)

    def _apply_setting_element(self, block, known, element):
        if isinstance(element, settings.RadioSetting):
            name = element.get_name()
            if name not in known:
                raise errors.InvalidValueError(
                    "Unknown radio setting"
                )
            if not element.value.get_mutable():
                return
            index = int(element.value)
            if index < 0 or index > 255:
                raise errors.InvalidValueError(
                    "That radio setting is out of range"
                )
            setattr(block, name, index)
            return
        if isinstance(element, settings.RadioSettingGroup):
            for child in element:
                self._apply_setting_element(block, known, child)

    def validate_memory(self, mem):
        msgs = chirp_common.Radio.validate_memory(self, mem)
        if mem.empty:
            return msgs
        problem = _gmrs_problem(mem)
        if problem:
            msgs.append(chirp_common.ValidationError(problem))
        rx_freq = int(mem.freq)
        if rx_freq % 12500:
            msgs.append(chirp_common.ValidationError(
                "Receive frequency must be on a 12.5 kHz channel"
            ))
        try:
            tx_freq = _tx_frequency(mem)
        except errors.InvalidValueError as exc:
            msgs.append(chirp_common.ValidationError(str(exc)))
            return msgs
        if tx_freq and tx_freq % 12500:
            msgs.append(chirp_common.ValidationError(
                "Transmit frequency must be on a 12.5 kHz channel"
            ))
        return msgs

    def sync_in(self):
        self._run_clone(self._download_image)

    def sync_out(self):
        if self._mmap is None or len(self._mmap) < MEM_SIZE:
            raise errors.RadioError(
                "Download from the radio before uploading"
            )
        self._run_clone(self._upload_image)

    def process_mmap(self):
        if self._mmap is None or len(self._mmap) < MEM_SIZE:
            raise errors.RadioError("This image is too small for an MXT295")
        self._memobj = bitwise.parse(MEM_FORMAT, self._mmap)

    def get_raw_memory(self, number):
        return repr(self._slot(number))

    def get_memory(self, number):
        _mem = self._slot(number)
        mem = chirp_common.Memory()
        mem.number = int(number)
        rx_freq = int(_mem.rx_freq)
        tx_freq = int(_mem.tx_freq)
        if rx_freq == 0:
            mem.empty = True
            return mem

        if tx_freq == 0:
            mem.freq = rx_freq
            mem.duplex = "off"
            mem.offset = 0
        else:
            chirp_common.split_to_offset(mem, rx_freq, tx_freq)

        chirp_common.split_tone_decode(
            mem,
            _tone_spec(int(_mem.tx_tone)),
            _tone_spec(int(_mem.rx_tone)),
        )
        mem.name = self._name_from_slot(_mem)
        mem.mode = "FM" if int(_mem.wide) else "NFM"
        mem.power = POWER_HIGH if int(_mem.high) else POWER_LOW
        mem.skip = "" if int(_mem.scan) else "S"
        mem.tuning_step = 12.5
        return mem

    def set_memory(self, mem):
        _mem = self._slot(mem.number)
        if mem.empty:
            plain_rx = PLAIN_REPEATER_RX.get(int(mem.number))
            if plain_rx is not None:
                self._write_plain_repeater(_mem, plain_rx)
                return
            # An already-empty slot keeps the padding from the radio.
            # Clearing a programmed slot uses the Midland empty pattern.
            if int(_mem.rx_freq) != 0:
                self._clear_slot(_mem)
            return
        if mem.mode not in ("FM", "NFM"):
            raise errors.InvalidValueError(
                "Mode %s is not supported" % mem.mode
            )
        if mem.skip not in ("", "S"):
            raise errors.InvalidValueError(
                "Skip %s is not supported" % mem.skip
            )
        if mem.power is not None and mem.power not in POWER_LEVELS:
            raise errors.InvalidValueError(
                "Power %s is not supported" % mem.power
            )
        problem = _gmrs_problem(mem)
        if problem:
            raise errors.InvalidValueError(problem)

        rx_freq = int(mem.freq)
        tx_freq = _tx_frequency(mem)
        _require_band(rx_freq, "Receive frequency")
        _require_step(rx_freq, "Receive frequency")
        if tx_freq:
            _require_band(tx_freq, "Transmit frequency")
            _require_step(tx_freq, "Transmit frequency")
        name = self._stored_name(mem.name)
        tx_spec, rx_spec = chirp_common.split_tone_encode(mem)
        rx_tone = _encode_tone(*rx_spec)
        tx_tone = 0xFFFF if tx_freq == 0 else _encode_tone(*tx_spec)

        _mem.name = name
        _mem.rx_freq = rx_freq
        _mem.tx_freq = tx_freq
        _mem.rx_tone = rx_tone
        _mem.tx_tone = tx_tone
        _mem.wide = 1 if mem.mode == "FM" else 0
        if mem.power == POWER_HIGH:
            _mem.high = 1
        elif mem.power == POWER_LOW:
            _mem.high = 0
        _mem.scan = 0 if mem.skip == "S" else 1
        _mem.repeater = 1 if tx_freq not in (0, rx_freq) else 0

    def _slot(self, number):
        try:
            number = int(number)
        except (TypeError, ValueError):
            raise errors.InvalidValueError(
                "Channel %s is not supported" % number
            )
        if number < 1 or number > SLOT_COUNT:
            raise errors.InvalidValueError(
                "Channel %s is out of range" % number
            )
        return self._memobj.slots[number - 1]

    def _name_from_slot(self, _mem):
        raw = str(_mem.name)
        return raw.split("\x00", 1)[0].split("\xff", 1)[0]

    def _stored_name(self, name):
        name = name or ""
        if len(name) > 8:
            raise errors.InvalidValueError(
                "The name can be at most 8 characters"
            )
        for char in name:
            if char not in chirp_common.CHARSET_UPPER_NUMERIC:
                raise errors.InvalidValueError(
                    "Use uppercase letters, numbers, and spaces in the name"
                )
        return name.ljust(8, "\x00")

    def _write_plain_repeater(self, _mem, rx_freq):
        _mem.name = "\x00" * 8
        _mem.rx_freq = rx_freq
        _mem.tx_freq = rx_freq + 5000000
        _mem.rx_tone = 0xFFFF
        _mem.tx_tone = 0xFFFF
        _mem.unknown7 = 0
        _mem.scan = 0
        _mem.wide = 1
        _mem.unknown2 = 0
        _mem.high = 1
        _mem.repeater = 1

    def _clear_slot(self, _mem):
        _mem.name = "\x00" * 8
        _mem.rx_freq = 0
        _mem.tx_freq = 0
        _mem.rx_tone = 0xFFFF
        _mem.tx_tone = 0xFFFF
        _mem.unknown7 = 0
        _mem.scan = 0
        _mem.wide = 0
        _mem.unknown2 = 0
        _mem.high = 0
        _mem.repeater = 0
        for index in range(11):
            _mem.pad[index] = 0

    def _run_clone(self, operation):
        if self.pipe is None:
            raise errors.RadioError("No serial port is open")
        self._in_program_mode = False
        old_timeout = getattr(self.pipe, "timeout", None)
        try:
            if old_timeout is not None:
                self.pipe.timeout = 1
            self._enter_program_mode()
            operation()
        finally:
            self._leave_program_mode()
            if old_timeout is not None:
                try:
                    self.pipe.timeout = old_timeout
                except Exception:
                    LOG.debug("Could not restore the serial timeout",
                              exc_info=True)

    def _enter_program_mode(self):
        self.pipe.write(b"\x02PROGRAM")
        if self._read_exact(1) != b"\x06":
            raise errors.RadioError(
                "The radio did not enter programming mode. Check 12 volt "
                "power, the MXPG15 cable, and that the Bluetooth mic is off."
            )
        self._in_program_mode = True
        self.pipe.write(b"\x02")
        ident = self._read_exact(8)
        LOG.debug("MXT295 ident %r", ident)
        if ident[:6] != b"SMP558":
            raise errors.RadioError(
                "This radio did not identify as an MXT295"
            )
        self.pipe.write(b"\x06")
        if self._read_exact(1) != b"\x06":
            raise errors.RadioError(
                "The radio did not confirm programming mode"
            )

    def _leave_program_mode(self):
        if not getattr(self, "_in_program_mode", False):
            return
        self._in_program_mode = False
        try:
            self.pipe.write(b"\x62")
        except Exception:
            LOG.warning("Could not leave programming mode", exc_info=True)

    def _download_image(self):
        data = bytearray(b"\xff" * MEM_SIZE)
        addresses = _block_addresses()
        status = chirp_common.Status()
        status.msg = "Downloading from radio"
        status.max = len(addresses)
        for index, addr in enumerate(addresses):
            status.cur = index
            self.status_fn(status)
            block = self._read_block(addr)
            data[addr:addr + SLOT_SIZE] = block
        status.cur = status.max
        self.status_fn(status)
        self._mmap = memmap.MemoryMapBytes(bytes(data))
        self.process_mmap()

    def _upload_image(self):
        addresses = _block_addresses()
        status = chirp_common.Status()
        status.msg = "Uploading to radio"
        status.max = len(addresses)
        for index, addr in enumerate(addresses):
            status.cur = index
            self.status_fn(status)
            self._write_block(addr, bytes(self._mmap[addr:addr + SLOT_SIZE]))
        status.cur = status.max
        self.status_fn(status)

    def _read_block(self, addr):
        command = bytes([
            0x52, (addr >> 8) & 0xFF, addr & 0xFF, 0x20,
        ])
        self.pipe.write(command)
        reply = self._read_exact(4 + SLOT_SIZE)
        if reply[:4] != command:
            LOG.error("Bad MXT295 read reply at %04X: %r", addr, reply[:4])
            raise errors.RadioError(
                "The radio sent an unexpected reply. The download was stopped."
            )
        return reply[4:]

    def _write_block(self, addr, block):
        if addr not in _block_addresses():
            raise errors.RadioError(
                "Refusing to write outside the known channel list"
            )
        if len(block) != SLOT_SIZE:
            raise errors.RadioError("Internal channel size error")
        command = bytes([
            0x57, (addr >> 8) & 0xFF, addr & 0xFF, 0x20,
        ]) + block
        self.pipe.write(command)
        if self._read_exact(1) != b"\x06":
            LOG.error("MXT295 rejected the block at %04X", addr)
            raise errors.RadioError(
                "The radio stopped accepting the upload, so it may only "
                "be partly updated. Download it and check the channels, "
                "or restore the Midland backup."
            )

    def _read_exact(self, count):
        data = b""
        while len(data) < count:
            chunk = self.pipe.read(count - len(data))
            if not chunk:
                raise errors.RadioError(
                    "The radio stopped answering. Check the cable and try again."
                )
            data += chunk
        return data
