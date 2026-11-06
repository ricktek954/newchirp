# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Retry malformed UV-K5 firmware replies without enabling unsafe writes."""

import struct
import time

from chirp import bitwise, chirp_common, directory, errors, memmap
from chirp.drivers import uvk5
from chirp.settings import (
    RadioSetting,
    RadioSettingGroup,
    RadioSettingValueBoolean,
    RadioSettingValueList,
)


HELLO_PACKET = b"\x14\x05\x04\x00\x6a\x39\x57\x64"
HELLO_RETRIES = 5


def _getstring(data: bytes, begin, maxlen):
    """Return printable text, including responses with no trailing NUL."""
    end = min(begin + maxlen + 1, len(data))
    chars = list(data[begin:end])
    for index, value in enumerate(chars):
        if value < ord(" ") or value > ord("~"):
            return "".join(chr(char) for char in chars[:index])
    return "".join(chr(char) for char in chars)


def _sayhello_with_retry(serport):
    last_reply = b""

    for attempt in range(HELLO_RETRIES):
        uvk5._send_command(serport, HELLO_PACKET)
        try:
            reply = uvk5._receive_reply(serport)
        except errors.RadioNoResponse:
            reply = b""
        except errors.RadioError:
            reply = b""

        if reply.startswith(b"\x18\x05"):
            raise errors.RadioError(
                "Radio is in programming mode; restart it into normal mode"
            )
        firmware = _getstring(reply, 4, 24)
        if firmware:
            return firmware
        if reply:
            last_reply = reply
        if attempt < HELLO_RETRIES - 1:
            time.sleep(0.08)

    if last_reply:
        raise errors.RadioError(
            "Unable to determine firmware version after %i attempts "
            "(reply %s). Restart the radio normally, reconnect the cable, "
            "and verify that the exact UV-K5-family model is selected."
            % (HELLO_RETRIES, last_reply[:32].hex(" "))
        )
    raise errors.RadioError(
        "Unable to determine firmware version after %i attempts. "
        "Restart the radio normally and reconnect the programming cable."
        % HELLO_RETRIES
    )


_sayhello_with_retry.newchirp_original = uvk5._sayhello
_getstring.newchirp_uvk5_fixed = True
if not getattr(uvk5._getstring, "newchirp_uvk5_fixed", False):
    uvk5._getstring = _getstring
if not getattr(uvk5._sayhello, "newchirp_hello_retry", False):
    _sayhello_with_retry.newchirp_hello_retry = True
    uvk5._sayhello = _sayhello_with_retry


# F4HWN 5.x and later replaced the stock 8 KiB UV-K1 memory map with a
# 1,024-channel map on the PY32F071's external flash. The serial transport is
# still the UV-K5 framed protocol, but none of the stock image offsets apply.
F4HWN_MEM_FORMAT = """
#seekto 0x000000;
struct {
  ul32 freq;
  ul32 offset;
  u8 rxcode;
  u8 txcode;
  u8 txcodeflag:4,
     rxcodeflag:4;
  u8 modulation:4,
     offsetDir:4;
  u8 __unused0c_0:1,
     txLock:1,
     busyChLockout:1,
     txpower:3,
     bandwidth:1,
     freq_reverse:1;
  u8 __unused0d:4,
     dtmf_pttid:3,
     dtmf_decode:1;
  u8 step;
  u8 __unused0f;
} channel[1024];

#seekto 0x004000;
struct {
  char name[16];
} channelname[1024];

#seekto 0x008000;
struct {
  u8 __unused80_0:3,
     compander:2,
     band:3;
  u8 scanlist;
} ch_attr[1031];

#seekto 0x009000;
struct {
  ul32 freq;
  ul32 offset;
  u8 rxcode;
  u8 txcode;
  u8 txcodeflag:4,
     rxcodeflag:4;
  u8 modulation:4,
     offsetDir:4;
  u8 __unused9c_0:1,
     txLock:1,
     busyChLockout:1,
     txpower:3,
     bandwidth:1,
     freq_reverse:1;
  u8 __unused9d:4,
     dtmf_pttid:3,
     dtmf_decode:1;
  u8 step;
  u8 __unused9f;
} vfo_channel[14];
"""

F4HWN_MEM_SIZE = 0xB190
F4HWN_PROG_SIZE = 0xA178
F4HWN_MEM_BLOCK = 0x80
F4HWN_CHANNEL_COUNT = 1024
F4HWN_VFO_COUNT = 14
F4HWN_FIRMWARE_PREFIX = "F4HWN v6.3."

F4HWN_OFFSET_NONE = 0b00
F4HWN_OFFSET_PLUS = 0b01
F4HWN_OFFSET_MINUS = 0b10

F4HWN_POWER_USER = 0b000
F4HWN_POWER_LOW1 = 0b001
F4HWN_POWER_LOW2 = 0b010
F4HWN_POWER_LOW3 = 0b011
F4HWN_POWER_LOW4 = 0b100
F4HWN_POWER_LOW5 = 0b101
F4HWN_POWER_MEDIUM = 0b110
F4HWN_POWER_HIGH = 0b111

F4HWN_POWER_LEVELS = [
    chirp_common.PowerLevel("USER = <20mW to 5W", watts=0.000),
    chirp_common.PowerLevel("LOW 1 = <20mW", watts=0.020),
    chirp_common.PowerLevel("LOW 2 = 125mW", watts=0.125),
    chirp_common.PowerLevel("LOW 3 = 250mW", watts=0.250),
    chirp_common.PowerLevel("LOW 4 = 500mW", watts=0.500),
    chirp_common.PowerLevel("LOW 5 = 1W", watts=1.00),
    chirp_common.PowerLevel("MID = 2W", watts=2.00),
    chirp_common.PowerLevel("HIGH = 5W", watts=5.00),
]

F4HWN_POWER_VALUES = [
    F4HWN_POWER_USER,
    F4HWN_POWER_LOW1,
    F4HWN_POWER_LOW2,
    F4HWN_POWER_LOW3,
    F4HWN_POWER_LOW4,
    F4HWN_POWER_LOW5,
    F4HWN_POWER_MEDIUM,
    F4HWN_POWER_HIGH,
]

F4HWN_MODES = ["FM", "NFM", "AM", "NAM", "USB"]
F4HWN_STEPS = [
    2.5, 5.0, 6.25, 10.0, 12.5, 25.0, 8.33, 0.01, 0.05, 0.1, 0.25,
    0.5, 1.0, 1.25, 9.0, 15.0, 20.0, 30.0, 50.0, 100.0, 125.0,
    200.0, 250.0, 500.0,
]
F4HWN_BANDS = {
    0: (18.0, 108.0),
    1: (108.0, 137.0),
    2: (137.0, 174.0),
    3: (174.0, 350.0),
    4: (350.0, 400.0),
    5: (400.0, 470.0),
    6: (470.0, 1300.0),
}
F4HWN_OFF_ON = ["OFF", "ON"]
F4HWN_PTT_ID = [
    "OFF", "UP CODE", "DOWN CODE", "UP+DOWN CODE", "APOLLO QUINDAR"
]
F4HWN_COMPANDER = ["OFF", "TX", "RX", "TX/RX"]
F4HWN_SCANLISTS = (
    ["OFF"] + ["List [%i]" % index for index in range(1, 25)] + ["ALL"]
)


def _f4hwn_firmware_supported(firmware):
    return firmware.upper().startswith(F4HWN_FIRMWARE_PREFIX.upper())


def _f4hwn_sayhello(serport):
    """Return the F4HWN firmware string, retrying a transient bad reply."""
    last_reply = b""
    for attempt in range(HELLO_RETRIES):
        uvk5._send_command(serport, HELLO_PACKET)
        try:
            reply = uvk5._receive_reply(serport)
        except errors.RadioError:
            reply = b""

        if reply.startswith(b"\x18\x05"):
            raise errors.RadioError(
                "Radio is in programming mode; restart it into normal mode"
            )
        if reply.startswith(b"\x15\x05"):
            firmware = _getstring(reply, 4, 24)
            if firmware:
                return firmware
            last_reply = reply
        elif reply:
            last_reply = reply

        if attempt < HELLO_RETRIES - 1:
            time.sleep(0.08)

    detail = (
        " (reply %s)" % last_reply[:32].hex(" ")
        if last_reply
        else ""
    )
    raise errors.RadioError(
        "Unable to determine the F4HWN firmware version after %i attempts%s"
        % (HELLO_RETRIES, detail)
    )


def _f4hwn_require_firmware(firmware):
    if not _f4hwn_firmware_supported(firmware):
        raise errors.RadioError(
            "This profile requires F4HWN v6.3.x firmware; the radio reports "
            "%r. Select the stock UV-K1 model for firmware 7.03.x."
            % firmware
        )


def _f4hwn_read_memory(serport, offset, length):
    command = (
        b"\x1b\x05\x08\x00"
        + struct.pack("<HBB", offset, length, 0)
        + HELLO_PACKET[4:]
    )
    uvk5._send_command(serport, command)
    reply = uvk5._receive_reply(serport)
    if len(reply) < 8 + length:
        raise errors.RadioError(
            "F4HWN read reply too short at 0x%04x: got %i bytes, need %i"
            % (offset, len(reply), 8 + length)
        )
    if reply[:2] != b"\x1c\x05":
        command_id = struct.unpack("<H", reply[:2])[0]
        raise errors.RadioError(
            "Unexpected F4HWN read reply 0x%04x at 0x%04x"
            % (command_id, offset)
        )
    returned_offset = struct.unpack("<H", reply[4:6])[0]
    if returned_offset != offset:
        raise errors.RadioError(
            "F4HWN read address mismatch: requested 0x%04x, received 0x%04x"
            % (offset, returned_offset)
        )
    return reply[8:8 + length]


def _f4hwn_write_memory(serport, offset, data):
    payload_length = len(data)
    command = (
        b"\x1d\x05"
        + struct.pack(
            "<BBHBB",
            payload_length + 8,
            0,
            offset,
            payload_length,
            1,
        )
        + HELLO_PACKET[4:]
        + data
    )
    uvk5._send_command(serport, command)
    reply = uvk5._receive_reply(serport)
    if (
        len(reply) < 6
        or reply[0] != 0x1E
        or reply[1] != 0x05
        or reply[4] != (offset & 0xFF)
        or reply[5] != ((offset >> 8) & 0xFF)
    ):
        raise errors.RadioError(
            "F4HWN did not acknowledge the write at 0x%04x" % offset
        )


def _f4hwn_download(radio):
    serport = radio.pipe
    serport.timeout = 6.0
    status = chirp_common.Status()
    status.cur = 0
    status.max = F4HWN_MEM_SIZE
    status.msg = "Downloading from F4HWN radio"
    radio.status_fn(status)

    firmware = _f4hwn_sayhello(serport)
    _f4hwn_require_firmware(firmware)
    metadata = dict(radio.metadata)
    metadata["uvk5_firmware"] = firmware
    metadata["f4hwn_firmware"] = firmware
    radio.metadata = metadata
    radio.F4HWN_FIRMWARE = firmware

    image = bytearray()
    address = 0
    while address < F4HWN_MEM_SIZE:
        image.extend(
            _f4hwn_read_memory(serport, address, F4HWN_MEM_BLOCK)
        )
        address += F4HWN_MEM_BLOCK
        status.cur = min(address, F4HWN_MEM_SIZE)
        radio.status_fn(status)

    # The final 0x80-byte request extends beyond 0xB190. Only the documented
    # image length is retained.
    return memmap.MemoryMapBytes(bytes(image[:F4HWN_MEM_SIZE]))


def _f4hwn_upload(radio):
    serport = radio.pipe
    serport.timeout = 6.0
    status = chirp_common.Status()
    status.cur = 0
    status.max = F4HWN_PROG_SIZE
    status.msg = "Uploading to F4HWN radio"
    radio.status_fn(status)

    firmware = _f4hwn_sayhello(serport)
    _f4hwn_require_firmware(firmware)
    image = radio.get_mmap()
    if len(image) < F4HWN_PROG_SIZE:
        raise errors.RadioError(
            "The image is too short for the F4HWN program region"
        )

    address = 0
    while address < F4HWN_PROG_SIZE:
        length = min(F4HWN_MEM_BLOCK, F4HWN_PROG_SIZE - address)
        data = image[address:address + length]
        if len(data) != length:
            raise errors.RadioError(
                "Memory upload incomplete at 0x%05x" % address
            )
        _f4hwn_write_memory(serport, address, bytes(data))
        address += length
        status.cur = address
        radio.status_fn(status)

    uvk5._send_command(serport, b"\xdd\x05\x00\x00")
    status.msg = "Uploaded OK"
    radio.status_fn(status)
    return True


@directory.register
class QuanshengUVK1F4HWN63(uvk5.UVK5RadioBase):
    """Quansheng UV-K1 / UV-K5 V3 running F4HWN 6.3 firmware."""

    VENDOR = "Quansheng"
    MODEL = "UV-K1 (F4HWN 6.3)"
    BAUD_RATE = 38400

    @classmethod
    def detect_from_serial(cls, pipe):
        firmware = _f4hwn_sayhello(pipe)
        _f4hwn_require_firmware(firmware)
        return cls

    @classmethod
    def get_prompts(cls):
        prompts = uvk5.UVK5RadioBase.get_prompts()
        prompts.experimental = (
            "This profile targets the open-source F4HWN v6.3.x firmware on "
            "the UV-K1 and UV-K5 V3. It uses the firmware's separate "
            "1,024-channel memory map. Download and keep an original image "
            "before writing. Only the program/configuration region is "
            "uploaded; calibration data is preserved."
        )
        return prompts

    def get_features(self):
        features = chirp_common.RadioFeatures()
        features.has_bank = False
        features.has_settings = False
        features.has_comment = False
        features.has_ctone = True
        features.has_rx_dtcs = True
        features.valid_dtcs_codes = list(uvk5.DTCS_CODES)
        features.valid_name_length = 10
        features.valid_power_levels = list(F4HWN_POWER_LEVELS)
        features.valid_special_chans = self._vfo_names()
        features.valid_duplexes = ["", "-", "+"]
        features.valid_skips = [""]
        features.valid_tuning_steps = list(F4HWN_STEPS)
        features.valid_tmodes = ["", "Tone", "TSQL", "DTCS", "Cross"]
        features.valid_cross_modes = [
            "Tone->Tone",
            "Tone->DTCS",
            "DTCS->Tone",
            "->Tone",
            "->DTCS",
            "DTCS->",
            "DTCS->DTCS",
        ]
        features.valid_characters = chirp_common.CHARSET_ASCII
        features.valid_modes = list(F4HWN_MODES)
        features.memory_bounds = (1, F4HWN_CHANNEL_COUNT)
        features.valid_bands = [
            (int(low * 1_000_000), int(high * 1_000_000))
            for low, high in F4HWN_BANDS.values()
        ]
        return features

    def sync_in(self):
        self._mmap = _f4hwn_download(self)
        self.process_mmap()

    def sync_out(self):
        _f4hwn_upload(self)

    def process_mmap(self):
        self._memobj = bitwise.parse(F4HWN_MEM_FORMAT, self._mmap)

    def get_settings(self):
        return []

    def set_settings(self, settings):
        if list(settings.walk()):
            raise errors.InvalidValueError(
                "F4HWN settings editing is not enabled in this profile"
            )
        return self._mmap

    @staticmethod
    def _vfo_names():
        names = []
        for index, (low, high) in F4HWN_BANDS.items():
            label = "F%i(%iM-%iM)" % (index + 1, round(low), round(high))
            names.extend([label + "A", label + "B"])
        return names

    def _vfo_index(self, number):
        names = self._vfo_names()
        if isinstance(number, str):
            return names.index(number)
        zero_based = int(number) - 1
        if zero_based < F4HWN_CHANNEL_COUNT:
            return None
        return zero_based - F4HWN_CHANNEL_COUNT

    def _attribute_index(self, zero_based):
        if zero_based < F4HWN_CHANNEL_COUNT:
            return zero_based
        vfo_index = zero_based - F4HWN_CHANNEL_COUNT
        return F4HWN_CHANNEL_COUNT + (vfo_index // 2)

    def _channel_record(self, zero_based):
        if zero_based < F4HWN_CHANNEL_COUNT:
            return self._memobj.channel[zero_based]
        return self._memobj.vfo_channel[
            zero_based - F4HWN_CHANNEL_COUNT
        ]

    def _find_band(self, frequency):
        mhz = frequency / 1_000_000.0
        for band, (low, high) in F4HWN_BANDS.items():
            if low <= mhz < high:
                return band
        if mhz == F4HWN_BANDS[6][1]:
            return 6
        return False

    def validate_memory(self, memory):
        messages = super().validate_memory(memory)
        if memory.empty:
            return messages

        tx_frequency = memory.freq
        if memory.duplex == "-":
            tx_frequency -= memory.offset
        elif memory.duplex == "+":
            tx_frequency += memory.offset

        if self._find_band(memory.freq) is False:
            messages.append(
                chirp_common.ValidationError(
                    "Receive frequency %.4f MHz is not supported by this radio"
                    % (memory.freq / 1_000_000.0)
                )
            )
        if tx_frequency and self._find_band(tx_frequency) is False:
            messages.append(
                chirp_common.ValidationError(
                    "Transmit frequency %.4f MHz is not supported by this radio"
                    % (tx_frequency / 1_000_000.0)
                )
            )
        return messages

    def _get_tone(self, memory, record):
        rx_type = int(record.rxcodeflag)
        tx_type = int(record.txcodeflag)
        if rx_type >= len(uvk5.TMODES):
            rx_type = 0
            record.rxcodeflag = 0
        if tx_type >= len(uvk5.TMODES):
            tx_type = 0
            record.txcodeflag = 0

        rx_mode = uvk5.TMODES[rx_type]
        tx_mode = uvk5.TMODES[tx_type]
        rx_tone = tx_tone = None

        if tx_mode == "Tone" and record.txcode < len(uvk5.CTCSS_TONES):
            tx_tone = uvk5.CTCSS_TONES[record.txcode]
        elif tx_mode == "DTCS" and record.txcode < len(uvk5.DTCS_CODES):
            tx_tone = uvk5.DTCS_CODES[record.txcode]
        else:
            tx_mode = ""

        if rx_mode == "Tone" and record.rxcode < len(uvk5.CTCSS_TONES):
            rx_tone = uvk5.CTCSS_TONES[record.rxcode]
        elif rx_mode == "DTCS" and record.rxcode < len(uvk5.DTCS_CODES):
            rx_tone = uvk5.DTCS_CODES[record.rxcode]
        else:
            rx_mode = ""

        chirp_common.split_tone_decode(
            memory,
            (tx_mode, tx_tone, "R" if tx_type == 3 else "N"),
            (rx_mode, rx_tone, "R" if rx_type == 3 else "N"),
        )

    def _set_tone(self, memory, record):
        ((tx_mode, tx_tone, tx_polarity),
         (rx_mode, rx_tone, rx_polarity)) = \
            chirp_common.split_tone_encode(memory)

        if tx_mode == "Tone":
            record.txcode = uvk5.CTCSS_TONES.index(tx_tone)
            record.txcodeflag = 1
        elif tx_mode == "DTCS":
            record.txcode = uvk5.DTCS_CODES.index(tx_tone)
            record.txcodeflag = 3 if tx_polarity == "R" else 2
        else:
            record.txcode = 0
            record.txcodeflag = 0

        if rx_mode == "Tone":
            record.rxcode = uvk5.CTCSS_TONES.index(rx_tone)
            record.rxcodeflag = 1
        elif rx_mode == "DTCS":
            record.rxcode = uvk5.DTCS_CODES.index(rx_tone)
            record.rxcodeflag = 3 if rx_polarity == "R" else 2
        else:
            record.rxcode = 0
            record.rxcodeflag = 0

    def get_memory(self, number):
        zero_based = self._vfo_index(number)
        if zero_based is None:
            zero_based = int(number) - 1

        memory = chirp_common.Memory()
        memory.number = (
            zero_based + F4HWN_CHANNEL_COUNT + 1
            if isinstance(number, str)
            else int(number)
        )
        if isinstance(number, str):
            memory.extd_number = number

        record = self._channel_record(zero_based)
        attribute = self._memobj.ch_attr[
            self._attribute_index(zero_based)
        ]
        memory.empty = int(record.freq) in (0, 0xFFFFFFFF)
        memory.power = F4HWN_POWER_LEVELS[0]
        memory.extra = RadioSettingGroup("Extra", "extra")

        if zero_based >= F4HWN_CHANNEL_COUNT:
            memory.name = self._vfo_names()[
                zero_based - F4HWN_CHANNEL_COUNT
            ]
            memory.immutable = ["name", "scanlists"]
        else:
            for char in self._memobj.channelname[zero_based].name:
                value = int(char)
                if value in (0, 0xFF):
                    break
                memory.name += chr(value)
            memory.name = memory.name.rstrip()

        if not memory.empty:
            memory.freq = int(record.freq) * 10
            memory.offset = int(record.offset) * 10
            offset_direction = int(record.offsetDir)
            memory.duplex = {
                F4HWN_OFFSET_MINUS: "-",
                F4HWN_OFFSET_PLUS: "+",
            }.get(offset_direction, "")
            self._get_tone(memory, record)

            modulation = int(record.modulation)
            bandwidth = int(record.bandwidth)
            mode_index = modulation * 2 + bandwidth
            if mode_index == 5:
                memory.mode = "USB"
            elif mode_index < len(F4HWN_MODES):
                memory.mode = F4HWN_MODES[mode_index]
            else:
                memory.mode = "FM"

            step_index = int(record.step)
            memory.tuning_step = (
                F4HWN_STEPS[step_index]
                if step_index < len(F4HWN_STEPS)
                else 2.5
            )
            power_index = int(record.txpower)
            memory.power = (
                F4HWN_POWER_LEVELS[
                    F4HWN_POWER_VALUES.index(power_index)
                ]
                if power_index in F4HWN_POWER_VALUES
                else F4HWN_POWER_LEVELS[0]
            )

        tx_lock = (
            int(record.txLock)
            if int(record.txLock) < len(F4HWN_OFF_ON)
            else 0
        )
        ptt_id = (
            int(record.dtmf_pttid)
            if int(record.dtmf_pttid) < len(F4HWN_PTT_ID)
            else 0
        )
        compander = (
            int(attribute.compander)
            if int(attribute.compander) < len(F4HWN_COMPANDER)
            else 0
        )
        scanlist = int(attribute.scanlist)
        if scanlist >= len(F4HWN_SCANLISTS):
            scanlist = 0

        memory.extra.append(RadioSetting(
            "txLock",
            "TX Lock (TXLock)",
            RadioSettingValueList(F4HWN_OFF_ON, None, tx_lock),
        ))
        memory.extra.append(RadioSetting(
            "busyChLockout",
            "Busy Ch Lockout (BusyCL)",
            RadioSettingValueBoolean(
                bool(int(record.busyChLockout))
            ),
        ))
        memory.extra.append(RadioSetting(
            "frev",
            "Reverse Frequencies (R)",
            RadioSettingValueBoolean(
                bool(int(record.freq_reverse))
            ),
        ))
        memory.extra.append(RadioSetting(
            "pttid",
            "PTT ID",
            RadioSettingValueList(F4HWN_PTT_ID, None, ptt_id),
        ))
        memory.extra.append(RadioSetting(
            "compander",
            "Compander",
            RadioSettingValueList(
                F4HWN_COMPANDER, None, compander
            ),
        ))
        memory.extra.append(RadioSetting(
            "scanlists",
            "Scanlists",
            RadioSettingValueList(
                F4HWN_SCANLISTS, None, scanlist
            ),
        ))
        return memory

    def set_memory(self, memory):
        zero_based = self._vfo_index(memory.number)
        if zero_based is None:
            zero_based = int(memory.number) - 1
        record = self._channel_record(zero_based)
        attribute = self._memobj.ch_attr[
            self._attribute_index(zero_based)
        ]

        if memory.empty:
            record.set_raw(b"\xFF" * 16)
            if zero_based < F4HWN_CHANNEL_COUNT:
                self._memobj.channelname[zero_based].set_raw(
                    b"\x20" * 16
                )
                attribute.set_raw(b"\xFF\xFF")
            return memory

        mode_index = (
            5 if memory.mode == "USB"
            else F4HWN_MODES.index(memory.mode)
        )
        record.modulation = mode_index // 2
        record.bandwidth = mode_index % 2
        record.freq = memory.freq // 10
        record.offset = memory.offset // 10
        record.offsetDir = {
            "": F4HWN_OFFSET_NONE,
            "-": F4HWN_OFFSET_MINUS,
            "+": F4HWN_OFFSET_PLUS,
        }[memory.duplex]
        record.step = F4HWN_STEPS.index(memory.tuning_step)
        record.txpower = F4HWN_POWER_VALUES[
            F4HWN_POWER_LEVELS.index(memory.power)
        ]
        attribute.band = self._find_band(memory.freq)
        self._set_tone(memory, record)

        if zero_based < F4HWN_CHANNEL_COUNT:
            name = memory.name[:10].ljust(10) + "\x00" * 6
            self._memobj.channelname[zero_based].name = name

        def extra(name, default):
            if name not in memory.extra:
                return default
            value = memory.extra[name].value
            if isinstance(value, RadioSettingValueList):
                return int(value)
            return int(value.get_value())

        record.txLock = extra("txLock", int(record.txLock))
        record.busyChLockout = extra(
            "busyChLockout", int(record.busyChLockout)
        )
        record.freq_reverse = extra(
            "frev", int(record.freq_reverse)
        )
        record.dtmf_pttid = extra(
            "pttid", int(record.dtmf_pttid)
        )
        attribute.compander = extra(
            "compander", int(attribute.compander)
        )
        if zero_based < F4HWN_CHANNEL_COUNT:
            attribute.scanlist = extra(
                "scanlists", int(attribute.scanlist)
            )
        return memory


def _detect_uvk1_profile(cls, pipe):
    """Route a manually selected UV-K1 to the profile matching its firmware."""
    firmware = _f4hwn_sayhello(pipe)
    if _f4hwn_firmware_supported(firmware):
        return QuanshengUVK1F4HWN63
    return cls


uvk5.UVK1Radio.detect_from_serial = classmethod(_detect_uvk1_profile)
