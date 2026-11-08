# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Radioddity GS-5B 1.XX driver recovered from the 2025 OEM CPS."""

from __future__ import annotations

import struct
import time

from chirp import chirp_common, directory, errors, memmap
from chirp.settings import (
    RadioSetting,
    RadioSettingGroup,
    RadioSettingValueBoolean,
)


ACK = b"\x06"
HANDSHAKE = b"PROGRAMSHXPU"
READY = b"F"
IDENT_SIZE = 16
READ_COMMAND = 0x52
WRITE_COMMAND = 0x57
EXIT_COMMAND = 0x45

PAGE_SIZE = 64
CHANNEL_SIZE = 32
CHANNEL_COUNT = 512
CHANNEL_BASE = 0x0000
VFO_BASE = 0x8000
SETTINGS_BASE = 0x9000
AUX_BASE = 0xA000
FM_BASE = 0xB000
IMAGE_SIZE = FM_BASE + PAGE_SIZE

READ_TIMEOUT = 2.5
RETRIES = 5

FREQ_STEPS = [2.5, 5.0, 6.25, 10.0, 12.5, 20.0, 25.0, 50.0]
POWER_LEVELS = (
    chirp_common.PowerLevel("High"),
    chirp_common.PowerLevel("Medium"),
    chirp_common.PowerLevel("Low"),
)
DCS_CODES = tuple(sorted(chirp_common.DTCS_CODES + (645,)))

FLAG_SCAN = 0x04
FLAG_BUSY_LOCK = 0x08
FLAG_NARROW = 0x40


def _send(radio, payload):
    try:
        reset = getattr(radio.pipe, "reset_input_buffer", None)
        if reset is not None:
            reset()
        radio.pipe.write(bytes(payload))
        radio.pipe.flush()
    except Exception as exc:
        raise errors.RadioError(
            "Could not send the GS-5B programming command."
        ) from exc


def _read_exact(radio, size, timeout=READ_TIMEOUT):
    deadline = time.monotonic() + timeout
    response = bytearray()
    while len(response) < size:
        if time.monotonic() >= deadline:
            break
        chunk = radio.pipe.read(size - len(response))
        if chunk:
            response.extend(chunk)
        else:
            remaining = deadline - time.monotonic()
            if remaining > 0:
                time.sleep(min(0.020, remaining))
    return bytes(response)


def _handshake(radio):
    time.sleep(0.100)
    radio.pipe.baudrate = 115200
    radio.pipe.parity = "N"
    radio.pipe.stopbits = 1
    radio.pipe.bytesize = 8
    radio.pipe.timeout = min(float(radio.pipe.timeout or 0.25), READ_TIMEOUT)
    _send(radio, HANDSHAKE)
    if _read_exact(radio, 1) != ACK:
        raise errors.RadioError(
            "The GS-5B 1.XX did not acknowledge the CPS handshake."
        )
    _send(radio, READY)
    ident = _read_exact(radio, IDENT_SIZE)
    if len(ident) != IDENT_SIZE:
        raise errors.RadioError(
            "The GS-5B 1.XX returned a short identity reply."
        )
    return ident


def _exit_clone(radio):
    try:
        _send(radio, bytes((EXIT_COMMAND,)))
    except errors.RadioError:
        pass


def _read_page(radio, address):
    command = struct.pack(">BHB", READ_COMMAND, address, PAGE_SIZE)
    _send(radio, command)
    response = _read_exact(radio, PAGE_SIZE + 4)
    if len(response) != PAGE_SIZE + 4:
        raise errors.RadioError(
            "Short reply from the GS-5B 1.XX at 0x%04X: expected %i "
            "bytes, received %i."
            % (address, PAGE_SIZE + 4, len(response))
        )
    if response[:4] != command:
        raise errors.RadioError(
            "The GS-5B 1.XX returned a mismatched reply header at 0x%04X."
            % address
        )
    return response[4:]


def _write_page(radio, address, data):
    if len(data) != PAGE_SIZE:
        raise errors.RadioError(
            "GS-5B 1.XX page 0x%04X is incomplete." % address
        )
    command = struct.pack(">BHB", WRITE_COMMAND, address, PAGE_SIZE)
    _send(radio, command + bytes(data))
    response = _read_exact(radio, 1)
    if response != ACK:
        detail = response.hex() if response else "no response"
        raise errors.RadioError(
            "The GS-5B 1.XX did not acknowledge page 0x%04X (%s)."
            % (address, detail)
        )


def _retry(operation):
    last_error = None
    for _attempt in range(RETRIES):
        try:
            return operation()
        except errors.RadioError as exc:
            last_error = exc
            time.sleep(0.050)
    raise last_error


def _clone_addresses():
    addresses = list(range(CHANNEL_BASE, CHANNEL_BASE + 0x4000, PAGE_SIZE))
    addresses.extend(range(VFO_BASE, VFO_BASE + PAGE_SIZE, PAGE_SIZE))
    addresses.extend(
        range(SETTINGS_BASE, SETTINGS_BASE + PAGE_SIZE, PAGE_SIZE)
    )
    addresses.extend(range(AUX_BASE, FM_BASE + PAGE_SIZE, PAGE_SIZE))
    return addresses


def _decode_frequency(raw):
    value = 0
    for byte in reversed(raw):
        high = byte >> 4
        low = byte & 0x0F
        if high > 9 or low > 9:
            return None
        value = value * 100 + (high * 10 + low)
    if value == 0:
        return None
    return value * 10


def _encode_frequency(frequency):
    value = int(round(frequency / 10.0))
    if value <= 0 or value > 99_999_999:
        raise errors.RadioError(
            "The GS-5B 1.XX cannot represent %.6f MHz."
            % (frequency / 1_000_000.0)
        )
    digits = ("%08d" % value)[-8:]
    encoded = bytearray()
    for index in range(3, -1, -1):
        pair = int(digits[index * 2:index * 2 + 2])
        encoded.append((pair // 10 << 4) | (pair % 10))
    return bytes(encoded)


def _nearest_tone(frequency):
    return min(chirp_common.TONES, key=lambda item: abs(item - frequency))


def _decode_tone(raw):
    low, high = raw
    if high == 0:
        if low == 0:
            return None
        index = low - 1
        if index < 0 or index >= len(DCS_CODES) * 2:
            return None
        inverted = index >= len(DCS_CODES)
        code = DCS_CODES[index % len(DCS_CODES)]
        return ("DCS", code, inverted)
    value = low | (high << 8)
    return ("Tone", _nearest_tone(value / 10.0), False)


def _encode_tone(tone):
    if tone is None:
        return b"\x00\x00"
    kind, value, inverted = tone
    if kind == "Tone":
        return struct.pack("<H", int(round(value * 10)))
    try:
        index = DCS_CODES.index(int(value))
    except ValueError as exc:
        raise errors.RadioError(
            "The GS-5B 1.XX does not support DCS %03i." % int(value)
        ) from exc
    if inverted:
        index += len(DCS_CODES)
    return bytes((index + 1, 0))


def _tone_fields(mem):
    tx = rx = None
    if mem.tmode == "Tone":
        tx = ("Tone", mem.rtone, False)
    elif mem.tmode == "TSQL":
        tx = ("Tone", mem.rtone, False)
        rx = ("Tone", mem.ctone, False)
    elif mem.tmode == "DTCS":
        tx = ("DCS", mem.dtcs, mem.dtcs_polarity[1:] == "R")
        rx = ("DCS", mem.rx_dtcs, mem.dtcs_polarity[:1] == "R")
    elif mem.tmode == "Cross":
        tx_side, rx_side = mem.cross_mode.split("->", 1)
        if tx_side == "Tone":
            tx = ("Tone", mem.rtone, False)
        elif tx_side == "DTCS":
            tx = ("DCS", mem.dtcs, mem.dtcs_polarity[1:] == "R")
        if rx_side == "Tone":
            rx = ("Tone", mem.ctone, False)
        elif rx_side == "DTCS":
            rx = ("DCS", mem.rx_dtcs, mem.dtcs_polarity[:1] == "R")
    return tx, rx


def _decode_tones(mem, tx, rx):
    if tx is None and rx is None:
        mem.tmode = ""
    elif tx is not None and rx is None:
        if tx[0] == "Tone":
            mem.tmode = "Tone"
            mem.rtone = tx[1]
        else:
            mem.tmode = "Cross"
            mem.cross_mode = "DTCS->"
            mem.dtcs = tx[1]
            mem.dtcs_polarity = "NR" if tx[2] else "NN"
    elif tx is None and rx is not None:
        mem.tmode = "Cross"
        if rx[0] == "Tone":
            mem.cross_mode = "->Tone"
            mem.ctone = rx[1]
        else:
            mem.cross_mode = "->DTCS"
            mem.rx_dtcs = rx[1]
            mem.dtcs_polarity = "RN" if rx[2] else "NN"
    elif tx == rx:
        mem.tmode = "TSQL" if tx[0] == "Tone" else "DTCS"
        if tx[0] == "Tone":
            mem.rtone = tx[1]
            mem.ctone = rx[1]
        else:
            mem.dtcs = tx[1]
            mem.rx_dtcs = rx[1]
            mem.dtcs_polarity = (
                ("R" if rx[2] else "N") + ("R" if tx[2] else "N")
            )
    else:
        mem.tmode = "Cross"
        mem.cross_mode = "%s->%s" % (
            "DTCS" if tx[0] == "DCS" else tx[0],
            "DTCS" if rx[0] == "DCS" else rx[0],
        )
        if tx[0] == "Tone":
            mem.rtone = tx[1]
        else:
            mem.dtcs = tx[1]
        if rx[0] == "Tone":
            mem.ctone = rx[1]
        else:
            mem.rx_dtcs = rx[1]
        mem.dtcs_polarity = (
            ("R" if rx[0] == "DCS" and rx[2] else "N")
            + ("R" if tx[0] == "DCS" and tx[2] else "N")
        )


def _decode_name(raw):
    raw = raw.split(b"\xff", 1)[0].rstrip(b"\x00")
    if not raw:
        return ""
    try:
        return raw.decode("gb2312")
    except UnicodeDecodeError:
        return raw.decode("latin-1", "replace")


def _encode_name(name):
    encoded = bytearray()
    for char in str(name):
        try:
            chunk = char.encode("gb2312")
        except UnicodeEncodeError:
            chunk = b"?"
        if len(encoded) + len(chunk) > 12:
            break
        encoded.extend(chunk)
    return bytes(encoded).ljust(12, b"\xff")


def _validate_frequency(frequency):
    if not (
        136_000_000 <= frequency <= 174_000_000
        or 400_000_000 <= frequency <= 520_000_000
    ):
        raise errors.RadioError(
            "The GS-5B 1.XX supports 136-174 and 400-520 MHz."
        )


@directory.register
class RadioddityGS5B1XX(chirp_common.CloneModeRadio,
                        chirp_common.ExperimentalRadio):
    """Radioddity GS-5B hardware reporting CPS version 1.XX."""

    VENDOR = "Radioddity"
    MODEL = "GS-5B (1.XX)"
    BAUD_RATE = 115200
    WANTS_DTR = True
    WANTS_RTS = True
    XON_XOFF = False
    _memsize = IMAGE_SIZE
    _ranges = [
        (CHANNEL_BASE, CHANNEL_BASE + CHANNEL_COUNT * CHANNEL_SIZE, PAGE_SIZE),
        (VFO_BASE, VFO_BASE + PAGE_SIZE, PAGE_SIZE),
        (SETTINGS_BASE, SETTINGS_BASE + PAGE_SIZE, PAGE_SIZE),
        (AUX_BASE, FM_BASE + PAGE_SIZE, PAGE_SIZE),
    ]

    @classmethod
    def get_prompts(cls):
        prompts = chirp_common.RadioPrompts()
        prompts.experimental = (
            "NewChirp GS-5B 1.XX support is experimental. Its transport and "
            "512-channel map were recovered from Radioddity's official 2025 "
            "GS-5B Pro CPS v1.1.3. Keep an OEM CPS backup before writing."
        )
        prompts.info = (
            "Select this entry only for GS-5B radios using the 1.XX CPS. "
            "Power the radio on normally and close Radioddity CPS."
        )
        prompts.pre_download = (
            "Connect the programming cable and read the radio. Save the "
            "unedited image before making changes."
        )
        prompts.pre_upload = (
            "Keep the unedited OEM CPS backup. Write only a saved GS-5B "
            "1.XX image, then read the radio back and verify every channel."
        )
        return prompts

    def get_features(self):
        rf = chirp_common.RadioFeatures()
        rf.memory_bounds = (1, CHANNEL_COUNT)
        rf.valid_bands = [
            (136_000_000, 174_000_000),
            (400_000_000, 520_000_000),
        ]
        rf.valid_modes = ["FM", "NFM"]
        rf.has_name = True
        rf.valid_name_length = 12
        rf.has_ctone = True
        rf.has_rx_dtcs = True
        rf.has_dtcs_polarity = True
        rf.valid_tmodes = ["", "Tone", "TSQL", "DTCS", "Cross"]
        rf.valid_cross_modes = [
            "Tone->Tone",
            "Tone->DTCS",
            "DTCS->Tone",
            "DTCS->DTCS",
            "Tone->",
            "->Tone",
            "DTCS->",
            "->DTCS",
        ]
        rf.valid_dtcs_codes = list(DCS_CODES)
        rf.valid_power_levels = list(POWER_LEVELS)
        rf.valid_tuning_steps = list(FREQ_STEPS)
        rf.valid_duplexes = ["", "+", "-", "split"]
        rf.can_odd_split = True
        rf.valid_skips = ["", "S"]
        rf.has_settings = False
        return rf

    def process_mmap(self):
        packed = self._mmap.get_packed()
        if len(packed) != IMAGE_SIZE:
            raise errors.InvalidDataError(
                "The GS-5B 1.XX image is %i bytes; expected %i."
                % (len(packed), IMAGE_SIZE)
            )

    def _channel_raw(self, number):
        if not 1 <= number <= CHANNEL_COUNT:
            raise errors.InvalidMemoryLocation(
                "The GS-5B 1.XX has channels 1 through %i." % CHANNEL_COUNT
            )
        offset = (number - 1) * CHANNEL_SIZE
        return offset, self._mmap.get_packed()[offset:offset + CHANNEL_SIZE]

    def get_memory(self, number):
        _offset, raw = self._channel_raw(number)
        mem = chirp_common.Memory()
        mem.number = number
        rx_frequency = _decode_frequency(raw[0:4])
        if rx_frequency is None:
            mem.empty = True
            return mem
        tx_frequency = _decode_frequency(raw[4:8]) or rx_frequency
        mem.empty = False
        mem.freq = rx_frequency
        if tx_frequency == rx_frequency:
            mem.duplex = ""
            mem.offset = 0
        else:
            mem.duplex = "split"
            mem.offset = tx_frequency
        mem.name = _decode_name(raw[20:32])
        _decode_tones(
            mem,
            _decode_tone(raw[10:12]),
            _decode_tone(raw[8:10]),
        )
        mem.mode = "NFM" if raw[15] & FLAG_NARROW else "FM"
        mem.skip = "" if raw[15] & FLAG_SCAN else "S"
        mem.power = POWER_LEVELS[(raw[14] % len(POWER_LEVELS))]
        extra = RadioSettingGroup("extra", "Extra")
        extra.append(
            RadioSetting(
                "busylock",
                "Busy Lock",
                RadioSettingValueBoolean(bool(raw[15] & FLAG_BUSY_LOCK)),
            )
        )
        mem.extra = extra
        return mem

    def set_memory(self, mem):
        offset, old = self._channel_raw(mem.number)
        rx_frequency = _decode_frequency(old[0:4])
        active = rx_frequency is not None
        if mem.empty:
            self._mmap.set(offset, b"\xff" * CHANNEL_SIZE)
            return

        _validate_frequency(mem.freq)
        tx_frequency = mem.freq
        if mem.duplex == "+":
            tx_frequency += mem.offset
        elif mem.duplex == "-":
            tx_frequency -= mem.offset
        elif mem.duplex == "split":
            tx_frequency = mem.offset
        _validate_frequency(tx_frequency)

        tx_tone, rx_tone = _tone_fields(mem)
        updated = bytearray(old if active else b"\xff" * CHANNEL_SIZE)
        updated[0:4] = _encode_frequency(mem.freq)
        updated[4:8] = _encode_frequency(tx_frequency)
        updated[8:10] = _encode_tone(rx_tone)
        updated[10:12] = _encode_tone(tx_tone)
        updated[12] = old[12] if active else 0
        updated[13] = old[13] if active else 0
        power = 1
        for index, level in enumerate(POWER_LEVELS):
            if mem.power is not None and str(mem.power) == str(level):
                power = index
                break
        updated[14] = power
        flags = old[15] if active else 0
        flags &= ~(FLAG_NARROW | FLAG_SCAN | FLAG_BUSY_LOCK)
        if mem.mode == "NFM":
            flags |= FLAG_NARROW
        if mem.skip != "S":
            flags |= FLAG_SCAN
        busy_lock = next(
            (
                setting.value.get_value()
                for setting in mem.extra
                if setting.get_name() == "busylock"
            ),
            False,
        )
        if busy_lock:
            flags |= FLAG_BUSY_LOCK
        updated[15] = flags
        updated[20:32] = _encode_name(mem.name)
        self._mmap.set(offset, bytes(updated))

    def sync_in(self):
        addresses = _clone_addresses()
        status = chirp_common.Status()
        status.msg = "Connecting to GS-5B 1.XX..."
        status.cur = 0
        status.max = len(addresses)
        self.status_fn(status)

        image = bytearray(b"\xff" * IMAGE_SIZE)
        try:
            _handshake(self)
            for index, address in enumerate(addresses):
                page = _retry(lambda: _read_page(self, address))
                image[address:address + PAGE_SIZE] = page
                status.cur = index + 1
                status.msg = "Reading GS-5B 1.XX memory..."
                self.status_fn(status)
        finally:
            _exit_clone(self)
        self._mmap = memmap.MemoryMapBytes(bytes(image))
        self.process_mmap()

    def sync_out(self):
        image = self._mmap.get_packed()
        if len(image) != IMAGE_SIZE:
            raise errors.RadioError(
                "The GS-5B 1.XX image is %i bytes; expected %i."
                % (len(image), IMAGE_SIZE)
            )
        addresses = _clone_addresses()
        status = chirp_common.Status()
        status.msg = "Connecting to GS-5B 1.XX..."
        status.cur = 0
        status.max = len(addresses)
        self.status_fn(status)

        try:
            _handshake(self)
            for index, address in enumerate(addresses):
                page = image[address:address + PAGE_SIZE]
                _retry(lambda: _write_page(self, address, page))
                status.cur = index + 1
                status.msg = "Writing GS-5B 1.XX memory..."
                self.status_fn(status)
        finally:
            _exit_clone(self)
