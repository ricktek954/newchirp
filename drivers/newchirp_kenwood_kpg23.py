# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Experimental read-only drivers for Kenwood KPG-23D/KPG-32D radios.

The OEM CPS traces establish a 9,600-baud 8N1 serial session, an eight-byte
identity response to 0x02, and an ``R`` command carrying a 16-bit address and
an eight-bit block length.  The supplied data files show 16-byte channel
records containing RX and TX frequency words followed by a four-character
name.

Uploads remain disabled.  The reply header after ``W`` and the complete
settings/option map still need physical-radio validation.
"""

from __future__ import annotations

import logging
import struct
import time

from chirp import chirp_common, directory, errors, memmap


LOG = logging.getLogger(__name__)

ACK = b"\x06"
NAK = b"\x15"
READ_REQUEST = b"R"
READ_DATA = b"W"
FILL_DATA = b"Z"
BLOCK_SIZE = 0x80
FIRST_ADDRESS = 0xF000
CHANNEL_SIZE = 16
MAX_CHANNELS = 160
IMAGE_SIZE = 0x0E00
READ_LIMIT = 2

RX_BASE_450 = 0x4D18
TX_BASE_450 = 0x6940
FREQUENCY_BASE = 450_000_000
FREQUENCY_STEP = 6_250

VALID_BANDS = [(450_000_000, 470_000_000)]
VALID_MODES = ["NFM", "FM"]
VALID_CHARS = chirp_common.CHARSET_UPPER_NUMERIC + " -_/\\*()"


def _identity_matches(identity, model):
    text = identity.replace(b"\x00", b"").replace(b"\xff", b"").strip()
    if b"350" in text:
        return model == "TK-350"
    if b"359" in text:
        return model == "TK-359"
    # The 1996 CPS accepts a small family of P/M identifiers.  The exact
    # TK-359 identifier is not exposed by the supplied sample, so retain the
    # read-only fallback and make the reported identity visible in logs.
    LOG.info("Kenwood %s reported identity %r", model, text)
    return bool(text)


def _open_session(radio):
    pipe = radio.pipe
    pipe.baudrate = 9600
    pipe.bytesize = 8
    pipe.parity = "N"
    pipe.stopbits = 1
    pipe.timeout = 1
    for name, value in (("rtscts", False), ("xonxoff", False)):
        try:
            setattr(pipe, name, value)
        except (AttributeError, ValueError):
            pass

    reset = getattr(pipe, "reset_input_buffer", None)
    if reset is not None:
        reset()

    pipe.write(b"\x02")
    identity = _read_exact(radio, 8, "reading the radio identity")
    if not _identity_matches(identity, radio.MODEL):
        raise errors.RadioError(
            "Connected Kenwood is not recognized as a %s: %s"
            % (radio.MODEL, identity.hex())
        )

    # KPG-23D acknowledges the identity and immediately begins addressed
    # reads.  It does not send the later NX-series checksum setup command.
    pipe.write(ACK)
    radio._session_open = True
    try:
        response = _read_exact(radio, 1, "acknowledging the radio identity",
                               timeout=0.2)
    except errors.RadioNoResponse:
        response = b""
    if response not in (b"", ACK):
        LOG.warning(
            "Kenwood %s returned %s after the identity ACK; continuing "
            "because KPG-23D does not require a second ACK on every cable.",
            radio.MODEL,
            response.hex(),
        )
    return identity


def _read_exact(radio, count, context, timeout=READ_LIMIT):
    data = bytearray()
    deadline = time.monotonic() + timeout
    while len(data) < count and time.monotonic() < deadline:
        chunk = radio.pipe.read(count - len(data))
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


def _exchange_ack(radio, context):
    radio.pipe.write(ACK)
    response = _read_exact(radio, 1, context)
    if response != ACK:
        raise errors.RadioError(
            "Radio rejected %s; response was %s"
            % (context, (response or NAK).hex())
        )


def _read_block(radio, address, length):
    last_error = None
    for _attempt in range(1, 4):
        try:
            radio.pipe.write(
                READ_REQUEST
                + struct.pack(">H", address)
                + bytes((length,))
            )
            status = _read_exact(
                radio, 1, "reading memory status at 0x%04X" % address
            )
            if status == FILL_DATA:
                payload = b"\xff" * length
            elif status == READ_DATA:
                # The KPG-family reply is a three-byte record header followed
                # by the requested bytes.  The header is retained by the OEM
                # but does not alter the memory data.
                response = _read_exact(
                    radio,
                    3 + length,
                    "reading memory data at 0x%04X" % address,
                    timeout=3,
                )
                payload = response[3:]
            else:
                raise errors.RadioError(
                    "Radio returned read status %s at 0x%04X"
                    % (status.hex(), address)
                )
            _exchange_ack(radio, "memory block 0x%04X" % address)
            return payload
        except errors.RadioError as exc:
            last_error = exc
            LOG.warning(
                "KPG block 0x%04X failed: %s", address, exc
            )
            reset = getattr(radio.pipe, "reset_input_buffer", None)
            if reset is not None:
                reset()
            time.sleep(0.15)
    raise errors.RadioNoResponse(
        "Radio did not return memory at 0x%04X" % address
    ) from last_error


def _download(radio):
    image = bytearray()
    try:
        identity = _open_session(radio)
        LOG.info(
            "Kenwood %s identity: %s", radio.MODEL, identity.hex()
        )
        status = chirp_common.Status()
        status.msg = "Cloning from %s" % radio.MODEL
        status.max = (radio._memsize + BLOCK_SIZE - 1) // BLOCK_SIZE
        address = FIRST_ADDRESS
        while len(image) < radio._memsize:
            length = min(BLOCK_SIZE, radio._memsize - len(image))
            block = _read_block(radio, address, length)
            if len(block) != length:
                raise errors.RadioError(
                    "Radio returned a short block at 0x%04X" % address
                )
            image.extend(block)
            address += BLOCK_SIZE
            status.cur = len(image) // BLOCK_SIZE
            if radio.status_fn:
                radio.status_fn(status)
    finally:
        if getattr(radio, "_session_open", False):
            try:
                radio.pipe.write(b"E")
                _read_exact(radio, 1, "leaving program mode")
            except (errors.RadioError, OSError):
                LOG.debug("Radio did not acknowledge mode exit")
            finally:
                radio._session_open = False
    return memmap.MemoryMapBytes(bytes(image))


def _frequency(word, anchor):
    steps = (word - anchor) & 0xFFFF
    if steps & 0x8000:
        steps -= 0x10000
    return FREQUENCY_BASE + steps * FREQUENCY_STEP


def _channel_record(image, number):
    offset = (number - 1) * CHANNEL_SIZE
    return bytes(image[offset:offset + CHANNEL_SIZE])


def _decode_name(raw):
    value = raw.split(b"\xff", 1)[0].split(b"\x00", 1)[0]
    value = value.rstrip(b" ")
    return value.decode("ascii", "replace")


class _KenwoodKPG23Base(
    chirp_common.CloneModeRadio,
    chirp_common.ExperimentalRadio,
):
    VENDOR = "Kenwood"
    BAUD_RATE = 9600
    _memsize = IMAGE_SIZE
    _channel_count = MAX_CHANNELS
    _image_name = "KPG-23D"
    _session_open = False

    @classmethod
    def get_prompts(cls):
        prompts = chirp_common.RadioPrompts()
        prompts.experimental = (
            "%s support is experimental and read-only. NewChirp recovered "
            "the KPG-family serial session and channel records from the OEM "
            "programmer and supplied samples. The complete raw image is "
            "kept, but physical read-back and the upload map have not been "
            "validated. Uploads are disabled."
            % cls.MODEL
        )
        prompts.info = (
            "Use a Kenwood KPG-8 or KPG-22 compatible programming cable. "
            "Close the OEM CPS before starting the NewChirp read."
        )
        prompts.pre_download = (
            "1. Connect the programming cable and power the radio on.\n"
            "2. Close the OEM CPS and any other program using the port.\n"
            "3. Click OK and leave the radio powered on.\n\n"
            "Save the complete image as a backup. This driver does not "
            "write to the radio."
        )
        return prompts

    def get_features(self):
        rf = chirp_common.RadioFeatures()
        rf.memory_bounds = (1, self._channel_count)
        rf.has_bank = False
        rf.has_cross = False
        rf.has_ctone = False
        rf.has_dtcs = False
        rf.has_dtcs_polarity = False
        rf.has_name = True
        rf.has_offset = True
        rf.has_rx_dtcs = False
        rf.has_settings = False
        rf.has_tuning_step = False
        rf.valid_bands = list(VALID_BANDS)
        rf.valid_characters = VALID_CHARS
        rf.valid_duplexes = ["", "+", "-", "off"]
        rf.valid_modes = list(VALID_MODES)
        rf.valid_name_length = 4
        rf.valid_tmodes = [""]
        rf.valid_tuning_steps = []
        return rf

    def process_mmap(self):
        raw = self._mmap.get_packed()
        if len(raw) != self._memsize:
            raise errors.RadioError(
                "%s image is %i bytes; expected %i"
                % (self.MODEL, len(raw), self._memsize)
            )
        self._memobj = None

    def sync_in(self):
        try:
            self._mmap = _download(self)
            self.process_mmap()
        except errors.RadioError:
            raise
        except Exception as exc:
            LOG.exception("%s read failed", self.MODEL)
            raise errors.RadioError(
                "Failed to read the %s: %s" % (self.MODEL, exc)
            ) from exc

    def sync_out(self):
        raise errors.RadioError(
            "%s support is read-only until the OEM upload map and a "
            "controlled physical read-back are validated." % self.MODEL
        )

    def get_raw_memory(self, number):
        return _channel_record(
            self._mmap.get_packed(), number
        ).hex(" ")

    def get_memory(self, number):
        if not 1 <= number <= self._channel_count:
            raise errors.InvalidMemoryLocation(
                "%s channel must be between 1 and %i"
                % (self.MODEL, self._channel_count)
            )
        record = _channel_record(self._mmap.get_packed(), number)
        memory = chirp_common.Memory()
        memory.number = number
        if record == b"\xff" * CHANNEL_SIZE:
            memory.empty = True
            return memory

        rx_word = record[0] | (record[1] << 8)
        tx_word = record[2] | (record[3] << 8)
        memory.freq = _frequency(rx_word, RX_BASE_450)
        if not any(
            low <= memory.freq < high for low, high in VALID_BANDS
        ):
            memory.empty = True
            LOG.info(
                "%s channel %i has an unsupported frequency %i",
                self.MODEL,
                number,
                memory.freq,
            )
            return memory

        tx_frequency = _frequency(tx_word, TX_BASE_450)
        offset = tx_frequency - memory.freq
        if offset > 0:
            memory.duplex = "+"
            memory.offset = offset
        elif offset < 0:
            memory.duplex = "-"
            memory.offset = abs(offset)
        else:
            memory.duplex = ""
            memory.offset = 0
        memory.name = _decode_name(record[8:12])
        memory.mode = "NFM"
        return memory

    def set_memory(self, memory):
        raise errors.RadioError(
            "%s channel writes are disabled in the experimental read-only "
            "driver." % self.MODEL
        )


@directory.register
class KenwoodTK350Radio(_KenwoodKPG23Base):
    """Kenwood TK-350 stored by the Kenwood KPG-23D programmer."""

    MODEL = "TK-350"


@directory.register
class KenwoodTK359Radio(_KenwoodKPG23Base):
    """Kenwood TK-359 stored by the Kenwood KPG-32D programmer."""

    MODEL = "TK-359"
    _memsize = 0x53FF
    _channel_count = 250
    _image_name = "KPG-32D"
