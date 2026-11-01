# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Experimental Retevis MA1 A9305B driver.

The transport and memory map were recovered from the official
``MA1-A9305B Programming Software-V1.0`` package released by Retevis.
The A9305B uses the same FE/FD addressed-block command family as the TYT
TH-UV88, with an initial 9600-baud handshake and a switch to 57600 baud.

This driver exposes the channel fields proven by the CPS. Unknown channel
bits and the factory/runtime regions are preserved byte-for-byte.
"""

import logging
import struct
import time

from chirp import chirp_common, directory, errors, memmap
from chirp.settings import (
    RadioSetting,
    RadioSettingGroup,
    RadioSettingValueBoolean,
)


LOG = logging.getLogger(__name__)

INITIAL_BAUD = 9600
FAST_BAUD = 57600
MEM_SIZE = 0xD000
CHANNEL_COUNT = 1000
CHANNEL_RECORD_SIZE = 21
WRITE_BLOCK_SIZE = 0x20
READ_BLOCK_SIZE = 0xF0

MODEL_MARKER = b"MA1-A9305B"
MODEL_MARKER_OFFSET = 0x19C0

HANDSHAKE = b"\xfe\xfe\xee\xef\xe0\x26\x72\x00\x00\xfd"
HANDSHAKE_ACK = b"\xfe\xfe\xef\xee\xe1\x26\x72\x00\x00"
BAUD_COMMAND = b"\xfe\xfe\xee\xef\xe6\x26\x72\x00\x00"
PASSWORD_COMMAND = b"\xfe\xfe\xee\xef\xe7"
PASSWORD = b"\x46" * 8
ENTER_READ = b"\xfe\xfe\xee\xef\xe2\x26\x72\x00\x00\xfd"
ENTER_WRITE = b"\xfe\xfe\xee\xef\xe3\x26\x72\x00\x00\xfd"
EXIT_PROGRAM = b"\xfe\xfe\xee\xef\xe5\x26\x72\x00\x00\xfd"

READ_COMMAND = b"\xfe\xfe\xee\xef\xeb"
READ_RESPONSE = b"\xfe\xfe\xef\xee\xe4"
WRITE_COMMAND = b"\xfe\xfe\xee\xef\xe4"
ACK = b"\xfe\xfe\xef\xee\xe6\x00\xfd"

# These ranges match the official CPS. They intentionally omit the
# factory/calibration and runtime ranges between them.
READ_RANGES = (
    (0x0000, 0x1680),
    (0x19C0, 0x2B80),
    (0x3200, 0x3284),
    (0x4000, 0xBED0),
)

CHANNEL_SECTIONS = (
    {
        "first": 1,
        "count": 200,
        "records": 0x0000,
        "active": 0x1180,
        "skip": 0x11A0,
        "names": 0x2300,
    },
    {
        "first": 201,
        "count": 800,
        "records": 0x4000,
        "active": 0xB600,
        "skip": 0xB680,
        "names": 0x8200,
    },
)

POWER_LEVELS = [
    chirp_common.PowerLevel("High", watts=50.0),
    chirp_common.PowerLevel("Mid", watts=20.0),
    chirp_common.PowerLevel("Low", watts=5.0),
]

TONES = list(chirp_common.TONES)
if 62.5 not in TONES:
    TONES.insert(0, 62.5)
if 169.9 not in TONES:
    TONES.append(169.9)

STEPS = [5.0, 6.25, 8.33, 10.0, 12.5, 15.0, 20.0, 25.0, 30.0, 50.0]
VALID_CHARS = chirp_common.CHARSET_ALPHANUMERIC + "-._/\\+"


def _read_exact(pipe, count, context, timeout=2.0):
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
            "Radio returned %i of %i bytes while %s"
            % (len(data), count, context)
        )
    return bytes(data)


def _reset_input(pipe):
    reset = getattr(pipe, "reset_input_buffer", None)
    if reset is not None:
        reset()


def _checksum(data):
    total = sum(data) & 0xFF
    return 0 if total == 0 else 256 - total


def _read_frame(address, length):
    return (
        READ_COMMAND
        + struct.pack(">IH", address, length)
        + b"\xFD"
    )


def _write_frame(address, data):
    payload = struct.pack(">IH", address, len(data)) + data
    return WRITE_COMMAND + payload + bytes((_checksum(payload),)) + b"\xFD"


def _section_for_channel(number):
    for section in CHANNEL_SECTIONS:
        if section["first"] <= number < section["first"] + section["count"]:
            return section, number - section["first"]
    raise errors.InvalidMemoryLocation(
        "Channel number must be between 1 and %i" % CHANNEL_COUNT
    )


def _bit_is_set(image, offset, index):
    raw = image.get(offset + index // 8, 1)
    return bool(raw[0] & (1 << (index % 8)))


def _set_bit(image, offset, index, enabled):
    byte = offset + index // 8
    mask = 1 << (index % 8)
    value = image.get(byte, 1)[0]
    image.set(
        byte,
        bytes([(value | mask) if enabled else (value & ~mask)]),
    )


def _record_offset(number):
    section, index = _section_for_channel(number)
    return section["records"] + index * CHANNEL_RECORD_SIZE


def _record(image, number):
    offset = _record_offset(number)
    return offset, bytearray(image.get(offset, CHANNEL_RECORD_SIZE))


def _decode_name(raw):
    return raw.rstrip(b"\x00\xff ").decode("ascii", "replace")


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
        return int(round(float(value) * 10)), "N"
    if mode == "DTCS":
        return int(str(value), 8) & 0x0FFF, polarity
    raise errors.InvalidDataError("Unsupported tone mode %r" % mode)


def _decode_frequency(raw):
    return struct.unpack("<I", raw)[0] * 10


def _encode_frequency(frequency):
    return struct.pack("<I", int(frequency) // 10)


def _tone_fields(raw):
    rx_word = struct.unpack("<H", raw[8:10])[0]
    tx_word = struct.unpack("<H", raw[10:12])[0]
    tx_polarity = "R" if tx_word & (1 << 12) else "N"
    rx_polarity = "R" if tx_word & (1 << 13) else "N"
    return (
        _decode_tone(rx_word, rx_polarity),
        _decode_tone(tx_word, tx_polarity),
    )


def _write_tone_fields(raw, tx_tone, rx_tone):
    rx_value, rx_polarity = _encode_tone(rx_tone)
    tx_value, tx_polarity = _encode_tone(tx_tone)

    rx_word = struct.unpack("<H", raw[8:10])[0]
    rx_word = (rx_word & 0xF000) | (rx_value & 0x0FFF)
    raw[8:10] = struct.pack("<H", rx_word)

    tx_word = struct.unpack("<H", raw[10:12])[0]
    tx_word &= ~0x3FFF
    tx_word |= tx_value & 0x0FFF
    if tx_polarity[0] == "R":
        tx_word |= 1 << 12
    if rx_polarity[0] == "R":
        tx_word |= 1 << 13
    raw[10:12] = struct.pack("<H", tx_word)


def _extra_enabled(memory, name):
    try:
        return bool(memory.extra[name].value)
    except (AttributeError, KeyError, TypeError):
        return False


def _handshake(radio):
    pipe = radio.pipe
    pipe.baudrate = INITIAL_BAUD
    pipe.timeout = 0.2
    _reset_input(pipe)
    pipe.write(HANDSHAKE)
    response = _read_exact(pipe, 36, "starting the A9305B session")
    if (
        not response.startswith(HANDSHAKE_ACK)
        or not response.endswith(b"\xFD")
    ):
        raise errors.RadioError(
            "Unexpected A9305B handshake response: %s" % response.hex()
        )

    # The CPS stores this two-byte tag from the handshake response. "45"
    # selects the protected programming-code exchange; other replies enter
    # directly after the baud switch.
    radio._response_code = response[-7:-5]

    pipe.write(BAUD_COMMAND + b"\x04\xFD")  # 57600 baud
    time.sleep(0.2)
    pipe.baudrate = FAST_BAUD
    pipe.timeout = 2.0
    _reset_input(pipe)
    ack = _read_exact(pipe, 7, "switching to 57600 baud")
    if ack != ACK:
        raise errors.RadioError(
            "A9305B did not switch to 57600 baud; response was %s"
            % ack.hex()
        )

    if radio._response_code == b"45":
        pipe.write(PASSWORD_COMMAND + PASSWORD + b"\xFD")
        ack = _read_exact(pipe, 7, "sending the programming code")
        if ack != ACK:
            raise errors.RadioError(
                "A9305B rejected the programming code; response was %s"
                % ack.hex()
            )


def _enter_mode(radio, command, label):
    radio.pipe.write(command)
    ack = _read_exact(radio.pipe, 7, label)
    if ack != ACK:
        raise errors.RadioError(
            "A9305B did not %s; response was %s" % (label, ack.hex())
        )


def _exit_program_mode(radio):
    try:
        radio.pipe.write(EXIT_PROGRAM)
        _read_exact(radio.pipe, 7, "leaving program mode", timeout=1.0)
    except Exception as exc:
        LOG.debug("A9305B exit acknowledgement was not received: %s", exc)


def _read_block(radio, address, length):
    radio.pipe.write(_read_frame(address, length))
    response = _read_exact(
        radio.pipe,
        length + 13,
        "reading 0x%04X" % address,
    )
    if (
        not response.startswith(READ_RESPONSE)
        or response[5:9] != struct.pack(">I", address)
        or response[9:11] != struct.pack(">H", length)
        or not response.endswith(b"\xFD")
    ):
        raise errors.RadioError(
            "Malformed A9305B response for 0x%04X: %s"
            % (address, response.hex())
        )
    if sum(response[5:-1]) & 0xFF:
        raise errors.RadioError(
            "A9305B checksum mismatch for read block 0x%04X" % address
        )
    return response[11:-2]


def _download(radio):
    _handshake(radio)
    _enter_mode(radio, ENTER_READ, "enter read mode")

    image = bytearray(b"\xFF" * MEM_SIZE)
    total = sum(end - start for start, end in READ_RANGES)
    completed = 0
    status = chirp_common.Status()
    status.msg = "Cloning from radio"
    status.max = total

    try:
        for start, end in READ_RANGES:
            address = start
            while address < end:
                length = min(READ_BLOCK_SIZE, end - address)
                image[address:address + length] = _read_block(
                    radio, address, length
                )
                address += length
                completed += length
                if radio.status_fn:
                    status.cur = completed
                    radio.status_fn(status)
    finally:
        try:
            _exit_program_mode(radio)
        finally:
            radio.pipe.baudrate = INITIAL_BAUD
    return memmap.MemoryMapBytes(bytes(image))


def _write_block(radio, address, data):
    radio.pipe.write(_write_frame(address, data))
    ack = _read_exact(
        radio.pipe,
        7,
        "writing 0x%04X" % address,
    )
    if ack != ACK:
        raise errors.RadioError(
            "A9305B rejected block 0x%04X; response was %s"
            % (address, ack.hex())
        )


def _upload(radio):
    _handshake(radio)
    _enter_mode(radio, ENTER_WRITE, "enter write mode")

    image = radio._mmap.get_packed()
    total = sum(end - start for start, end in READ_RANGES)
    completed = 0
    status = chirp_common.Status()
    status.msg = "Cloning to radio"
    status.max = total

    try:
        for start, end in READ_RANGES:
            address = start
            while address < end:
                length = min(
                    WRITE_BLOCK_SIZE,
                    end - address,
                    WRITE_BLOCK_SIZE - (address % WRITE_BLOCK_SIZE),
                )
                _write_block(
                    radio,
                    address,
                    image[address:address + length],
                )
                address += length
                completed += length
                if radio.status_fn:
                    status.cur = completed
                    radio.status_fn(status)
    finally:
        try:
            _exit_program_mode(radio)
        finally:
            radio.pipe.baudrate = INITIAL_BAUD


@directory.register
class RetevisMA1A9305BRadio(
    chirp_common.CloneModeRadio,
    chirp_common.ExperimentalRadio,
):
    """Retevis MA1 model A9305B mobile transceiver."""

    VENDOR = "Retevis"
    MODEL = "MA1-A9305B"
    BAUD_RATE = INITIAL_BAUD
    WANTS_DTR = True
    WANTS_RTS = True
    HARDWARE_FLOW = False
    XON_XOFF = False
    POWER_LEVELS = POWER_LEVELS

    @classmethod
    def get_prompts(cls):
        prompts = chirp_common.RadioPrompts()
        prompts.experimental = (
            "Retevis MA1-A9305B support is experimental. The serial "
            "transport, block checksums, channel records, names, power, "
            "bandwidth, tones, and skip flags were recovered from the "
            "official Retevis MA1-A9305B CPS V1.0, but this implementation "
            "has not been validated on a physical radio. Read the radio and "
            "save an unedited backup before writing. The driver preserves "
            "factory/calibration regions and channel bits it does not expose."
        )
        prompts.info = (
            "Use the programming cable supplied with the MA1-A9305B. The CPS "
            "starts at 9600 baud, negotiates 57600 baud, and uses 8 data "
            "bits, no parity, one stop bit, DTR, and RTS. Close the Retevis "
            "CPS before starting a transfer."
        )
        prompts.pre_download = (
            "1. Turn on the A9305B and connect the programming cable.\n"
            "2. Close the Retevis CPS and any other program using the port.\n"
            "3. Read the radio and save the unedited image as a backup.\n\n"
            "Confirm that channel order, frequencies, tones, names, power, "
            "and skip settings match the radio before editing."
        )
        prompts.pre_upload = (
            "Keep the unedited backup image. Uploading changes the writable "
            "channel and settings ranges recovered from the official CPS; "
            "factory/calibration ranges are not written. Do not disconnect "
            "the cable or turn off the radio during the transfer. Read the "
            "radio back afterward and verify every edited channel."
        )
        return prompts

    def get_features(self):
        rf = chirp_common.RadioFeatures()
        rf.memory_bounds = (1, CHANNEL_COUNT)
        rf.valid_bands = [(136_000_000, 174_000_000),
                          (400_000_000, 480_000_000)]
        rf.valid_modes = ["FM", "NFM", "AM", "NAM"]
        rf.valid_duplexes = ["", "+", "-", "split", "off"]
        rf.can_odd_split = True
        rf.valid_tmodes = ["", "Tone", "TSQL", "DTCS", "Cross"]
        rf.valid_cross_modes = list(chirp_common.CROSS_MODES)
        rf.has_ctone = True
        rf.has_dtcs = True
        rf.has_rx_dtcs = True
        rf.has_dtcs_polarity = True
        rf.has_name = True
        rf.valid_name_length = 16
        rf.valid_characters = VALID_CHARS
        rf.has_tuning_step = True
        rf.valid_tuning_steps = list(STEPS)
        rf.valid_power_levels = list(POWER_LEVELS)
        rf.valid_tones = list(TONES)
        rf.valid_skips = ["", "S"]
        rf.has_bank = False
        rf.has_settings = False
        return rf

    def process_mmap(self):
        image = self._mmap.get_packed()
        if len(image) != MEM_SIZE:
            raise errors.InvalidDataError(
                "MA1-A9305B image is %i bytes; expected %i"
                % (len(image), MEM_SIZE)
            )
        if not image.startswith(MODEL_MARKER, MODEL_MARKER_OFFSET):
            raise errors.InvalidDataError(
                "MA1-A9305B model marker is missing at 0x%04X"
                % MODEL_MARKER_OFFSET
            )

    @classmethod
    def match_model(cls, filedata, filename):
        return (
            len(filedata) == MEM_SIZE
            and filedata.startswith(MODEL_MARKER, MODEL_MARKER_OFFSET)
        )

    def sync_in(self):
        try:
            self._mmap = _download(self)
        except errors.RadioError:
            raise
        except Exception as exc:
            raise errors.RadioError(
                "Failed to communicate with the MA1-A9305B: %s" % exc
            ) from exc
        self.process_mmap()

    def sync_out(self):
        try:
            _upload(self)
        except errors.RadioError:
            raise
        except Exception as exc:
            raise errors.RadioError(
                "Failed to communicate with the MA1-A9305B: %s" % exc
            ) from exc

    def _name_offset(self, number):
        section, index = _section_for_channel(number)
        return section["names"] + index * 10

    def get_raw_memory(self, number):
        _offset, raw = _record(self._mmap, number)
        return repr(bytes(raw))

    def get_memory(self, number):
        section, index = _section_for_channel(number)
        mem = chirp_common.Memory()
        mem.number = number
        if not _bit_is_set(self._mmap, section["active"], index):
            mem.empty = True
            return mem

        _offset, raw = _record(self._mmap, number)
        rx_freq = _decode_frequency(raw[0:4])
        tx_raw = bytes(raw[4:8])
        tx_freq = _decode_frequency(tx_raw)
        if not 1_000_000 <= rx_freq <= 2_000_000_000:
            mem.empty = True
            return mem

        mem.freq = rx_freq
        tx_inhibit = bool(raw[12] & 0x01)
        if tx_inhibit or tx_raw == b"\xFF\xFF\xFF\xFF":
            mem.duplex = "off"
            mem.offset = 0
        elif tx_freq == rx_freq:
            mem.duplex = ""
            mem.offset = 0
        elif abs(tx_freq - rx_freq) > 25_000_000:
            mem.duplex = "split"
            mem.offset = tx_freq
        else:
            mem.duplex = "+" if tx_freq > rx_freq else "-"
            mem.offset = abs(tx_freq - rx_freq)

        rx_tone, tx_tone = _tone_fields(raw)
        chirp_common.split_tone_decode(mem, tx_tone, rx_tone)

        am = bool(raw[13] & 0x01)
        narrow = ((raw[12] >> 6) & 0x03) >= 2
        if am:
            mem.mode = "NAM" if narrow else "AM"
        else:
            mem.mode = "NFM" if narrow else "FM"

        power_index = (raw[12] >> 4) & 0x03
        mem.power = POWER_LEVELS[
            power_index if power_index < len(POWER_LEVELS) else 0
        ]

        step_index = raw[14] & 0x0F
        if step_index < len(STEPS):
            mem.tuning_step = STEPS[step_index]

        name_offset = self._name_offset(number)
        extended_name = bytes(self._mmap.get(name_offset, 10))
        mem.name = _decode_name(bytes(raw[15:21]) + extended_name)

        mem.skip = (
            ""
            if _bit_is_set(self._mmap, section["skip"], index)
            else "S"
        )

        mem.extra = RadioSettingGroup("extra", "Extra")
        mem.extra.append(
            RadioSetting(
                "talk_around",
                "Talk-around",
                RadioSettingValueBoolean(bool(raw[13] & 0x02)),
            )
        )
        mem.extra.append(
            RadioSetting(
                "reverse",
                "Reverse",
                RadioSettingValueBoolean(bool(raw[12] & 0x02)),
            )
        )
        return mem

    def set_memory(self, memory):
        section, index = _section_for_channel(memory.number)
        if memory.empty:
            _set_bit(self._mmap, section["active"], index, False)
            _set_bit(self._mmap, section["skip"], index, False)
            return

        _offset, raw = _record(self._mmap, memory.number)
        if not _bit_is_set(self._mmap, section["active"], index):
            raw = bytearray(
                b"\xFF" * 8
                + bytes.fromhex("FF0FFF0F000006")
                + b" " * 6
            )
        raw[0:4] = _encode_frequency(memory.freq)

        if memory.duplex == "off":
            raw[4:8] = b"\xFF\xFF\xFF\xFF"
        elif memory.duplex == "split":
            raw[4:8] = _encode_frequency(memory.offset)
        elif memory.duplex == "+":
            raw[4:8] = _encode_frequency(memory.freq + memory.offset)
        elif memory.duplex == "-":
            raw[4:8] = _encode_frequency(memory.freq - memory.offset)
        else:
            raw[4:8] = raw[0:4]

        tx_tone, rx_tone = chirp_common.split_tone_encode(memory)
        _write_tone_fields(raw, tx_tone, rx_tone)

        raw[12] &= ~0x03
        if memory.duplex == "off":
            raw[12] |= 0x01
        if _extra_enabled(memory, "reverse"):
            raw[12] |= 0x02

        try:
            power_index = POWER_LEVELS.index(memory.power)
        except ValueError:
            power_index = 0
        raw[12] = (raw[12] & 0xCF) | ((power_index & 0x03) << 4)

        if memory.mode in ("NFM", "NAM"):
            raw[12] = (raw[12] & 0x3F) | 0x80
        else:
            raw[12] &= 0x3F

        raw[13] &= ~0x07
        if memory.mode in ("AM", "NAM"):
            raw[13] |= 0x01
        if _extra_enabled(memory, "talk_around"):
            raw[13] |= 0x02
        if memory.name:
            raw[13] |= 0x04

        step_index = 0
        if memory.tuning_step in STEPS:
            step_index = STEPS.index(memory.tuning_step)
        raw[14] = (raw[14] & 0xF0) | step_index

        encoded_name = _encode_name(memory.name)
        raw[15:21] = encoded_name[:6]
        self._mmap.set(self._name_offset(memory.number), encoded_name[6:])
        self._mmap.set(_record_offset(memory.number), bytes(raw))

        _set_bit(self._mmap, section["active"], index, True)
        _set_bit(
            self._mmap,
            section["skip"],
            index,
            memory.skip != "S",
        )
