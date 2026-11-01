# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Experimental nicFW950 support for RT-950 Pro and BJ-9000.

Adapted from the user-supplied nicfw_950_v4.py protocol/layout reference.
This is a memory programmer for radios already running nicFW950, not a
firmware flasher. Read/write validation covers one nicFW950 6.00.16c unit.
"""

import logging
import struct
import time

from chirp import bitwise, chirp_common, directory, errors, memmap
from chirp.settings import (
    RadioSetting,
    RadioSettingGroup,
    RadioSettingValueBoolean,
    RadioSettingValueFloat,
    RadioSettingValueInteger,
    RadioSettingValueList,
    RadioSettingValueString,
)

LOG = logging.getLogger(__name__)

BASE = 0x50200
CHANNEL_IMAGE_SIZE = 0xF400
SETTINGS_BASE = 0x5F600
SETTINGS_SIZE = 0x400
GROUP_NAMES_BASE = 0x5FB00
GROUP_NAMES_SIZE = 0x200
GROUP_NAME_SLOT_SIZE = 13
GROUP_NAME_MAX_LENGTH = 12
# Include intervening calibration/power-band blocks unchanged.
IMAGE_SIZE = GROUP_NAMES_BASE + GROUP_NAMES_SIZE - BASE
BLOCK = 128
RECORD = 62
FIRST_RECORD = 4
CHANNELS = 999
DEFAULT_BAUD = 38400
FAST_BAUD = 460800
MAGIC = 0xC950

FORMAT = r"""
#seekto 0x0000;
u8 reserved_records[248];
struct {
  ul32 rxFrequency;
  ul32 txFrequency;
  ul32 groups;
  ul16 rxSubtone;
  ul16 txSubtone;
  il16 clarifier;
  u8 modulation;
  u8 bandwidth;
  u8 busyLock;
  u8 txPower;
  u8 reversed;
  u8 pttID;
  ul16 magic;
  u8 scrambler;
  u8 scanpersist_override;
  u8 scanmonitor_override;
  u8 permanent;
  u8 reserved[2];
  char name[30];
} channels[999];
"""

MODULATIONS = ["FM", "AM", "DSB", "Automatic"]
BANDWIDTHS = ["Wide", "Narrow", "Automatic"]
POWERS = [
    "TX Disabled",
    "Zero",
    "Very Low",
    "Low",
    "Medium",
    "High",
    "Very High",
]
GROUPS = ["None"] + list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
PTT_TIMING = ["Off", "Beginning", "End", "Both"]
PTT_TYPE = ["DTMF", "MDC1200"]

SETTING_DEFINITIONS = [
    ("Squelch", "number", "Squelch Level", 4, 0, 9, 0, 3, 2),
    ("Squelch", "number", "Noise Trigger", 6, 0, 127, 0, 37, 2),
    ("Squelch", "number", "Noise Hysteresis", 10, 0, 20, 0, 3, 2),
    ("Squelch", "number", "RSSI Hysteresis", 376, 0, 20, 0, 4, 2),
    ("Squelch", "number", "Throttle (ds)", 12, 0, 9, 0, 5, 2),
    ("Squelch", "number", "Noise Ceiling", 8, 0, 127, 0, 48, 2),
    (
        "Squelch",
        "options",
        "Tail Elimination",
        40,
        0,
        ["Off", "RX", "TX", "Both"],
    ),
    ("Squelch", "number", "Squelch Tail (s)", 378, 0, 5, 1, 0.6, 2),
    ("Scanning", "number", "VFO Start (MHz)", 236, 18, 1299.99999, 5, 118, 4),
    ("Scanning", "number", "VFO Range (MHz)", 240, 0.025, 500, 5, 19, 4),
    ("Scanning", "number", "VFO Step (kHz)", 244, 0.01, 500, 2, 8.33, 2),
    (
        "Scanning",
        "options",
        "Scan Return",
        496,
        0,
        ["Last Signal", "Start", "Last Scanned", "Original VFO"],
    ),
    (
        "Scanning",
        "options",
        "Scan Modulation",
        248,
        0,
        ["FM", "AM", "DSB", "Automatic"],
    ),
    (
        "Scanning",
        "options",
        "Scan Bandwidth",
        250,
        0,
        ["Wide", "Narrow", "Automatic"],
    ),
    ("Scanning", "bool", "Save Ignores", 494, False),
    ("Scanning", "number", "Ultra Scan Level", 246, 0, 50, 0, 12, 2),
    ("Scanning", "number", "Ultra Scan Time (us)", 498, 1, 9999, 0, 1500, 2),
    ("Scanning", "bool", "Smart Scan", 500, False),
    ("Scanning", "number", "Scan Monitor Time (s)", 252, 0, 500, 0, 0, 2),
    ("Scanning", "number", "Scan Hold Time (s)", 268, 0, 20, 1, 0, 2),
    ("Scanning", "bool", "Scan TX Too?", 256, False),
    ("Scanning", "bool", "Stop Any Key", 506, False),
    ("Scanning", "number", "Channel Scan Speed", 560, 0, 50, 0, 26, 2),
    ("VFO", "number", "Step (kHz)", 14, 0.01, 500, 2, 12.5, 2),
    ("VFO", "number", "TX Timeout (s)", 16, 10, 998, 0, 120, 2),
    ("VFO", "number", "Microphone Gain", 18, 0, 63, 0, 48, 2),
    ("VFO", "number", "Microphone Boost", 566, 0, 30, 0, 1, 2),
    ("VFO", "options", "Ext Microphone Click", 598, 1, ["Off", "On"]),
    ("VFO", "options", "Multi-Watch", 20, 0, ["Off", "On", "Group"]),
    (
        "VFO",
        "options",
        "Group Watch VFOs",
        522,
        7,
        [
            "--",
            "A Only",
            "B Only",
            "A And B",
            "C Only",
            "C And A",
            "C And B",
            "All",
        ],
    ),
    ("VFO", "bool", "Group Watch Fast Mode", 524, True),
    ("VFO", "number", "Multi-Watch Pause (s)", 22, 0, 10, 1, 2, 2),
    ("VFO", "bool", "Multi-Watch Keep VFO", 282, False),
    ("VFO", "number", "VOX Level", 36, 0, 15, 0, 0, 2),
    ("VFO", "number", "VOX Tail (s)", 38, 0.05, 9.98, 2, 2, 2),
    ("VFO", "options", "Tone Monitor", 230, 0, ["Off", "On", "Clone"]),
    ("VFO", "number", "Key Beep Frequency (Hz)", 276, 0, 5000, 0, 0, 2),
    ("VFO", "number", "Roger Beep Sequence", 278, 0, 9999, 0, 0, 2),
    ("VFO", "number", "Roger Beep Time (ms)", 280, 20, 400, 0, 100, 2),
    ("VFO", "bool", "Multi PTT", 478, False),
    (
        "Display",
        "options",
        "Battery Style",
        24,
        2,
        ["Off", "Voltage", "Icon", "Percent"],
    ),
    ("Display", "number", "LCD Timeout (s)", 26, 0, 998, 0, 0, 2),
    ("Display", "number", "Heartbeat (s)", 28, 0, 500, 0, 10, 2),
    (
        "Display",
        "options",
        "Heartbeat Style",
        492,
        0,
        ["Keypad", "RX/TX LEDs", "Both"],
    ),
    ("Display", "bool", "Inverted LCD", 30, False),
    ("Display", "number", "Gamma", 32, 0, 3, 0, 0, 2),
    (
        "Display",
        "options",
        "Signal Bar Style",
        2,
        0,
        ["Stepped", "Segment", "Solid", "Solid Stepped"],
    ),
    ("Display", "number", "Day Brightness", 258, 1, 31, 0, 31, 2),
    ("Display", "number", "Night Brightness", 260, 1, 31, 0, 5, 2),
    ("Display", "number", "Dimmed Brightness", 274, 0, 31, 0, 5, 2),
    ("Display", "options", "Brightness Mode", 262, 0, ["Day", "Night"]),
    ("Display", "number", "Dimmed VFO Level", 384, 0, 10, 0, 3, 2),
    (
        "Display",
        "options",
        "Wake LCD On",
        400,
        3,
        ["Keys Only", "Keys + RX", "Keys + TX", "All"],
    ),
    ("Display", "bool", "S-Meter Always On", 510, False),
    ("DTMF / MDC1200", "number", "Deviation", 264, 1, 8000, 0, 127, 2),
    ("DTMF / MDC1200", "number", "Digit Time (ms)", 386, 0, 999, 0, 125, 2),
    ("DTMF / MDC1200", "number", "Gap Time (ms)", 388, 0, 999, 0, 40, 2),
    ("DTMF / MDC1200", "number", "Start Pause (ms)", 390, 0, 3000, 0, 1000, 2),
    (
        "DTMF / MDC1200",
        "options",
        "Decode DTMF/MDC1200",
        392,
        0,
        ["Off", "On", "P-ID"],
    ),
    (
        "DTMF / MDC1200",
        "number",
        "Display DTMF/MDC1200 For (s)",
        394,
        1,
        99,
        0,
        7,
        2,
    ),
    ("DTMF / MDC1200", "number", "DTMF End Pause (s)", 396, 0.1, 9.9, 1, 1, 2),
    ("Time", "number", "Time Zone", 284, -12, 14, 0, 0, 2),
    ("Time", "options", "Time Format", 398, 0, ["24 Hour", "12 Hour"]),
    ("Time", "bool", "Time Enabled", 406, True),
    ("GPS", "bool", "GPS Enabled", 286, True),
    ("GPS", "options", "Units", 288, 1, ["Nautical", "Imperial", "Metric"]),
    (
        "Advanced",
        "number",
        "Repeater Burst Tone (Hz)",
        266,
        1,
        8000,
        0,
        1750,
        2,
    ),
    ("Advanced", "number", "FM Deviation", 42, 1, 150, 0, 64, 2),
    ("Advanced", "number", "Subtone Deviation", 44, 0, 150, 0, 70, 2),
    ("Advanced", "number", "Tone Monitor Time (s)", 232, 2, 99, 0, 7, 2),
    ("Advanced", "options", "FM Receive Method", 600, 0, ["BK4819", "BK4829"]),
    (
        "Advanced",
        "options",
        "AM Receive Method",
        544,
        1,
        ["BK4819", "BK4829", "Hybrid"],
    ),
    ("Advanced", "bool", "AM AGC Fix", 254, True),
    ("Advanced", "number", "AM/DSB TX Depth", 380, 100, 3000, 0, 256, 2),
    ("Advanced", "number", "AM/DSB TX Mic Gain", 538, 0, 15, 0, 8, 2),
    ("Advanced", "number", "AM TX Envelope", 548, 1024, 16384, 0, 16384, 2),
    ("Advanced", "number", "AM/DSB Sample Frequency", 562, 6, 40, 2, 24.23, 2),
    ("Advanced", "number", "DSB Phase Frequency", 550, 0, 41, 2, 21, 2),
    ("Advanced", "number", "Audio Streaming Gain", 558, 1, 32, 0, 5, 2),
    ("Advanced", "bool", "Noise Gate", 270, False),
    (
        "Advanced",
        "options",
        "Audio Filters",
        272,
        0,
        [
            "All",
            "High + Low Pass",
            "High Pass + De-emphasis",
            "High Pass Only",
            "Low Pass + De-emphasis",
            "Low Pass Only",
            "De-emphasis Only",
            "None",
            "FSK",
        ],
    ),
    ("Advanced", "number", "PIN", 402, 0, 9999, 0, 0, 2),
    ("Advanced", "options", "PIN Action", 404, 0, ["Unlock", "Power on"]),
    ("Advanced", "number", "Auto Keypad Lock (s)", 480, 0, 999, 0, 0, 2),
    ("Advanced", "number", "DAC Gain", 454, 0, 15, 0, 8, 2),
    ("Advanced", "number", "LW Band Start (kHz)", 504, 103, 211, 0, 103, 2),
    ("Advanced", "number", "Name Scroll", 508, 0, 20, 0, 0, 2),
    ("Advanced", "bool", "Swap Freq/Chan Names", 554, False),
    ("Advanced", "number", "T9 Advance (s)", 512, 0, 2, 1, 0, 2),
    ("Advanced", "number", "Battery Save (s)", 514, 0, 2, 2, 0, 2),
    ("Advanced", "bool", "Use Keypad LED", 516, True),
    ("Advanced", "bool", "Hunt for CTCSS/DCS", 518, False),
    ("Advanced", "bool", "Bluetooth Enabled", 526, False),
    ("Advanced", "number", "Menu Timeout (s)", 528, 0, 300, 0, 0, 2),
    ("Advanced", "bool", "Double Font in Focus", 530, False),
    ("APRS", "number", "APRS Deviation", 408, 0, 150, 0, 70, 2),
    ("APRS", "number", "Beacon Timer (secs)", 410, 0, 9999, 0, 0, 2),
    ("APRS", "number", "Beacon Distance (m)", 412, 0, 9999, 0, 0, 2),
    (
        "APRS",
        "options",
        "Beacon TX-ID",
        414,
        0,
        ["Off", "Start of TX", "End of TX", "Both"],
    ),
    ("APRS", "string", "Beacon Comment", 416, "Beacon", 24),
    ("APRS", "bool", "Beacon RX Override", 502, False),
    ("APRS", "string", "Callsign", 441, "NICFW", 6),
    (
        "APRS",
        "options",
        "SSID",
        450,
        7,
        [
            "Primary",
            "1-Vehicle",
            "2-Mobile",
            "3-Camper",
            "4-Home",
            "5-Portable",
            "6-Special",
            "7-Human",
            "8-BBS",
            "9-IGate",
            "10-Weather",
            "11.Satellite",
            "12-Digitpeater",
            "13-Experiment",
            "14-Truck",
            "15-Emergency",
        ],
    ),
    (
        "APRS",
        "options",
        "APRS Enabled",
        470,
        4,
        ["Active VFO", "VFO-A", "VFO-B", "VFO-C", "Off", "Channel 999"],
    ),
    ("APRS", "bool", "Hear Tones", 448, False),
    ("APRS", "options", "Decode Mode", 452, 0, ["Off", "On", "Pop-up"]),
    ("APRS", "number", "Pop-up Time (s)", 468, 0.0, 99.9, 1, 3, 2),
    ("APRS", "number", "Blip Symbol (ASCII)", 464, 33, 126, 0, 91, 2),
    (
        "APRS",
        "options",
        "APRS Status",
        460,
        7,
        [
            "0-Emergency",
            "1-Priority",
            "2-Special",
            "3-Committed",
            "4-Returning",
            "5-In Service",
            "6-En Route",
            "7-Off Duty",
        ],
    ),
    (
        "APRS",
        "options",
        "Digipeaters",
        462,
        0,
        ["None", "Preset WIDE1-1", "Preset WIDE2-2", "Custom"],
    ),
    ("APRS", "string", "Custom Digipeater", 482, "AR0ISS", 6),
    ("APRS", "number", "Custom Digipeater SSID", 474, 0, 15, 0, 0, 2),
    (
        "APRS",
        "options",
        "Ambiguity (Accuracy)",
        466,
        0,
        ["20m (Best Possible)", "200 m", "2 km"],
    ),
    (
        "APRS",
        "options",
        "APRS Audio Filters",
        472,
        5,
        [
            "All",
            "High + Low Pass",
            "High Pass + De-emphasis",
            "High Pass Only",
            "Low Pass + De-emphasis",
            "Low Pass Only",
            "De-emphasis Only",
            "None",
            "FSK",
        ],
    ),
    ("APRS", "number", "APRS Noise Filter", 476, 0, 3, 0, 2, 2),
    ("APRS", "number", "APRS Noise Rejection", 370, 0, 3, 0, 1, 2),
    (
        "APRS",
        "options",
        "Demodulator",
        568,
        0,
        ["Peak / Valley", "Goertzel", "Both"],
    ),
    ("APRS", "number", "KISS Mode Persist", 456, 0, 255, 0, 128, 2),
    ("APRS", "number", "KISS Mode Slot Time (cc)", 458, 0, 200, 0, 10, 2),
    ("APRS", "bool", "Ignore Own Packets", 520, False),
    ("APRS", "bool", "Hex Dump Packets", 602, False),
]


def _read_exact(pipe, count):
    data = bytearray()
    while len(data) < count:
        part = pipe.read(count - len(data))
        if not part:
            raise errors.RadioNoResponse(
                "Serial timeout (%d of %d bytes)" % (len(data), count)
            )
        data.extend(part)
    return bytes(data)


def _exchange_ack(pipe, packet, command):
    pipe.write(packet)
    pipe.flush()
    reply = _read_exact(pipe, 2)
    if reply != bytes((0xAA, command)):
        raise errors.RadioError(
            "Unexpected ACK for 0x%02X: %r" % (command, reply)
        )


def _negotiate(pipe):
    pipe.baudrate = DEFAULT_BAUD
    pipe.timeout = 1.5
    packet = b"\xaa\x70" + struct.pack("<I", FAST_BAUD) + b"\x55"
    for attempt in range(2):
        pipe.reset_input_buffer()
        try:
            _exchange_ack(pipe, packet, 0x70)
            break
        except errors.RadioNoResponse:
            if attempt:
                raise
            # A preceding download leaves the radio at high speed until its
            # idle timeout. Allow a quiet interval before retrying at 38400.
            # Only the initial, read-only baud handshake may be retried.
            LOG.info("Waiting for nicFW950 serial idle reset before retry")
            time.sleep(3.0)
    pipe.baudrate = FAST_BAUD
    if _read_exact(pipe, 2) != b"\xaa\x70":
        raise errors.RadioError("No high-speed baud ACK")
    pipe.timeout = 2.0


def _read_block(pipe, address):
    pipe.write(b"\xaa\x30" + struct.pack("<I", address) + b"\x55")
    pipe.flush()
    response = _read_exact(pipe, 135)
    if response[:2] != b"\xaa\x30":
        raise errors.RadioError("Bad read header at 0x%X" % address)
    if struct.unpack_from("<I", response, 2)[0] != address:
        raise errors.RadioError("Read address mismatch at 0x%X" % address)
    if (sum(response[2:-1]) & 0xFF) != response[-1]:
        raise errors.RadioError("Read checksum mismatch at 0x%X" % address)
    return response[6:134]


def _write_block(pipe, address, data):
    if len(data) != BLOCK:
        raise errors.RadioError("Invalid write block size")
    payload = b"\x40" + struct.pack("<I", address) + data
    packet = b"\xaa" + payload + bytes((sum(payload[1:]) & 0xFF,)) + b"\x55"
    _exchange_ack(pipe, packet, 0x40)


def _finalize(pipe):
    old_timeout = pipe.timeout
    try:
        pipe.timeout = 15.0
        _exchange_ack(pipe, b"\xaa\x48\x55", 0x48)
        # Reboot without saving the radio's RAM-cached settings over flash.
        # This command is exactly two bytes and has no expected ACK.
        pipe.write(b"\xaa\x50")
        pipe.flush()
    finally:
        pipe.timeout = old_timeout


def _tone_decode(value):
    value = int(value)
    if value == 0:
        return ("", None, None)
    if value & 0x8000:
        # nicFW stores the DCS designation as a binary octal value.
        # For example D114 is stored as decimal 76 (0x004C).
        code = value & 0x3FFF
        return (
            "DTCS",
            int(format(code, "03o")),
            "R" if value & 0x4000 else "N",
        )
    return ("Tone", value / 10.0, None)


def _tone_encode(mode, value, polarity):
    if mode == "":
        return 0
    if mode == "Tone":
        return int(round(float(value) * 10))
    if mode == "DTCS":
        return 0x8000 | (0x4000 if polarity == "R" else 0) | int(str(value), 8)
    raise errors.RadioError("Unsupported tone mode %r" % mode)


def _choice(name, choices, value):
    return RadioSetting(
        name,
        name.replace("_", " ").title(),
        RadioSettingValueList(choices, current_index=value),
    )


@directory.register
class NicFW950Radio(
    chirp_common.CloneModeRadio, chirp_common.ExperimentalRadio
):
    VENDOR = "Radtel"
    MODEL = "RT-950 Pro"
    VARIANT = "nicFW950"
    BAUD_RATE = DEFAULT_BAUD
    NEEDS_COMPAT_SERIAL = False
    _memsize = IMAGE_SIZE

    @classmethod
    def get_prompts(cls):
        prompts = chirp_common.RadioPrompts()
        prompts.experimental = (
            "Experimental nicFW950 driver. Read/write tested on one unit "
            "running nicFW950 6.00.16c; other versions need validation. "
            "Use only with nicFW950 firmware, not stock firmware."
        )
        prompts.info = (
            "For RT-950 Pro and Bajeton BJ-9000 radios already "
            "running nicsure nicFW950 with the 999-channel layout. "
            "USB serial uses 38400 baud, 8N1, then negotiates 460800 baud. "
            "Groups are entered as up to four A-Z letters in Comment; "
            "group names are available in radio settings."
        )
        prompts.pre_download = (
            "Turn on the radio normally with nicFW950 installed and connect "
            "the USB programming cable. Close CHIRP, RMS and other serial "
            "programs. Download and keep the original image before editing. "
            "Do not enter firmware flashing mode."
        )
        prompts.pre_upload = (
            "Upload changed nicFW950 channel/settings blocks from this "
            "radio's downloaded image. Keep stable power throughout. "
            "The radio reboots after the flash commit is acknowledged. "
            "Hardware validation covers nicFW950 6.00.16c on one unit."
        )
        return prompts

    def get_features(self):
        f = chirp_common.RadioFeatures()
        f.has_settings = True
        f.has_bank = False
        f.has_bank_names = False
        f.has_name = True
        f.has_comment = True
        f.has_cross = True
        f.has_rx_dtcs = True
        f.has_dtcs_polarity = True
        f.has_tuning_step = False
        f.has_ctone = True
        f.has_offset = True
        f.can_odd_split = True
        f.has_mode = True
        f.has_nostep_tuning = True
        f.valid_modes = ["FM", "NFM", "AM"]
        f.valid_tmodes = ["", "Tone", "TSQL", "DTCS", "Cross"]
        f.valid_cross_modes = [
            "Tone->Tone",
            "Tone->DTCS",
            "DTCS->Tone",
            "DTCS->DTCS",
            "->Tone",
            "->DTCS",
            "Tone->",
            "DTCS->",
        ]
        f.valid_duplexes = ["", "+", "-", "split", "off"]
        f.valid_name_length = 30
        f.valid_characters = chirp_common.CHARSET_ASCII
        f.valid_skips = [""]
        f.memory_bounds = (1, CHANNELS)
        f.valid_bands = [(18000000, 1300000000)]
        f.valid_power_levels = [
            chirp_common.PowerLevel(name) for name in POWERS
        ]
        return f

    def process_mmap(self):
        packed = self._mmap.get_packed()
        if len(packed) != IMAGE_SIZE:
            raise errors.RadioError("Unexpected nicFW950 image size")
        self._memobj = bitwise.parse(FORMAT, self._mmap)
        # Upload and settings writes run in fresh bridge processes. Remember
        # the loaded image before edits, without resetting it on re-parsing.
        if not hasattr(self, "_original"):
            self._original = bytes(packed)

    def load_mmap(self, filename):
        super().load_mmap(filename)
        self._original = bytes(self._mmap.get_packed())

    def validate_memory(self, memory):
        messages = super().validate_memory(memory)
        if not memory.empty:
            try:
                self._validate_channel(memory)
            except (errors.RadioError, UnicodeError, ValueError) as exc:
                messages.append(chirp_common.ValidationError(str(exc)))
        return messages

    @staticmethod
    def _validate_channel(memory):
        tx = memory.freq
        if memory.duplex == "split":
            tx = memory.offset
        elif memory.duplex in ("+", "-"):
            tx += (1 if memory.duplex == "+" else -1) * memory.offset
        if min(memory.freq, tx) < 0 or memory.freq % 10 or tx % 10:
            raise errors.RadioError(
                "Frequency must be a nonnegative multiple of 10 Hz"
            )
        if len(memory.name.encode("ascii")) > 30:
            raise errors.RadioError("Channel name exceeds 30 characters")
        comment = (memory.comment or "").strip().upper()
        if len(comment) > 4 or any(c < "A" or c > "Z" for c in comment):
            raise errors.RadioError("Groups must be 0-4 letters from A to Z")
        for tone in chirp_common.split_tone_encode(memory):
            _tone_encode(*tone)
        return tx, comment

    def _check_protected_bytes(self, current):
        # Never upload edits to VFO/reserved records, calibration, power bands,
        # or unused gaps, even when they share a block with an editable field.
        ranges = (
            (FIRST_RECORD * RECORD, (FIRST_RECORD + CHANNELS) * RECORD),
            (SETTINGS_BASE - BASE, SETTINGS_BASE - BASE + SETTINGS_SIZE),
            (
                GROUP_NAMES_BASE - BASE + GROUP_NAME_SLOT_SIZE,
                GROUP_NAMES_BASE - BASE + 27 * GROUP_NAME_SLOT_SIZE,
            ),
        )
        previous = 0
        for start, end in ranges + ((IMAGE_SIZE, IMAGE_SIZE),):
            if current[previous:start] != self._original[previous:start]:
                raise errors.RadioError(
                    "Refusing to change protected nicFW950 image bytes"
                )
            previous = end

    def _status(self, message, current, maximum):
        status = chirp_common.Status()
        status.msg = message
        status.cur = current
        status.max = maximum
        self.status_fn(status)

    def sync_in(self):
        try:
            _negotiate(self.pipe)
            result = bytearray()
            for i in range(IMAGE_SIZE // BLOCK):
                result.extend(_read_block(self.pipe, BASE + i * BLOCK))
                self._status(
                    "Downloading nicFW channels, settings and group names",
                    i + 1,
                    IMAGE_SIZE // BLOCK,
                )
            self._mmap = memmap.MemoryMapBytes(bytes(result))
            self.process_mmap()
            self._original = bytes(result)
        except errors.RadioError:
            raise
        except Exception as exc:
            LOG.exception("Download failed")
            raise errors.RadioError("Download failed: %s" % exc)
        finally:
            # Radio resets to 38400 after its idle timeout.
            self.pipe.baudrate = DEFAULT_BAUD

    def sync_out(self):
        if not hasattr(self, "_original"):
            raise errors.RadioError("Download from the radio before uploading")
        try:
            current = self._mmap.get_packed()
            if isinstance(current, str):
                current = current.encode("latin-1")
            if len(current) != IMAGE_SIZE:
                raise errors.RadioError("Unexpected channel image size")
            self._check_protected_bytes(current)
            changes = [
                (i, current[i : i + BLOCK])
                for i in range(0, IMAGE_SIZE, BLOCK)
                if current[i : i + BLOCK] != self._original[i : i + BLOCK]
            ]
            if not changes:
                return
            _negotiate(self.pipe)
            total = len(changes) * 2 + 1
            # A saved image can be stale or belong to another radio. Check all
            # affected blocks before the first write, including adjacent bytes
            # which must be preserved by a 128-byte read/modify/write.
            for index, (offset, _data) in enumerate(changes):
                if (
                    _read_block(self.pipe, BASE + offset)
                    != self._original[offset : offset + BLOCK]
                ):
                    raise errors.RadioError(
                        "Radio memory changed since download at 0x%X; "
                        "download a fresh image before uploading"
                        % (BASE + offset)
                    )
                self._status(
                    "Checking changed blocks against the radio",
                    index + 1,
                    total,
                )
            for index, (offset, data) in enumerate(changes):
                _write_block(self.pipe, BASE + offset, data)
                self._status(
                    "Uploading changed flash blocks",
                    len(changes) + index + 1,
                    total,
                )
            self._status("Committing nicFW950 flash", total - 1, total)
            _finalize(self.pipe)
            self._original = bytes(current)
            self._status(
                "nicFW950 flash committed; reboot requested", total, total
            )
        except errors.RadioError:
            raise
        except Exception as exc:
            LOG.exception("Upload failed")
            raise errors.RadioError("Upload failed: %s" % exc)
        finally:
            self.pipe.baudrate = DEFAULT_BAUD

    def _settings_bytes(self):
        packed = self._mmap.get_packed()
        if isinstance(packed, str):
            packed = packed.encode("latin-1")
        return packed[CHANNEL_IMAGE_SIZE : CHANNEL_IMAGE_SIZE + SETTINGS_SIZE]

    def get_settings(self):
        data = self._settings_bytes()
        root = RadioSettingGroup("nicfw", "nicFW Settings")
        groups = {}
        for index, spec in enumerate(SETTING_DEFINITIONS):
            category, kind, label, offset, *args = spec
            if category not in groups:
                group = RadioSettingGroup(
                    "category_%d" % len(groups), category
                )
                root.append(group)
                groups[category] = group
            key = "setting_%d" % index
            if kind == "number":
                low, high, places, default, width = args
                signed = low < 0
                raw = int.from_bytes(
                    data[offset : offset + width], "little", signed=signed
                )
                scale = 10**places
                if not low <= raw / scale <= high:
                    LOG.warning(
                        "Invalid %s=%s; displaying default", label, raw
                    )
                    raw = int(round(default * scale))
                if places:
                    value = RadioSettingValueFloat(
                        float(low), float(high), raw / scale, precision=places
                    )
                else:
                    value = RadioSettingValueInteger(int(low), int(high), raw)
            elif kind == "options":
                default, choices = args
                raw = int.from_bytes(data[offset : offset + 2], "little")
                if not 0 <= raw < len(choices):
                    LOG.warning(
                        "Invalid option %s=%d; displaying default", label, raw
                    )
                    raw = default
                value = RadioSettingValueList(choices, current_index=raw)
            elif kind == "bool":
                value = RadioSettingValueBoolean(
                    bool(int.from_bytes(data[offset : offset + 2], "little"))
                )
            else:
                default, width = args
                raw = data[offset : offset + width].split(b"\x00", 1)[0]
                text = "".join(chr(c) if 32 <= c < 127 else "?" for c in raw)
                value = RadioSettingValueString(0, width, text, autopad=False)
            groups[category].append(RadioSetting(key, label, value))
        names = RadioSettingGroup("group_names", "Group Names")
        packed = self._mmap.get_packed()
        if isinstance(packed, str):
            packed = packed.encode("latin-1")
        start = GROUP_NAMES_BASE - BASE
        for group_index in range(1, 27):
            pos = start + group_index * GROUP_NAME_SLOT_SIZE
            slot = packed[pos : pos + GROUP_NAME_SLOT_SIZE]
            if slot[0] == 0xAA:
                name = "".join(
                    chr(c) if 32 <= c < 127 else "?" for c in slot[1:]
                ).rstrip(" ")
            else:
                name = "Group-%s" % chr(64 + group_index)
            names.append(
                RadioSetting(
                    "group_name_%d" % group_index,
                    "Group %s" % chr(64 + group_index),
                    RadioSettingValueString(
                        0, GROUP_NAME_MAX_LENGTH, name, autopad=False
                    ),
                )
            )
        root.append(names)
        return root

    def set_settings(self, settings):
        packed = self._mmap.get_packed()
        if isinstance(packed, str):
            packed = packed.encode("latin-1")
        image = bytearray(packed)
        data = bytearray(self._settings_bytes())

        def apply(group):
            for item in group:
                # RadioSetting is itself group-like/iterable in CHIRP; test for
                # an actual setting before recursively traversing groups.
                if isinstance(item, RadioSetting):
                    if not item.changed():
                        continue
                    key = item.get_name()
                elif isinstance(item, RadioSettingGroup):
                    apply(item)
                    continue
                else:
                    continue
                if key.startswith("group_name_"):
                    group_index = int(key.rsplit("_", 1)[1])
                    if not 1 <= group_index <= 26:
                        raise errors.RadioError("Invalid group name index")
                    try:
                        encoded_name = str(item.value).encode("ascii")
                    except UnicodeEncodeError:
                        raise errors.RadioError("Group names must be ASCII")
                    if len(encoded_name) > GROUP_NAME_MAX_LENGTH:
                        raise errors.RadioError(
                            "Group names cannot exceed 12 characters"
                        )
                    pos = (
                        GROUP_NAMES_BASE
                        - BASE
                        + group_index * GROUP_NAME_SLOT_SIZE
                    )
                    previous = bytes(image[pos : pos + GROUP_NAME_SLOT_SIZE])
                    if previous[0] == 0xAA:
                        displayed = (
                            previous[1:].decode("ascii", "replace").rstrip(" ")
                        )
                    else:
                        displayed = "Group-%s" % chr(64 + group_index)
                    # Preserve unnamed/default slots unless the user actually edits them.
                    if str(item.value) != displayed:
                        image[pos : pos + GROUP_NAME_SLOT_SIZE] = (
                            b"\xaa"
                            + encoded_name.ljust(GROUP_NAME_MAX_LENGTH, b" ")
                        )
                    continue
                if not key.startswith("setting_"):
                    continue
                index = int(key.split("_", 1)[1])
                category, kind, label, offset, *args = SETTING_DEFINITIONS[
                    index
                ]
                if kind == "number":
                    low, high, places, default, width = args
                    stored = int(round(float(item.value) * (10**places)))
                    encoded = stored.to_bytes(width, "little", signed=low < 0)
                elif kind == "options":
                    default, choices = args
                    encoded = choices.index(str(item.value)).to_bytes(
                        2, "little"
                    )
                elif kind == "bool":
                    encoded = int(bool(item.value)).to_bytes(2, "little")
                else:
                    default, width = args
                    encoded = str(item.value).encode("ascii")
                    if len(encoded) > width:
                        raise errors.RadioError(
                            "%s exceeds %d bytes" % (label, width)
                        )
                    encoded = encoded.ljust(width, b"\x00")
                data[offset : offset + len(encoded)] = encoded

        apply(settings)
        # Preserve channels, calibration, power bands, and all unrelated bytes.
        image[CHANNEL_IMAGE_SIZE : CHANNEL_IMAGE_SIZE + SETTINGS_SIZE] = data
        self._mmap = memmap.MemoryMapBytes(bytes(image))
        self.process_mmap()

    def get_raw_memory(self, number):
        return repr(self._memobj.channels[number - 1])

    def get_memory(self, number):
        if not 1 <= number <= CHANNELS:
            raise errors.InvalidMemoryLocation("Channel outside 1-999")
        raw = self._memobj.channels[number - 1]
        mem = chirp_common.Memory()
        mem.number = number
        if int(raw.magic) != MAGIC:
            mem.empty = True
            return mem
        mem.freq = int(raw.rxFrequency) * 10
        tx = int(raw.txFrequency) * 10
        if int(raw.txPower) == 0:
            mem.duplex = "off"
        elif tx == mem.freq:
            mem.duplex = ""
            mem.offset = 0
        elif abs(tx - mem.freq) <= 10000000:
            mem.duplex = "+" if tx > mem.freq else "-"
            mem.offset = abs(tx - mem.freq)
        else:
            mem.duplex = "split"
            mem.offset = tx
        name_bytes = str(raw.name).encode("latin-1")
        mem.name = "".join(
            chr(c) if 32 <= c < 127 else "?"
            for c in name_bytes.split(b"\x00", 1)[0]
        ).rstrip()
        modulation = int(raw.modulation)
        bandwidth = int(raw.bandwidth)
        mem.mode = (
            "AM" if modulation in (1, 2) else "NFM" if bandwidth == 1 else "FM"
        )
        mem.power = self.get_features().valid_power_levels[
            min(int(raw.txPower), 6)
        ]
        tx_tone = _tone_decode(raw.txSubtone)
        rx_tone = _tone_decode(raw.rxSubtone)
        chirp_common.split_tone_decode(mem, tx_tone, rx_tone)
        # Each byte contains 0 (unused) or 1..26 (groups A..Z).
        group_values = [(int(raw.groups) >> (8 * i)) & 0xFF for i in range(4)]
        mem.comment = "".join(
            chr(ord("A") + value - 1)
            for value in group_values
            if 1 <= value <= 26
        )
        extra = RadioSettingGroup("extra", "nicFW Settings")
        extra.append(_choice("modulation", MODULATIONS, min(modulation, 3)))
        extra.append(_choice("bandwidth", BANDWIDTHS, min(bandwidth, 2)))
        extra.append(
            RadioSetting(
                "clarifier",
                "Clarifier (10 Hz)",
                RadioSettingValueInteger(
                    -20000, 20000, max(-20000, min(20000, int(raw.clarifier)))
                ),
            )
        )
        for key, label in (
            ("busyLock", "Busy Lock"),
            ("reversed", "Reverse RX/TX"),
            ("permanent", "Permanent"),
        ):
            extra.append(
                RadioSetting(
                    key,
                    label,
                    RadioSettingValueBoolean(bool(int(getattr(raw, key)))),
                )
            )
        extra.append(_choice("ptt_timing", PTT_TIMING, int(raw.pttID) & 3))
        extra.append(_choice("ptt_type", PTT_TYPE, (int(raw.pttID) >> 7) & 1))
        extra.append(
            RadioSetting(
                "scrambler",
                "Scrambler (0-20)",
                RadioSettingValueInteger(0, 20, min(20, int(raw.scrambler))),
            )
        )
        extra.append(
            RadioSetting(
                "scanpersist_override",
                "Scan Persist (0.1s)",
                RadioSettingValueInteger(
                    0, 90, min(90, int(raw.scanpersist_override))
                ),
            )
        )
        extra.append(
            RadioSetting(
                "scanmonitor_override",
                "Scan Monitor (s)",
                RadioSettingValueInteger(
                    0, 99, min(99, int(raw.scanmonitor_override))
                ),
            )
        )
        mem.extra = extra
        return mem

    def set_memory(self, mem):
        if not 1 <= mem.number <= CHANNELS:
            raise errors.InvalidMemoryLocation("Channel outside 1-999")
        raw = self._memobj.channels[mem.number - 1]
        if mem.empty:
            # Invalidate only; leave other bytes unchanged.
            raw.magic = 0
            return
        self._validate_channel(mem)
        saved = raw.get_raw()
        try:
            self._set_channel(mem, raw)
        except Exception:
            raw.set_raw(saved)
            raise

    def _set_channel(self, mem, raw):
        was_valid = int(raw.magic) == MAGIC
        previous = self.get_memory(mem.number) if was_valid else None
        if not was_valid:
            # Initialize only newly-created channels; reserved bytes are preserved.
            raw.groups = 0
            raw.rxSubtone = 0
            raw.txSubtone = 0
            raw.clarifier = 0
            raw.modulation = 3
            raw.bandwidth = 2
            raw.busyLock = 0
            raw.txPower = 4
            raw.reversed = 0
            raw.pttID = 0
            raw.scrambler = 0
            raw.scanpersist_override = 0
            raw.scanmonitor_override = 0
            raw.permanent = 0
        tx, comment = self._validate_channel(mem)
        if previous is None or (mem.freq, mem.duplex, mem.offset) != (
            previous.freq,
            previous.duplex,
            previous.offset,
        ):
            raw.rxFrequency = int(mem.freq) // 10
            raw.txFrequency = int(tx) // 10
        if previous is None or mem.name != previous.name:
            raw.name = (
                mem.name.encode("ascii").ljust(30, b"\x00").decode("latin-1")
            )
        tx_tone, rx_tone = chirp_common.split_tone_encode(mem)
        raw.txSubtone = _tone_encode(*tx_tone)
        raw.rxSubtone = _tone_encode(*rx_tone)
        # Preserve nicFW automatic modes unless user explicitly changes extras.
        # Standard mode changes are reflected only if they differ from the old effective mode.
        old_modulation, old_bandwidth = int(raw.modulation), int(raw.bandwidth)
        old_mode = (
            "AM"
            if old_modulation in (1, 2)
            else "NFM"
            if old_bandwidth == 1
            else "FM"
        )
        if mem.mode != old_mode:
            if mem.mode == "AM":
                raw.modulation = 1
            elif mem.mode in ("FM", "NFM"):
                raw.modulation = 0
                raw.bandwidth = 1 if mem.mode == "NFM" else 0
        if mem.duplex == "off":
            raw.txPower = 0
        elif mem.power is not None and (
            previous is None or str(mem.power) != str(previous.power)
        ):
            for index, level in enumerate(
                self.get_features().valid_power_levels
            ):
                if str(mem.power) == str(level):
                    raw.txPower = index
                    break
        settings = {}
        if mem.extra:
            settings = {
                setting.get_name(): setting.value
                for setting in mem.extra
                if not was_valid or setting.changed()
            }
        for key in (
            "modulation",
            "bandwidth",
            "clarifier",
            "scrambler",
            "scanpersist_override",
            "scanmonitor_override",
        ):
            if key in settings:
                value = settings[key]
                if key in ("modulation", "bandwidth"):
                    value = (
                        MODULATIONS if key == "modulation" else BANDWIDTHS
                    ).index(str(value))
                setattr(raw, key, int(value))
        for key in ("busyLock", "reversed", "permanent"):
            if key in settings:
                setattr(raw, key, int(bool(settings[key])))
        # The Comment column is the canonical nicFW group list for CSV compatibility.
        if previous is None or comment != previous.comment:
            raw.groups = sum(
                (ord(letter) - ord("A") + 1) << (8 * i)
                for i, letter in enumerate(comment)
            )
        ptt = int(raw.pttID)
        if "ptt_timing" in settings:
            ptt = (ptt & ~3) | PTT_TIMING.index(str(settings["ptt_timing"]))
        if "ptt_type" in settings:
            ptt = (ptt & ~0x80) | (
                PTT_TYPE.index(str(settings["ptt_type"])) << 7
            )
        raw.pttID = ptt
        raw.magic = MAGIC


@directory.register
class BajetonNicFW950Radio(NicFW950Radio):
    VENDOR = "Bajeton"
    MODEL = "BJ-9000"
