# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Experimental read-only Kenwood TK-863G driver.

The transport and memory map were recovered from Kenwood KPG-76D 1.00.
KPG-76D uses 9,600-baud 8E2 serial framing, a ``PROGRAM`` session,
an ``M0863`` model identity, the ``NRK`` tuning record, 256-byte ``R``
blocks, and additive byte checksums.

Uploads remain disabled until the complete write map has been validated
on a physical radio.
"""

from __future__ import annotations

import logging
import struct
import time

from chirp import chirp_common, directory, errors, memmap


LOG = logging.getLogger(__name__)

ACK = b"\x06"
PROGRAM = b"PROGRAM"
MODEL_ID = b"M0863"
RADIO_ID = b"TK-863G"
MEM_SIZE = 0x8000
DAT_HEADER_SIZE = 0x70
DAT_SIZE = DAT_HEADER_SIZE + MEM_SIZE
DAT_MAGIC = b"KPG76D"
BLOCK_SIZE = 0x100
BLOCK_COUNT = MEM_SIZE // BLOCK_SIZE
CHANNEL_OFFSET = 0x02F0
CHANNEL_COUNT = 128
CHANNEL_SIZE = 0x20
IDENTITY_OFFSET = 0x58D0
IDENTITY_SIZE = 7
VALID_BANDS = [(450_000_000, 490_000_000)]
NAME_LENGTH = 8

# KPG-76D tries these speeds in this exact order. The host waits 500 ms for
# the first acknowledgement and uses the 0x16 speed-change response for the
# fallback probes.
AUTODETECT_BAUDS = (9600, 19200, 4800, 2400, 1200)

VALID_MODES = ["NFM", "FM"]
VALID_TMODES = ["", "Tone", "TSQL", "DTCS", "Cross"]
VALID_CROSS_MODES = [
    "Tone->Tone",
    "DTCS->",
    "->DTCS",
    "Tone->DTCS",
    "DTCS->Tone",
    "->Tone",
    "DTCS->DTCS",
]
VALID_CHARS = chirp_common.CHARSET_UPPER_NUMERIC + r"_-*()/\-+=)"


def _sum8(data):
    return sum(data) & 0xFF


def _read_exact(radio, count, context, timeout=None):
    data = bytearray()
    deadline = time.monotonic() + (timeout or radio.pipe.timeout or 1)
    while len(data) < count and time.monotonic() < deadline:
        chunk = radio.pipe.read(count - len(data))
        if chunk:
            data.extend(chunk)
        else:
            break
    if len(data) != count:
        raise errors.RadioNoResponse(
            "Radio returned %i of %i bytes while %s"
            % (len(data), count, context)
        )
    return bytes(data)


def _read_or_none(radio, count, timeout):
    try:
        return _read_exact(radio, count, "probing programming speed", timeout)
    except errors.RadioNoResponse:
        return b""


def _reset_input(radio):
    reset = getattr(radio.pipe, "reset_input_buffer", None)
    if reset is not None:
        reset()
        return
    flush = getattr(radio.pipe, "flush", None)
    if flush is not None:
        flush()


def _set_port(radio, baud):
    radio.pipe.baudrate = baud
    radio.pipe.bytesize = 8
    radio.pipe.parity = "E"
    radio.pipe.stopbits = 2
    radio.pipe.timeout = 1
    for name, value in (("rtscts", False), ("xonxoff", False)):
        try:
            setattr(radio.pipe, name, value)
        except (AttributeError, ValueError):
            pass


def _exchange_ack(radio, context):
    radio.pipe.write(ACK)
    response = _read_exact(radio, 1, context)
    if response != ACK:
        raise errors.RadioError(
            "Radio rejected %s; response was %s"
            % (context, response.hex() or "empty")
        )


def _enter_program_mode(radio):
    for index, baud in enumerate(AUTODETECT_BAUDS):
        _set_port(radio, baud)
        _reset_input(radio)
        radio.pipe.write(PROGRAM)
        time.sleep(0.5 if index == 0 else 0.1)
        response = _read_or_none(radio, 1, 1)
        if response == ACK:
            radio._session_baud = baud
            return
        if index > 0 and response == b"\x16":
            time.sleep(0.5)
            if _read_or_none(radio, 1, 1) == ACK:
                radio._session_baud = baud
                return
    raise errors.RadioNoResponse(
        "TK-863G did not accept the KPG-76D PROGRAM command at any "
        "supported baud rate."
    )


def _read_identity(radio):
    time.sleep(0.05)
    radio.pipe.write(b"\x02")
    identity = _read_exact(radio, 8, "reading radio identity")
    if MODEL_ID not in identity:
        raise errors.RadioError(
            "This is not a TK-863G/KPG-76D radio; identity was %s"
            % identity.hex()
        )
    _exchange_ack(radio, "acknowledging the radio identity")
    return identity


def _read_tuning_record(radio):
    radio.pipe.write(b"NRK")
    response = _read_exact(radio, 34, "reading the KPG-76D tuning record")
    if response[:1] != b"N":
        raise errors.RadioError(
            "Unexpected KPG-76D tuning response header %s"
            % response[:1].hex()
        )
    if _sum8(response[1:33]) != response[33]:
        raise errors.RadioError(
            "KPG-76D tuning record checksum failed "
            "(received %02x, calculated %02x)"
            % (response[33], _sum8(response[1:33]))
        )
    return response


def _open_clone_session(radio):
    _enter_program_mode(radio)
    radio._clone_session_open = True
    identity = _read_identity(radio)
    tuning = _read_tuning_record(radio)

    # The OEM CPS deliberately waits three seconds after the tuning record
    # before beginning the bulk memory session.
    time.sleep(3)
    radio.pipe.write(b"\x7c")
    readiness = _read_exact(radio, 2, "starting the memory session")
    time.sleep(0.5)
    _exchange_ack(radio, "starting the memory session")
    return identity, tuning, readiness


def _read_block(radio, address):
    last_error = None
    for attempt in range(1, 4):
        try:
            _reset_input(radio)
            radio.pipe.write(b"R" + struct.pack(">H", address))
            status = _read_exact(
                radio, 1, "reading memory at 0x%04X" % address
            )
            if status == b"W":
                response = _read_exact(
                    radio,
                    BLOCK_SIZE + 1,
                    "reading memory data at 0x%04X" % address,
                )
                payload = response[:-1]
                received_checksum = response[-1]
                calculated_checksum = _sum8(payload)
                if received_checksum != calculated_checksum:
                    LOG.warning(
                        "TK-863G block 0x%04X checksum mismatch on attempt "
                        "%i (received %02x, calculated %02x)",
                        address,
                        attempt,
                        received_checksum,
                        calculated_checksum,
                    )
                    radio.pipe.write(b"\x15")
                    ack = _read_exact(
                        radio, 1, "reporting a block checksum error"
                    )
                    if ack != ACK:
                        raise errors.RadioError(
                            "Radio did not acknowledge block checksum "
                            "recovery at 0x%04X" % address
                        )
                    continue
            else:
                # KPG-76D treats any non-W response as a uniform/fill block
                # and repeats one byte across the 256-byte transfer.
                fill = _read_exact(
                    radio,
                    1,
                    "reading the fill byte at 0x%04X" % address,
                )
                payload = fill * BLOCK_SIZE

            _exchange_ack(radio, "acknowledging block 0x%04X" % address)
            return payload
        except errors.RadioNoResponse as exc:
            last_error = exc
            LOG.warning(
                "TK-863G block 0x%04X read failed on attempt %i: %s",
                address,
                attempt,
                exc,
            )

    raise errors.RadioNoResponse(
        "TK-863G block 0x%04X failed after three read attempts"
        % address
    ) from last_error


def _download(radio):
    memory = bytearray(b"\xFF" * MEM_SIZE)
    try:
        identity, tuning, readiness = _open_clone_session(radio)
        LOG.info(
            "Kenwood TK-863G identity=%s tuning=%s readiness=%s",
            identity.hex(),
            tuning.hex(),
            readiness.hex(),
        )

        status = chirp_common.Status()
        status.msg = "Cloning from TK-863G"
        status.max = BLOCK_COUNT
        for block in range(BLOCK_COUNT):
            address = block * BLOCK_SIZE
            memory[address:address + BLOCK_SIZE] = _read_block(
                radio, address
            )
            status.cur = block + 1
            radio.status_fn(status)
    finally:
        if getattr(radio, "_clone_session_open", False):
            try:
                radio.pipe.write(b"E")
                _read_exact(radio, 1, "leaving program mode")
            except (errors.RadioError, OSError):
                LOG.debug("TK-863G did not acknowledge program-mode exit")
            finally:
                radio._clone_session_open = False

    return memmap.MemoryMapBytes(bytes(memory))


def _decode_lbcd(raw):
    digits = []
    for value in reversed(raw):
        high = value >> 4
        low = value & 0x0F
        if high > 9 or low > 9:
            return None
        digits.extend((high, low))
    result = 0
    for digit in digits:
        result = result * 10 + digit
    return result


def _decode_tone(raw):
    value = int.from_bytes(raw, "little")
    if value == 0xFFFF:
        return "", None, None
    if value >= 0x2800:
        code = int("%03o" % (value & 0x07FF))
        if code not in chirp_common.DTCS_CODES:
            LOG.warning("Unsupported TK-863G DTCS code %s", code)
            return "", None, None
        return "DTCS", code, "R" if value & 0x8000 else "N"
    tone = value / 10.0
    if tone not in chirp_common.TONES:
        LOG.warning("Unsupported TK-863G CTCSS tone %.1f", tone)
        return "", None, None
    return "Tone", tone, None


def _decode_name(raw):
    value = raw.split(b"\xff", 1)[0].split(b"\x00", 1)[0]
    return value.rstrip(b" ").decode("ascii", "replace")


def _channel_record(image, number):
    start = CHANNEL_OFFSET + (number - 1) * CHANNEL_SIZE
    return bytes(image[start:start + CHANNEL_SIZE])


def _unwrap_image(raw):
    if len(raw) == DAT_SIZE and raw[:6] == DAT_MAGIC:
        return raw[DAT_HEADER_SIZE:]
    return raw


@directory.register
class KenwoodTK863GRadio(
    chirp_common.CloneModeRadio,
    chirp_common.ExperimentalRadio,
):
    """Kenwood TK-863G programmed by KPG-76D."""

    VENDOR = "Kenwood"
    MODEL = "TK-863G"
    BAUD_RATE = 9600
    _memsize = MEM_SIZE
    _session_baud = 9600

    @classmethod
    def get_prompts(cls):
        prompts = chirp_common.RadioPrompts()
        prompts.experimental = (
            "TK-863G support is experimental and read-only. The KPG-76D "
            "transport, 32 KiB memory image, and 128-channel record layout "
            "were recovered from the OEM CPS and checked against a CPS-read "
            "DAT. Uploads remain disabled until a physical read and "
            "controlled write/read-back are validated."
        )
        prompts.info = (
            "Use a Kenwood KPG-76-compatible programming cable. KPG-76D "
            "uses 9,600 baud, 8 data bits, even parity, and 2 stop bits. "
            "Close the OEM CPS before starting the NewChirp read."
        )
        prompts.pre_download = (
            "1. Connect the programming cable and power the radio on.\n"
            "2. Close KPG-76D and any other program using the port.\n"
            "3. Click OK and leave the radio powered on during the read.\n\n"
            "This driver does not upload to the radio."
        )
        return prompts

    @classmethod
    def match_model(cls, filedata, filename):
        raw = _unwrap_image(bytes(filedata))
        return (
            len(raw) == MEM_SIZE
            and raw[
                IDENTITY_OFFSET:IDENTITY_OFFSET + IDENTITY_SIZE
            ] == RADIO_ID
        )

    def get_features(self):
        rf = chirp_common.RadioFeatures()
        rf.memory_bounds = (1, CHANNEL_COUNT)
        rf.has_bank = False
        rf.has_cross = True
        rf.has_ctone = True
        rf.has_dtcs = True
        rf.has_dtcs_polarity = True
        rf.has_name = True
        rf.has_offset = True
        rf.has_rx_dtcs = True
        rf.has_settings = False
        rf.has_tuning_step = False
        rf.valid_bands = list(VALID_BANDS)
        rf.valid_characters = VALID_CHARS
        rf.valid_cross_modes = list(VALID_CROSS_MODES)
        rf.valid_dtcs_codes = list(chirp_common.DTCS_CODES)
        rf.valid_duplexes = ["", "+", "-", "off"]
        rf.valid_modes = list(VALID_MODES)
        rf.valid_name_length = NAME_LENGTH
        rf.valid_tmodes = list(VALID_TMODES)
        rf.valid_tuning_steps = []
        return rf

    def process_mmap(self):
        raw = self._mmap.get_packed()
        raw = _unwrap_image(raw)
        if len(raw) != MEM_SIZE:
            raise errors.RadioError(
                "TK-863G image is %i bytes; expected %i"
                % (len(raw), MEM_SIZE)
            )
        if raw[
            IDENTITY_OFFSET:IDENTITY_OFFSET + IDENTITY_SIZE
        ] != RADIO_ID:
            raise errors.RadioError(
                "Image does not contain the TK-863G radio identity"
            )
        self._mmap = memmap.MemoryMapBytes(raw)
        self._memobj = None

    def sync_in(self):
        try:
            self._mmap = _download(self)
            self.process_mmap()
        except errors.RadioError:
            raise
        except Exception as exc:
            LOG.exception("TK-863G read failed")
            raise errors.RadioError(
                "Failed to read the TK-863G: %s" % exc
            ) from exc

    def sync_out(self):
        raise errors.RadioError(
            "TK-863G support is read-only until the KPG-76D upload map and "
            "write/read-back behavior are validated on physical hardware."
        )

    def get_raw_memory(self, number):
        return _channel_record(
            self._mmap.get_packed(), number
        ).hex(" ")

    def get_memory(self, number):
        if not 1 <= number <= CHANNEL_COUNT:
            raise errors.InvalidMemoryLocation(
                "TK-863G channel must be between 1 and %i"
                % CHANNEL_COUNT
            )

        record = _channel_record(self._mmap.get_packed(), number)
        mem = chirp_common.Memory()
        mem.number = number
        if record == b"\xFF" * CHANNEL_SIZE or record[0] == 0xFF:
            mem.empty = True
            return mem

        rx_units = _decode_lbcd(record[1:5])
        if rx_units is None:
            LOG.warning("TK-863G channel %i has an invalid RX frequency", number)
            mem.empty = True
            return mem
        mem.freq = rx_units * 10
        if not any(
            low <= mem.freq < high for low, high in VALID_BANDS
        ):
            LOG.warning(
                "TK-863G channel %i has an out-of-range RX frequency %i",
                number,
                mem.freq,
            )
            mem.empty = True
            return mem

        if record[5:9] == b"\xFF" * 4:
            mem.duplex = "off"
            mem.offset = 0
        else:
            tx_units = _decode_lbcd(record[5:9])
            if tx_units is None:
                LOG.warning(
                    "TK-863G channel %i has an invalid TX frequency", number
                )
                mem.duplex = "off"
                mem.offset = 0
            else:
                tx_frequency = tx_units * 10
                offset = tx_frequency - mem.freq
                if offset > 0:
                    mem.duplex = "+"
                    mem.offset = offset
                elif offset < 0:
                    mem.duplex = "-"
                    mem.offset = abs(offset)
                else:
                    mem.duplex = ""
                    mem.offset = 0

        mem.name = _decode_name(record[15:23])
        mem.mode = "FM" if record[26] & 0x08 else "NFM"
        chirp_common.split_tone_decode(
            mem,
            _decode_tone(record[13:15]),
            _decode_tone(record[11:13]),
        )
        return mem

    def set_memory(self, memory):
        raise errors.RadioError(
            "TK-863G channel writes are disabled in the read-only driver."
        )
