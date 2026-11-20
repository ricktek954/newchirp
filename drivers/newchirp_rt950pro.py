# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Experimental driver for the Radtel RT-950 Pro, from the Pro's own CPS.

Source: Radtel ``RT-950PRO_CPS_Setup_v1.3.3`` (``BT-RT950PRO_CPS.exe``,
``KDH.RWDataOperation``). See docs/RT950PRO_PROTOCOL.md. The Pro shares the
RT-950/BT-9000 handshake and channel encoding but reports model code
``RT-950`` (the base radio reports ``BT-9000``), stores 990 channels, and
keeps zone names at 0xC000.

Writes follow ``WriteRadioData`` exactly: the same blocks the CPS reads,
sent with ``0x57`` (APRS with ``0x58``), one ``0x06`` ACK per block, up to
three resends after a one-second timeout, then ``E``. Blocks NewChirp does
not edit are written back byte-for-byte as they were read.
"""

from __future__ import annotations

import importlib
import logging
import sys
import time

from chirp import chirp_common, directory, errors, memmap
from chirp.settings import (
    RadioSettingGroup,
    RadioSettingValueList,
    RadioSettingValueString,
)


LOG = logging.getLogger(__name__)

try:
    _BASE = sys.modules["newchirp.drivers.newchirp_rt950"]
except KeyError:
    try:
        _BASE = importlib.import_module("newchirp.drivers.newchirp_rt950")
    except ModuleNotFoundError:
        # Packaged overrides are colocated inside CHIRP's driver package.
        _BASE = importlib.import_module(".newchirp_rt950", __package__)


PRO_CHANNEL_COUNT = 990        # ChannelData: new Channel[990]
PRO_MODEL_CODE = b"RT-950"     # RWDataOperation.strModelCode
PRO_MODEL_PREFIXES = (b"RT-950", b"RT950", b"BT-9000")
PRO_INITIAL_ACK_TIMEOUT = 3.0
WRITE_ACK_TIMEOUT = 1.0        # TimerInit: 1000 ms
WRITE_RETRIES = 3              # timesRetry

# Image layout. The radio's 0x52/0x57 address space is mirrored 1:1; the
# APRS block read with 0x54 (written with 0x58) is kept after it at 0xD300.
PRO_MEM_SIZE = 0xD380
APRS_IMAGE_OFFSET = 0xD300
# Images saved before CPS 1.3.3 analysis: 960 channels, no zone names, and
# APRS stored at 0xC000. They still open, but cannot be written back.
LEGACY_PRO_MEM_SIZE = 0xD300

# (read command, write command, radio address, length, image address), in
# the order the CPS reads and writes them.
PRO_SEGMENTS = (
    (0x52, 0x57, 0x0000, 0x8000, 0x0000),   # channels (990 x 32) + tail
    (0x52, 0x57, 0x8000, 0x0080, 0x8000),   # VFO A/B/C
    (0x52, 0x57, 0x9000, 0x0080, 0x9000),   # function settings parts 1-3
    (0x52, 0x57, 0xA000, 0x0180, 0xA000),   # DTMF
    (0x52, 0x57, 0xB000, 0x0100, 0xB000),   # modulation parameters
    (0x52, 0x57, 0xC000, 0x0100, 0xC000),   # zone names
    (0x52, 0x57, 0xD000, 0x0300, 0xD000),   # modulation channel names
    (0x54, 0x58, 0x0000, 0x0080, APRS_IMAGE_OFFSET),  # APRS
)

PRO_PTT_ID_OPTIONS = ("OFF", "BOT", "EOT", "BOTH")
PRO_SIGNALLING_GROUPS = tuple(str(n) for n in range(1, 16))
FHSS_DIGITS = "0123456789ABCDEF"


def _pro_blocks():
    for read_cmd, write_cmd, source, length, target in PRO_SEGMENTS:
        for offset in range(0, length, _BASE.BLOCK_SIZE):
            yield read_cmd, write_cmd, source + offset, target + offset


def _encode_frequency(hz):
    """SetFreq_StrToHex: 10 Hz units, four little-endian BCD pairs."""
    value = int(round(hz / 10))
    out = bytearray(4)
    for index in range(4):
        pair = value % 100
        value //= 100
        out[index] = ((pair // 10) << 4) | (pair % 10)
    if value:
        raise errors.InvalidValueError("Frequency %i Hz is out of range" % hz)
    return bytes(out)


def _encode_tone(mode, value, polarity):
    """SetSubaudio_StrToHex: CTCSS tone*10 LE; DCS table index + 1."""
    if mode == "Tone":
        word = int(round(float(value) * 10))
        return bytes((word & 0xFF, word >> 8))
    if mode == "DTCS":
        index = _BASE.DCS_CODES.index(int(value))
        if polarity == "R":
            index += len(_BASE.DCS_CODES)
        return bytes((index + 1, 0))
    return b"\x00\x00"


def _extra_value(memory, name, default):
    for setting in memory.extra or []:
        if setting.get_name() == name:
            return setting.value
    return default


def _option_index(value, options, default=0):
    text = str(value)
    return options.index(text) if text in options else default


def transmit_frequency(memory):
    """TX frequency in Hz, or None for an empty or receive-only channel."""
    if memory.empty:
        return None
    duplex = memory.duplex or ""
    if duplex == "off":
        return None
    if duplex == "+":
        return int(memory.freq) + int(memory.offset)
    if duplex == "-":
        return int(memory.freq) - int(memory.offset)
    if duplex == "split":
        return int(memory.offset)
    return int(memory.freq)


def encode_channel(memory):
    """KDH.RWDataOperation.SetCHInfo_Parameter for one 32-byte record."""
    record = bytearray(b"\xFF" * 32)
    if memory.empty:
        return bytes(record)

    rx = int(memory.freq)
    duplex = memory.duplex or ""
    if duplex == "off":
        tx = None                       # CPS: empty TX frequency = TX off
    elif duplex == "+":
        tx = rx + int(memory.offset)
    elif duplex == "-":
        tx = rx - int(memory.offset)
    elif duplex == "split":
        tx = int(memory.offset)
    else:
        tx = rx
    record[0:4] = _encode_frequency(rx)
    if tx is not None:
        record[4:8] = _encode_frequency(tx)

    (tx_mode, tx_value, tx_pol), (rx_mode, rx_value, rx_pol) = (
        chirp_common.split_tone_encode(memory)
    )
    record[8:10] = _encode_tone(rx_mode, rx_value, rx_pol)
    record[10:12] = _encode_tone(tx_mode, tx_value, tx_pol)

    signalling = _option_index(
        _extra_value(memory, "signalling_group", "1"), PRO_SIGNALLING_GROUPS)
    ptt_id = _option_index(
        _extra_value(memory, "ptt_id", "OFF"), PRO_PTT_ID_OPTIONS)
    scramble = _option_index(
        _extra_value(memory, "scramble", "Off"), _BASE.SCRAMBLE_OPTIONS)
    encryption = _option_index(
        _extra_value(memory, "encryption", "Off"), _BASE.ENCRYPTION_OPTIONS)
    power = (_BASE.POWER_LEVELS.index(str(memory.power))
             if memory.power and str(memory.power) in _BASE.POWER_LEVELS
             else 0)
    record[12] = signalling
    record[13] = ptt_id
    record[14] = (scramble << 4) | power
    record[15] = (
        (int(bool(_extra_value(memory, "hopping", False))) << 7)
        | (int(memory.mode in ("NFM", "NAM")) << 6)
        | (encryption << 4)
        | (int(bool(_extra_value(memory, "bcl", False))) << 3)
        | (int(memory.skip != "S") << 2)
        | int(memory.mode in ("AM", "NAM"))
    )

    code = str(_extra_value(memory, "fhss_code", "") or "").upper()
    if code:
        if (len(code) != 6 or any(c not in FHSS_DIGITS for c in code)
                or code[0] not in "01234567"):
            # GetFHSSCode_HexToStr keeps only three bits of the first digit.
            raise errors.InvalidValueError(
                "FHSS code must be six hexadecimal digits starting 0-7")
        record[16] = int(code[4:6], 16)
        record[17] = int(code[2:4], 16)
        record[18] = int(code[0:2], 16)
        record[19] = 0xA0

    name = (memory.name or "").encode("gb2312", errors="replace")[:12]
    record[20:20 + len(name)] = name
    return bytes(record)


@directory.register
class RT950ProRadio(_BASE.RT950Radio):
    """Radtel RT-950 Pro, using the Pro CPS read/write map."""

    VENDOR = "Radtel"
    MODEL = "RT-950 Pro"
    # Writes follow the Pro CPS but are suspended: on 2026-11-20 an owner's
    # RT-950 Pro stopped transmitting (beeps on PTT) after its first write
    # (ledger w-20261120-9877, INBOX:849). Keep both flags until the pre-
    # and post-write images are compared and the cause is known.
    NEWCHIRP_WRITE_DISABLED = True
    WRITES_SUSPENDED = True
    WRITES_SUSPENDED_MESSAGE = (
        "RT-950 Pro writing is paused while a report of a radio that stopped "
        "transmitting after a write is investigated. Reading and saving "
        "still work. The radio was not changed."
    )
    # The radio stores and receives any channel in valid_bands but only
    # transmits in the amateur bands; elsewhere it beeps on PTT (2026-11-20
    # owner report, ledger w-20261120-9877: marine VHF channels). NewChirp
    # warns about such channels; it never blocks or changes them.
    NEWCHIRP_TX_BANDS = ((144_000_000, 148_000_000),
                         (420_000_000, 450_000_000))
    BAUD_RATE = 115200
    INITIAL_ACK_TIMEOUT = PRO_INITIAL_ACK_TIMEOUT
    _memsize = PRO_MEM_SIZE
    _channel_count = PRO_CHANNEL_COUNT

    @classmethod
    def get_prompts(cls):
        prompts = chirp_common.RadioPrompts()
        prompts.experimental = (
            "NewChirp RT-950 Pro support follows Radtel's RT-950 Pro CPS "
            "1.3.3. Reading works; writing is paused while a report of a "
            "radio that stopped transmitting after a write is investigated. "
            "Read the radio and save the image as a backup."
        )
        prompts.info = (
            "Use the RT-950 Pro programming cable, power the radio on "
            "normally, and close Radtel CPS before connecting. The interface "
            "uses 115200 baud, 8N1, with RTS and DTR asserted and no hardware "
            "or XON/XOFF flow control."
        )
        prompts.pre_download = (
            "1. Close Radtel CPS and any other serial software.\n"
            "2. Connect the cable directly and start the read while the "
            "radio is powered on.\n"
            "3. Save the image after the first successful read as a backup."
        )
        prompts.pre_upload = (
            "Write only an image that NewChirp read from this radio, and "
            "keep a saved backup.\n"
            "1. Close Radtel CPS and any other serial software.\n"
            "2. Keep the radio powered on and the cable connected until the "
            "write finishes.\n"
            "3. Read the radio again afterwards to confirm the channels."
        )
        return prompts

    def get_features(self):
        rf = super().get_features()
        rf.valid_bands = [
            (18_000_000, 64_000_000),
            (70_000_000, 137_000_000),
            (136_000_000, 174_000_000),
            (174_000_000, 400_000_000),
            (400_000_000, 480_000_000),
            (480_000_000, 580_000_000),
        ]
        rf.has_settings = False
        # The CPS stores frequencies to 10 Hz (SetFreq_StrToHex), so any
        # usual channel step is valid, including 6.25/12.5 kHz GMRS ones.
        rf.valid_tuning_steps = [2.5, 5.0, 6.25, 10.0, 12.5, 20.0, 25.0,
                                 50.0, 100.0]
        return rf

    # -- image layout -----------------------------------------------------

    @property
    def _writable_image(self):
        return (self._mmap is not None
                and len(self._mmap.get_packed()) == PRO_MEM_SIZE)

    def get_memory(self, number):
        if (number > _BASE.CHANNEL_COUNT and self._mmap is not None
                and len(self._mmap.get_packed()) == LEGACY_PRO_MEM_SIZE):
            # Legacy images never read channels 961-990.
            mem = chirp_common.Memory()
            mem.number = number
            mem.empty = True
            mem.immutable = ["empty"]
            return mem
        mem = super().get_memory(number)
        # The Pro CPS has no per-channel TX-enable flag (it masks byte 15
        # with % 2); transmit is disabled by an empty TX frequency, shown as
        # duplex "off". Use the CPS labels for PTT ID and signalling group,
        # and let the FHSS code be edited as the CPS allows.
        rebuilt = RadioSettingGroup("Extra", "extra")
        for setting in mem.extra:
            name = setting.get_name()
            if name == "tx_enabled":
                continue
            if name == "ptt_id":
                setting = _BASE._extra(
                    "ptt_id", "PTT ID",
                    RadioSettingValueList(
                        PRO_PTT_ID_OPTIONS,
                        current_index=min(int(setting.value), 3)),
                    "Sends the PTT ID at the beginning (BOT), end (EOT) or "
                    "both ends of each transmission.")
            elif name == "signalling_group":
                setting = _BASE._extra(
                    "signalling_group", "Signalling group",
                    RadioSettingValueList(
                        PRO_SIGNALLING_GROUPS,
                        current_index=min(int(setting.value), 14)),
                    "Selects the channel's signalling group (1-15).")
            elif name == "fhss_code":
                setting = _BASE._extra(
                    "fhss_code", "FHSS code",
                    RadioSettingValueString(
                        0, 6, str(setting.value), autopad=False),
                    "Six hexadecimal digits used by frequency-hopping mode.")
            rebuilt.append(setting)
        mem.extra = rebuilt
        return mem

    def validate_memory(self, mem):
        messages = super().validate_memory(mem)
        tx = transmit_frequency(mem)
        if tx and not any(lo <= tx < hi for lo, hi in self.NEWCHIRP_TX_BANDS):
            messages.append(chirp_common.ValidationWarning(
                "The RT-950 Pro only transmits on 144-148 and 420-450 MHz. "
                "It will receive this channel but beep on PTT."))
        return messages

    def set_memory(self, memory):
        if not 1 <= memory.number <= self._channel_count:
            raise errors.InvalidMemoryLocation(
                "Channel number must be between 1 and %i"
                % self._channel_count)
        if not self._writable_image:
            raise errors.RadioError(
                "This RT-950 Pro image was saved by an older NewChirp that "
                "did not read channels 961-990 or the zone names. Read the "
                "radio again before editing or writing."
            )
        self._mmap.set((memory.number - 1) * 32, encode_channel(memory))

    # -- transport --------------------------------------------------------

    def _handshake_once(self):
        if hasattr(self.pipe, "reset_input_buffer"):
            self.pipe.reset_input_buffer()

        self.pipe.write(_BASE.HANDSHAKE)
        if self._read_exact(
            1, timeout=self.INITIAL_ACK_TIMEOUT
        ) != _BASE.ACK:
            raise errors.RadioNoResponse(
                "The RT-950 Pro did not acknowledge programming mode "
                "within %.1f seconds." % self.INITIAL_ACK_TIMEOUT
            )

        self.pipe.write(b"F")
        self._read_exact(16)

        self.pipe.write(b"M")
        model = self._read_exact(12).replace(b"\x00", b"").strip()
        if not model:
            raise errors.RadioError(
                "The RT-950 Pro returned an empty model identifier."
            )
        if not any(model.startswith(prefix) for prefix in PRO_MODEL_PREFIXES):
            raise errors.RadioError(
                "RT-950 Pro driver received unrecognized model code %r"
                % model
            )
        self._pro_model = model
        LOG.debug("RT-950 Pro model code: %s", model.decode("ascii", "replace"))

        send_packet, self._encryption_symbol = _BASE._send_packet_and_symbol()
        self.pipe.write(send_packet)
        if self._read_exact(1) != _BASE.ACK:
            raise errors.RadioNoResponse(
                "The RT-950 Pro did not acknowledge data encryption."
            )

    def _read_pro_block(self, command, address):
        request = bytes(
            (command, address >> 8, address & 0xFF, _BASE.BLOCK_SIZE)
        )
        self.pipe.write(request)
        reply = self._read_exact(4 + _BASE.BLOCK_SIZE)
        if reply[1:3] != request[1:3]:
            raise errors.RadioError(
                "RT-950 Pro returned the wrong block address for 0x%04x: %r"
                % (address, reply[1:3])
            )
        return _BASE._decode_payload(reply[4:], self._encryption_symbol)

    def _write_pro_block(self, command, address, data):
        # The symbol substitution is its own inverse (WriteStep1 applies the
        # same rule to plaintext that ReadStep2 applies to ciphertext).
        frame = bytes(
            (command, address >> 8, address & 0xFF, _BASE.BLOCK_SIZE)
        ) + _BASE._decode_payload(data, self._encryption_symbol)
        for attempt in range(WRITE_RETRIES + 1):
            self.pipe.write(frame)
            deadline = time.monotonic() + WRITE_ACK_TIMEOUT
            while time.monotonic() < deadline:
                reply = self.pipe.read(1)
                if reply == _BASE.ACK:
                    return
                # WriteStep2 ignores any byte other than ACK.
            LOG.warning("RT-950 Pro block 0x%02X %04X not acknowledged "
                        "(attempt %i)", command, address, attempt + 1)
        raise errors.RadioNoResponse(
            "The RT-950 Pro stopped acknowledging the write at block "
            "0x%04X. The radio may be partly written: keep it powered on "
            "and write again, or restore your saved backup." % address
        )

    def sync_in(self):
        session_started = False
        try:
            self._handshake()
            session_started = True

            memory = memmap.MemoryMapBytes(b"\xff" * PRO_MEM_SIZE)
            blocks = tuple(_pro_blocks())
            for current, (command, _write, address, target) in enumerate(
                    blocks, 1):
                status = chirp_common.Status()
                status.cur = current
                status.max = len(blocks)
                status.msg = (
                    "Reading RT-950 Pro channels"
                    if command == 0x52 and address < 0x8000
                    else "Reading RT-950 Pro settings"
                )
                self.status_fn(status)
                memory.set(target, self._read_pro_block(command, address))
        except errors.RadioError:
            raise
        except Exception as exc:
            raise errors.RadioError(
                "Failed to communicate with the RT-950 Pro: %s" % exc
            ) from exc
        finally:
            if session_started:
                try:
                    self.pipe.write(b"E")
                except Exception:
                    pass

        self._mmap = memory
        self.process_mmap()

    def sync_out(self):
        if self.WRITES_SUSPENDED:
            raise errors.RadioError(self.WRITES_SUSPENDED_MESSAGE)
        if not self._writable_image:
            raise errors.RadioError(
                "This RT-950 Pro image is incomplete (saved by an older "
                "NewChirp). Read the radio again, then write. The radio was "
                "not changed."
            )
        image = self._mmap.get_packed()
        session_started = False
        try:
            self._handshake()
            session_started = True
            if self._pro_model != PRO_MODEL_CODE:
                # The Pro CPS refuses any other model code; a base RT-950
                # (BT-9000) has a different memory layout.
                raise errors.RadioError(
                    "The connected radio reports %r, not the RT-950 Pro's "
                    "%r. The radio was not changed."
                    % (self._pro_model.decode("ascii", "replace"),
                       PRO_MODEL_CODE.decode())
                )
            blocks = tuple(_pro_blocks())
            for current, (_read, command, address, target) in enumerate(
                    blocks, 1):
                status = chirp_common.Status()
                status.cur = current
                status.max = len(blocks)
                status.msg = "Writing RT-950 Pro"
                self.status_fn(status)
                self._write_pro_block(
                    command, address,
                    image[target:target + _BASE.BLOCK_SIZE])
        except errors.RadioError:
            raise
        except Exception as exc:
            raise errors.RadioError(
                "Failed to write the RT-950 Pro: %s" % exc
            ) from exc
        finally:
            if session_started:
                try:
                    self.pipe.write(b"E")
                except Exception:
                    pass
