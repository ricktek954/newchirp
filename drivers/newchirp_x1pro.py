# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Radioddity X1 Pro GMRS driver recovered from the 2026 CPS."""

from __future__ import annotations

import struct
import time

from chirp import chirp_common, directory, errors, memmap
from chirp.settings import (
    RadioSetting,
    RadioSettingGroup,
    RadioSettingValueBoolean,
    RadioSettingValueList,
)


ACK = b"\x06"
HANDSHAKE = b"\x02PROGRAM"
IDENT = bytes.fromhex("53 4D 50 35 35 38 FF FF")
READ_COMMAND = 0x52
WRITE_COMMAND = 0x57
EXIT_COMMAND = 0x62
BLOCK_SIZE = 16
CHANNEL_COUNT = 30
CHANNEL_BASE = 0x0000
PARAM_BASE = 0xE000
IMAGE_SIZE = PARAM_BASE + BLOCK_SIZE

READ_TIMEOUT = 2.0
OPEN_SETTLE_DELAY = 0.100
INTER_BLOCK_DELAY = 0.020

FREQ_MIN = 462_550_000
FREQ_MAX = 467_725_000
POWER_LEVELS = (
    chirp_common.PowerLevel("Low", watts=0.5),
    chirp_common.PowerLevel("Medium", watts=5),
    chirp_common.PowerLevel("High", watts=7),
)

FLAG_POWER_MASK = 0x03
FLAG_WIDE = 0x04
FLAG_SCAN = 0x10
FLAG_BUSY_LOCK = 0x20


def _reset_input(pipe):
    reset = getattr(pipe, "reset_input_buffer", None)
    if reset is not None:
        reset()


def _send(pipe, payload):
    try:
        _reset_input(pipe)
        pipe.write(bytes(payload))
        pipe.flush()
    except Exception as exc:
        raise errors.RadioError(
            "Could not send the X1 Pro programming command."
        ) from exc


def _read_exact(pipe, size, timeout=None):
    if timeout is None:
        timeout = READ_TIMEOUT
    deadline = time.monotonic() + timeout
    response = bytearray()
    while len(response) < size:
        if time.monotonic() >= deadline:
            break
        chunk = pipe.read(size - len(response))
        if chunk:
            response.extend(chunk)
        else:
            remaining = deadline - time.monotonic()
            if remaining > 0:
                time.sleep(min(0.020, remaining))
    return bytes(response)


def _handshake(radio):
    time.sleep(OPEN_SETTLE_DELAY)
    radio.pipe.baudrate = 115200
    radio.pipe.parity = "N"
    radio.pipe.stopbits = 1
    radio.pipe.bytesize = 8
    radio.pipe.timeout = min(float(radio.pipe.timeout or 0.25), READ_TIMEOUT)
    _send(radio.pipe, HANDSHAKE)
    if _read_exact(radio.pipe, 1) != ACK:
        raise errors.RadioNoResponse(
            "The X1 Pro did not acknowledge the CPS programming handshake."
        )

    _send(radio.pipe, b"\x02")
    ident = _read_exact(radio.pipe, len(IDENT))
    if ident != IDENT:
        raise errors.RadioError(
            "The connected radio did not identify as an X1 Pro "
            "(reply %s)." % (ident.hex() if ident else "no data")
        )

    _send(radio.pipe, ACK)
    if _read_exact(radio.pipe, 1) != ACK:
        raise errors.RadioNoResponse(
            "The X1 Pro did not complete the CPS handshake."
        )


def _read_block(radio, address):
    command = struct.pack(">BHB", READ_COMMAND, address, BLOCK_SIZE)
    _send(radio.pipe, command)
    response = _read_exact(radio.pipe, BLOCK_SIZE + 4)
    if len(response) != BLOCK_SIZE + 4:
        raise errors.RadioError(
            "Short reply from the X1 Pro reading block 0x%04X: expected "
            "%i bytes, received %i."
            % (address, BLOCK_SIZE + 4, len(response))
        )
    if response[:4] != command:
        raise errors.RadioError(
            "The X1 Pro returned a mismatched read header for 0x%04X."
            % address
        )
    return response[4:]


def _write_block(radio, address, data, delay=0):
    if len(data) != BLOCK_SIZE:
        raise errors.RadioError(
            "X1 Pro write block 0x%04X must contain %i bytes."
            % (address, BLOCK_SIZE)
        )
    command = struct.pack(">BHB", WRITE_COMMAND, address, BLOCK_SIZE)
    _send(radio.pipe, command + bytes(data))
    response = _read_exact(radio.pipe, 1)
    if response != ACK:
        detail = response.hex() if response else "no response"
        raise errors.RadioError(
            "The X1 Pro did not acknowledge write block 0x%04X (%s)."
            % (address, detail)
        )
    if delay:
        time.sleep(delay)


def _exit_clone(radio):
    try:
        _send(radio.pipe, bytes((EXIT_COMMAND,)))
    except errors.RadioError:
        pass


def _nearest(values, value):
    return min(values, key=lambda item: abs(item - value))


def _decode_tone(raw):
    if raw == b"\xff\xff":
        return None
    value = struct.unpack("<H", raw)[0]
    inverted = bool(value & 0x8000)
    value &= 0x7FFF
    if 0x2800 <= value < 0x3000:
        code = int(("%o" % (value - 0x2800)))
        return ("DCS", code, inverted)
    hz = value / 10.0
    return ("Tone", _nearest(chirp_common.TONES, hz), inverted)


def _encode_ctcss(tone):
    return struct.pack("<H", int(round(tone * 10)))


def _encode_dcs(code, inverted):
    value = 0x2800 + int(str(code), 8)
    if inverted:
        value |= 0x8000
    return struct.pack("<H", value)


def _channel_page_for_write(page):
    """Convert canonical read-order tone words to the OEM write byte order."""
    if len(page) != BLOCK_SIZE:
        raise errors.RadioError(
            "X1 Pro channel pages must contain %i bytes." % BLOCK_SIZE
        )
    wire = bytearray(page)
    wire[8:10] = bytes((wire[9], wire[8]))
    wire[10:12] = bytes((wire[11], wire[10]))
    return bytes(wire)


def _tone_fields(mem):
    tx = rx = None
    tx_inverted = rx_inverted = False
    cross = mem.cross_mode

    if mem.tmode == "Tone":
        tx = ("Tone", mem.rtone, False)
    elif mem.tmode == "TSQL":
        tx = ("Tone", mem.rtone, False)
        rx = ("Tone", mem.ctone, False)
    elif mem.tmode == "DTCS":
        tx_inverted = mem.dtcs_polarity[1:] == "R"
        rx_inverted = mem.dtcs_polarity[:1] == "R"
        tx = ("DCS", mem.dtcs, tx_inverted)
        rx = ("DCS", mem.rx_dtcs, rx_inverted)
    elif mem.tmode == "Cross":
        tx_side, rx_side = cross.split("->", 1)
        if tx_side == "Tone":
            tx = ("Tone", mem.rtone, False)
        elif tx_side == "DTCS":
            tx_inverted = mem.dtcs_polarity[1:] == "R"
            tx = ("DCS", mem.dtcs, tx_inverted)
        if rx_side == "Tone":
            rx = ("Tone", mem.ctone, False)
        elif rx_side == "DTCS":
            rx_inverted = mem.dtcs_polarity[:1] == "R"
            rx = ("DCS", mem.rx_dtcs, rx_inverted)
    return tx, rx


def _encode_tone(tone):
    if tone is None:
        return b"\xff\xff"
    kind, value, inverted = tone
    if kind == "Tone":
        return _encode_ctcss(value)
    return _encode_dcs(value, inverted)


def _decode_tones(mem, tx, rx):
    if tx is None and rx is None:
        mem.tmode = ""
        return
    if tx is not None and rx is None:
        if tx[0] == "Tone":
            mem.tmode = "Tone"
            mem.rtone = tx[1]
        else:
            mem.tmode = "Cross"
            mem.cross_mode = "DTCS->"
            mem.dtcs = tx[1]
            mem.dtcs_polarity = "NR" if tx[2] else "NN"
        return
    if tx is None and rx is not None:
        mem.tmode = "Cross"
        if rx[0] == "Tone":
            mem.cross_mode = "->Tone"
            mem.ctone = rx[1]
        else:
            mem.cross_mode = "->DTCS"
            mem.rx_dtcs = rx[1]
            mem.dtcs_polarity = "RN" if rx[2] else "NN"
        return

    if tx[0] == "Tone" and rx[0] == "Tone":
        if tx[1] == rx[1]:
            mem.tmode = "TSQL"
            mem.rtone = tx[1]
            mem.ctone = rx[1]
        else:
            mem.tmode = "Cross"
            mem.cross_mode = "Tone->Tone"
            mem.rtone = tx[1]
            mem.ctone = rx[1]
    elif tx[0] == "DCS" and rx[0] == "DCS":
        mem.tmode = "DTCS"
        mem.dtcs = tx[1]
        mem.rx_dtcs = rx[1]
        mem.dtcs_polarity = (
            ("R" if rx[2] else "N")
            + ("R" if tx[2] else "N")
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


def _get_setting_bits(raw, byte, bit, length):
    return (raw[byte] >> bit) & ((1 << length) - 1)


def _set_setting_bits(raw, byte, bit, length, value):
    mask = ((1 << length) - 1) << bit
    raw[byte] = (raw[byte] & ~mask) | ((int(value) << bit) & mask)


@directory.register
class RadioddityX1Pro(chirp_common.CloneModeRadio,
                      chirp_common.ExperimentalRadio):
    """Radioddity X1 Pro GMRS transceiver."""

    VENDOR = "Radioddity"
    MODEL = "X1 Pro"
    BAUD_RATE = 115200
    WANTS_DTR = False
    WANTS_RTS = False
    XON_XOFF = False
    _memsize = IMAGE_SIZE
    _ranges = [
        (CHANNEL_BASE, CHANNEL_BASE + CHANNEL_COUNT * BLOCK_SIZE, BLOCK_SIZE),
        (PARAM_BASE, PARAM_BASE + BLOCK_SIZE, BLOCK_SIZE),
    ]

    @classmethod
    def get_prompts(cls):
        prompts = chirp_common.RadioPrompts()
        prompts.experimental = (
            "NewChirp X1 Pro support is experimental. The CPS transport, "
            "30-channel map, settings page, tones, and write path were "
            "recovered from Radioddity's 2026-07-15 firmware/CPS package. "
            "This driver has not yet been validated on physical hardware."
        )
        prompts.info = (
            "Use the X1 Pro programming cable, power the radio on normally, "
            "and close Radioddity CPS before connecting. The radio uses "
            "115200 8N1."
        )
        prompts.pre_download = (
            "Connect the programming cable and read the radio. Save the "
            "unedited image as a backup before making changes."
        )
        prompts.pre_upload = (
            "Keep the unedited backup image. The OEM CPS writes settings and "
            "all 30 channel pages in 16-byte blocks. Do not disconnect the "
            "cable during the write. Read the radio back afterward and verify "
            "all 22 GMRS channels and 8 repeater channels."
        )
        return prompts

    def get_features(self):
        rf = chirp_common.RadioFeatures()
        rf.memory_bounds = (1, CHANNEL_COUNT)
        rf.valid_bands = [(FREQ_MIN, FREQ_MAX)]
        rf.valid_modes = ["NFM", "FM"]
        rf.has_name = False
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
        rf.valid_power_levels = list(POWER_LEVELS)
        rf.valid_tuning_steps = [2.5, 5.0, 6.25, 12.5]
        rf.valid_duplexes = ["", "+", "-", "split"]
        rf.can_odd_split = True
        rf.valid_skips = ["", "S"]
        rf.has_settings = True
        return rf

    def process_mmap(self):
        packed = self._mmap.get_packed()
        if len(packed) != IMAGE_SIZE:
            raise errors.InvalidDataError(
                "The X1 Pro image is %i bytes; expected %i."
                % (len(packed), IMAGE_SIZE)
            )

    def _validate_frequency(self, frequency):
        if not FREQ_MIN <= frequency <= FREQ_MAX:
            raise errors.RadioError(
                "X1 Pro frequencies must stay within the GMRS range of "
                "462.550000 to 467.725000 MHz."
            )

    def get_memory(self, number):
        if not 1 <= number <= CHANNEL_COUNT:
            raise errors.InvalidMemoryLocation(
                "The X1 Pro has channels 1 through %i." % CHANNEL_COUNT
            )
        mem = chirp_common.Memory()
        mem.number = number
        offset = (number - 1) * BLOCK_SIZE
        raw = self._mmap.get_packed()[offset:offset + BLOCK_SIZE]
        rx_frequency, tx_frequency = struct.unpack(">II", raw[:8])
        if rx_frequency == 0 or not FREQ_MIN <= rx_frequency <= FREQ_MAX:
            mem.empty = True
            return mem

        mem.empty = False
        _decode_tones(mem, _decode_tone(raw[10:12]), _decode_tone(raw[8:10]))
        mem.freq = rx_frequency
        if tx_frequency == rx_frequency:
            mem.duplex = ""
            mem.offset = 0
        elif tx_frequency == rx_frequency + 5_000_000:
            mem.duplex = "+"
            mem.offset = 5_000_000
        elif tx_frequency == rx_frequency - 5_000_000:
            mem.duplex = "-"
            mem.offset = 5_000_000
        else:
            mem.duplex = "split"
            mem.offset = tx_frequency

        flags = raw[12]
        power = flags & FLAG_POWER_MASK
        mem.power = (
            POWER_LEVELS[power]
            if power < len(POWER_LEVELS)
            else POWER_LEVELS[1]
        )
        mem.mode = "FM" if flags & FLAG_WIDE else "NFM"
        mem.skip = "" if flags & FLAG_SCAN else "S"
        extra = RadioSettingGroup("extra", "Extra")
        extra.append(
            RadioSetting(
                "busylock",
                "Busy Lock",
                RadioSettingValueBoolean(bool(flags & FLAG_BUSY_LOCK)),
            )
        )
        mem.extra = extra
        return mem

    def set_memory(self, mem):
        if not 1 <= mem.number <= CHANNEL_COUNT:
            raise errors.InvalidMemoryLocation(
                "The X1 Pro has channels 1 through %i." % CHANNEL_COUNT
            )
        offset = (mem.number - 1) * BLOCK_SIZE
        old = bytearray(self._mmap.get_packed()[offset:offset + BLOCK_SIZE])
        if mem.empty:
            self._mmap.set(offset, bytes(BLOCK_SIZE))
            return

        self._validate_frequency(mem.freq)
        tx_frequency = mem.freq
        if mem.duplex == "+":
            tx_frequency += mem.offset
        elif mem.duplex == "-":
            tx_frequency -= mem.offset
        elif mem.duplex == "split":
            tx_frequency = mem.offset
        self._validate_frequency(tx_frequency)

        tx_tone, rx_tone = _tone_fields(mem)
        flags = old[12]
        power = 1
        for index, level in enumerate(POWER_LEVELS):
            if mem.power is not None and str(mem.power) == str(level):
                power = index
                break
        flags &= ~(FLAG_POWER_MASK | FLAG_WIDE | FLAG_SCAN | FLAG_BUSY_LOCK)
        flags |= power
        if mem.mode == "FM":
            flags |= FLAG_WIDE
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

        updated = bytearray(old)
        updated[0:8] = struct.pack(">II", mem.freq, tx_frequency)
        updated[8:10] = _encode_tone(rx_tone)
        updated[10:12] = _encode_tone(tx_tone)
        updated[12] = flags
        self._mmap.set(offset, bytes(updated))

    def get_settings(self):
        raw = self._mmap.get_packed()[PARAM_BASE:PARAM_BASE + BLOCK_SIZE]
        group = RadioSettingGroup("settings", "Settings")
        group.append(
            RadioSetting(
                "sqlevel",
                "Squelch Level",
                RadioSettingValueList(
                    [str(value) for value in range(10)],
                    current_index=min(
                        _get_setting_bits(raw, 0, 1, 4),
                        9,
                    ),
                ),
            )
        )
        group.append(
            RadioSetting(
                "keytone",
                "Key Tone",
                RadioSettingValueBoolean(bool(_get_setting_bits(raw, 0, 0, 1))),
            )
        )
        group.append(
            RadioSetting(
                "recode",
                "Record",
                RadioSettingValueBoolean(bool(_get_setting_bits(raw, 0, 6, 1))),
            )
        )
        group.append(
            RadioSetting(
                "rogerbeep",
                "Roger Beep",
                RadioSettingValueBoolean(bool(_get_setting_bits(raw, 0, 7, 1))),
            )
        )
        group.append(
            RadioSetting(
                "powsave",
                "Power Save",
                RadioSettingValueBoolean(bool(_get_setting_bits(raw, 1, 5, 1))),
            )
        )
        group.append(
            RadioSetting(
                "scanmode",
                "Scan Mode",
                RadioSettingValueList(
                    ["OS", "TS"],
                    current_index=(
                        _get_setting_bits(raw, 2, 3, 3)
                        if _get_setting_bits(raw, 2, 3, 3) < 2
                        else 0
                    ),
                ),
            )
        )
        group.append(
            RadioSetting(
                "nrc",
                "Noise Reduction",
                RadioSettingValueList(
                    ["Off", "1", "2", "3"],
                    current_index=min(
                        _get_setting_bits(raw, 6, 0, 8),
                        3,
                    ),
                ),
            )
        )
        group.append(
            RadioSetting(
                "vox",
                "VOX",
                RadioSettingValueList(
                    ["Off", "On"],
                    current_index=(
                        1 if _get_setting_bits(raw, 7, 0, 8) else 0
                    ),
                ),
            )
        )
        return group

    def set_settings(self, settings):
        image = bytearray(self._mmap.get_packed())
        raw = bytearray(image[PARAM_BASE:PARAM_BASE + BLOCK_SIZE])
        for element in settings:
            if not isinstance(element, RadioSetting):
                continue
            name = element.get_name()
            value = element.value.get_value()
            if name == "sqlevel":
                _set_setting_bits(raw, 0, 1, 4, int(value))
            elif name == "keytone":
                _set_setting_bits(raw, 0, 0, 1, int(bool(value)))
            elif name == "recode":
                _set_setting_bits(raw, 0, 6, 1, int(bool(value)))
            elif name == "rogerbeep":
                _set_setting_bits(raw, 0, 7, 1, int(bool(value)))
            elif name == "powsave":
                _set_setting_bits(raw, 1, 5, 1, int(bool(value)))
            elif name == "scanmode":
                _set_setting_bits(raw, 2, 3, 3, ["OS", "TS"].index(str(value)))
            elif name == "nrc":
                _set_setting_bits(
                    raw, 6, 0, 8, ["Off", "1", "2", "3"].index(str(value))
                )
            elif name == "vox":
                _set_setting_bits(raw, 7, 0, 8, ["Off", "On"].index(str(value)))
        image[PARAM_BASE:PARAM_BASE + BLOCK_SIZE] = raw
        self._mmap = memmap.MemoryMapBytes(bytes(image))

    def sync_in(self):
        status = chirp_common.Status()
        status.msg = "Connecting to X1 Pro..."
        status.cur = 0
        status.max = CHANNEL_COUNT + 1
        self.status_fn(status)

        image = bytearray(IMAGE_SIZE)
        try:
            _handshake(self)
            image[PARAM_BASE:PARAM_BASE + BLOCK_SIZE] = _read_block(
                self, PARAM_BASE
            )
            status.cur = 1
            status.msg = "Reading X1 Pro settings..."
            self.status_fn(status)
            for index in range(CHANNEL_COUNT):
                address = CHANNEL_BASE + index * BLOCK_SIZE
                image[address:address + BLOCK_SIZE] = _read_block(
                    self, address
                )
                status.cur = index + 2
                status.msg = "Reading X1 Pro channels..."
                self.status_fn(status)
        finally:
            _exit_clone(self)

        self._mmap = memmap.MemoryMapBytes(bytes(image))
        self.process_mmap()

    def sync_out(self):
        image = self._mmap.get_packed()
        if len(image) != IMAGE_SIZE:
            raise errors.RadioError(
                "The X1 Pro image is %i bytes; expected %i."
                % (len(image), IMAGE_SIZE)
            )
        status = chirp_common.Status()
        status.msg = "Connecting to X1 Pro..."
        status.cur = 0
        status.max = CHANNEL_COUNT + 1
        self.status_fn(status)

        try:
            _handshake(self)
            _write_block(self, PARAM_BASE, image[PARAM_BASE:IMAGE_SIZE])
            for index in range(CHANNEL_COUNT):
                address = CHANNEL_BASE + index * BLOCK_SIZE
                page = image[address:address + BLOCK_SIZE]
                _write_block(
                    self,
                    address,
                    _channel_page_for_write(page),
                    delay=INTER_BLOCK_DELAY,
                )
                status.cur = index + 1
                status.msg = "Writing X1 Pro channels..."
                self.status_fn(status)
        finally:
            _exit_clone(self)
