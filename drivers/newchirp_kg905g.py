# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""Wouxun KG-905G Plus experimental clone driver.

The transport, memory map, channel records, and write policy were recovered
from the official KG-905G Plus Programming Software V2.1.1 (20250514).
"""

import struct
import time

from chirp import chirp_common
from chirp import directory
from chirp import errors
from chirp import memmap


IDENT = b"B3-10"
CAPTURE_IDENT = b"KG-905G+"
MEM_SIZE = 0x4000
CHANNEL_COUNT = 400
BLOCK_SIZE = 64

SERIAL_DATA = (0x0340, 0x0440)
COMPAT_ID_DATA = (0x0040, 0x0080)
MEMORY_RANGES = (
    (0x0440, 0x04C0),  # system settings, 128 bytes
    (0x0540, 0x0550),  # VFO data, 16 bytes
    (0x05E0, 0x1EF0),  # channel records, 400 * 16 + 16 bytes
    (0x1F00, 0x2B88),  # channel names, 400 * 8 + 8 bytes
    (0x3000, 0x3191),  # channel-present flags, 400 + 1 bytes
    (0x3700, 0x3728),  # radio settings, 40 bytes
    (0x3360, 0x33DE),  # call-code data, 126 bytes
    (0x35C0, 0x3668),  # call-code names, 168 bytes
)
READ_RANGES = (SERIAL_DATA,) + MEMORY_RANGES
WRITE_RANGES = MEMORY_RANGES

MODEL_OFFSET = 0x0376
CAPTURE_MODEL_OFFSET = 0x0040
CHANNEL_BASE = 0x05E0
NAME_BASE = 0x1F00
VALID_BASE = 0x3000
VALID_FLAG = 0x9E
RECORD_SIZE = 16
NAME_LEN = 8

SEED = 0x54
REPEATER_OFFSET = 5_000_000
RF_MODES = ("FM", "NFM", "AM", "NAM")

POWER_LOW = chirp_common.PowerLevel("Low", watts=0.5)
POWER_HIGH = chirp_common.PowerLevel("High", watts=5.0)
POWER_LEVELS = [POWER_LOW, POWER_HIGH]
CHARSET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789- "

SIMPLEX_HZ = (
    462562500, 462587500, 462612500, 462637500, 462662500, 462687500,
    462712500, 462550000, 462575000, 462600000, 462625000, 462650000,
    462675000, 462700000, 462725000, 467562500, 467587500, 467612500,
    467637500, 467662500, 467687500, 467712500,
)
REPEATER_RX_HZ = (
    462550000, 462575000, 462600000, 462625000, 462650000, 462675000,
    462700000, 462725000,
)
INTERSTITIAL_HZ = (
    467562500, 467587500, 467612500, 467637500, 467662500, 467687500,
    467712500,
)


def encrypt(plain, seed=SEED):
    if not plain:
        return b""
    out = bytearray(len(plain))
    out[0] = seed ^ plain[0]
    for index in range(1, len(plain)):
        out[index] = out[index - 1] ^ plain[index]
    return bytes(out)


def decrypt(encoded, seed=SEED):
    if not encoded:
        return b""
    out = bytearray(len(encoded))
    out[0] = seed ^ encoded[0]
    for index in range(1, len(encoded)):
        out[index] = encoded[index - 1] ^ encoded[index]
    return bytes(out)


def checksum(cmd, direction, length, payload):
    total = (cmd + direction + length + sum(payload)) & 0xFF
    adjust = {0: 3, 1: 1, 2: -1, 3: -3}[(payload[0] if payload else 0) & 0x03]
    return (total + adjust) & 0xFF


def build_frame(cmd, direction, payload):
    check = checksum(cmd, direction, len(payload), payload)
    return bytes((0x7C, cmd, direction, len(payload))) + encrypt(
        payload + bytes((check,))
    )


def _decode_tone(word):
    kind = (word >> 12) & 0x0F
    low = word & 0x0FFF
    if kind == 0 or word == 0:
        return "", None, None
    if kind == 8:
        return "Tone", low / 10.0, None
    if kind in (4, 6):
        for code in chirp_common.DTCS_CODES:
            if int(str(code), 8) == low:
                return "DTCS", code, "N" if kind == 4 else "R"
    return "", None, None


def _encode_tone(mode, value, polarity):
    if not mode:
        return 0
    if mode == "Tone":
        tenths = int(round(float(value) * 10))
        if tenths <= 0 or tenths > 0x0FFF:
            raise errors.InvalidValueError("That CTCSS tone is out of range")
        return 0x8000 + tenths
    if mode == "DTCS":
        if int(value) not in chirp_common.DTCS_CODES:
            raise errors.InvalidValueError("DCS code %s is not supported" % value)
        base = 0x6000 if polarity == "R" else 0x4000
        return base + int(str(int(value)), 8)
    raise errors.InvalidValueError("Tone mode %s is not supported" % mode)


def _tones_from_memory(mem):
    tx_mode, tx_val, tx_pol = "", None, "N"
    rx_mode, rx_val, rx_pol = "", None, "N"
    if mem.tmode == "Tone":
        tx_mode, tx_val = "Tone", mem.rtone
    elif mem.tmode == "TSQL":
        tx_mode, tx_val = "Tone", mem.ctone
        rx_mode, rx_val = "Tone", mem.ctone
    elif mem.tmode == "DTCS":
        tx_pol = mem.dtcs_polarity[0] if mem.dtcs_polarity else "N"
        rx_pol = mem.dtcs_polarity[1] if mem.dtcs_polarity else "N"
        tx_mode, tx_val = "DTCS", mem.dtcs
        rx_mode, rx_val = "DTCS", mem.rx_dtcs or mem.dtcs
    elif mem.tmode == "Cross":
        left, right = (mem.cross_mode or "->").split("->")
        if left == "Tone":
            tx_mode, tx_val = "Tone", mem.rtone
        elif left == "DTCS":
            tx_pol = mem.dtcs_polarity[0] if mem.dtcs_polarity else "N"
            tx_mode, tx_val = "DTCS", mem.dtcs
        if right == "Tone":
            rx_mode, rx_val = "Tone", mem.ctone
        elif right == "DTCS":
            rx_pol = mem.dtcs_polarity[1] if mem.dtcs_polarity else "N"
            rx_mode, rx_val = "DTCS", mem.rx_dtcs or mem.dtcs
    elif mem.tmode:
        raise errors.InvalidValueError("Tone mode %s is not supported" % mem.tmode)
    return (
        _encode_tone(tx_mode, tx_val, tx_pol),
        _encode_tone(rx_mode, rx_val, rx_pol),
    )


def _apply_tones(mem, rx_word, tx_word):
    rx_mode, rx_val, rx_pol = _decode_tone(rx_word)
    tx_mode, tx_val, tx_pol = _decode_tone(tx_word)
    mem.tmode = ""
    mem.cross_mode = "Tone->Tone"
    mem.dtcs_polarity = "NN"
    if tx_mode == "Tone" and not rx_mode:
        mem.tmode = "Tone"
        mem.rtone = tx_val
    elif tx_mode == "Tone" and rx_mode == "Tone" and tx_val == rx_val:
        mem.tmode = "TSQL"
        mem.rtone = tx_val
        mem.ctone = rx_val
    elif (
        tx_mode == "DTCS"
        and rx_mode == "DTCS"
        and tx_val == rx_val
        and tx_pol == rx_pol
    ):
        mem.tmode = "DTCS"
        mem.dtcs = tx_val
        mem.rx_dtcs = rx_val
        mem.dtcs_polarity = tx_pol + rx_pol
    elif tx_mode or rx_mode:
        mem.tmode = "Cross"
        mem.cross_mode = "%s->%s" % (tx_mode, rx_mode)
        if tx_mode == "Tone":
            mem.rtone = tx_val
        if rx_mode == "Tone":
            mem.ctone = rx_val
        if tx_mode == "DTCS":
            mem.dtcs = tx_val
        if rx_mode == "DTCS":
            mem.rx_dtcs = rx_val
        mem.dtcs_polarity = (tx_pol or "N") + (rx_pol or "N")


def _tx_hz(mem):
    freq = int(mem.freq)
    if mem.duplex in ("", " "):
        if freq not in SIMPLEX_HZ:
            raise errors.InvalidValueError(
                "Simplex must be a GMRS channel frequency"
            )
        if int(mem.offset or 0) != 0:
            raise errors.InvalidValueError("Simplex offset must be 0")
        return freq
    if mem.duplex == "+":
        if freq not in REPEATER_RX_HZ:
            raise errors.InvalidValueError(
                "A repeater must use a GMRS repeater output"
            )
        if int(mem.offset) != REPEATER_OFFSET:
            raise errors.InvalidValueError("Repeater offset must be +5 MHz")
        return freq + REPEATER_OFFSET
    raise errors.InvalidValueError(
        "This radio accepts simplex or a +5 MHz GMRS repeater"
    )


def _identity_matches(image):
    model = image[MODEL_OFFSET:MODEL_OFFSET + 16].rstrip(b"\x00 ")
    capture_model = image[
        CAPTURE_MODEL_OFFSET:CAPTURE_MODEL_OFFSET + len(CAPTURE_IDENT)
    ]
    return model.startswith(IDENT) or capture_model == CAPTURE_IDENT


@directory.register
class KG905GPlusRadio(
    chirp_common.CloneModeRadio,
    chirp_common.ExperimentalRadio,
):
    """Wouxun KG-905G Plus."""

    VENDOR = "Wouxun"
    MODEL = "KG-905G Plus"
    BAUD_RATE = 19200
    NEEDS_COMPAT_SERIAL = False
    WANTS_DTR = True
    WANTS_RTS = True
    _memsize = MEM_SIZE

    @classmethod
    def get_prompts(cls):
        prompts = chirp_common.RadioPrompts()
        prompts.experimental = (
            "The KG-905G Plus driver is experimental. The protocol and memory "
            "map were recovered from the official Wouxun Programming Software "
            "V2.1.1. Read the radio and save an unedited backup before writing."
        )
        prompts.info = (
            "Use a Wouxun K-plug programming cable. The link is 19200 baud, "
            "8 data bits, no parity, and one stop bit. All 400 channel slots "
            "are supported. Radio-wide settings are preserved."
        )
        prompts.pre_download = (
            "1. Power on the KG-905G Plus.\n"
            "2. Plug in the programming cable.\n"
            "3. Close the Wouxun program so it releases the port.\n"
            "4. Click OK to download."
        )
        prompts.pre_upload = (
            "Make a backup with the Wouxun program before uploading. NewChirp "
            "writes only the program-data regions used by the official CPS; "
            "the model and firmware information region is read-only."
        )
        return prompts

    @classmethod
    def match_model(cls, filedata, filename):
        return len(filedata) == MEM_SIZE and _identity_matches(filedata)

    def get_features(self):
        rf = chirp_common.RadioFeatures()
        rf.has_bank = False
        rf.has_settings = False
        rf.has_name = True
        rf.has_tuning_step = False
        rf.has_nostep_tuning = True
        rf.has_rx_dtcs = True
        rf.has_ctone = True
        rf.has_cross = True
        rf.can_odd_split = False
        rf.memory_bounds = (1, CHANNEL_COUNT)
        rf.valid_bands = [
            (462550000, 462725001),
            (467550000, 467725001),
        ]
        rf.valid_modes = list(RF_MODES)
        rf.valid_power_levels = list(POWER_LEVELS)
        rf.valid_tuning_steps = [12.5]
        rf.valid_duplexes = ["", "+"]
        rf.valid_tmodes = ["", "Tone", "TSQL", "DTCS", "Cross"]
        rf.valid_cross_modes = list(chirp_common.CROSS_MODES)
        rf.valid_skips = ["", "S"]
        rf.valid_dtcs_codes = list(chirp_common.DTCS_CODES)
        rf.valid_dtcs_pols = ["NN", "NR", "RN", "RR"]
        rf.valid_characters = CHARSET
        rf.valid_name_length = NAME_LEN
        return rf

    def process_mmap(self):
        self._validated_image()

    def sync_in(self):
        try:
            self._prepare_port()
            self._mmap = memmap.MemoryMapBytes(self._download())
        except (errors.RadioError, errors.InvalidDataError):
            raise
        except Exception as exc:
            raise errors.RadioError(
                "Failed to communicate with the KG-905G Plus: %s" % exc
            ) from exc
        self.process_mmap()

    def sync_out(self):
        try:
            self._upload()
        except (errors.RadioError, errors.InvalidDataError):
            raise
        except Exception as exc:
            raise errors.RadioError(
                "Failed to communicate with the KG-905G Plus: %s" % exc
            ) from exc

    def _number(self, number):
        if not 1 <= int(number) <= CHANNEL_COUNT:
            raise errors.InvalidValueError(
                "Memory %s is outside 1-%i" % (number, CHANNEL_COUNT)
            )
        return int(number)

    def _packed(self):
        if self._mmap is None:
            raise errors.RadioError("Download from the radio before editing")
        return self._mmap.get_packed()

    def _record_offset(self, number):
        return CHANNEL_BASE + self._number(number) * RECORD_SIZE

    def _name_offset(self, number):
        return NAME_BASE + self._number(number) * NAME_LEN

    def _valid_offset(self, number):
        return VALID_BASE + self._number(number)

    def get_raw_memory(self, number):
        raw = self._packed()[self._record_offset(number):]
        return repr(raw[:RECORD_SIZE])

    def get_memory(self, number):
        self._number(number)
        raw = self._packed()
        offset = self._record_offset(number)
        record = raw[offset:offset + RECORD_SIZE]
        mem = chirp_common.Memory()
        mem.number = number
        if raw[self._valid_offset(number)] == 0:
            mem.empty = True
            return mem
        rx, tx, rx_tone, tx_tone = struct.unpack_from("<IIHH", record)
        if rx in (0, 0xFFFFFFFF):
            mem.empty = True
            return mem
        mem.freq = rx * 10
        if tx == rx:
            mem.duplex = ""
            mem.offset = 0
        elif tx == rx + REPEATER_OFFSET // 10 and mem.freq in REPEATER_RX_HZ:
            mem.duplex = "+"
            mem.offset = REPEATER_OFFSET
        elif tx not in (0, 0xFFFFFFFF):
            mem.duplex = "split"
            mem.offset = tx * 10
        else:
            mem.duplex = ""
            mem.offset = 0
        power = record[12] & 0x03
        mem.power = POWER_LOW if power == 0 else POWER_HIGH
        am = bool((record[12] >> 2) & 0x03)
        wide = bool(record[13] & 0x01)
        if am:
            mem.mode = "AM" if wide else "NAM"
        else:
            mem.mode = "FM" if wide else "NFM"
        mem.skip = "" if record[13] & 0x20 else "S"
        _apply_tones(mem, rx_tone, tx_tone)
        name = raw[self._name_offset(number):self._name_offset(number) + NAME_LEN]
        mem.name = name.split(b"\x00", 1)[0].decode("ascii", "replace").rstrip()
        return mem

    def set_memory(self, mem):
        self._number(mem.number)
        raw = bytearray(self._packed())
        offset = self._record_offset(mem.number)
        name_offset = self._name_offset(mem.number)
        valid_offset = self._valid_offset(mem.number)
        if mem.empty or not mem.freq:
            raw[offset:offset + RECORD_SIZE] = bytes(RECORD_SIZE)
            raw[name_offset:name_offset + NAME_LEN] = bytes(NAME_LEN)
            raw[valid_offset] = 0
            self._mmap = memmap.MemoryMapBytes(bytes(raw))
            return
        tx_hz = _tx_hz(mem)
        rx_hz = int(mem.freq)
        if mem.mode not in RF_MODES:
            raise errors.InvalidValueError(
                "Mode must be FM, NFM, AM, or NAM"
            )
        am = mem.mode in ("AM", "NAM")
        wide = mem.mode in ("FM", "AM")
        power = 0 if mem.power == POWER_LOW else 1
        if rx_hz in INTERSTITIAL_HZ:
            wide = False
            power = 0
        scan = mem.skip != "S"
        tx_tone, rx_tone = _tones_from_memory(mem)
        current = bytearray(raw[offset:offset + RECORD_SIZE])
        if current == bytes(RECORD_SIZE):
            current = bytearray(bytes.fromhex("00000000000000000000000001010100"))
        struct.pack_into(
            "<IIHH",
            current,
            0,
            rx_hz // 10,
            tx_hz // 10,
            rx_tone,
            tx_tone,
        )
        current[12] = (current[12] & ~0x07) | power | (0x04 if am else 0)
        flags = current[13] & ~0x21
        if wide:
            flags |= 0x01
        if scan:
            flags |= 0x20
        current[13] = flags
        if current[14] == 0:
            current[14] = 1
        raw[offset:offset + RECORD_SIZE] = current
        raw[name_offset:name_offset + NAME_LEN] = self._name_bytes(
            mem.name,
            bytes(raw[name_offset:name_offset + NAME_LEN]),
        )
        raw[valid_offset] = VALID_FLAG
        self._mmap = memmap.MemoryMapBytes(bytes(raw))

    def _name_bytes(self, name, previous):
        text = "" if name is None else str(name)
        try:
            encoded = text.encode("ascii")
        except UnicodeEncodeError as exc:
            raise errors.InvalidValueError(
                "Channel name must be plain text"
            ) from exc
        if len(encoded) > NAME_LEN:
            raise errors.InvalidValueError(
                "Channel name is limited to %i characters" % NAME_LEN
            )
        if any(chr(byte) not in CHARSET for byte in encoded):
            raise errors.InvalidValueError(
                "Channel name has a character this radio does not store"
            )
        stored = previous.split(b"\x00", 1)[0].decode("ascii", "replace").rstrip()
        if stored == text:
            return previous
        return encoded.ljust(NAME_LEN, b"\x00")

    def _prepare_port(self):
        self.pipe.baudrate = self.BAUD_RATE
        self.pipe.timeout = 2
        try:
            self.pipe.dtr = True
            self.pipe.rts = True
        except Exception:
            pass
        reset = getattr(self.pipe, "reset_input_buffer", None)
        if reset:
            reset()
        time.sleep(0.2)

    def _status(self, message, current, total):
        if not self.status_fn:
            return
        status = chirp_common.Status()
        status.msg = message
        status.cur = current
        status.max = total
        self.status_fn(status)

    def _read_exact(self, size, timeout=2.0):
        data = bytearray()
        deadline = time.monotonic() + timeout
        while len(data) < size:
            chunk = self.pipe.read(size - len(data))
            if chunk:
                data.extend(chunk)
                continue
            if time.monotonic() > deadline:
                raise errors.RadioNoResponse()
            time.sleep(0.01)
        return bytes(data)

    def _read_frame(self, timeout=2.0):
        header = self._read_exact(4, timeout=timeout)
        if header[0] != 0x7C or header[2] != 0x00:
            raise errors.RadioError("Radio sent an unexpected reply")
        encoded = self._read_exact(header[3] + 1, timeout=timeout)
        plain = decrypt(encoded)
        payload, check = plain[:-1], plain[-1]
        expect = checksum(header[1], header[2], header[3], payload)
        if check != expect:
            raise errors.RadioError("Radio reply failed its checksum")
        return header[1], payload

    def _read_block(self, addr, size):
        request = build_frame(0x82, 0xFF, struct.pack(">HB", addr, size))
        last_error = None
        for _attempt in range(3):
            reset = getattr(self.pipe, "reset_input_buffer", None)
            if reset:
                reset()
            self.pipe.write(request)
            try:
                cmd, payload = self._read_frame()
            except errors.RadioNoResponse as exc:
                last_error = exc
                continue
            if cmd != 0x82 or len(payload) != size + 2:
                last_error = errors.RadioError("Bad read block at %04X" % addr)
                continue
            got = (payload[0] << 8) | payload[1]
            if got != addr:
                last_error = errors.RadioError(
                    "Radio returned address %04X for %04X" % (got, addr)
                )
                continue
            return payload[2:]
        raise last_error or errors.RadioNoResponse()

    def _read_ranges(self, ranges, message):
        image = bytearray(b"\xFF" * MEM_SIZE)
        total = sum(end - start for start, end in ranges)
        completed = 0
        for start, end in ranges:
            address = start
            while address < end:
                size = min(BLOCK_SIZE, end - address)
                self._status(message, completed, total)
                image[address:address + size] = self._read_block(address, size)
                address += size
                completed += size
        self._status(message, total, total)
        return image

    def _download(self):
        try:
            serial = self._read_ranges((SERIAL_DATA,), "Reading radio identity")
            identity = bytearray(b"\xFF" * MEM_SIZE)
            identity[SERIAL_DATA[0]:SERIAL_DATA[1]] = serial[
                SERIAL_DATA[0]:SERIAL_DATA[1]
            ]
            if not _identity_matches(identity):
                compat = self._read_ranges(
                    (COMPAT_ID_DATA,),
                    "Reading alternate radio identity",
                )
                identity[
                    COMPAT_ID_DATA[0]:COMPAT_ID_DATA[1]
                ] = compat[COMPAT_ID_DATA[0]:COMPAT_ID_DATA[1]]
                if not _identity_matches(identity):
                    raise errors.RadioError(
                        "Radio did not identify as a KG-905G Plus"
                    )
            image = self._read_ranges(MEMORY_RANGES, "Cloning from radio")
            image[SERIAL_DATA[0]:SERIAL_DATA[1]] = identity[
                SERIAL_DATA[0]:SERIAL_DATA[1]
            ]
            image[COMPAT_ID_DATA[0]:COMPAT_ID_DATA[1]] = identity[
                COMPAT_ID_DATA[0]:COMPAT_ID_DATA[1]
            ]
            return bytes(image)
        finally:
            try:
                self.pipe.write(build_frame(0x81, 0xFF, b""))
            except Exception:
                pass

    def _validated_image(self):
        image = self._packed()
        if len(image) != MEM_SIZE:
            raise errors.InvalidDataError(
                "KG-905G Plus image is %i bytes; expected %i"
                % (len(image), MEM_SIZE)
            )
        if not _identity_matches(image):
            raise errors.InvalidDataError(
                "The KG-905G Plus model marker is missing"
            )
        return image

    def _write_block(self, address, data):
        request = build_frame(
            0x83,
            0xFF,
            struct.pack(">H", address) + bytes(data),
        )
        expected = struct.pack(">H", address)
        last_error = None
        for _attempt in range(3):
            self.pipe.write(request)
            try:
                cmd, payload = self._read_frame(timeout=1.0)
            except errors.RadioNoResponse as exc:
                last_error = exc
                continue
            if cmd == 0x83 and payload == expected:
                return
            last_error = errors.RadioError(
                "Radio did not accept the block at %04X" % address
            )
        raise last_error or errors.RadioNoResponse()

    def _upload(self):
        image = self._validated_image()
        self._prepare_port()
        try:
            serial = self._read_ranges((SERIAL_DATA,), "Checking radio identity")
            if not _identity_matches(serial):
                raise errors.RadioError(
                    "Radio did not identify as a KG-905G Plus"
                )
            total = sum(end - start for start, end in WRITE_RANGES)
            completed = 0
            for start, end in WRITE_RANGES:
                address = start
                while address < end:
                    size = min(BLOCK_SIZE, end - address)
                    self._status("Cloning to radio", completed, total)
                    self._write_block(address, image[address:address + size])
                    address += size
                    completed += size
            self._status("Cloning to radio", total, total)
        finally:
            try:
                self.pipe.write(build_frame(0x81, 0xFF, b""))
            except Exception:
                pass
