# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Experimental read-only Kenwood TK-3401D dPMR446 driver.

The clone transport was recovered from Kenwood KPG-171D 1.10.1.0.
The radio uses the command/acknowledgement family shared with Kenwood's
NX-x00 programmers, but it transfers 128-byte addressed blocks and has
not yet had its codeplug offsets confirmed against a physical image.

This driver deliberately does not write. Until the channel and digital
mode records are confirmed, uploads would be unsafe.
"""

import collections
import logging
import struct
import time

from chirp import chirp_common
from chirp import directory
from chirp import errors
from chirp import memmap
from chirp.drivers import nx800


LOG = logging.getLogger(__name__)

MODEL_IDS = (
    b"PTK 3401",
    b"PTK-3401",
    b"PTKS3401",
)
MODEL_ID = MODEL_IDS[0]
MEM_SIZE = 0x10000
READ_BLOCK_SIZE = 0x80
ACK = b"\x06"
PROGRAM = b"PROGRAM"
PMR446_MIN = 446_000_000
PMR446_MAX = 446_200_000
PMR446_STEP = 6_250
POWER_LEVELS = [chirp_common.PowerLevel("Low", watts=0.5)]


def _read_exact(radio, count, context):
    data = bytearray()
    deadline = time.monotonic() + 2
    while len(data) < count and time.monotonic() < deadline:
        chunk = radio.pipe.read(count - len(data))
        if chunk:
            data.extend(chunk)
        elif not data:
            time.sleep(0.01)
    if len(data) != count:
        raise errors.RadioNoResponse(
            "Radio returned %i of %i bytes while %s"
            % (len(data), count, context)
        )
    return bytes(data)


def _read_xor(radio, count, context):
    data = _read_exact(radio, count, context)
    return bytes(value ^ radio._wire_xor_key for value in data)


def _send_xor(radio, data):
    radio.pipe.write(
        bytes(value ^ radio._wire_xor_key for value in bytes(data))
    )


def _exchange_ack(radio, context):
    _send_xor(radio, ACK)
    ack = _read_xor(radio, 1, context)
    if ack != ACK:
        raise errors.RadioError(
            "Radio rejected %s; response was %s"
            % (context, ack.hex() or "empty")
        )


def _identify(radio):
    radio.pipe.baudrate = 9600
    radio.pipe.stopbits = 2
    radio.pipe.timeout = 1

    radio.pipe.write(PROGRAM)
    response = _read_exact(radio, 1, "starting program mode")
    if response == b"\x16":
        radio.pipe.baudrate = 19200
        ready = _read_exact(radio, 1, "switching to 19200 baud")
        if ready != ACK:
            raise errors.RadioError(
                "Radio did not acknowledge 19200 baud programming mode"
            )
    elif response != ACK:
        raise errors.RadioError(
            "Radio did not enter programming mode; response was %s"
            % response.hex()
        )

    # KPG-171D reads a 48-byte identity record after command 0x02.
    radio.pipe.write(b"\x02")
    identity = _read_exact(radio, 48, "reading radio identity")
    if not any(model_id in identity[:16] for model_id in MODEL_IDS):
        model = identity[:16].rstrip(b"\x00\xff ")
        raise errors.RadioError(
            "Unsupported Kenwood model %r; expected TK-3401D"
            % model
        )

    # The CPS accepts a zero-key session. In its no-encryption mode it
    # sends the checksum of identity bytes 0x20 through 0x2b, then a
    # normal acknowledgement. All following traffic then uses XOR key 0.
    checksum = sum(identity[0x20:0x2C]) & 0xFF
    radio.pipe.write(bytes((checksum,)))
    _exchange_ack(radio, "enabling the programming session")
    radio._wire_xor_key = 0
    return identity


def _read_block(radio, address):
    request = struct.pack(
        ">BBBB", 0x52, address >> 8, address & 0xFF, READ_BLOCK_SIZE
    )
    _send_xor(radio, request)
    status = _read_xor(radio, 1, "reading memory at 0x%04X" % address)
    if status == b"Z":
        payload = bytes((0xFF,)) * READ_BLOCK_SIZE
    elif status == b"W":
        # KPG-171D reads a three-byte response header followed by the
        # 128 data bytes.
        response = _read_xor(
            radio,
            0x83,
            "reading memory data at 0x%04X" % address,
        )
        payload = response[3:3 + READ_BLOCK_SIZE]
    else:
        raise errors.RadioError(
            "Radio returned unexpected read status %s at 0x%04X"
            % (status.hex(), address)
        )
    _exchange_ack(radio, "acknowledging memory at 0x%04X" % address)
    return payload


def _download(radio):
    try:
        identity = _identify(radio)
        LOG.info("Kenwood TK-3401D identity: %s", identity.hex())
        image = bytearray(b"\xFF" * MEM_SIZE)
        status = chirp_common.Status()
        status.msg = "Cloning from radio"
        status.max = MEM_SIZE
        for address in range(0, MEM_SIZE, READ_BLOCK_SIZE):
            image[address:address + READ_BLOCK_SIZE] = _read_block(
                radio, address
            )
            if radio.status_fn:
                status.cur = address + READ_BLOCK_SIZE
                radio.status_fn(status)
    finally:
        try:
            _send_xor(radio, b"E")
            _read_xor(radio, 1, "leaving program mode")
        except errors.RadioError:
            LOG.debug("Radio did not acknowledge program-mode exit")
    return memmap.MemoryMapBytes(bytes(image))


def _decode_bcd(raw, little):
    value = 0
    digits = []
    ordered = reversed(raw) if little else raw
    for byte in ordered:
        high = byte >> 4
        low = byte & 0x0F
        if high > 9 or low > 9:
            return None
        digits.extend((high, low))
    for digit in digits:
        value = value * 10 + digit
    return value


def _frequency_candidates(data):
    """Return frequency fields grouped by their wire representation."""
    candidates = collections.defaultdict(list)
    for offset in range(0, len(data) - 4):
        raw = data[offset:offset + 4]
        values = {
            "u32-le": int.from_bytes(raw, "little"),
            "u32-be": int.from_bytes(raw, "big"),
            "u32x10-le": int.from_bytes(raw, "little") * 10,
            "u32x10-be": int.from_bytes(raw, "big") * 10,
            "bcd-be": _decode_bcd(raw, False),
            "bcd-le": _decode_bcd(raw, True),
        }
        for encoding, frequency in values.items():
            if frequency is None:
                continue
            if (
                PMR446_MIN <= frequency <= PMR446_MAX
                and frequency % PMR446_STEP == 0
            ):
                candidates[encoding].append((offset, frequency))
    return candidates


def _cluster(candidates, distance=32):
    clusters = []
    for candidate in candidates:
        if not clusters or candidate[0] - clusters[-1][-1][0] > distance:
            clusters.append([candidate])
        else:
            clusters[-1].append(candidate)
    return clusters


def _decode_text(raw):
    raw = raw.split(b"\x00", 1)[0].split(b"\xff", 1)[0].rstrip()
    if not raw:
        return ""
    for encoding in ("shift_jis", "ascii"):
        try:
            value = raw.decode(encoding)
        except UnicodeDecodeError:
            continue
        if all(character.isprintable() or character == " "
               for character in value):
            return value.strip()
    return ""


def _nearest_name(data, offset):
    choices = []
    for start in range(max(0, offset - 24), min(len(data), offset + 33)):
        for length in (8, 10, 12, 14, 16):
            if start + length > len(data):
                continue
            value = _decode_text(data[start:start + length])
            if len(value) < 3:
                continue
            alphanumeric = sum(
                character.isalnum() for character in value
            )
            score = alphanumeric * 3 + len(value)
            choices.append((score, start, value))
    if not choices:
        return ""
    return max(choices)[2]


def _scan_channels(data):
    """Find PMR446 channel records when the exact vendor map is unknown."""
    candidates = _frequency_candidates(data)
    options = []
    for encoding, values in candidates.items():
        clusters = _cluster(values)
        if not clusters:
            continue
        # Prefer the representation that most closely accounts for the
        # radio's 32 channel slots without selecting arbitrary duplicates.
        score = abs(len(clusters) - 32)
        options.append((score, -len(clusters), encoding, clusters))
    if not options:
        return []

    _score, _negative_count, encoding, clusters = min(options)
    LOG.warning(
        "TK-3401D codeplug layout not confirmed; using %s inference for %i "
        "PMR446 records",
        encoding,
        len(clusters),
    )
    records = []
    for cluster in clusters[:32]:
        offset, frequency = cluster[0]
        records.append({
            "offset": offset,
            "freq": frequency,
            "name": _nearest_name(data, offset),
        })
    return records


@directory.register
class KenwoodTK3401DRadio(
    nx800.KenwoodNXx00Radio,
    chirp_common.ExperimentalRadio,
):
    """Kenwood TK-3401D dPMR446/analogue PMR446 radio."""

    VENDOR = "Kenwood"
    MODEL = "TK-3401D"
    VALID_BANDS = [(PMR446_MIN, PMR446_MAX)]
    _model = MODEL_ID
    _memsize = MEM_SIZE
    _scan_records = None
    _wire_xor_key = 0

    @classmethod
    def get_prompts(cls):
        prompts = chirp_common.RadioPrompts()
        prompts.experimental = (
            "TK-3401D support is experimental and read-only. The KPG-171D "
            "clone transport and addressed-memory protocol have been "
            "recovered, but the 32-channel analogue/dPMR codeplug map has "
            "not yet been confirmed on physical hardware. NewChirp will "
            "scan the downloaded image for PMR446 channel records and keep "
            "the complete raw image. Upload is disabled."
        )
        prompts.pre_download = (
            "1. Turn the radio on and connect the programming cable.\n"
            "2. Close KPG-171D and any other program using the port.\n"
            "3. Start the download and leave the radio powered on.\n\n"
            "Save the complete downloaded image as a backup. This driver "
            "does not write to the radio."
        )
        return prompts

    def sync_in(self):
        try:
            self._mmap = _download(self)
            self.process_mmap()
        except errors.RadioError:
            raise
        except Exception as exc:
            LOG.exception("TK-3401D download failed")
            raise errors.RadioError(
                "Failed to download from the TK-3401D: %s" % exc
            )

    def sync_out(self):
        raise errors.RadioError(
            "TK-3401D support is read-only until the codeplug map and "
            "upload behavior are validated on physical hardware."
        )

    def process_mmap(self):
        self._scan_records = None
        try:
            super().process_mmap()
            if getattr(self, "_zones", None):
                return
        except Exception as exc:
            LOG.info("TK-3401D NX-x00 layout probe failed: %s", exc)

        self._zones = []
        self._channel_map = []
        self._scan_records = _scan_channels(self._mmap.get_packed())
        if not self._scan_records:
            raise errors.RadioError(
                "Downloaded image contains no recognizable PMR446 channel "
                "records. Keep the saved image for driver analysis."
            )

    def get_sub_devices(self):
        if self._scan_records is not None or not getattr(self, "_zones", None):
            return []
        return super().get_sub_devices()

    def get_features(self):
        if self._scan_records is None:
            return super().get_features()
        rf = chirp_common.RadioFeatures()
        rf.memory_bounds = (1, len(self._scan_records))
        rf.has_name = True
        rf.has_settings = False
        rf.has_bank = False
        rf.has_ctone = False
        rf.has_rx_dtcs = False
        rf.has_tuning_step = False
        rf.has_cross = False
        rf.can_odd_split = False
        rf.valid_bands = self.VALID_BANDS
        rf.valid_modes = ["FM", "NFM"]
        rf.valid_tmodes = [""]
        rf.valid_duplexes = ["", "-", "+"]
        rf.valid_power_levels = list(POWER_LEVELS)
        rf.valid_name_length = 16
        return rf

    def get_memory(self, number):
        if self._scan_records is None:
            return super().get_memory(number)
        if number < 1 or number > len(self._scan_records):
            raise errors.InvalidMemoryLocation(
                "Channel number must be between 1 and %i"
                % len(self._scan_records)
            )
        record = self._scan_records[number - 1]
        memory = chirp_common.Memory(number)
        memory.freq = record["freq"]
        memory.name = record["name"]
        memory.mode = "FM"
        memory.power = POWER_LEVELS[0]
        return memory

    def get_raw_memory(self, number):
        if self._scan_records is None:
            return super().get_raw_memory(number)
        if number < 1 or number > len(self._scan_records):
            raise errors.InvalidMemoryLocation(
                "Channel number must be between 1 and %i"
                % len(self._scan_records)
            )
        record = self._scan_records[number - 1]
        start = max(0, record["offset"] - 32)
        stop = min(len(self._mmap), record["offset"] + 64)
        return self._mmap.get(start, stop - start).hex()

    def set_memory(self, memory):
        raise errors.RadioError(
            "TK-3401D writes are disabled until the codeplug map is validated."
        )

    @classmethod
    def match_model(cls, filedata, filename):
        return False
