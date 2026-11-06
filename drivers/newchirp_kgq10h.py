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

"""Wouxun KG-Q10H experimental clone driver.

The transport and memory layout were recovered from Wouxun's official
KG-Q10H Programming Software V2.02.02 (20231115).
"""

import struct
import time

from chirp import chirp_common
from chirp import directory
from chirp import errors
from chirp import memmap


MEM_SIZE = 0x8000
CHANNEL_COUNT = 999
RECORD_SIZE = 16
NAME_SIZE = 12
READ_BLOCK_SIZE = 64
WRITE_BLOCK_SIZE = 32
VALID_FLAG = 0x9E

CHANNEL_BASE = 0x05E0
NAME_BASE = 0x4460
VALID_BASE = 0x7340

SERIAL_RANGE = (0x0340, 0x0440)
PROGRAM_RANGES = (
    (0x0440, 0x0508),  # system settings, 200 bytes
    (0x0540, 0x05C0),  # VFO A/B records, 128 bytes
    (0x05E0, 0x4460),  # 1,000 channel records, 16,000 bytes
    (0x4460, 0x7340),  # 1,000 channel names, 12,000 bytes
    (0x7340, 0x7728),  # channel-present flags, 1,000 bytes
    (0x7740, 0x78A8),  # scan groups, 360 bytes
    (0x78B0, 0x78D8),  # FM presets, 40 bytes
    (0x78E0, 0x7B38),  # call-code records, 600 bytes
    (0x7B40, 0x8000),  # call-code names, 1,200 bytes
)
READ_RANGES = (SERIAL_RANGE,) + PROGRAM_RANGES

IDENT_OFFSET = 0x036C
INTERNAL_MODEL_OFFSET = 0x0382
SOFTWARE_OFFSET = 0x0392
IDENT_NAMES = (b"KG-Q10H", b"KG-Q10G")
INTERNAL_MODEL = b"KG-Q332"
SOFTWARE_PREFIX = b"VC"

ENCRYPT_SEED = 0x57
CMD_READ = 0x82
CMD_WRITE = 0x83
CMD_END = 0x81
RETRY_DELAY = 0.24
READ_TIMEOUT = 0.22
WRITE_TIMEOUT = 0.22
RETRIES = 25

RX_BANDS = (
    (50_000_000, 54_000_000),
    (108_000_000, 174_000_000),
    (222_000_000, 225_000_000),
    (320_000_000, 480_000_000),
    (714_000_000, 999_999_999),
)
TX_BANDS = (
    (50_000_000, 54_000_000),
    (144_000_000, 148_000_000),
    (222_000_000, 225_000_000),
    (420_000_000, 450_000_000),
)
AIRBAND = (108_000_000, 136_000_000)
TUNING_STEPS = (2.5, 5.0, 6.25, 8.33, 10.0, 12.5, 20.0, 25.0, 50.0, 100.0)

POWER_LEVELS = (
    chirp_common.PowerLevel("Low"),
    chirp_common.PowerLevel("Middle"),
    chirp_common.PowerLevel("High"),
    chirp_common.PowerLevel("Ultrahigh"),
)


def encrypt(data, seed=ENCRYPT_SEED):
    """Apply the CPS' chained XOR encoding."""
    if not data:
        return b""
    output = bytearray(len(data))
    output[0] = seed ^ data[0]
    for index in range(1, len(data)):
        output[index] = output[index - 1] ^ data[index]
    return bytes(output)


def decrypt(data, seed=ENCRYPT_SEED):
    """Reverse the CPS' chained XOR encoding."""
    if not data:
        return b""
    output = bytearray(len(data))
    output[0] = seed ^ data[0]
    for index in range(1, len(data)):
        output[index] = data[index] ^ data[index - 1]
    return bytes(output)


def checksum(command, direction, payload):
    """Return the sum used by the CPS for the frame checksum byte."""
    return (
        command
        + direction
        + len(payload)
        + sum(payload)
    ) & 0xFF


def build_frame(command, payload=b""):
    """Build one host-to-radio frame exactly as the CPS does."""
    check = checksum(command, 0xFF, payload)
    plain = payload + bytes((check,))
    return (
        bytes((0x7C, command, 0xFF, len(payload)))
        + encrypt(plain)
    )


def end_frame():
    return build_frame(CMD_END)


def _identity_matches(image):
    if len(image) != MEM_SIZE:
        return False
    display = bytes(image[IDENT_OFFSET:IDENT_OFFSET + 12]).rstrip(b"\x00 ")
    internal = bytes(
        image[
            INTERNAL_MODEL_OFFSET:
            INTERNAL_MODEL_OFFSET + len(INTERNAL_MODEL)
        ]
    )
    software = bytes(
        image[SOFTWARE_OFFSET:SOFTWARE_OFFSET + len(SOFTWARE_PREFIX)]
    )
    return (
        any(display.startswith(name) for name in IDENT_NAMES)
        and internal == INTERNAL_MODEL
        and software == SOFTWARE_PREFIX
    )


def _decode_tone(word):
    if word in (0, 0xFFFF):
        return "", None, None
    if word & 0x8000:
        value = (word & 0x3FFF) / 10.0
        return ("Tone", value, None) if value else ("", None, None)
    if word & 0x4000:
        raw = word & 0x01FF
        code = int("%03o" % raw)
        polarity = "R" if word & 0x2000 else "N"
        if code in chirp_common.DTCS_CODES:
            return "DTCS", code, polarity
    return "", None, None


def _encode_tone(mode, value, polarity):
    if not mode:
        return 0
    if mode == "Tone":
        tenths = int(round(float(value) * 10))
        if not 650 <= tenths <= 2600:
            raise errors.InvalidValueError(
                "CTCSS must be between 65.0 and 260.0 Hz"
            )
        return 0x8000 | tenths
    if mode == "DTCS":
        if int(value) not in chirp_common.DTCS_CODES:
            raise errors.InvalidValueError(
                "DTCS code %s is not supported" % value
            )
        raw = int(str(int(value)), 8)
        return 0x4000 | (0x2000 if polarity == "R" else 0) | raw
    raise errors.InvalidValueError("Unsupported tone mode %s" % mode)


def _apply_tones(mem, rx_word, tx_word):
    rx_mode, rx_value, rx_polarity = _decode_tone(rx_word)
    tx_mode, tx_value, tx_polarity = _decode_tone(tx_word)
    mem.tmode = ""
    mem.cross_mode = "Tone->Tone"
    mem.dtcs_polarity = "NN"

    if tx_mode == "Tone" and not rx_mode:
        mem.tmode = "Tone"
        mem.rtone = tx_value
    elif tx_mode == rx_mode == "Tone" and tx_value == rx_value:
        mem.tmode = "TSQL"
        mem.rtone = tx_value
        mem.ctone = rx_value
    elif (
        tx_mode == rx_mode == "DTCS"
        and tx_value == rx_value
    ):
        mem.tmode = "DTCS"
        mem.dtcs = tx_value
        mem.rx_dtcs = rx_value
        mem.dtcs_polarity = tx_polarity + rx_polarity
    elif tx_mode or rx_mode:
        mem.tmode = "Cross"
        mem.cross_mode = "%s->%s" % (tx_mode or "", rx_mode or "")
        if tx_mode == "Tone":
            mem.rtone = tx_value
        elif tx_mode == "DTCS":
            mem.dtcs = tx_value
        if rx_mode == "Tone":
            mem.ctone = rx_value
        elif rx_mode == "DTCS":
            mem.rx_dtcs = rx_value
        mem.dtcs_polarity = (
            (tx_polarity if tx_mode == "DTCS" else "N")
            + (rx_polarity if rx_mode == "DTCS" else "N")
        )


def _tones_from_memory(mem):
    tx_mode = rx_mode = ""
    tx_value = rx_value = None
    tx_polarity = rx_polarity = "N"

    if mem.tmode == "Tone":
        tx_mode, tx_value = "Tone", mem.rtone
    elif mem.tmode == "TSQL":
        tx_mode = rx_mode = "Tone"
        tx_value = rx_value = mem.ctone
    elif mem.tmode == "DTCS":
        tx_mode = rx_mode = "DTCS"
        tx_value = mem.dtcs
        rx_value = mem.rx_dtcs or mem.dtcs
        tx_polarity = mem.dtcs_polarity[0]
        rx_polarity = mem.dtcs_polarity[1]
    elif mem.tmode == "Cross":
        tx_mode, rx_mode = (mem.cross_mode or "->").split("->")
        if tx_mode == "Tone":
            tx_value = mem.rtone
        elif tx_mode == "DTCS":
            tx_value = mem.dtcs
            tx_polarity = mem.dtcs_polarity[0]
        if rx_mode == "Tone":
            rx_value = mem.ctone
        elif rx_mode == "DTCS":
            rx_value = mem.rx_dtcs or mem.dtcs
            rx_polarity = mem.dtcs_polarity[1]
    elif mem.tmode:
        raise errors.InvalidValueError(
            "Tone mode %s is not supported" % mem.tmode
        )

    return (
        _encode_tone(rx_mode, rx_value, rx_polarity),
        _encode_tone(tx_mode, tx_value, tx_polarity),
    )


def _in_bands(frequency, bands):
    return any(start <= frequency <= end for start, end in bands)


def _tx_frequency(mem):
    rx_hz = int(mem.freq)
    if mem.duplex == "off":
        return 0
    if mem.duplex in ("", " "):
        return rx_hz
    if mem.duplex == "+":
        return rx_hz + int(mem.offset)
    if mem.duplex == "-":
        return rx_hz - int(mem.offset)
    if mem.duplex == "split":
        return int(mem.offset)
    raise errors.InvalidValueError(
        "Unsupported duplex setting %s" % mem.duplex
    )


@directory.register
class KGQ10HRadio(
    chirp_common.CloneModeRadio,
    chirp_common.ExperimentalRadio,
):
    """Wouxun KG-Q10H."""

    VENDOR = "Wouxun"
    MODEL = "KG-Q10H"
    BAUD_RATE = 115200
    NEEDS_COMPAT_SERIAL = False
    WANTS_DTR = True
    WANTS_RTS = True
    _memsize = MEM_SIZE

    @classmethod
    def get_prompts(cls):
        prompts = chirp_common.RadioPrompts()
        prompts.experimental = (
            "The KG-Q10H driver is experimental. Its transport and memory "
            "layout were recovered from Wouxun Programming Software V2.02.02 "
            "(20231115). Read and save an unedited backup before writing."
        )
        prompts.info = (
            "Use a Wouxun K-plug programming cable. The radio uses 115200 "
            "baud, 8 data bits, no parity, one stop bit, DTR, and RTS."
        )
        prompts.pre_download = (
            "Power on the KG-Q10H, connect the programming cable, and close "
            "the Wouxun programming software so it releases the serial port."
        )
        prompts.pre_upload = (
            "Keep an unedited image from the Wouxun software and from "
            "NewChirp. NewChirp writes only the nine program-memory regions "
            "written by the OEM CPS and never writes the identity region."
        )
        return prompts

    @classmethod
    def match_model(cls, filedata, filename):
        raw, _metadata = chirp_common.CloneModeRadio._strip_metadata(filedata)
        return _identity_matches(raw)

    def process_mmap(self):
        self._validated_image()

    def get_features(self):
        rf = chirp_common.RadioFeatures()
        rf.has_settings = False
        rf.has_ctone = True
        rf.has_rx_dtcs = True
        rf.has_cross = True
        rf.has_tuning_step = False
        rf.has_bank = False
        rf.can_odd_split = True
        rf.valid_skips = ["", "S"]
        rf.valid_tmodes = ["", "Tone", "TSQL", "DTCS", "Cross"]
        rf.valid_cross_modes = [
            "Tone->Tone",
            "Tone->DTCS",
            "DTCS->Tone",
            "DTCS->",
            "->Tone",
            "->DTCS",
            "DTCS->DTCS",
        ]
        rf.valid_modes = ["FM", "NFM", "AM"]
        rf.valid_power_levels = list(POWER_LEVELS)
        rf.valid_name_length = NAME_SIZE
        rf.valid_duplexes = ["", "-", "+", "split", "off"]
        rf.valid_bands = list(RX_BANDS)
        rf.valid_characters = chirp_common.CHARSET_ASCII
        rf.memory_bounds = (1, CHANNEL_COUNT)
        rf.valid_tuning_steps = list(TUNING_STEPS)
        return rf

    def _number(self, number):
        number = int(number)
        if not 1 <= number <= CHANNEL_COUNT:
            raise errors.InvalidValueError(
                "Channel must be between 1 and %i" % CHANNEL_COUNT
            )
        return number

    def _record_offset(self, number):
        return CHANNEL_BASE + self._number(number) * RECORD_SIZE

    def _name_offset(self, number):
        return NAME_BASE + self._number(number) * NAME_SIZE

    def _valid_offset(self, number):
        return VALID_BASE + self._number(number)

    def get_raw_memory(self, number):
        offset = self._record_offset(number)
        return repr(self._packed()[offset:offset + RECORD_SIZE])

    def get_memory(self, number):
        number = self._number(number)
        raw = self._packed()
        if raw[self._valid_offset(number)] != VALID_FLAG:
            mem = chirp_common.Memory()
            mem.number = number
            mem.empty = True
            return mem

        offset = self._record_offset(number)
        record = raw[offset:offset + RECORD_SIZE]
        rx_frequency, tx_frequency, rx_tone, tx_tone = struct.unpack_from(
            "<IIHH", record
        )
        if rx_frequency in (0, 0xFFFFFFFF):
            mem = chirp_common.Memory()
            mem.number = number
            mem.empty = True
            return mem

        mem = chirp_common.Memory()
        mem.number = number
        mem.empty = False
        mem.freq = rx_frequency * 10
        if tx_frequency in (0, 0xFFFFFFFF):
            mem.duplex = "off"
            mem.offset = 0
        elif tx_frequency == rx_frequency:
            mem.duplex = ""
            mem.offset = 0
        else:
            delta = abs(int(tx_frequency) - int(rx_frequency)) * 10
            if delta > 70_000_000:
                mem.duplex = "split"
                mem.offset = tx_frequency * 10
            else:
                mem.duplex = "+" if tx_frequency > rx_frequency else "-"
                mem.offset = delta

        power = record[12] & 0x03
        mem.power = POWER_LEVELS[power]
        am_mode = (record[12] >> 2) & 0x03
        mem.mode = "AM" if am_mode else ("FM" if record[13] & 0x01 else "NFM")
        mem.skip = "" if record[13] & 0x20 else "S"
        _apply_tones(mem, rx_tone, tx_tone)

        name_offset = self._name_offset(number)
        stored_name = bytes(raw[name_offset:name_offset + NAME_SIZE])
        mem.name = stored_name.split(b"\x00", 1)[0].decode(
            "gb18030", "replace"
        ).rstrip()
        return mem

    def set_memory(self, mem):
        number = self._number(mem.number)
        raw = bytearray(self._packed())
        offset = self._record_offset(number)
        name_offset = self._name_offset(number)
        valid_offset = self._valid_offset(number)

        if mem.empty or not mem.freq:
            raw[offset:offset + RECORD_SIZE] = bytes(RECORD_SIZE)
            raw[name_offset:name_offset + NAME_SIZE] = bytes(NAME_SIZE)
            raw[valid_offset] = 0
            self._mmap = memmap.MemoryMapBytes(bytes(raw))
            return

        rx_hz = int(mem.freq)
        tx_hz = _tx_frequency(mem)
        if rx_hz % 10 or tx_hz % 10:
            raise errors.InvalidValueError(
                "Station frequencies must use 10 Hz steps"
            )
        if not _in_bands(rx_hz, RX_BANDS):
            raise errors.InvalidValueError(
                "Receive frequency is outside this radio's channel bands"
            )
        if tx_hz and not _in_bands(tx_hz, TX_BANDS):
            raise errors.InvalidValueError(
                "Transmit frequency is outside the KG-Q10H amateur bands"
            )
        if mem.mode not in ("FM", "NFM", "AM"):
            raise errors.InvalidValueError(
                "Mode must be FM, NFM, or AM"
            )
        if _in_bands(rx_hz, (AIRBAND,)) and mem.mode != "AM":
            raise errors.InvalidValueError(
                "Airband receive channels must use AM mode"
            )

        current = bytearray(raw[offset:offset + RECORD_SIZE])
        if current == bytes(RECORD_SIZE):
            current[12] = 0x02
            current[13] = 0x21
            current[14] = 0x01

        rx_tone, tx_tone = _tones_from_memory(mem)
        struct.pack_into(
            "<IIHH",
            current,
            0,
            rx_hz // 10,
            tx_hz // 10,
            rx_tone,
            tx_tone,
        )

        power = 2
        for index, level in enumerate(POWER_LEVELS):
            if level is mem.power or str(level) == str(mem.power):
                power = index
                break
        current[12] = (
            (current[12] & 0xF0)
            | power
            | (0x04 if mem.mode == "AM" else 0)
        )

        flags = current[13] & ~0x21
        if mem.mode in ("FM", "AM"):
            flags |= 0x01
        if mem.skip != "S":
            flags |= 0x20
        current[13] = flags
        raw[offset:offset + RECORD_SIZE] = current
        raw[name_offset:name_offset + NAME_SIZE] = self._name_bytes(
            mem.name,
            bytes(raw[name_offset:name_offset + NAME_SIZE]),
        )
        raw[valid_offset] = VALID_FLAG
        self._mmap = memmap.MemoryMapBytes(bytes(raw))

    def _name_bytes(self, name, previous):
        text = "" if name is None else str(name)
        try:
            encoded = text.encode("gb18030")
        except UnicodeEncodeError as exc:
            raise errors.InvalidValueError(
                "Channel name cannot be stored by this radio"
            ) from exc
        if len(encoded) > NAME_SIZE:
            raise errors.InvalidValueError(
                "Channel name cannot exceed %i stored bytes" % NAME_SIZE
            )
        if any(chr(byte) not in chirp_common.CHARSET_ASCII for byte in encoded):
            if not any(byte >= 0x80 for byte in encoded):
                raise errors.InvalidValueError(
                    "Channel name has a character this radio does not store"
                )
        stored = previous.split(b"\x00", 1)[0].decode(
            "gb18030", "replace"
        ).rstrip()
        if stored == text:
            return previous
        return encoded.ljust(NAME_SIZE, b"\x00")

    def validate_memory(self, mem):
        messages = []
        if mem.empty:
            return super().validate_memory(mem)
        if _in_bands(int(mem.freq), (AIRBAND,)) and mem.mode != "AM":
            messages.append(chirp_common.ValidationError(
                "Airband receive requires AM mode"
            ))
        if not _in_bands(int(mem.freq), (AIRBAND,)) and mem.mode == "AM":
            messages.append(chirp_common.ValidationWarning(
                "AM is intended for airband receive channels"
            ))
        try:
            tx_hz = _tx_frequency(mem)
        except errors.InvalidValueError as exc:
            messages.append(chirp_common.ValidationError(str(exc)))
        else:
            if tx_hz and not _in_bands(tx_hz, TX_BANDS):
                messages.append(chirp_common.ValidationError(
                    "Transmit frequency is outside the KG-Q10H amateur bands"
                ))
        return messages + super().validate_memory(mem)

    def _packed(self):
        if self._mmap is None:
            raise errors.RadioError("Load or download an image first")
        return self._mmap.get_packed()

    def _validated_image(self):
        image = self._packed()
        if len(image) != MEM_SIZE:
            raise errors.InvalidDataError(
                "KG-Q10H image is %i bytes; expected %i"
                % (len(image), MEM_SIZE)
            )
        if not _identity_matches(image):
            raise errors.InvalidDataError(
                "The KG-Q10H model marker is missing or unsupported"
            )
        return image

    def _prepare_port(self):
        try:
            self.pipe.baudrate = self.BAUD_RATE
            self.pipe.timeout = READ_TIMEOUT
            self.pipe.write_timeout = 1.0
            self.pipe.dtr = True
            self.pipe.rts = True
        except Exception:
            pass
        reset = getattr(self.pipe, "reset_input_buffer", None)
        if reset:
            reset()
        time.sleep(0.1)

    def _status(self, message, current, total):
        if not self.status_fn:
            return
        status = chirp_common.Status()
        status.msg = message
        status.cur = current
        status.max = total
        self.status_fn(status)

    def _read_exact(self, size, timeout):
        data = bytearray()
        deadline = time.monotonic() + timeout
        while len(data) < size:
            chunk = self.pipe.read(size - len(data))
            if chunk:
                data.extend(chunk)
                continue
            if time.monotonic() >= deadline:
                raise errors.RadioNoResponse()
            time.sleep(0.005)
        return bytes(data)

    def _read_frame(self, timeout):
        header = self._read_exact(4, timeout)
        if header[0] != 0x7C or header[2] != 0x00:
            raise errors.RadioError("Radio sent an unexpected reply")
        encoded = self._read_exact(header[3] + 1, timeout)
        plain = decrypt(encoded)
        payload, received_check = plain[:-1], plain[-1]
        expected_check = checksum(header[1], header[2], payload)
        if received_check != expected_check:
            raise errors.RadioError("Radio reply failed its checksum")
        return header[1], payload

    def _read_block(self, address, size):
        request = build_frame(
            CMD_READ, struct.pack(">HB", address, size)
        )
        last_error = None
        for _attempt in range(RETRIES + 1):
            reset = getattr(self.pipe, "reset_input_buffer", None)
            if reset:
                reset()
            self.pipe.write(request)
            try:
                command, payload = self._read_frame(READ_TIMEOUT)
            except (errors.RadioNoResponse, errors.RadioError) as exc:
                last_error = exc
                time.sleep(RETRY_DELAY)
                continue
            if command != CMD_READ or len(payload) < 2:
                last_error = errors.RadioError(
                    "Radio sent an invalid read reply"
                )
                time.sleep(RETRY_DELAY)
                continue
            returned_address = struct.unpack_from(">H", payload)[0]
            data = payload[2:]
            if returned_address != address:
                last_error = errors.RadioError(
                    "Radio returned address %04X for %04X"
                    % (returned_address, address)
                )
                time.sleep(RETRY_DELAY)
                continue
            if len(data) != size:
                last_error = errors.RadioError(
                    "Radio returned %i bytes for a %i-byte read at %04X"
                    % (len(data), size, address)
                )
                time.sleep(RETRY_DELAY)
                continue
            return data
        raise last_error or errors.RadioNoResponse()

    def _read_ranges(self, ranges, message):
        image = bytearray(b"\xFF" * MEM_SIZE)
        total = sum(end - start for start, end in ranges)
        completed = 0
        for start, end in ranges:
            address = start
            while address < end:
                size = min(READ_BLOCK_SIZE, end - address)
                self._status(message, completed, total)
                image[address:address + size] = self._read_block(address, size)
                address += size
                completed += size
        self._status(message, total, total)
        return image

    def _write_block(self, address, data):
        request = build_frame(
            CMD_WRITE, struct.pack(">H", address) + bytes(data)
        )
        expected = struct.pack(">H", address)
        last_error = None
        for _attempt in range(RETRIES + 1):
            reset = getattr(self.pipe, "reset_input_buffer", None)
            if reset:
                reset()
            self.pipe.write(request)
            try:
                command, payload = self._read_frame(WRITE_TIMEOUT)
            except (errors.RadioNoResponse, errors.RadioError) as exc:
                last_error = exc
                time.sleep(RETRY_DELAY)
                continue
            if command == CMD_WRITE and payload == expected:
                return
            last_error = errors.RadioError(
                "Radio did not acknowledge the block at %04X" % address
            )
            time.sleep(RETRY_DELAY)
        raise last_error or errors.RadioNoResponse()

    def sync_in(self):
        self._prepare_port()
        try:
            image = self._read_ranges(READ_RANGES, "Cloning from radio")
            if not _identity_matches(image):
                raise errors.RadioError(
                    "Radio did not identify as a supported KG-Q10H family model"
                )
            self._mmap = memmap.MemoryMapBytes(bytes(image))
        finally:
            try:
                self.pipe.write(end_frame())
            except Exception:
                pass

    def sync_out(self):
        image = self._validated_image()
        self._prepare_port()
        try:
            identity = self._read_ranges(
                (SERIAL_RANGE,), "Checking radio identity"
            )
            if not _identity_matches(identity):
                raise errors.RadioError(
                    "Connected radio does not identify as a KG-Q10H family model"
                )
            total = sum(end - start for start, end in PROGRAM_RANGES)
            completed = 0
            for start, end in PROGRAM_RANGES:
                address = start
                while address < end:
                    size = min(WRITE_BLOCK_SIZE, end - address)
                    self._status("Cloning to radio", completed, total)
                    self._write_block(
                        address, image[address:address + size]
                    )
                    address += size
                    completed += size
            self._status("Cloning to radio", total, total)
        finally:
            try:
                self.pipe.write(end_frame())
            except Exception:
                pass
