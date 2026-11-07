# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""NewChirp-maintained Retevis RA89 driver.

The transport, flow-control setup, session state, block framing, and memory
layout in this module were recovered from Retevis RA89 Programming Software
V1.08. The upstream CHIRP RA89 profile was used only to compare field
semantics after the OEM artifacts had been decoded.
"""

import logging
import struct
import time

from chirp import chirp_common, directory, errors, memmap
from chirp.settings import (
    RadioSetting,
    RadioSettingGroup,
    RadioSettingValueBoolean,
    RadioSettingValueInteger,
    RadioSettingValueList,
    RadioSettingValueString,
    RadioSettings,
)


LOG = logging.getLogger(__name__)

BAUD_RATE = 57600
MEM_SIZE = 0x22A0
BLOCK_SIZE = 0x20
CHANNEL_COUNT = 200
CHANNEL_RECORD_SIZE = 21

ACTIVE_BASE = 0x1180
SKIP_BASE = 0x11A0
WORKMODE_BASE = 0x1140
SETTINGS_BASE = 0x1160
REGION_OFFSET = 0x191E
INTRO_BASE = 0x1940
NAME_BASE = 0x1960
NAME_EXTRA_SIZE = 10

WRITE_SKIP_START = 0x1680
WRITE_SKIP_END = 0x1940

HANDSHAKE = b"\xFE\xFE\xEE\xEF\xE0UV99\xFD"
HANDSHAKE_RESPONSE = b"\xFE\xFE\xEF\xEE\xE1UV99"
AUTH_COMMAND = b"\xFE\xFE\xEE\xEF\xE7"
AUTH_RESPONSE_CODE = b"3435"
OPEN_PASSWORD = b"FFFFFFFF"
SET_BAUD = b"\xFE\xFE\xEE\xEF\xE6UV99\x04\xFD"
ENTER_READ = b"\xFE\xFE\xEE\xEF\xE2UV99\xFD"
ENTER_WRITE = b"\xFE\xFE\xEE\xEF\xE3UV99\xFD"
EXIT_SESSION = b"\xFE\xFE\xEE\xEF\xE5UV99\xFD"

READ_COMMAND = b"\xFE\xFE\xEE\xEF\xEB"
READ_RESPONSE = b"\xFE\xFE\xEF\xEE\xE4"
WRITE_COMMAND = b"\xFE\xFE\xEE\xEF\xE4"
COMMAND_ACK = b"\xFE\xFE\xEF\xEE\xE6\x00\xFD"
COMMAND_TIMEOUT = 3.0

POWER_LEVELS = [
    chirp_common.PowerLevel("High", watts=5.0),
    chirp_common.PowerLevel("Mid", watts=2.5),
    chirp_common.PowerLevel("Low", watts=0.5),
]
MODES = ["WFM", "FM", "NFM"]
SCRAMBLE_LIST = ["OFF", "ON"]
B_LOCK_LIST = ["OFF", "Sub", "Carrier"]
OPTSIG_LIST = ["OFF", "DTMF", "2TONE", "5TONE"]
PTTID_LIST = ["Off", "BOT", "EOT", "Both"]
STEPS = [2.5, 5.0, 6.25, 10.0, 12.5, 25.0, 50.0, 100.0]
LIST_STEPS = [str(step) for step in STEPS]
TONES = list(chirp_common.TONES)
if 62.5 not in TONES:
    TONES.insert(0, 62.5)
if 169.9 not in TONES:
    TONES.append(169.9)
VALID_CHARS = (
    chirp_common.CHARSET_ALPHANUMERIC
    + "`!\"#$%&'()*+,-./:;<=>?@[]^_"
)

SIDE_KEY_OPTIONS = [
    "None",
    "VOX",
    "Dual Wait",
    "Scan",
    "Moni",
    "1750 Tone",
    "Flashlight",
    "Power Level",
    "Alarm",
    "Noise Cancellation",
    "Temp Monitor",
    "FM Radio",
    "Talk Around",
    "Frequency Reverse",
]


def _checksum(data):
    total = sum(data) & 0xFF
    return 0 if total == 0 else 256 - total


def make_read_frame(address, length):
    return (
        READ_COMMAND
        + struct.pack(">I", address)
        + struct.pack(">H", length)
        + b"\xFD"
    )


def make_write_frame(address, data):
    check = _checksum(
        struct.pack(">I", address)
        + struct.pack(">H", len(data))
        + data
    )
    return (
        WRITE_COMMAND
        + struct.pack(">I", address)
        + struct.pack(">H", len(data))
        + data
        + bytes((check,))
        + b"\xFD"
    )


def _reset_input(pipe):
    reset = getattr(pipe, "reset_input_buffer", None)
    if reset is not None:
        reset()


def _read_exact(pipe, count, context, timeout=COMMAND_TIMEOUT):
    data = bytearray()
    deadline = time.monotonic() + timeout
    while len(data) < count and time.monotonic() < deadline:
        chunk = pipe.read(count - len(data))
        if chunk:
            data.extend(chunk)
        else:
            time.sleep(0.01)
    if len(data) != count:
        raise errors.RadioNoResponse(
            "RA89 returned %i of %i bytes while %s"
            % (len(data), count, context)
        )
    return bytes(data)


def _expect_ack(pipe, context):
    response = _read_exact(pipe, len(COMMAND_ACK), context)
    if response != COMMAND_ACK:
        raise errors.RadioError(
            "RA89 did not acknowledge %s; response was %s"
            % (context, response.hex())
        )


def _send_ack_command(pipe, command, context):
    pipe.write(command)
    _expect_ack(pipe, context)


def _start_session(radio):
    pipe = radio.pipe
    old_timeout = getattr(pipe, "timeout", None)
    old_baud = getattr(pipe, "baudrate", None)
    pipe.baudrate = BAUD_RATE
    pipe.timeout = 0.25
    _reset_input(pipe)

    # The CPS waits 500 ms after opening the port. The RA89 firmware otherwise
    # misses the first frame on some USB-serial cables.
    time.sleep(0.5)
    pipe.write(HANDSHAKE)
    response = _read_exact(
        pipe,
        36,
        "starting the RA89 session",
    )
    if not response.startswith(HANDSHAKE_RESPONSE) or not response.endswith(
        b"\xFD"
    ):
        raise errors.RadioError(
            "Unexpected RA89 handshake response: %s" % response.hex()
        )

    # This four-character field is captured by the OEM receive path. When it
    # is 3435, the CPS performs the E7 programming-code exchange before the
    # baud-rate command. FFFFFFFF selects the no-code path in the OEM dialog.
    response_code = response[-14:-10]
    if response_code == AUTH_RESPONSE_CODE:
        _send_ack_command(
            pipe,
            AUTH_COMMAND + OPEN_PASSWORD + b"\xFD",
            "opening the programming code stage",
        )

    _send_ack_command(
        pipe,
        SET_BAUD,
        "selecting 57600 baud",
    )
    pipe.baudrate = BAUD_RATE
    radio._ra89_old_timeout = old_timeout
    radio._ra89_old_baud = old_baud


def _exit_session(radio):
    pipe = radio.pipe
    try:
        pipe.write(EXIT_SESSION)
        _expect_ack(pipe, "ending the session")
    except Exception as exc:
        LOG.debug("RA89 exit acknowledgement was not received: %s", exc)
    finally:
        old_timeout = getattr(radio, "_ra89_old_timeout", None)
        old_baud = getattr(radio, "_ra89_old_baud", None)
        if old_timeout is not None:
            pipe.timeout = old_timeout
        if old_baud is not None:
            pipe.baudrate = old_baud


def _read_block(radio, address, requested):
    pipe = radio.pipe
    pipe.write(make_read_frame(address, requested))
    response = _read_exact(
        pipe,
        requested + 13,
        "reading 0x%04X" % address,
    )
    if response[:5] != READ_RESPONSE:
        raise errors.RadioError(
            "Malformed RA89 response marker for 0x%04X: %s"
            % (address, response[:5].hex())
        )
    returned_address = int.from_bytes(response[5:9], "big")
    returned_length = int.from_bytes(response[9:11], "big")
    if returned_address != address:
        raise errors.RadioError(
            "RA89 returned address 0x%04X for a 0x%04X request"
            % (returned_address, address)
        )
    if returned_length <= 0 or returned_length > requested:
        raise errors.RadioError(
            "RA89 returned %i bytes for a %i-byte request at 0x%04X"
            % (returned_length, requested, address)
        )
    if response[-1:] != b"\xFD":
        raise errors.RadioError(
            "RA89 response for 0x%04X did not end with FD" % address
        )

    payload = response[11:11 + returned_length]
    returned_check = response[11 + returned_length]
    expected_check = _checksum(
        response[5:9] + bytes((returned_length,)) + payload
    )
    if returned_check != expected_check:
        # The OEM receive path converts the frame to hexadecimal text and
        # discards the returned checksum without validating it. Keep the same
        # read policy while recording the mismatch for diagnostics.
        LOG.debug(
            "RA89 read checksum at 0x%04X is %02X, expected %02X",
            address,
            returned_check,
            expected_check,
        )
    return payload


def _download(radio):
    _start_session(radio)
    try:
        _send_ack_command(
            radio.pipe,
            ENTER_READ,
            "entering read mode",
        )
        image = bytearray(b"\xFF" * MEM_SIZE)
        status = chirp_common.Status()
        status.msg = "Reading RA89 memory"
        status.max = MEM_SIZE // BLOCK_SIZE
        address = 0
        while address < MEM_SIZE:
            payload = _read_block(
                radio,
                address,
                min(BLOCK_SIZE, MEM_SIZE - address),
            )
            image[address:address + len(payload)] = payload
            address += len(payload)
            if radio.status_fn:
                status.cur = len(range(0, address, BLOCK_SIZE))
                radio.status_fn(status)
    finally:
        _exit_session(radio)
    return memmap.MemoryMapBytes(bytes(image))


def _write_block(radio, address, data):
    radio.pipe.write(make_write_frame(address, data))
    _expect_ack(radio.pipe, "writing 0x%04X" % address)


def _upload(radio):
    _start_session(radio)
    try:
        _send_ack_command(
            radio.pipe,
            ENTER_WRITE,
            "entering write mode",
        )
        image = radio._packed()
        status = chirp_common.Status()
        status.msg = "Writing RA89 memory"
        write_blocks = [
            address
            for address in range(0, MEM_SIZE, BLOCK_SIZE)
            if not WRITE_SKIP_START <= address < WRITE_SKIP_END
        ]
        status.max = len(write_blocks)
        for index, address in enumerate(write_blocks, 1):
            _write_block(
                radio,
                address,
                image[address:address + BLOCK_SIZE],
            )
            if radio.status_fn:
                status.cur = index
                radio.status_fn(status)
    finally:
        _exit_session(radio)


def _bit_is_set(image, offset, index):
    return bool(image[offset + index // 8] & (1 << (index % 8)))


def _set_bit(image, offset, index, enabled):
    byte = offset + index // 8
    mask = 1 << (index % 8)
    if enabled:
        image[byte] |= mask
    else:
        image[byte] &= ~mask


def _get_bits(value, shift, width):
    return (value >> shift) & ((1 << width) - 1)


def _set_bits(image, offset, shift, width, value):
    mask = ((1 << width) - 1) << shift
    image[offset] = (image[offset] & ~mask) | ((value << shift) & mask)


def _channel_offset(number):
    return (number - 1) * CHANNEL_RECORD_SIZE


def _name_offset(number):
    return NAME_BASE + (number - 1) * NAME_EXTRA_SIZE


def _decode_name(raw):
    return raw.rstrip(b"\x00\xFF ").decode("ascii", "replace")


def _encode_name(name):
    return name.encode("ascii", "replace")[:16].ljust(16, b" ")


def _decode_tone(value, polarity):
    value &= 0x0FFF
    if value > 2600:
        return ("", None, "N")
    if value > 511:
        return ("Tone", value / 10.0, "N")
    return ("DTCS", int(format(value, "o")), polarity)


def _encode_tone(spec):
    mode, value, polarity = spec
    if mode == "":
        return 0x0FFF, "N"
    if mode == "Tone":
        return int(float(value) * 10), "N"
    if mode == "DTCS":
        return int(str(value), 8) & 0x0FFF, polarity
    raise errors.InvalidDataError("Unsupported tone mode %r" % mode)


def _tone_fields(raw):
    rx_word = int.from_bytes(raw[8:10], "big")
    tx_word = int.from_bytes(raw[10:12], "big")
    rx_polarity = "R" if tx_word & (1 << 12) else "N"
    tx_polarity = "R" if tx_word & (1 << 13) else "N"
    return (
        _decode_tone(rx_word, rx_polarity),
        _decode_tone(tx_word, tx_polarity),
    )


def _write_tone_fields(raw, tx_tone, rx_tone):
    rx_value, rx_polarity = _encode_tone(rx_tone)
    tx_value, tx_polarity = _encode_tone(tx_tone)

    rx_word = int.from_bytes(raw[8:10], "big")
    rx_word = (rx_word & 0xF000) | (rx_value & 0x0FFF)
    raw[8:10] = rx_word.to_bytes(2, "big")

    tx_word = int.from_bytes(raw[10:12], "big")
    tx_word &= 0xCFFF
    tx_word |= tx_value & 0x0FFF
    if rx_polarity[0] == "R":
        tx_word |= 1 << 12
    if tx_polarity[0] == "R":
        tx_word |= 1 << 13
    raw[10:12] = tx_word.to_bytes(2, "big")


def _extra_enabled(memory, name):
    try:
        return bool(memory.extra[name].value)
    except (AttributeError, KeyError, TypeError):
        return False


def _decode_region(image):
    code = (image[REGION_OFFSET] >> 4) & 0x0F
    labels = {
        0: "Unlocked",
        3: "EU",
        4: "US",
    }
    return labels.get(code, "Unknown %i" % code)


@directory.register
class NewChirpRA89Radio(
    chirp_common.CloneModeRadio,
    chirp_common.ExperimentalRadio,
):
    """Retevis RA89 dual-band handheld."""

    VENDOR = "Retevis"
    MODEL = "RA89"
    BAUD_RATE = BAUD_RATE
    WANTS_DTR = True
    WANTS_RTS = True
    HARDWARE_FLOW = False
    XON_XOFF = False
    MODES = MODES
    TONES = TONES
    DTCS_CODES = chirp_common.DTCS_CODES
    NAME_LENGTH = 16
    VALID_BANDS = [
        (136_000_000, 174_000_000),
        (400_000_000, 480_000_000),
    ]
    VALID_CHARS = VALID_CHARS
    POWER_LEVELS = POWER_LEVELS

    @classmethod
    def get_prompts(cls):
        prompts = chirp_common.RadioPrompts()
        prompts.experimental = (
            "Retevis RA89 support is experimental. The 57,600-baud serial "
            "transport, DTR/RTS setup, 32-byte addressed reads and writes, "
            "checksum, protected region, channel memory, names, tones, and "
            "core settings were recovered from the official Retevis RA89 "
            "Programming Software V1.08. Save an unedited backup before "
            "writing and verify an edited channel by reading it back."
        )
        prompts.info = (
            "Use the RA89 programming cable, turn the radio on, and close the "
            "official programming software before starting. NewChirp asserts "
            "DTR and RTS at 57,600 baud, 8 data bits, no parity, and one stop "
            "bit, matching the OEM CPS."
        )
        prompts.pre_download = (
            "1. Turn on the RA89 and connect the programming cable.\n"
            "2. Close the Retevis programming software and any other program "
            "using the serial port.\n"
            "3. Read the radio and save an unedited image as a backup.\n\n"
            "If the radio does not answer, disconnect and reconnect the cable "
            "and check that no other program owns the port."
        )
        prompts.pre_upload = (
            "Keep the unedited backup image. The driver writes every "
            "32-byte block except the protected factory region "
            "0x1680-0x193F. Do not disconnect the cable or power off the "
            "radio during the transfer. Read the radio back afterward and "
            "verify all edited channels and settings."
        )
        return prompts

    def get_features(self):
        rf = chirp_common.RadioFeatures()
        rf.has_settings = True
        rf.has_bank = False
        rf.has_comment = False
        rf.has_tuning_step = False
        rf.valid_tuning_steps = STEPS
        rf.can_odd_split = True
        rf.has_name = True
        rf.has_offset = True
        rf.has_mode = True
        rf.has_dtcs = True
        rf.has_rx_dtcs = True
        rf.has_dtcs_polarity = True
        rf.has_ctone = True
        rf.has_cross = True
        rf.has_sub_devices = False
        rf.valid_name_length = self.NAME_LENGTH
        rf.valid_modes = self.MODES
        rf.valid_characters = self.VALID_CHARS
        rf.valid_duplexes = ["", "-", "+", "split", "off"]
        rf.valid_tmodes = ["", "Tone", "TSQL", "DTCS", "Cross"]
        rf.valid_cross_modes = [
            "Tone->Tone",
            "DTCS->",
            "->DTCS",
            "Tone->DTCS",
            "DTCS->Tone",
            "->Tone",
            "DTCS->DTCS",
        ]
        rf.valid_skips = ["", "S"]
        rf.valid_power_levels = POWER_LEVELS
        rf.valid_tones = TONES
        rf.valid_dtcs_codes = self.DTCS_CODES
        rf.valid_bands = self.VALID_BANDS
        rf.memory_bounds = (1, CHANNEL_COUNT)
        return rf

    def sync_in(self):
        try:
            self._mmap = _download(self)
        except errors.RadioError:
            raise
        except Exception as exc:
            raise errors.RadioError(
                "Failed to communicate with the RA89: %s" % exc
            ) from exc
        self.process_mmap()

    def sync_out(self):
        try:
            _upload(self)
        except errors.RadioError:
            raise
        except Exception as exc:
            raise errors.RadioError(
                "Failed to communicate with the RA89: %s" % exc
            ) from exc

    def process_mmap(self):
        image = self._packed()
        if len(image) != MEM_SIZE:
            raise errors.InvalidDataError(
                "RA89 image is %i bytes; expected %i"
                % (len(image), MEM_SIZE)
            )
        if self.VENDOR.encode("ascii") not in image[INTRO_BASE:INTRO_BASE + 16]:
            LOG.debug("RA89 vendor marker is not present in the image")

    @classmethod
    def match_model(cls, filedata, filename):
        return (
            len(filedata) == MEM_SIZE
            and b"Retevis" in filedata[INTRO_BASE:INTRO_BASE + 16]
            and b"RA89" in filedata[INTRO_BASE + 16:INTRO_BASE + 32]
        )

    def _packed(self):
        return bytes(self._mmap.get_packed())

    def get_raw_memory(self, number):
        image = self._packed()
        offset = _channel_offset(number)
        return repr(
            image[offset:offset + CHANNEL_RECORD_SIZE]
            + image[
                _name_offset(number):
                _name_offset(number) + NAME_EXTRA_SIZE
            ]
        )

    def get_memory(self, number):
        if not 1 <= number <= CHANNEL_COUNT:
            raise errors.InvalidMemoryLocation(
                "Channel number must be between 1 and %i" % CHANNEL_COUNT
            )
        image = self._packed()
        index = number - 1
        mem = chirp_common.Memory()
        mem.number = number
        if not _bit_is_set(image, ACTIVE_BASE, index):
            mem.empty = True
            return mem

        offset = _channel_offset(number)
        raw = image[offset:offset + CHANNEL_RECORD_SIZE]
        rx_freq = int.from_bytes(raw[0:4], "little") * 10
        tx_freq = int.from_bytes(raw[4:8], "little") * 10
        if not 1_000_000 <= rx_freq <= 2_000_000_000:
            mem.empty = True
            return mem

        mem.freq = rx_freq
        if raw[4:8] == b"\xFF\xFF\xFF\xFF":
            mem.duplex = "off"
            mem.offset = 0
        elif abs(rx_freq - tx_freq) > 25_000_000:
            mem.duplex = "split"
            mem.offset = tx_freq
        elif rx_freq == tx_freq:
            mem.duplex = ""
            mem.offset = 0
        else:
            mem.duplex = "+" if tx_freq > rx_freq else "-"
            mem.offset = abs(tx_freq - rx_freq)

        rx_tone, tx_tone = _tone_fields(raw)
        chirp_common.split_tone_decode(mem, tx_tone, rx_tone)

        mode_index = _get_bits(raw[12], 2, 2)
        mem.mode = MODES[min(mode_index, len(MODES) - 1)]
        power_index = _get_bits(raw[12], 0, 2)
        mem.power = POWER_LEVELS[min(power_index, len(POWER_LEVELS) - 1)]
        mem.skip = (
            ""
            if _bit_is_set(image, SKIP_BASE, index)
            else "S"
        )

        extra_name = image[
            _name_offset(number):
            _name_offset(number) + NAME_EXTRA_SIZE
        ]
        mem.name = _decode_name(raw[15:21] + extra_name)
        mem.extra = RadioSettingGroup("extra", "Extra")
        mem.extra.append(
            RadioSetting(
                "b_lock",
                "B_Lock",
                RadioSettingValueList(
                    B_LOCK_LIST,
                    current_index=min(
                        _get_bits(raw[12], 4, 2),
                        len(B_LOCK_LIST) - 1,
                    ),
                ),
            )
        )
        mem.extra.append(
            RadioSetting(
                "step",
                "Step",
                RadioSettingValueList(
                    LIST_STEPS,
                    current_index=min(
                        _get_bits(raw[14], 5, 3),
                        len(LIST_STEPS) - 1,
                    ),
                ),
            )
        )
        mem.extra.append(
            RadioSetting(
                "scramble",
                "Scramble",
                RadioSettingValueBoolean(
                    bool(int.from_bytes(raw[8:10], "big") >> 12)
                ),
            )
        )
        mem.extra.append(
            RadioSetting(
                "signal",
                "Optional signaling",
                RadioSettingValueList(
                    OPTSIG_LIST,
                    current_index=min(
                        _get_bits(raw[13], 3, 2),
                        len(OPTSIG_LIST) - 1,
                    ),
                ),
            )
        )
        mem.extra.append(
            RadioSetting(
                "pttid",
                "PTT ID",
                RadioSettingValueList(
                    PTTID_LIST,
                    current_index=min(
                        _get_bits(raw[14], 2, 2),
                        len(PTTID_LIST) - 1,
                    ),
                ),
            )
        )
        return mem

    def set_memory(self, memory):
        if not 1 <= memory.number <= CHANNEL_COUNT:
            raise errors.InvalidMemoryLocation(
                "Channel number must be between 1 and %i" % CHANNEL_COUNT
            )
        image = bytearray(self._packed())
        index = memory.number - 1
        offset = _channel_offset(memory.number)

        if memory.empty:
            _set_bit(image, ACTIVE_BASE, index, False)
            self._mmap.set(0, bytes(image))
            return

        raw = bytearray(image[offset:offset + CHANNEL_RECORD_SIZE])
        if not _bit_is_set(image, ACTIVE_BASE, index):
            raw = bytearray(
                b"\xFF" * 8
                + bytes.fromhex("FF0FFF0F000006")
                + b" " * 6
            )

        raw[0:4] = int(memory.freq // 10).to_bytes(4, "little")
        if memory.duplex == "off":
            raw[4:8] = b"\xFF\xFF\xFF\xFF"
        elif memory.duplex == "split":
            raw[4:8] = int(memory.offset // 10).to_bytes(4, "little")
        elif memory.duplex == "+":
            raw[4:8] = int((memory.freq + memory.offset) // 10).to_bytes(
                4, "little"
            )
        elif memory.duplex == "-":
            raw[4:8] = int((memory.freq - memory.offset) // 10).to_bytes(
                4, "little"
            )
        else:
            raw[4:8] = raw[0:4]

        tx_tone, rx_tone = chirp_common.split_tone_encode(memory)
        _write_tone_fields(raw, tx_tone, rx_tone)

        power_index = 0
        if memory.power in POWER_LEVELS:
            power_index = POWER_LEVELS.index(memory.power)
        raw[12] = (raw[12] & ~0x03) | power_index
        raw[12] = (
            (raw[12] & ~0x0C)
            | (MODES.index(memory.mode) << 2)
        )
        if hasattr(memory.extra, "b_lock"):
            raw[12] = (
                (raw[12] & ~0x30)
                | (int(memory.extra["b_lock"].value) << 4)
            )

        if memory.name:
            raw[13] |= 0x20
        else:
            raw[13] &= ~0x20
        if hasattr(memory.extra, "signal"):
            raw[13] = (
                (raw[13] & ~0x18)
                | (int(memory.extra["signal"].value) << 3)
            )

        if hasattr(memory.extra, "pttid"):
            raw[14] = (
                (raw[14] & ~0x0C)
                | (int(memory.extra["pttid"].value) << 2)
            )
        if hasattr(memory.extra, "step"):
            raw[14] = (
                (raw[14] & ~0xE0)
                | (int(memory.extra["step"].value) << 5)
            )
        scramble = (
            _extra_enabled(memory, "scramble")
            if hasattr(memory.extra, "scramble")
            else bool(int.from_bytes(raw[8:10], "big") >> 12)
        )
        rx_word = int.from_bytes(raw[8:10], "big")
        rx_word = (rx_word & 0x0FFF) | ((1 if scramble else 0) << 12)
        raw[8:10] = rx_word.to_bytes(2, "big")

        encoded_name = _encode_name(memory.name)
        raw[15:21] = encoded_name[:6]
        image[offset:offset + CHANNEL_RECORD_SIZE] = raw
        image[
            _name_offset(memory.number):
            _name_offset(memory.number) + NAME_EXTRA_SIZE
        ] = encoded_name[6:]
        _set_bit(image, ACTIVE_BASE, index, True)
        _set_bit(image, SKIP_BASE, index, memory.skip != "S")
        self._mmap.set(0, bytes(image))

    def get_settings(self):
        image = self._packed()
        basic = RadioSettingGroup("basic", "Basic Settings")
        advanced = RadioSettingGroup("advanced", "Advanced Settings")
        workmode = RadioSettingGroup("workmode", "Work Mode Settings")
        group = RadioSettings(basic, advanced, workmode)

        def add_list(parent, name, label, offset, shift, width, options):
            current = min(
                _get_bits(image[offset], shift, width),
                len(options) - 1,
            )

            def apply(setting, offset=offset, shift=shift, width=width):
                self._update_image_bits(
                    offset,
                    shift,
                    width,
                    int(setting.value),
                )

            setting = RadioSetting(
                name,
                label,
                RadioSettingValueList(options, current_index=current),
            )
            setting.set_apply_callback(apply)
            parent.append(setting)

        def add_bool(parent, name, label, offset, shift):
            def apply(setting, offset=offset, shift=shift):
                self._update_image_bits(
                    offset,
                    shift,
                    1,
                    1 if setting.value else 0,
                )

            setting = RadioSetting(
                name,
                label,
                RadioSettingValueBoolean(
                    bool(_get_bits(image[offset], shift, 1))
                ),
            )
            setting.set_apply_callback(apply)
            parent.append(setting)

        def add_string(parent, name, label, offset, length):
            raw = image[offset:offset + length]
            text = raw.replace(b"\x00", b" ").decode("ascii", "replace").rstrip()

            def apply(setting, offset=offset, length=length):
                encoded = str(setting.value).encode(
                    "ascii", "replace"
                )[:length].ljust(length, b" ")
                self._update_image(offset, encoded)

            setting = RadioSetting(
                name,
                label,
                RadioSettingValueString(0, length, text),
            )
            setting.set_apply_callback(apply)
            parent.append(setting)

        add_list(
            basic,
            "txChSelect",
            "Priority Transmit",
            SETTINGS_BASE + 0x0D,
            7,
            1,
            ["Last Channel", "Main Channel"],
        )
        vox_level = RadioSettingValueInteger(
            1,
            7,
            min(
                max(
                    _get_bits(image[SETTINGS_BASE + 0x15], 5, 3) + 1,
                    1,
                ),
                7,
            ),
        )

        def apply_vox_level(setting):
            self._update_image_bits(
                SETTINGS_BASE + 0x15,
                5,
                3,
                int(setting.value) - 1,
            )

        vox_level_setting = RadioSetting(
            "voxLevel",
            "VOX Level",
            vox_level,
        )
        vox_level_setting.set_apply_callback(apply_vox_level)
        basic.append(vox_level_setting)
        add_list(
            basic,
            "sqlLevel",
            "Squelch Level",
            SETTINGS_BASE + 0x0C,
            4,
            4,
            ["OFF"] + [str(value) for value in range(1, 10)],
        )
        add_bool(
            basic,
            "dualWait",
            "Dual Wait/Standby",
            SETTINGS_BASE + 0x14,
            3,
        )
        add_list(
            basic,
            "ledMode",
            "LED Display Mode",
            SETTINGS_BASE + 0x10,
            4,
            4,
            ["Off", "On", "5s", "10s", "15s", "20s", "25s", "30s"],
        )
        add_list(
            basic,
            "light",
            "Background Light Color",
            SETTINGS_BASE + 0x14,
            5,
            3,
            [str(value) for value in range(1, 8)],
        )
        add_bool(basic, "beep", "Keypad Beep", SETTINGS_BASE + 0x0D, 0)
        add_list(
            basic,
            "tot",
            "Transmission Time-out Timer",
            SETTINGS_BASE + 0x0E,
            4,
            4,
            ["Off"] + [
                "%s seconds" % seconds
                for seconds in range(30, 300, 30)
            ],
        )
        add_bool(basic, "voxSw", "VOX Switch", SETTINGS_BASE + 0x15, 0)
        add_bool(basic, "roger", "Roger Beep", SETTINGS_BASE + 0x0F, 1)
        add_list(
            basic,
            "saveMode",
            "Battery Save Mode",
            SETTINGS_BASE + 0x16,
            4,
            2,
            ["Off", "1:1", "1:2", "1:4"],
        )
        add_list(
            basic,
            "scanType",
            "Scan Type",
            SETTINGS_BASE + 0x10,
            0,
            2,
            ["TO", "CO", "SE"],
        )
        add_bool(
            basic,
            "keylock",
            "Auto Key Lock",
            SETTINGS_BASE + 0x14,
            2,
        )
        add_bool(
            basic,
            "swAudio",
            "Voice Prompts",
            SETTINGS_BASE + 0x14,
            0,
        )
        add_list(
            basic,
            "introScreen",
            "Intro Screen",
            SETTINGS_BASE + 0x0D,
            3,
            2,
            ["Off", "Voltage", "Character String", "Startup Logo"],
        )
        add_list(
            basic,
            "keyMode",
            "Key Lock Mode",
            SETTINGS_BASE + 0x16,
            6,
            2,
            ["ALL", "PTT", "KEY", "Key & Side Key"],
        )
        add_list(
            basic,
            "disMode",
            "Display Mode",
            SETTINGS_BASE + 0x10,
            2,
            2,
            ["Frequency", "Channel #", "Name"],
        )
        add_bool(
            basic,
            "radioMoni",
            "Radio Monitor",
            SETTINGS_BASE + 0x14,
            1,
        )

        add_list(
            advanced,
            "endToneElim",
            "End Tone Elim",
            SETTINGS_BASE + 0x0F,
            4,
            2,
            ["Frequency", "120", "180", "240"],
        )
        add_string(
            advanced,
            "introLine1",
            "Intro Line 1",
            INTRO_BASE,
            16,
        )
        add_string(
            advanced,
            "introLine2",
            "Intro Line 2",
            INTRO_BASE + 16,
            16,
        )
        add_list(
            advanced,
            "voxDelay",
            "VOX Delay",
            SETTINGS_BASE + 0x15,
            1,
            4,
            [
                "0.5S",
                "1.0S",
                "1.5S",
                "2.0S",
                "2.5S",
                "3.0S",
                "3.5S",
                "4.0S",
                "4.5S",
                "5.0S",
            ],
        )
        region = RadioSettingValueList(
            [_decode_region(image)],
            current_index=0,
        )
        region.set_mutable(False)
        advanced.append(RadioSetting("region", "Region", region))
        for name, label, offset, shift in (
            ("sideKey1", "Side Key 1", SETTINGS_BASE, 0),
            ("sideKey1_long", "Side Key 1 Long", SETTINGS_BASE + 1, 0),
            ("sideKey2", "Side Key 2", SETTINGS_BASE, 4),
            ("sideKey2_long", "Side Key 2 Long", SETTINGS_BASE + 1, 4),
        ):
            add_list(
                advanced,
                name,
                label,
                offset,
                shift,
                4,
                SIDE_KEY_OPTIONS,
            )

        add_list(
            workmode,
            "vfomrmode",
            "VFO/MR Mode",
            WORKMODE_BASE,
            3,
            1,
            ["Frequency", "Channel"],
        )
        add_list(
            workmode,
            "vfomrmodeb",
            "VFO/MR Mode B",
            WORKMODE_BASE,
            2,
            1,
            ["Frequency", "Channel"],
        )
        add_list(
            workmode,
            "ab",
            "A/B Select",
            WORKMODE_BASE + 2,
            5,
            1,
            ["B", "A"],
        )

        mr_a = RadioSettingValueInteger(
            1,
            CHANNEL_COUNT,
            min(max(image[WORKMODE_BASE + 1] + 1, 1), CHANNEL_COUNT),
        )
        mr_b = RadioSettingValueInteger(
            1,
            CHANNEL_COUNT,
            min(
                max(_get_bits(image[WORKMODE_BASE + 2], 0, 5) + 1, 1),
                CHANNEL_COUNT,
            ),
        )

        def apply_mr_a(setting):
            self._update_image(
                WORKMODE_BASE + 1,
                bytes((int(setting.value) - 1,)),
            )

        def apply_mr_b(setting):
            self._update_image_bits(
                WORKMODE_BASE + 2,
                0,
                5,
                int(setting.value) - 1,
            )

        setting_a = RadioSetting("mrAch", "MR A Channel #", mr_a)
        setting_a.set_apply_callback(apply_mr_a)
        workmode.append(setting_a)
        setting_b = RadioSetting("mrBch", "MR B Channel #", mr_b)
        setting_b.set_apply_callback(apply_mr_b)
        workmode.append(setting_b)
        return group

    def _update_image(self, offset, data):
        self._mmap.set(offset, bytes(data))

    def _update_image_bits(self, offset, shift, width, value):
        image = bytearray(self._packed())
        _set_bits(image, offset, shift, width, value)
        self._mmap.set(0, bytes(image))

    def set_settings(self, settings):
        for element in settings:
            if isinstance(element, RadioSetting):
                if element.has_apply_callback():
                    element.run_apply_callback()
            else:
                self.set_settings(element)
