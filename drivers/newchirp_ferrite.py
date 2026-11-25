# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Experimental channel programming for RT-950 Pro radios running Ferrite.

Ferrite (https://github.com/FerriteFW/ferrite) is replacement firmware for
the Radtel RT-950 Pro. Unlike stock or nicFW950 it is not programmed by
copying flash blocks: the PC speaks Ferrite's link protocol and the radio
reads, checks and stores each channel record itself.

Written from the published specification only (FerriteFW/docs, manual
appendix G "Link protocol", protocol 1, and chapter 10 for channel rules),
read 2026-11-24 at docs 7dcbe19. No Ferrite code is used.

Wire summary (cable, 115200 8N1):

* A frame is COBS(type, seq, payload, CRC-16/CCITT-FALSE little-endian)
  followed by 0x00. The PC first sends 0x03 (ends a terminal session) and
  then 0x00, which hands the cable to the link (TERM-2).
* Every request is answered with ``type | 0x80``, the same seq, and a
  payload starting with a status byte.
* ``HELLO`` (0x01) checks the protocol number (1) and the chip's layout (3).
* ``READ_MANY`` (0x17) lists held channel (what 2) and zone (what 3)
  records; ``WRITE_MANY`` (0x18) writes channel records, an empty record
  deleting one. ``BEGIN``/``END`` frame the radio's progress screen.

The image is NewChirp's own container: a header, one slot per channel and
zone holding a "held" flag and the record exactly as the link gives it, then
a second copy of the channel slots as they were read (the baseline). Uploads
send only channels that differ from the baseline, after checking that each
is still on the radio as it was read, so a saved image written later, or by
the Web Programmer, gets the same check. A successful write moves the
baseline forward.
"""

import logging
import struct
import time

from chirp import chirp_common, directory, errors, memmap
from chirp.settings import (
    RadioSetting,
    RadioSettingValueBoolean,
    RadioSettingValueList,
)

LOG = logging.getLogger(__name__)

BAUD = 115200
PROTOCOL = 1
LAYOUT = 3
CLIENT_NAME = b"NewChirp"

# Frame types (appendix G).
HELLO = 0x01
BEGIN = 0x13
END = 0x14
READ_MANY = 0x17
WRITE_MANY = 0x18

WHAT_CHANNEL = 2
WHAT_ZONE = 3

STATUS_TEXT = {
    1: "the radio could not read NewChirp's request (bad frame)",
    2: "this Ferrite version does not know the request",
    3: "the radio refused a request argument",
    4: "the radio refuses this over the link",
    5: "the radio's PIN lock is on",
    7: "the radio is busy (its own editor or storage)",
    8: "not found",
    9: "the radio refused the value",
    10: "cancelled on the radio",
}
STATUS_BUSY = 7
STATUS_INVALID = 9
STATUS_CANCELLED = 10

CHANNELS = 4000
ZONES = 512
NO_ZONE = 0xFFFF
CHANNEL_LEN = 41
ZONE_READ_LEN = 28
MAX_PAYLOAD = 240
NAME_LEN = 16

IMAGE_MAGIC = b"NEWCHIRP-FERRITE"
IMAGE_VERSION = 1
HEADER_SIZE = 64
FW_TEXT = 32
CHANNEL_SLOT = 1 + CHANNEL_LEN
ZONE_SLOT = 1 + ZONE_READ_LEN
CHANNEL_BASE = HEADER_SIZE
ZONE_BASE = CHANNEL_BASE + CHANNELS * CHANNEL_SLOT
BASELINE_BASE = ZONE_BASE + ZONES * ZONE_SLOT
IMAGE_SIZE = BASELINE_BASE + CHANNELS * CHANNEL_SLOT
HELD = 0x01

# Channel record (41 bytes, little-endian), as READ_MANY gives it:
# 0 number u16 (0-based), 2 zone u16 (0xFFFF none), 4 RX u32 (10 Hz),
# 8 name[16], 24 mode, 25 narrow, 26 RX tone u16, 28 TX tone u16,
# 30 offset i32 (10 Hz shift, or the TX frequency with split), 34 power,
# 35 step index, 36 squelch (0-9, 10 Global), 37 busy lockout,
# 38 bit 0 reverse / bit 1 split, 39 flags, 40 end tone and tail.
RECORD = struct.Struct("<HHI16sBBHHiBBBBBBB")

MODES = {0: "FM", 1: "NFM", 2: "AM", 3: "USB", 4: "LSB", 5: "CW",
         6: "WFM", 7: "NAM"}
MODE_IDS = {name: value for value, name in MODES.items()}
NARROW_MODES = ("NFM", "NAM")
POWERS = ["Low", "Mid", "High"]
STEPS = ["10 Hz", "50 Hz", "100 Hz", "500 Hz", "1 kHz", "2.5 kHz", "5 kHz",
         "6.25 kHz", "8.33 kHz", "10 kHz", "12.5 kHz", "25 kHz", "50 kHz",
         "100 kHz"]
STEP_12K5 = 10
SQUELCH = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "Global"]
SQ_GLOBAL = 10

FLAG_SKIP = 0x01
FLAG_APRS = 0x02
FLAG_RX_ONLY = 0x04
FLAG_HIDDEN = 0x40
FLAG_PRIORITY = 0x80

DCS_FLAG = 0x8000
DCS_INV = 0x4000
CTCSS_MIN = 600
CTCSS_MAX = 2600

# CHAN-31: other characters are stored as "-" by the radio.
NAME_CHARS = (
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    " -./_#+&()'!"
)
# CHAN-22: 0.15-64 MHz (HF), 64-630 and 756-1300 MHz.
VALID_BANDS = [(150000, 630000000), (756000000, 1300000000)]

FRAME_TIMEOUT = 2.0
BUSY_RETRIES = 20


def crc16(data):
    """CRC-16/CCITT-FALSE: poly 0x1021, init 0xFFFF, no reflection."""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte << 8
        for _bit in range(8):
            crc = ((crc << 1) ^ 0x1021) if crc & 0x8000 else crc << 1
            crc &= 0xFFFF
    return crc


def cobs_encode(data):
    out = bytearray()
    block = bytearray()
    for byte in data:
        if byte == 0:
            out.append(len(block) + 1)
            out += block
            block = bytearray()
            continue
        block.append(byte)
        if len(block) == 254:
            out.append(255)
            out += block
            block = bytearray()
    out.append(len(block) + 1)
    out += block
    return bytes(out)


def cobs_decode(data):
    out = bytearray()
    index = 0
    while index < len(data):
        code = data[index]
        if code == 0 or index + code > len(data) + (0 if code > 1 else 1):
            raise ValueError("bad COBS frame")
        out += data[index + 1:index + code]
        index += code
        if code < 255 and index < len(data):
            out.append(0)
    return bytes(out)


def encode_frame(frame_type, seq, payload=b""):
    body = bytes((frame_type, seq)) + bytes(payload)
    return cobs_encode(body + struct.pack("<H", crc16(body))) + b"\x00"


def decode_frame(raw):
    """(type, seq, payload) or None for terminal text or a damaged frame."""
    try:
        body = cobs_decode(raw)
    except ValueError:
        return None
    if len(body) < 4:
        return None
    if crc16(body[:-2]) != struct.unpack("<H", body[-2:])[0]:
        return None
    return body[0], body[1], body[2:-2]


class FerriteError(errors.RadioError):
    pass


class FerriteLink:
    """One cable session with a radio running Ferrite."""

    def __init__(self, pipe):
        self.pipe = pipe
        self.seq = 0
        self.buffer = bytearray()
        self.firmware = ""
        self.build = 0

    def _read_some(self):
        waiting = getattr(self.pipe, "in_waiting", 0) or 0
        data = self.pipe.read(max(1, min(int(waiting), 4096)))
        return bytes(data or b"")

    def _next_frame(self, deadline):
        while True:
            if b"\x00" in self.buffer:
                raw, _sep, rest = bytes(self.buffer).partition(b"\x00")
                self.buffer = bytearray(rest)
                if not raw:
                    continue
                frame = decode_frame(raw)
                if frame is not None:
                    return frame
                continue
            if time.monotonic() > deadline:
                return None
            self.buffer += self._read_some()

    def take_cable(self):
        # 0x03 closes a terminal session if one holds the cable; 0x00 then
        # gives the cable to the link (TERM-2). Terminal text is dropped.
        self.pipe.write(b"\x03")
        time.sleep(0.3)
        deadline = time.monotonic() + 0.2
        while time.monotonic() < deadline:
            if not self._read_some():
                break
        self.buffer.clear()
        self.pipe.write(b"\x00")

    def request(self, frame_type, payload=b"", timeout=FRAME_TIMEOUT):
        """Send one request; return (status, the answer after the status)."""
        self.seq = (self.seq + 1) & 0xFF
        self.pipe.write(encode_frame(frame_type, self.seq, payload))
        deadline = time.monotonic() + timeout
        while True:
            frame = self._next_frame(deadline)
            if frame is None:
                raise FerriteError(
                    "No answer from Ferrite. Check that the radio is on, "
                    "running Ferrite, and connected with the programming "
                    "cable, and that Ferrite Console is closed."
                )
            answer_type, seq, body = frame
            if answer_type == 0x51:
                continue  # an unasked event
            if answer_type != frame_type | 0x80 or seq != self.seq:
                continue
            if not body:
                raise FerriteError("Ferrite sent an empty answer")
            return body[0], body[1:]

    def ok(self, frame_type, payload=b""):
        status, rest = self.request(frame_type, payload)
        if status:
            raise FerriteError(_status_message(status, rest))
        return rest

    def hello(self):
        payload = bytes((PROTOCOL,)) + bytes(8) + CLIENT_NAME
        status, rest = self.request(HELLO, payload)
        if status:
            raise FerriteError(_status_message(status, rest))
        if not rest or rest[0] != PROTOCOL:
            raise FerriteError(
                "This radio speaks Ferrite link protocol %s; NewChirp "
                "supports protocol %d. Update Ferrite with Ferrite Console "
                "or update NewChirp."
                % (rest[0] if rest else "?", PROTOCOL)
            )
        if len(rest) < 4:
            raise FerriteError("Ferrite HELLO answer is too short")
        may_go_on = rest[2]
        length = rest[3]
        self.firmware = rest[4:4 + length].decode("ascii", "replace")
        tail = rest[4 + length:]
        if len(tail) < 4:
            raise FerriteError("Ferrite HELLO answer is too short")
        self.build = tail[0]
        chip_layout = tail[3]
        if not may_go_on:
            raise FerriteError(
                "The radio's PIN lock is on. Unlock it on the radio, then "
                "read again."
            )
        if chip_layout != LAYOUT:
            raise FerriteError(
                "This radio's data is waiting for a Ferrite update to "
                "finish (layout %d). Open Ferrite Console to complete it, "
                "then read again." % chip_layout
            )
        return self.firmware

    def read_many(self, what, count, status=None):
        """Every held record of one kind: {index: record bytes}."""
        records = {}
        first = 0
        while first < count:
            rest = self.ok(
                READ_MANY, struct.pack("<BHH", what, first, count - first)
            )
            if len(rest) < 2:
                raise FerriteError("Ferrite READ_MANY answer is too short")
            following = struct.unpack("<H", rest[:2])[0]
            body = rest[2:]
            while body:
                if len(body) < 3:
                    raise FerriteError("Ferrite record list is cut short")
                index, length = struct.unpack("<HB", body[:3])
                record = body[3:3 + length]
                if len(record) != length:
                    raise FerriteError("Ferrite record list is cut short")
                records[index] = bytes(record)
                body = body[3 + length:]
            if following == first and not rest[2:]:
                # The range is cut at the last index held (appendix G
                # READ_MANY: zones are numbered densely), so an empty answer
                # that stays put means there is nothing more to read.
                break
            if following <= first:
                raise FerriteError("Ferrite READ_MANY did not advance")
            first = following
            if status:
                status(min(first, count), count)
        return records

    def write_many(self, what, items, status=None):
        """Write (index, record) pairs in order; an empty record deletes."""
        pending = list(items)
        total = len(pending)
        busy = 0
        while pending:
            batch, size = [], 1
            for index, record in pending:
                if batch and size + 3 + len(record) > MAX_PAYLOAD:
                    break
                batch.append((index, record))
                size += 3 + len(record)
            payload = bytes((what,)) + b"".join(
                struct.pack("<HB", index, len(record)) + record
                for index, record in batch
            )
            code, rest = self.request(WRITE_MANY, payload)
            applied = rest[0] if rest else 0
            if code == 0:
                applied = len(batch)
            elif code in (STATUS_BUSY, STATUS_INVALID, STATUS_CANCELLED):
                applied = min(applied, len(batch))
            else:
                raise FerriteError(_status_message(code, rest))
            pending = pending[applied:]
            if status:
                status(total - len(pending), total)
            if code == 0:
                continue
            if code == STATUS_BUSY and busy < BUSY_RETRIES:
                busy += 1
                time.sleep(0.25)
                continue
            failed = batch[applied][0] + 1 if applied < len(batch) else None
            reason = rest[1:].decode("ascii", "replace").strip()
            message = _status_message(code, b"")
            if failed is not None:
                message = "Channel %d: %s" % (failed, reason or message)
            raise FerriteError(
                "%s. %d of %d channel changes were written before it "
                "stopped." % (message, total - len(pending), total)
            )


def _status_message(status, rest):
    text = STATUS_TEXT.get(status, "Ferrite status %d" % status)
    if status == STATUS_INVALID and rest:
        reason = bytes(rest).decode("ascii", "replace").strip()
        if reason:
            return "%s: %s" % (text, reason)
    return text


def decode_tone(word):
    """CHAN-3 tone word -> (mode, value, polarity) for split_tone_decode."""
    if not word:
        return "", None, None
    if word & DCS_FLAG:
        code = int("%o" % (word & 0x3FFF))
        return "DTCS", code, "R" if word & DCS_INV else "N"
    return "Tone", word / 10.0, None


def encode_tone(mode, value, polarity):
    if not mode:
        return 0
    if mode == "DTCS":
        word = DCS_FLAG | int(str(int(value)), 8)
        return word | (DCS_INV if polarity == "R" else 0)
    word = int(round(float(value) * 10))
    if not CTCSS_MIN <= word <= CTCSS_MAX:
        raise errors.RadioError("CTCSS tones must be 60.0 to 260.0 Hz")
    return word


def clean_name(name):
    text = (name or "")[:NAME_LEN]
    return "".join(char if char in NAME_CHARS else "-" for char in text)


def new_record(index):
    return bytearray(RECORD.pack(
        index, NO_ZONE, 0, b"", 1, 1, 0, 0, 0, 0, STEP_12K5, SQ_GLOBAL,
        0, 0, 0, 0,
    ))


def empty_image():
    image = bytearray(b"\xFF" * IMAGE_SIZE)
    image[:HEADER_SIZE] = bytes(HEADER_SIZE)
    image[:len(IMAGE_MAGIC)] = IMAGE_MAGIC
    image[16] = IMAGE_VERSION
    image[17] = PROTOCOL
    image[18] = LAYOUT
    for index in range(CHANNELS):
        image[channel_slot(index)] = 0
        image[channel_slot(index, BASELINE_BASE)] = 0
    for index in range(ZONES):
        image[ZONE_BASE + index * ZONE_SLOT] = 0
    return image


def channel_slot(index, base=CHANNEL_BASE):
    return base + index * CHANNEL_SLOT


def zone_slot(index):
    return ZONE_BASE + index * ZONE_SLOT


def build_image(firmware, build, channels, zones):
    image = empty_image()
    image[19] = build & 0xFF
    text = firmware.encode("ascii", "replace")[:FW_TEXT]
    image[24:24 + len(text)] = text
    for index, record in channels.items():
        if 0 <= index < CHANNELS and len(record) in (CHANNEL_LEN,
                                                    CHANNEL_LEN - 1):
            record = bytes(record) + bytes(CHANNEL_LEN - len(record))
            for base in (CHANNEL_BASE, BASELINE_BASE):
                offset = channel_slot(index, base)
                image[offset] = HELD
                image[offset + 1:offset + CHANNEL_SLOT] = record
    for index, record in zones.items():
        if 0 <= index < ZONES and len(record) >= 16:
            record = bytes(record[:ZONE_READ_LEN])
            record += b"\xFF" * (ZONE_READ_LEN - len(record))
            offset = zone_slot(index)
            image[offset] = HELD
            image[offset + 1:offset + ZONE_SLOT] = record
    return bytes(image)


def held_channels(image, base=CHANNEL_BASE):
    out = {}
    for index in range(CHANNELS):
        offset = channel_slot(index, base)
        if image[offset] == HELD:
            out[index] = bytes(image[offset + 1:offset + CHANNEL_SLOT])
    return out


def channel_changes(image):
    """[(index, record or b"" to delete)] that differ from the baseline."""
    before = held_channels(image, BASELINE_BASE)
    after = held_channels(image)
    changes = []
    for index in sorted(set(before) | set(after)):
        record = after.get(index)
        if record is None:
            changes.append((index, b""))
        elif before.get(index) != record:
            changes.append((index, record))
    return changes


def same_channel(radio_record, image_record):
    """Whether the radio holds this channel. Byte 40 (end tone and tail) is
    left out: a writer may omit it and the radio then keeps its own. Names
    are already limited to the radio's character set (CHAN-31)."""
    if radio_record is None or image_record is None:
        return radio_record is None and image_record is None
    return radio_record[:40] == image_record[:40]


@directory.register
class FerriteRT950ProRadio(
    chirp_common.CloneModeRadio, chirp_common.ExperimentalRadio
):
    """Radtel RT-950 Pro running Ferrite firmware."""

    VENDOR = "Radtel"
    MODEL = "RT-950 Pro"
    VARIANT = "Ferrite"
    BAUD_RATE = BAUD
    NEEDS_COMPAT_SERIAL = False
    _memsize = IMAGE_SIZE

    @classmethod
    def get_prompts(cls):
        prompts = chirp_common.RadioPrompts()
        prompts.experimental = (
            "Experimental Ferrite support, written from Ferrite's published "
            "link protocol (protocol 1). It has not yet been tested on a "
            "radio. Use only with Ferrite firmware, not stock or nicFW950."
        )
        prompts.info = (
            "For Radtel RT-950 Pro radios running Ferrite "
            "(github.com/FerriteFW). NewChirp reads and writes channels; "
            "the radio checks and stores each one itself. Zones are kept "
            "and can be chosen per channel; settings, APRS, positions and "
            "other lists stay as they are. Keep the full backup Ferrite "
            "Console made when Ferrite was installed."
        )
        prompts.pre_download = (
            "1. Turn the radio on (running Ferrite) and connect the USB "
            "programming cable.\n"
            "2. Close Ferrite Console and any terminal using the port.\n"
            "3. If the radio has a PIN lock, unlock it.\n"
            "4. Click OK. The radio shows its link screen while NewChirp "
            "reads."
        )
        prompts.pre_upload = (
            "NewChirp sends only the channels you changed, added or "
            "deleted. It first checks that each of them is still on the "
            "radio as it was read. The radio checks every channel and "
            "refuses one it can't store, naming the field."
        )
        return prompts

    @classmethod
    def match_model(cls, filedata, filename):
        data = bytes(filedata)
        return len(data) == IMAGE_SIZE and data.startswith(IMAGE_MAGIC)

    def get_features(self):
        rf = chirp_common.RadioFeatures()
        rf.memory_bounds = (1, CHANNELS)
        rf.has_bank = False
        rf.has_ctone = True
        rf.has_cross = True
        rf.has_rx_dtcs = True
        rf.has_dtcs_polarity = True
        rf.has_name = True
        rf.has_offset = True
        rf.can_odd_split = True
        rf.has_tuning_step = False
        rf.has_settings = False
        rf.has_comment = False
        rf.has_nostep_tuning = True
        rf.valid_name_length = NAME_LEN
        rf.valid_characters = NAME_CHARS
        rf.valid_modes = ["FM", "NFM", "AM", "NAM", "WFM", "USB", "LSB",
                          "CW"]
        rf.valid_tmodes = ["", "Tone", "TSQL", "DTCS", "Cross"]
        rf.valid_cross_modes = [
            "Tone->Tone", "Tone->DTCS", "DTCS->Tone", "DTCS->DTCS",
            "->Tone", "->DTCS", "Tone->", "DTCS->",
        ]
        rf.valid_duplexes = ["", "+", "-", "split", "off"]
        rf.valid_skips = ["", "S", "P"]
        rf.valid_power_levels = [
            chirp_common.PowerLevel(name) for name in POWERS
        ]
        rf.valid_dtcs_codes = list(chirp_common.ALL_DTCS_CODES)
        rf.valid_bands = list(VALID_BANDS)
        return rf

    def process_mmap(self):
        packed = self._image()
        if len(packed) != IMAGE_SIZE or not packed.startswith(IMAGE_MAGIC):
            raise errors.RadioError("This is not a NewChirp Ferrite image")

    def _image(self):
        packed = self._mmap.get_packed()
        if isinstance(packed, str):
            packed = packed.encode("latin-1")
        return packed

    def _status(self, message, current, maximum):
        status = chirp_common.Status()
        status.msg = message
        status.cur = current
        status.max = maximum
        self.status_fn(status)

    def _open(self):
        self.pipe.baudrate = BAUD
        link = FerriteLink(self.pipe)
        link.take_cable()
        link.hello()
        return link

    def sync_in(self):
        try:
            link = self._open()
            channels = link.read_many(
                WHAT_CHANNEL, CHANNELS,
                lambda cur, top: self._status(
                    "Reading Ferrite channels", cur, top),
            )
            zones = link.read_many(WHAT_ZONE, ZONES)
            self._mmap = memmap.MemoryMapBytes(
                build_image(link.firmware, link.build, channels, zones))
            self.process_mmap()
            LOG.info(
                "Ferrite %s: %d channels, %d zones",
                link.firmware, len(channels), len(zones),
            )
        except errors.RadioError:
            raise
        except Exception as exc:
            LOG.exception("Ferrite read failed")
            raise errors.RadioError("Ferrite read failed: %s" % exc)

    def sync_out(self):
        current = self._image()
        if len(current) != IMAGE_SIZE or not current.startswith(IMAGE_MAGIC):
            raise errors.RadioError("Read the radio before writing")
        changes = channel_changes(current)
        if not changes:
            return
        before = held_channels(current, BASELINE_BASE)
        try:
            link = self._open()
            pending = self._check_unchanged(link, changes, before)
            if pending:
                link.ok(BEGIN, struct.pack("<H", len(pending)))
                try:
                    link.write_many(
                        WHAT_CHANNEL, pending,
                        lambda cur, top: self._status(
                            "Writing Ferrite channels", cur, top),
                    )
                finally:
                    try:
                        link.ok(END)
                    except errors.RadioError:
                        LOG.warning("Ferrite END was not acknowledged")
                self._verify(link, pending)
            # The radio now holds this list: it is the next write's baseline.
            self._mmap.set(
                BASELINE_BASE,
                current[CHANNEL_BASE:CHANNEL_BASE + CHANNELS * CHANNEL_SLOT])
        except errors.RadioError:
            raise
        except Exception as exc:
            LOG.exception("Ferrite write failed")
            raise errors.RadioError("Ferrite write failed: %s" % exc)

    @staticmethod
    def _fetch_one(link, index):
        rest = link.ok(READ_MANY, struct.pack("<BHH", WHAT_CHANNEL, index, 1))
        body = rest[2:]
        if len(body) >= 3:
            got, length = struct.unpack("<HB", body[:3])
            if got == index:
                return bytes(body[3:3 + length])
        return None

    def _check_unchanged(self, link, changes, before):
        """Changes still to send; refuse if the radio moved on since read.

        A channel already as this image wants it (an earlier write of the
        same saved image) is skipped rather than refused.
        """
        pending = []
        for count, (index, record) in enumerate(changes, 1):
            now = self._fetch_one(link, index)
            if same_channel(now, record or None):
                pass
            elif same_channel(now, before.get(index)):
                pending.append((index, record))
            else:
                raise errors.RadioError(
                    "Channel %d changed on the radio since it was read. "
                    "Read the radio again before writing." % (index + 1)
                )
            self._status("Checking channels on the radio", count,
                         len(changes))
        return pending

    def _verify(self, link, changes):
        wrong = [
            index + 1 for index, record in changes
            if not same_channel(self._fetch_one(link, index), record or None)
        ]
        if wrong:
            raise errors.RadioError(
                "Ferrite stored different values for channel(s) %s. Read "
                "the radio again to see what it kept."
                % ", ".join(str(number) for number in wrong[:10])
            )

    def _record(self, number):
        offset = channel_slot(number - 1)
        image = self._image()
        if image[offset] != HELD:
            return None
        return bytearray(image[offset + 1:offset + CHANNEL_SLOT])

    def _zone_names(self):
        image = self._image()
        names = {}
        for index in range(ZONES):
            offset = zone_slot(index)
            if image[offset] == HELD:
                raw = image[offset + 1:offset + 1 + 16]
                name = raw.split(b"\x00")[0].decode("ascii", "replace")
                names[index] = name.strip() or "Zone %d" % (index + 1)
        return names

    def _zone_choices(self):
        names = self._zone_names()
        choices = ["(none)"]
        seen = set(choices)
        lookup = {}
        for index in sorted(names):
            label = names[index]
            if label in seen:
                label = "%s (%d)" % (label, index + 1)
            seen.add(label)
            choices.append(label)
            lookup[label] = index
        return choices, lookup

    def get_raw_memory(self, number):
        record = self._record(number)
        return record.hex(" ") if record else ""

    def get_memory(self, number):
        mem = chirp_common.Memory()
        mem.number = number
        record = self._record(number)
        if record is None:
            mem.empty = True
            return mem
        (_num, zone, rx, name, mode, _narrow, rx_tone, tx_tone, offset,
         power, step, squelch, busy, revsplit, flags,
         _tones) = RECORD.unpack(bytes(record))
        mem.freq = rx * 10
        mem.name = name.split(b"\x00")[0].decode("ascii", "replace")
        mem.mode = MODES.get(mode, "FM")
        if flags & FLAG_RX_ONLY:
            mem.duplex = "off"
            mem.offset = 0
        elif revsplit & 2:
            mem.duplex = "split"
            mem.offset = offset * 10
        elif offset:
            mem.duplex = "+" if offset > 0 else "-"
            mem.offset = abs(offset) * 10
        chirp_common.split_tone_decode(
            mem, decode_tone(tx_tone), decode_tone(rx_tone)
        )
        mem.power = chirp_common.PowerLevel(POWERS[min(power, 2)])
        if flags & FLAG_PRIORITY:
            mem.skip = "P"
        elif flags & FLAG_SKIP:
            mem.skip = "S"

        choices, lookup = self._zone_choices()
        reverse = {value: key for key, value in lookup.items()}
        current = reverse.get(zone, "(none)")
        if current not in choices:
            choices.append(current)
        mem.extra = [
            RadioSetting("zone", "Zone",
                         RadioSettingValueList(
                             choices, current_index=choices.index(current))),
            RadioSetting("squelch", "Squelch",
                         RadioSettingValueList(
                             SQUELCH,
                             current_index=min(squelch, SQ_GLOBAL))),
            RadioSetting("step", "Step",
                         RadioSettingValueList(
                             STEPS,
                             current_index=step if step < len(STEPS)
                             else STEP_12K5)),
            RadioSetting("busy", "Busy lockout",
                         RadioSettingValueBoolean(bool(busy))),
            RadioSetting("reverse", "Reverse",
                         RadioSettingValueBoolean(bool(revsplit & 1))),
            RadioSetting("aprs", "APRS",
                         RadioSettingValueBoolean(bool(flags & FLAG_APRS))),
            RadioSetting("hidden", "Hidden",
                         RadioSettingValueBoolean(
                             bool(flags & FLAG_HIDDEN))),
        ]
        return mem

    def validate_memory(self, memory):
        messages = super().validate_memory(memory)
        if memory.empty:
            return messages
        if memory.freq % 10 or memory.offset % 10:
            messages.append(chirp_common.ValidationError(
                "Ferrite stores frequencies in 10 Hz steps"))
        try:
            for tone in chirp_common.split_tone_encode(memory):
                encode_tone(*tone)
        except (errors.RadioError, ValueError) as exc:
            messages.append(chirp_common.ValidationError(str(exc)))
        return messages

    def set_memory(self, memory):
        index = memory.number - 1
        offset = channel_slot(index)
        if memory.empty:
            self._mmap.set(offset, bytes(CHANNEL_SLOT))
            return
        record = self._record(memory.number) or new_record(index)
        fields = list(RECORD.unpack(bytes(record)))
        fields[0] = index
        fields[2] = memory.freq // 10
        fields[3] = clean_name(memory.name).encode("ascii")
        mode = memory.mode if memory.mode in MODE_IDS else "FM"
        if MODE_IDS[mode] != fields[4]:
            # VFO-20: the narrow filter follows the mode. An unchanged mode
            # keeps the radio's own byte.
            fields[4] = MODE_IDS[mode]
            fields[5] = 1 if mode in NARROW_MODES else 0
        txmode, rxmode = chirp_common.split_tone_encode(memory)
        fields[6] = encode_tone(*rxmode)
        fields[7] = encode_tone(*txmode)
        flags = fields[14] & ~(FLAG_SKIP | FLAG_PRIORITY | FLAG_RX_ONLY)
        revsplit = fields[13] & ~2
        if memory.duplex == "split":
            fields[8] = memory.offset // 10
            revsplit |= 2
        elif memory.duplex in ("+", "-"):
            shift = memory.offset // 10
            fields[8] = shift if memory.duplex == "+" else -shift
        elif memory.duplex == "off":
            flags |= FLAG_RX_ONLY
            fields[8] = 0
        else:
            fields[8] = 0
        if memory.power and str(memory.power) in POWERS:
            fields[9] = POWERS.index(str(memory.power))
        if memory.skip == "S":
            flags |= FLAG_SKIP
        elif memory.skip == "P":
            flags |= FLAG_PRIORITY

        _choices, lookup = self._zone_choices()
        for setting in memory.extra or []:
            name = setting.get_name()
            value = setting.value
            if name == "zone":
                fields[1] = lookup.get(str(value), NO_ZONE)
            elif name == "squelch":
                fields[11] = SQUELCH.index(str(value))
            elif name == "step":
                fields[10] = STEPS.index(str(value))
            elif name == "busy":
                fields[12] = 1 if bool(value) else 0
            elif name == "reverse":
                revsplit = (revsplit & ~1) | (1 if bool(value) else 0)
            elif name == "aprs":
                flags = (flags & ~FLAG_APRS) | (
                    FLAG_APRS if bool(value) else 0)
            elif name == "hidden":
                flags = (flags & ~FLAG_HIDDEN) | (
                    FLAG_HIDDEN if bool(value) else 0)
        fields[13] = revsplit
        fields[14] = flags
        self._mmap.set(offset, bytes((HELD,)) + RECORD.pack(*fields))
