# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.

"""Experimental read-only driver for the KSUN UV-K60 Plus."""

from __future__ import annotations

import struct
import time

from chirp import chirp_common, directory, errors, memmap


ACK = b"\x06"
ENTRY = b"P{OJI}E"
IDENTITY_REQUEST = b"\x02"
IDENTITY_PREFIX = b"P311"
READ = b"R"
END = b"E"
BLOCK_SIZE = 0x20
IMAGE_SIZE = 0x2A00
CHANNEL_COUNT = 128
CHANNEL_START = 0x10
CHANNEL_SIZE = 0x10
NAME_START = 0x2000
NAME_SIZE = 0x10
NAME_FIELD_OFFSET = 4
NAME_LENGTH = 12
READ_RANGES = ((0x0000, 0x1F40), (0x2000, IMAGE_SIZE))


def _read_exact(pipe, count, context, timeout=2.0):
    data = bytearray()
    old_timeout = getattr(pipe, "timeout", None)
    if old_timeout is not None:
        pipe.timeout = min(float(old_timeout or timeout), timeout)
    deadline = time.monotonic() + timeout
    try:
        while len(data) < count and time.monotonic() < deadline:
            chunk = pipe.read(count - len(data))
            if chunk:
                data.extend(chunk)
            else:
                time.sleep(0.01)
    finally:
        if old_timeout is not None:
            pipe.timeout = old_timeout
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


def _enter(pipe):
    pipe.baudrate = 38400
    pipe.bytesize = 8
    pipe.parity = "N"
    pipe.stopbits = 1

    for _attempt in range(5):
        _reset_input(pipe)
        pipe.write(ENTRY)
        try:
            if _read_exact(pipe, 1, "entering programming mode", 1.0) == ACK:
                break
        except errors.RadioNoResponse:
            continue
        time.sleep(0.05)
    else:
        raise errors.RadioNoResponse(
            "UV-K60 Plus did not acknowledge the programming entry"
        )

    pipe.write(IDENTITY_REQUEST)
    identity = _read_exact(pipe, 8, "reading the radio identity")
    if identity[:4] != IDENTITY_PREFIX or identity[-1] != 0xFF:
        raise errors.RadioError(
            "Connected radio is not a compatible KSUN UV-K60 Plus: %s"
            % identity.hex()
        )

    pipe.write(ACK)
    if _read_exact(pipe, 1, "acknowledging the radio identity", 1.0) != ACK:
        raise errors.RadioError("UV-K60 Plus did not confirm the identity")


def _leave(pipe):
    try:
        pipe.write(END)
    except Exception:
        return
    time.sleep(1.0)


def _decode_bcd_frequency(raw):
    if len(raw) != 4 or raw == b"\xff" * 4:
        return None
    digits = raw[::-1].hex()
    if not digits.isdigit():
        return None
    frequency = int(digits) * 10
    if not 0 < frequency <= 999_999_990:
        return None
    return frequency


def _decode_tone(raw):
    if raw in (b"\x00\x00", b"\xff\xff"):
        return "", None, None
    digits = raw[::-1].hex()
    if not digits.isdigit():
        return "", None, None
    tone = int(digits) / 10.0
    if tone in chirp_common.TONES:
        return "Tone", tone, None
    return "", None, None


@directory.register
class KSUNUVK60Plus(chirp_common.CloneModeRadio):
    """KSUN UV-K60 Plus from the MH-580 OEM programmer."""

    VENDOR = "KSUN"
    MODEL = "UV-K60-Plus"
    BAUD_RATE = 38400
    HARDWARE_FLOW = False
    WANTS_RTS = False
    WANTS_DTR = False
    ident_mode = b"P31183\xff\xff"
    _memsize = IMAGE_SIZE

    @classmethod
    def match_model(cls, filedata, filename):
        return False

    @classmethod
    def get_prompts(cls):
        prompts = chirp_common.RadioPrompts()
        prompts.experimental = (
            "Read-only KSUN UV-K60 Plus support derived from the MH-580 "
            "OEM programmer. Writes are disabled until the OEM channel "
            "fields and a physical write/read-back are validated."
        )
        prompts.pre_download = (
            "Connect the programming cable, power the radio on normally, "
            "and keep it connected while NewChirp reads the full 0x2A00 "
            "image."
        )
        return prompts

    def get_features(self):
        features = chirp_common.RadioFeatures()
        features.has_settings = False
        features.has_bank = False
        features.has_name = True
        features.has_cross = True
        features.has_ctone = True
        features.has_rx_dtcs = False
        features.has_tuning_step = True
        features.memory_bounds = (1, CHANNEL_COUNT)
        features.valid_bands = [(18_000_000, 600_000_000)]
        features.valid_cross_modes = [
            "Tone->Tone",
            "->Tone",
            "Tone->",
        ]
        features.valid_duplexes = ["", "+", "-", "off"]
        features.valid_modes = ["FM"]
        features.valid_name_length = NAME_LENGTH
        features.valid_tmodes = ["", "Tone", "TSQL", "Cross"]
        features.valid_tuning_steps = [5.0, 6.25, 12.5]
        return features

    def process_mmap(self):
        if len(self._mmap) < IMAGE_SIZE:
            raise errors.RadioError("UV-K60 Plus image is incomplete")

    def _read_page(self, address):
        last_error = None
        header = READ + struct.pack(">H", address) + bytes((BLOCK_SIZE,))
        for _attempt in range(3):
            _reset_input(self.pipe)
            self.pipe.write(header)
            try:
                response = _read_exact(
                    self.pipe,
                    BLOCK_SIZE + 5,
                    "reading block 0x%04X" % address,
                    2.0,
                )
            except errors.RadioError as exc:
                last_error = exc
                continue
            if (
                response[:4] != b"W" + header[1:]
                or sum(response[4:-1]) & 0xFF != response[-1]
            ):
                last_error = errors.RadioError(
                    "Invalid UV-K60 Plus response at 0x%04X" % address
                )
                continue
            return response[4:-1]
        raise errors.RadioNoResponse(
            "UV-K60 Plus did not return block 0x%04X" % address
        ) from last_error

    def sync_in(self):
        _enter(self.pipe)
        image = bytearray(b"\xff" * IMAGE_SIZE)
        addresses = [
            address
            for start, stop in READ_RANGES
            for address in range(start, stop, BLOCK_SIZE)
        ]
        status = chirp_common.Status()
        status.max = len(addresses)
        status.msg = "Reading KSUN UV-K60 Plus"
        try:
            for index, address in enumerate(addresses, 1):
                image[address:address + BLOCK_SIZE] = self._read_page(
                    address
                )
                status.cur = index
                self.status_fn(status)
        finally:
            _leave(self.pipe)
        self._mmap = memmap.MemoryMapBytes(bytes(image))
        self.process_mmap()

    def sync_out(self):
        raise errors.RadioError(
            "KSUN UV-K60 Plus channel writes are not validated"
        )

    def set_memory(self, memory):
        raise errors.RadioError(
            "KSUN UV-K60 Plus channel writes are not validated"
        )

    def get_raw_memory(self, number):
        start = CHANNEL_START + (number - 1) * CHANNEL_SIZE
        return self._mmap[start:start + CHANNEL_SIZE].hex()

    def get_memory(self, number):
        memory = chirp_common.Memory(number)
        start = CHANNEL_START + (number - 1) * CHANNEL_SIZE
        record = bytes(self._mmap[start:start + CHANNEL_SIZE])
        frequency = _decode_bcd_frequency(record[0:4])
        if frequency is None:
            memory.empty = True
            return memory

        memory.freq = frequency
        tx_frequency = _decode_bcd_frequency(record[4:8])
        if tx_frequency is None:
            memory.duplex = "off"
            memory.offset = 0
        else:
            offset = tx_frequency - frequency
            if offset > 0:
                memory.duplex = "+"
            elif offset < 0:
                memory.duplex = "-"
            else:
                memory.duplex = ""
            memory.offset = abs(offset)

        rx_tone = _decode_tone(record[8:10])
        tx_tone = _decode_tone(record[10:12])
        chirp_common.split_tone_decode(memory, tx_tone, rx_tone)
        memory.mode = "FM"
        memory.tuning_step = 6.25

        name_start = NAME_START + (number - 1) * NAME_SIZE
        raw_name = bytes(
            self._mmap[
                name_start + NAME_FIELD_OFFSET:name_start + NAME_SIZE
            ]
        )
        memory.name = raw_name.split(b"\x00", 1)[0].rstrip(
            b" \xff"
        ).decode("ascii", "replace")
        return memory
