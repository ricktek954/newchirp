# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Experimental read-only drivers for Kenwood KPG-23D/KPG-32D radios.

Both sessions were traced from the OEM DOS programmers in QEMU (see
docs/KPG23_PROTOCOL.md).  Channel layouts were checked against files saved by
the same programmers with known frequencies typed in (2026-11-26):

- TK-350 (KPG-23D): 16-byte records from offset 0, RX/TX words in 6.25 kHz
  steps, four-character name at +8, model/band record ``P350<band>`` at
  0x0D00.
- TK-359 (KPG-32D): 32-byte records from 0x3400; each frequency is a flag
  byte (bit 7 = 6.25 kHz steps, else 5 kHz; bit 0 = step bit 16) and a
  big-endian 16-bit step count; name at +0x12.

Uploads remain disabled until a physical write/read-back is validated.
"""

from __future__ import annotations

import base64
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
IDENTITY_ATTEMPTS = 3

RX_BASE_450 = 0x4D18
TX_BASE_450 = 0x6940
FREQUENCY_BASE = 450_000_000
FREQUENCY_STEP = 6_250

# KPG-23D UHF band choices for the TK-350, keyed by the digit after "P350"
# at image offset 0x0D00 (sample.u1f = "P3501", sample.u4f = "P3504").
TK350_BANDS = {
    b"1": (450_000_000, 470_000_000),
    b"2": (470_000_000, 490_000_000),
    b"3": (490_000_000, 520_000_000),
    b"4": (400_000_000, 430_000_000),
}
TK350_MODEL_OFFSET = 0x0D00
VALID_BANDS = [(400_000_000, 520_000_000)]
# Anything decoding outside this is not a channel (erased or unknown data).
PLAUSIBLE_UHF = (300_000_000, 600_000_000)
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


def _set_line(pipe, name, value):
    try:
        setattr(pipe, name, value)
    except (AttributeError, ValueError, OSError):
        pass


def _configure_port(radio):
    pipe = radio.pipe
    pipe.baudrate = radio.BAUD_RATE
    pipe.bytesize = 8
    pipe.parity = "N"
    pipe.stopbits = radio._stop_bits
    pipe.timeout = 1
    _set_line(pipe, "rtscts", False)
    _set_line(pipe, "xonxoff", False)
    if radio._bios_lines:
        # Both OEM programmers send with PC BIOS INT 14h AH=01 and receive
        # with AH=02. An IBM-compatible BIOS raises DTR and RTS to send a
        # byte and leaves only DTR raised to receive.
        _set_line(pipe, "dtr", True)
        _set_line(pipe, "rts", False)


def _send(radio, data):
    """Write like the OEM's INT 14h loop: RTS only while transmitting."""
    pipe = radio.pipe
    if not radio._bios_lines:
        pipe.write(data)
        return
    _set_line(pipe, "rts", True)
    try:
        pipe.write(data)
        flush = getattr(pipe, "flush", None)
        if flush is not None:
            flush()
    finally:
        _set_line(pipe, "rts", False)


def _open_session(radio):
    pipe = radio.pipe
    _configure_port(radio)

    reset = getattr(pipe, "reset_input_buffer", None)
    if reset is not None:
        reset()

    last_error = None
    identity = None
    for attempt in range(1, IDENTITY_ATTEMPTS + 1):
        _send(radio, b"\x02")
        try:
            identity = _read_exact(
                radio,
                radio._identity_length,
                "reading the radio identity",
            )
            break
        except errors.RadioError as exc:
            last_error = exc
            LOG.warning(
                "Kenwood %s identity attempt %i/%i failed: %s",
                radio.MODEL,
                attempt,
                IDENTITY_ATTEMPTS,
                exc,
            )
            if attempt < IDENTITY_ATTEMPTS:
                if reset is not None:
                    reset()
                time.sleep(0.15)
    if identity is None:
        raise errors.RadioNoResponse(
            "Kenwood %s returned no identity after %i attempts; last result: %s"
            % (radio.MODEL, IDENTITY_ATTEMPTS, last_error)
        )
    if radio._identity_checked and not _identity_matches(
            identity, radio.MODEL
    ):
        raise errors.RadioError(
            "Connected Kenwood is not recognized as a %s: %s"
            % (radio.MODEL, identity.hex())
        )

    # KPG-23D acknowledges the identity and immediately begins addressed
    # reads.  It does not send the later NX-series checksum setup command.
    _send(radio, ACK)
    radio._session_open = True
    try:
        response = _read_exact(radio, 1, "acknowledging the radio identity",
                               timeout=0.2)
    except errors.RadioNoResponse:
        response = b""
    radio._identity_ack = response
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
    _send(radio, ACK)
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
            _send(
                radio,
                READ_REQUEST
                + struct.pack(">H", address)
                + bytes((length,)),
            )
            status = _read_exact(
                radio, 1, "reading memory status at 0x%04X" % address
            )
            if status == FILL_DATA and radio._fill_reply:
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
    if radio._protocol == "kpg32":
        return _kpg32_download(radio)
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
        if getattr(radio, "_session_open", False) and not radio._exit_command:
            radio._session_open = False
        if getattr(radio, "_session_open", False):
            try:
                _send(radio, radio._exit_command)
                _read_exact(radio, 1, "leaving program mode")
            except (errors.RadioError, OSError):
                LOG.debug("Radio did not acknowledge mode exit")
            finally:
                radio._session_open = False
    return memmap.MemoryMapBytes(bytes(image))


# ---------------------------------------------------------------------------
# KPG-32D (TK-259/TK-359) session, from KPG32D.EXE 1.00 (SHA-256
# 5c1014f201b0dbb8887a4789cd6380878482c7bca109db9695f4fe570283e7fa), traced
# in QEMU and run to "Done Reading" against a simulated radio, 2026-11-26.
# Constants at DS:0x32CA: "PROGRAM", 02, 'S', 'X', 15, 06, 80, 'E', the
# INT 14h init byte E7 (9600 baud, no parity, 2 stop bits, 8 bits), and at
# DS:0x32DF 'Z', the fill reply real TK-359s send for blank blocks.
KPG32_SYNC = b"PROGRAM"
KPG32_READ = b"S"
KPG32_REPLY = b"X"
KPG32_FILL = b"Z"       # DS:0x32DF, the radio's "whole block is one value" reply
KPG32_EXIT = b"E"
KPG32_ADDRESS_BASE = 0x03AC00
KPG32_SKIP = range(0x0400, 0x0500)   # never requested by KPG-32D


def _kpg32_address(offset):
    # 03, (high + 0xAC) without carry, low  (0x162A0: ed51 = hi + 0xAC)
    return bytes((0x03, ((offset >> 8) + 0xAC) & 0xFF, offset & 0xFF))


def _kpg32_identity_ok(identity):
    """0x15F1F: the 8 bytes are compared back to front."""
    return (
        len(identity) == 8
        and identity[7:8] == b"P"
        and identity[6:7] == b"0"
        and identity[5:6] in (b"2", b"3")
        and identity[4:5] == b"5"
        and identity[3:4] == b"9"
        and identity[2:3] in (b"1", b"2")
        and identity[1] == 0x81
    )


def _kpg32_open(radio):
    _configure_port(radio)
    reset = getattr(radio.pipe, "reset_input_buffer", None)
    last_error = None
    for attempt in range(1, IDENTITY_ATTEMPTS + 1):
        if reset is not None:
            reset()
        try:
            _send(radio, KPG32_SYNC)
            if _read_exact(radio, 1, "entering program mode") != ACK:
                raise errors.RadioError("Radio refused program mode")
            _send(radio, b"\x02")
            identity = _read_exact(radio, 8, "reading the radio identity")
            break
        except errors.RadioError as exc:
            last_error = exc
            LOG.warning("Kenwood %s handshake attempt %i/%i failed: %s",
                        radio.MODEL, attempt, IDENTITY_ATTEMPTS, exc)
            time.sleep(0.15)
    else:
        raise errors.RadioNoResponse(
            "Kenwood %s returned no identity after %i attempts; last result: %s"
            % (radio.MODEL, IDENTITY_ATTEMPTS, last_error))
    radio._session_open = True
    if not _kpg32_identity_ok(identity):
        _send(radio, NAK)
        raise errors.RadioError(
            "Connected radio is not a TK-259/TK-359 (KPG-32D) radio; "
            "identity %s" % identity.hex(" "))
    model = "TK-%s59" % identity[5:6].decode("ascii")
    if model != radio.MODEL:
        _send(radio, NAK)
        raise errors.RadioError(
            "Connected radio identifies as a %s, not a %s" % (model, radio.MODEL))
    _exchange_ack(radio, "the radio identity")
    return identity


def _kpg32_read_block(radio, offset, length):
    address = _kpg32_address(offset)
    expected = KPG32_REPLY + address + bytes((length,))
    last_error = None
    for _attempt in range(3):
        try:
            _send(radio, KPG32_READ + address + bytes((length,)))
            header = _read_exact(radio, 5, "reading the block header at 0x%04X" % offset)
            if header == KPG32_FILL + expected[1:]:
                # 0x16468: Z <same address and length> + one fill byte, no
                # checksum; KPG-32D answers 06/06 and fills the whole block.
                fill = _read_exact(radio, 1, "reading the fill byte at 0x%04X" % offset)
                _exchange_ack(radio, "memory block 0x%04X" % offset)
                return fill * length
            if header != expected:
                raise errors.RadioError(
                    "Unexpected block header %s at 0x%04X" % (header.hex(" "), offset))
            data = _read_exact(radio, length + 1,
                               "reading memory at 0x%04X" % offset, timeout=3)
            payload, checksum = data[:-1], data[-1]
            if sum(payload) & 0xFF != checksum:
                # 0x16384: NAK, the radio answers ACK, then the CPS retries.
                _send(radio, NAK)
                _read_exact(radio, 1, "acknowledging a checksum retry")
                raise errors.RadioError("Checksum mismatch at 0x%04X" % offset)
            _exchange_ack(radio, "memory block 0x%04X" % offset)
            return payload
        except errors.RadioError as exc:
            last_error = exc
            LOG.warning("KPG-32D block 0x%04X failed: %s", offset, exc)
            reset = getattr(radio.pipe, "reset_input_buffer", None)
            if reset is not None:
                reset()
            time.sleep(0.15)
    raise errors.RadioNoResponse(
        "Radio did not return memory at 0x%04X" % offset) from last_error


def _kpg32_download(radio):
    image = bytearray(b"\xff" * radio._memsize)
    offsets = [offset for offset in range(0, radio._memsize, BLOCK_SIZE)
               if offset not in KPG32_SKIP]
    try:
        _kpg32_open(radio)
        status = chirp_common.Status()
        status.msg = "Cloning from %s" % radio.MODEL
        status.max = len(offsets)
        for index, offset in enumerate(offsets, 1):
            block = _kpg32_read_block(radio, offset, BLOCK_SIZE)
            end = min(offset + BLOCK_SIZE, radio._memsize)
            image[offset:end] = block[:end - offset]
            if end - offset < len(block):
                # The image is 0x53FF bytes but the radio's last block is
                # 128; keep the byte the image cannot hold for writes.
                radio._metadata["newchirp_kpg32_tail"] = block[end - offset:].hex()
            status.cur = index
            if radio.status_fn:
                radio.status_fn(status)
    finally:
        if getattr(radio, "_session_open", False):
            try:
                _send(radio, KPG32_EXIT)
                _read_exact(radio, 1, "leaving program mode")
            except (errors.RadioError, OSError):
                LOG.debug("Radio did not acknowledge mode exit")
            finally:
                radio._session_open = False
    # What the radio held when it was read: writes send only blocks that
    # differ from it (see _kpg32_upload).
    radio._metadata["newchirp_kpg32_baseline"] = base64.b64encode(
        bytes(image)).decode("ascii")
    return memmap.MemoryMapBytes(bytes(image))


# ---------------------------------------------------------------------------
# Writes, traced from both OEM programmers in QEMU on 2026-11-26 (see
# docs/KPG23_PROTOCOL.md, "Write sessions").

TK350_WRITE_SKIP = range(0xFC00, 0xFD00)   # KPG-23D never writes this
KPG32_COMMIT = b"\x03"                     # DS:0x32DE, after each X frame
WRITE_REPLY_TIMEOUT = 3


def _expect_ack(radio, context):
    reply = _read_exact(radio, 1, context, timeout=WRITE_REPLY_TIMEOUT)
    if reply != ACK:
        raise errors.RadioError(
            "Radio answered %s instead of 06 while %s; the write stopped "
            "there, as KPG-23D/KPG-32D do" % (reply.hex(), context))


def _kpg23_upload(radio):
    """KPG-23D 1.01 write: 02/identity/06/06, then W frames, no exit."""
    image = radio._mmap.get_packed()
    expected = bytes(image[TK350_MODEL_OFFSET:TK350_MODEL_OFFSET + 5])
    status = chirp_common.Status()
    status.msg = "Cloning to %s" % radio.MODEL
    blocks = [FIRST_ADDRESS + offset
              for offset in range(0, radio._memsize, BLOCK_SIZE)
              if FIRST_ADDRESS + offset not in TK350_WRITE_SKIP]
    status.max = len(blocks)
    try:
        identity = _open_session(radio)
        if radio._identity_ack != ACK:
            # KPG-23D waits for this 06 before the first W frame; a late one
            # must not be mistaken for block 0xF000's acknowledgement.
            _expect_ack(radio, "acknowledging the radio identity")
        # KPG-23D compares the identity with the file's model/band record
        # and asks before overwriting a different one; NewChirp refuses.
        if identity[:5] != expected:
            raise errors.RadioError(
                "The connected radio reports %r, but this image is for %r "
                "(model and band). Read this radio first and write that "
                "image back." % (identity[:5].decode("ascii", "replace"),
                                 expected.decode("ascii", "replace")))
        for index, address in enumerate(blocks, 1):
            offset = address - FIRST_ADDRESS
            _send(radio, READ_DATA + struct.pack(">H", address)
                  + bytes((BLOCK_SIZE,))
                  + bytes(image[offset:offset + BLOCK_SIZE]))
            _expect_ack(radio, "writing block 0x%04X" % address)
            status.cur = index
            if radio.status_fn:
                radio.status_fn(status)
    finally:
        radio._session_open = False


def _kpg32_write_block(radio, offset, block):
    address = _kpg32_address(offset)
    header = address + bytes((len(block),))
    if block == block[:1] * len(block):
        # 0x168a9: a uniform block goes as Z + header + the fill byte.
        _send(radio, KPG32_FILL + header + block[:1])
        _expect_ack(radio, "writing fill block 0x%04X" % offset)
        return
    _send(radio, KPG32_REPLY + header + block + bytes((sum(block) & 0xFF,)))
    _expect_ack(radio, "writing block 0x%04X" % offset)
    _send(radio, KPG32_COMMIT)
    _expect_ack(radio, "committing block 0x%04X" % offset)


def _kpg32_changed_blocks(radio, image):
    encoded = radio._metadata.get("newchirp_kpg32_baseline")
    if not encoded:
        raise errors.RadioError(
            "This %s image has no record of what the radio held when it was "
            "read. Read the radio with this version of NewChirp, make the "
            "changes, then write." % radio.MODEL)
    baseline = base64.b64decode(encoded)
    if len(baseline) != len(image):
        raise errors.RadioError("The saved %s read does not match this "
                                "image's size." % radio.MODEL)
    tail = bytes.fromhex(radio._metadata.get("newchirp_kpg32_tail", ""))
    changed = []
    for offset in range(0, len(image), BLOCK_SIZE):
        if offset in KPG32_SKIP:
            continue
        new = bytes(image[offset:offset + BLOCK_SIZE])
        if new == baseline[offset:offset + BLOCK_SIZE]:
            continue
        if len(new) < BLOCK_SIZE:
            if len(new) + len(tail) != BLOCK_SIZE:
                raise errors.RadioError(
                    "Block 0x%04X changed but its last byte was not kept "
                    "from the read; read the radio again." % offset)
            new += tail
        changed.append((offset, new))
    return changed


def _kpg32_upload(radio):
    """KPG-32D 1.00 write, limited to blocks changed since the read."""
    image = radio._mmap.get_packed()
    changed = _kpg32_changed_blocks(radio, image)
    if not changed:
        LOG.info("No %s blocks changed since the read; nothing to write",
                 radio.MODEL)
        return
    status = chirp_common.Status()
    status.msg = "Cloning to %s" % radio.MODEL
    status.max = len(changed)
    try:
        identity = _kpg32_open(radio)
        if identity != bytes(image[0x0500:0x0508]):
            raise errors.RadioError(
                "The connected radio's identity %s differs from the one in "
                "this image (%s). Read this radio first and write that image "
                "back." % (identity.hex(" "), image[0x0500:0x0508].hex(" ")))
        for index, (offset, block) in enumerate(changed, 1):
            _kpg32_write_block(radio, offset, block)
            status.cur = index
            if radio.status_fn:
                radio.status_fn(status)
    finally:
        if getattr(radio, "_session_open", False):
            try:
                _send(radio, KPG32_EXIT)
                _read_exact(radio, 1, "leaving program mode")
            except (errors.RadioError, OSError):
                LOG.debug("Radio did not acknowledge mode exit")
            finally:
                radio._session_open = False
    radio._metadata["newchirp_kpg32_baseline"] = base64.b64encode(
        bytes(image)).decode("ascii")


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
    value = value.strip(b" ")
    return value.decode("ascii", "replace")


class _KenwoodKPG23Base(
    chirp_common.CloneModeRadio,
    chirp_common.ExperimentalRadio,
):
    VENDOR = "Kenwood"
    BAUD_RATE = 9600
    WANTS_DTR = True
    WANTS_RTS = False
    _protocol = "kpg23"
    _stop_bits = 1
    _bios_lines = True
    _identity_length = 8
    _identity_checked = True
    _fill_reply = True
    _exit_command = b"E"
    _memsize = IMAGE_SIZE
    _channel_count = MAX_CHANNELS
    _image_name = "KPG-23D"
    _session_open = False

    @classmethod
    def get_prompts(cls):
        prompts = chirp_common.RadioPrompts()
        if getattr(cls, "NEWCHIRP_WRITE_DISABLED", False):
            prompts.experimental = (
                "%s support is experimental and read-only. NewChirp "
                "recovered the serial session and channel records from the "
                "OEM programmer; writing stays off until a write has been "
                "confirmed on a radio." % cls.MODEL)
        else:
            prompts.experimental = (
                "%s support is experimental. Reads are confirmed on an "
                "owner's radio; writing follows Kenwood's own programmer "
                "exactly but has not yet been confirmed on a radio. Only "
                "existing channels can be edited. Save a backup image before "
                "writing." % cls.MODEL)
            prompts.pre_upload = (
                "1. Read this radio first and save the image as a backup.\n"
                "2. Switch the radio off and on (it stays in programming "
                "mode after a read), with the cable connected.\n"
                "3. Close the OEM CPS and any other program using the port.\n"
                "4. Click OK and leave the radio powered on until the write "
                "finishes.")
        prompts.info = (
            "Use a Kenwood KPG-8 or KPG-22 compatible programming cable. "
            "Close the OEM CPS before starting the NewChirp read."
        )
        prompts.pre_download = (
            "1. Connect the programming cable and power the radio on.\n"
            "2. Close the OEM CPS and any other program using the port.\n"
            "3. Click OK and leave the radio powered on.\n\n"
            "Save the complete image as a backup. Switch the radio off and "
            "on before reading it again."
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
        if getattr(self, "NEWCHIRP_WRITE_DISABLED", False):
            raise errors.RadioError(
                "%s support is read-only until a write has been tested and "
                "read back on a real radio." % self.MODEL)
        try:
            if self._protocol == "kpg32":
                _kpg32_upload(self)
            else:
                _kpg23_upload(self)
        except errors.RadioError:
            raise
        except Exception as exc:
            LOG.exception("%s write failed", self.MODEL)
            raise errors.RadioError(
                "Failed to write the %s: %s" % (self.MODEL, exc)) from exc

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
        if rx_word == 0xFFFF:
            memory.empty = True
            return memory
        # The encoding is the same for every UHF band (checked against
        # KPG-23D files for 450-470 and 400-430 MHz), so channels are shown
        # whatever band the radio is.
        memory.freq = _frequency(rx_word, RX_BASE_450)
        low, high = PLAUSIBLE_UHF
        if not low <= memory.freq < high:
            memory.empty = True
            LOG.info(
                "%s channel %i decodes to %i Hz; treating it as blank",
                self.MODEL,
                number,
                memory.freq,
            )
            return memory

        if tx_word == 0xFFFF:
            # KPG-23D shows these channels with an empty Transmit column.
            memory.duplex = "off"
            memory.offset = 0
            memory.name = _decode_name(record[8:12])
            memory.mode = "NFM"
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

    def _check_edit(self, memory):
        """Only existing channels can be edited until more is traced."""
        if memory is None:
            raise errors.RadioError("%s channel edit is missing" % self.MODEL)
        current = self.get_memory(memory.number)
        if current.empty or memory.empty:
            raise errors.RadioError(
                "Adding or deleting %s channels is disabled until the CPS's "
                "channel tables are traced; edit existing channels only."
                % self.MODEL)
        return current

    @staticmethod
    def _tx_frequency(memory):
        if memory.duplex == "+":
            return memory.freq + memory.offset
        if memory.duplex == "-":
            return memory.freq - memory.offset
        if memory.duplex == "off":
            return None
        return memory.freq

    def set_memory(self, memory):
        self._check_edit(memory)
        for frequency in (memory.freq, self._tx_frequency(memory)):
            if frequency is not None and frequency % FREQUENCY_STEP:
                raise errors.RadioError(
                    "%s frequencies must be multiples of 6.25 kHz"
                    % self.MODEL)
        rx_word = (RX_BASE_450 + (memory.freq - FREQUENCY_BASE)
                   // FREQUENCY_STEP) & 0xFFFF
        tx = self._tx_frequency(memory)
        tx_word = 0xFFFF if tx is None else (
            TX_BASE_450 + (tx - FREQUENCY_BASE) // FREQUENCY_STEP) & 0xFFFF
        if _frequency(rx_word, RX_BASE_450) != memory.freq or (
                tx is not None and _frequency(tx_word, TX_BASE_450) != tx):
            raise errors.RadioError(
                "%s cannot store %i Hz" % (self.MODEL, memory.freq))
        offset = (memory.number - 1) * CHANNEL_SIZE
        self._mmap[offset] = struct.pack("<HH", rx_word, tx_word)
        # Names: four characters, space padded like KPG-23D ("CH1 ").
        name = (memory.name or "").upper()[:4].ljust(4)
        self._mmap[offset + 8] = name.encode("ascii", "replace")


@directory.register
class KenwoodTK350Radio(_KenwoodKPG23Base):
    """Kenwood TK-350 stored by the Kenwood KPG-23D programmer."""

    MODEL = "TK-350"
    # Writing enabled 2026-11-26 for a controlled owner test: reads are
    # confirmed on hardware (116/120 channels match the owner's UK plan) and
    # the write follows the traced KPG-23D session; graduate after a
    # physical write/read-back passes.
    NEWCHIRP_WRITE_DISABLED = False

    # KPG-23D 1.01 (KPG23D.EXE SHA-256 32973eac...8248) traced in QEMU with
    # serial_write/serial_read events against a simulated radio, TK-350
    # 160ch UHF selected (2026-11-26): divisor 0x18 = 4800 baud, LCR 0x07 =
    # 8N2, 0x02 answered by a 6-byte identity that is not checked, ACK
    # 06/06, 28 reads of R <hi> <lo> 80 from 0xF000 answered W <hi> <lo> 80
    # + 128 bytes with ACK 06/06 after each, and no exit command. A Z reply
    # fails the read. Bytes go through BIOS INT 14h (AH=0/1/2), so on a PC
    # DTR stays raised and RTS is raised only while sending.
    BAUD_RATE = 4800
    _stop_bits = 2
    _identity_length = 6
    _identity_checked = False
    _fill_reply = False
    _exit_command = b""


@directory.register
class KenwoodTK359Radio(_KenwoodKPG23Base):
    """Kenwood TK-359 stored by the Kenwood KPG-32D programmer."""

    MODEL = "TK-359"
    # Read-only until a physical write/read-back is validated; the app
    # explains this before a write starts (see chirp_bridge model-info).
    NEWCHIRP_WRITE_DISABLED = True
    # KPG-32D 1.00: 9600 8N2 (INT 14h init E7), PROGRAM/06, 02 -> 8-byte
    # identity checked back to front ("P0359" + band + 81), 06/06, then
    # S 03 <hi+AC> <lo> 80 -> X <same> + 128 bytes + sum8, 06/06, E/06.
    BAUD_RATE = 9600
    _protocol = "kpg32"
    _stop_bits = 2
    _memsize = 0x53FF
    _channel_count = 250
    _image_name = "KPG-32D"

    # KPG-32D channel records (checked 2026-11-26 against SAMPLE.FDT, a
    # TK-259 file showing 150/151/152 MHz, and a TK-359 450-470 MHz file
    # saved by KPG-32D with 460.0125/465.000 and 455.500/455.500 typed in):
    #   +0x02 RX flag, +0x03 RX step count (big-endian)
    #   +0x08 TX step count (big-endian), +0x0A TX flag
    #   +0x12 name
    # Flag bit 7 = 6.25 kHz steps (else 5 kHz); RX flag bit 0 = step bit 16.
    CHANNEL_BASE = 0x3400
    RECORD_SIZE = 0x20
    NAME_OFFSET = 0x12
    NAME_LENGTH = 4

    def get_features(self):
        rf = super().get_features()
        rf.valid_bands = [(406_000_000, 470_000_000)]
        return rf

    def _record(self, number):
        offset = self.CHANNEL_BASE + (number - 1) * self.RECORD_SIZE
        return bytes(self._mmap.get_packed()[offset:offset + self.RECORD_SIZE])

    def get_raw_memory(self, number):
        return self._record(number).hex(" ")

    @staticmethod
    def _kpg32_frequency(flag, word, high_bit):
        step = 6_250 if flag & 0x80 else 5_000
        steps = word | (0x10000 if high_bit else 0)
        if not high_bit and steps * step < 300_000_000:
            # UHF counts all exceed 16 bits except 406-409.6 MHz at 6.25 kHz.
            steps |= 0x10000
        return steps * step

    def get_memory(self, number):
        if not 1 <= number <= self._channel_count:
            raise errors.InvalidMemoryLocation(
                "%s channel must be between 1 and %i"
                % (self.MODEL, self._channel_count))
        record = self._record(number)
        memory = chirp_common.Memory()
        memory.number = number
        if record[2:5] == b"\xff\xff\xff":
            memory.empty = True
            return memory
        rx_flag = record[2]
        memory.freq = self._kpg32_frequency(
            rx_flag, (record[3] << 8) | record[4], rx_flag & 0x01)
        low, high = PLAUSIBLE_UHF
        if not low <= memory.freq < high:
            LOG.info("%s channel %i decodes to %i Hz; treating it as blank",
                     self.MODEL, number, memory.freq)
            memory.empty = True
            return memory
        tx_frequency = memory.freq
        if record[8:11] != b"\xff\xff\xff":
            tx_frequency = self._kpg32_frequency(
                record[10], (record[8] << 8) | record[9], False)
        offset = tx_frequency - memory.freq
        memory.duplex = "+" if offset > 0 else "-" if offset < 0 else ""
        memory.offset = abs(offset)
        raw_name = record[self.NAME_OFFSET:self.NAME_OFFSET + self.NAME_LENGTH]
        name = bytearray()
        for byte in raw_name:
            if not 0x20 <= byte < 0x7F:
                break
            name.append(byte)
        memory.name = name.decode("ascii").strip()
        memory.mode = "NFM"
        return memory

    @staticmethod
    def _kpg32_encode(frequency, flag):
        """Flag byte and big-endian step count for a frequency."""
        if frequency % 6_250 == 0:
            flag |= 0x80
            step = 6_250
        elif frequency % 5_000 == 0:
            flag &= ~0x80 & 0xFF
            step = 5_000
        else:
            raise errors.RadioError(
                "TK-359 frequencies must be multiples of 5 or 6.25 kHz")
        steps = frequency // step
        return flag, steps

    def set_memory(self, memory):
        current = self._check_edit(memory)
        if (memory.name or "").strip() != current.name:
            raise errors.RadioError(
                "Renaming TK-359 channels is disabled until the name length "
                "is confirmed on a radio; change frequencies only.")
        record = bytearray(self._record(memory.number))
        rx_flag, rx_steps = self._kpg32_encode(memory.freq, record[2])
        rx_flag = (rx_flag & 0xFE) | ((rx_steps >> 16) & 0x01)
        record[2:5] = bytes((rx_flag, (rx_steps >> 8) & 0xFF, rx_steps & 0xFF))
        tx = self._tx_frequency(memory)
        if tx is None:
            raise errors.RadioError(
                "Turning TX off on a TK-359 channel is disabled until the "
                "KPG-32D encoding for it is confirmed.")
        tx_flag, tx_steps = self._kpg32_encode(tx, record[10])
        record[8:10] = bytes(((tx_steps >> 8) & 0xFF, tx_steps & 0xFF))
        record[10] = tx_flag
        if (self._kpg32_frequency(record[2], (record[3] << 8) | record[4],
                                  record[2] & 0x01) != memory.freq or
                self._kpg32_frequency(record[10], (record[8] << 8) | record[9],
                                      False) != tx):
            raise errors.RadioError(
                "TK-359 cannot store RX %i / TX %i Hz" % (memory.freq, tx))
        offset = self.CHANNEL_BASE + (memory.number - 1) * self.RECORD_SIZE
        self._mmap[offset] = bytes(record)
