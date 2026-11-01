# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Experimental Yaesu FTX-1 live CAT memory driver.

The FTX-1 exposes memory read/write, tag, mode, and tone controls through its
documented CAT command set.  Channels are edited by selecting one memory at a
time, so this driver uses CHIRP's live-radio interface rather than a clone
memory map.
"""

import logging
import time

from chirp import chirp_common, directory, errors


LOG = logging.getLogger(__name__)

IDENTIFICATION = "0840"
MODE_TO_RADIO = {
    "LSB": "1",
    "USB": "2",
    "CW": "3",
    "FM": "4",
    "AM": "5",
    "NFM": "B",
}
RADIO_TO_MODE = {
    "1": "LSB",
    "2": "USB",
    "3": "CW",
    "4": "FM",
    "5": "AM",
    "B": "NFM",
}
CTCSS_TONES = (
    67.0, 69.3, 71.9, 74.4, 77.0, 79.7, 82.5, 85.4,
    88.5, 91.5, 94.8, 97.4, 100.0, 103.5, 107.2, 110.9,
    114.8, 118.8, 123.0, 127.3, 131.8, 136.5, 141.3, 146.2,
    151.4, 156.7, 159.8, 162.2, 165.5, 167.9, 171.3, 173.8,
    177.3, 179.9, 183.5, 186.2, 189.9, 192.8, 196.6, 199.5,
    203.5, 206.5, 210.7, 218.1, 225.7, 229.1, 233.6, 241.8,
    250.3, 254.1,
)
DCS_CODES = (
    23, 25, 26, 31, 32, 36, 43, 47, 51, 53, 54, 65, 71, 72,
    73, 74, 114, 115, 116, 122, 125, 131, 132, 134, 143, 145,
    152, 155, 156, 162, 165, 172, 174, 205, 212, 223, 225, 226,
    243, 244, 245, 246, 251, 252, 255, 261, 263, 265, 266, 271,
    274, 306, 311, 315, 325, 331, 332, 343, 346, 351, 356, 364,
    365, 371, 411, 412, 413, 423, 431, 432, 445, 446, 452, 454,
    455, 462, 464, 465, 466, 503, 506, 516, 523, 526, 532, 546,
    565, 606, 612, 624, 627, 631, 632, 654, 662, 664, 703, 712,
    723, 731, 732, 734, 743, 754,
)


def _read_command(pipe, command, timeout=0.8):
    pipe.reset_input_buffer()
    pipe.write(command.encode("ascii"))
    deadline = time.monotonic() + timeout
    response = bytearray()
    while time.monotonic() < deadline:
        chunk = pipe.read(1)
        if chunk:
            response.extend(chunk)
            if chunk == b";":
                break
        else:
            time.sleep(0.005)
    if not response:
        raise errors.RadioNoResponse(
            "No response to FTX-1 CAT command %s" % command
        )
    if not response.endswith(b";"):
        raise errors.RadioNoResponse(
            "Incomplete FTX-1 CAT response to %s: %s"
            % (command, response.decode("ascii", errors="replace"))
        )
    text = response.decode("ascii", errors="replace")
    if text == "?;":
        return ""
    return text[:-1]


def _standard_offset(frequency):
    if 144_000_000 <= frequency <= 148_000_000:
        return 600_000
    if 420_000_000 <= frequency <= 470_000_000:
        return 5_000_000
    if 50_000_000 <= frequency <= 54_000_000:
        return 1_000_000
    if 28_000_000 <= frequency <= 29_700_000:
        return 100_000
    return 0


@directory.register
class YaesuFTX1Radio(
    chirp_common.LiveRadio,
    chirp_common.ExperimentalRadio,
):
    """Yaesu FTX-1/FTX-1 Field CAT memory programmer."""

    VENDOR = "Yaesu"
    MODEL = "FTX-1"
    BAUD_RATE = 38400
    HARDWARE_FLOW = False
    WANTS_RTS = False
    WANTS_DTR = False
    _detected_baud = None

    @classmethod
    def get_prompts(cls):
        prompts = chirp_common.RadioPrompts()
        prompts.experimental = (
            "Yaesu FTX-1 support is experimental and uses the radio's live "
            "CAT interface. Memory frequency, mode, name, shift, CTCSS and "
            "DCS are read and written through the commands documented by "
            "Yaesu. The radio must be in a CAT-compatible firmware version "
            "1.08 or newer. Nonstandard repeater splits and optional "
            "signalling are not editable."
        )
        prompts.info = (
            "Set one FTX-1 CAT port to 115200, 38400, 19200, 9600, or 4800 "
            "baud, choose the matching serial port in NewChirp, and avoid "
            "using that CAT port from another program."
        )
        return prompts

    @classmethod
    def detect_from_serial(cls, pipe):
        pipe.timeout = 0.35
        for baud in (115200, 38400, 19200, 9600, 4800):
            pipe.baudrate = baud
            try:
                response = _read_command(pipe, "ID;", timeout=0.5)
            except errors.RadioError:
                continue
            if response.endswith(IDENTIFICATION):
                cls._detected_baud = baud
                return cls
        raise errors.RadioNoResponse(
            "FTX-1 CAT identification was not received at any supported "
            "baud rate"
        )

    def __init__(self, pipe):
        super().__init__(pipe)
        if self._detected_baud:
            pipe.baudrate = self._detected_baud
        pipe.timeout = 0.35
        identity = self._command("ID;")
        if not identity.endswith(IDENTIFICATION):
            raise errors.RadioError(
                "Unsupported Yaesu CAT identity %r; expected FTX-1 (%s)"
                % (identity, IDENTIFICATION)
            )
        self._command("AI0;")

    def get_features(self):
        rf = chirp_common.RadioFeatures()
        rf.has_name = True
        rf.has_settings = False
        rf.has_bank = False
        rf.has_tuning_step = False
        rf.has_cross = False
        rf.can_odd_split = False
        rf.valid_name_length = 12
        rf.valid_modes = ["FM", "NFM", "AM", "USB", "LSB", "CW"]
        rf.valid_tmodes = ["", "Tone", "TSQL", "DTCS"]
        rf.valid_duplexes = ["", "+", "-"]
        rf.valid_bands = [
            (30_000, 56_000_000),
            (76_000_000, 108_000_000),
            (118_000_000, 174_000_000),
            (420_000_000, 470_000_000),
        ]
        rf.memory_bounds = (1, 999)
        return rf

    def _command(self, command, timeout=0.8):
        return _read_command(self.pipe, command, timeout=timeout)

    def _memory_read(self, number):
        response = self._command("MR%05i;" % number)
        if not response:
            return None
        if (
            len(response) != 29
            or response[2:7] != "%05i" % number
            or not response[7:16].isdigit()
            or response[16] not in "+-"
            or not response[17:21].isdigit()
            or response[24] != "1"
            or response[26:28] != "00"
        ):
            raise errors.RadioError(
                "Invalid FTX-1 MR response for channel %i: %r"
                % (number, response)
            )
        return response

    def _tag_read(self, number):
        try:
            response = self._command("MT%05i;" % number)
        except errors.RadioError:
            return ""
        if not response.startswith("MT%05i" % number):
            return ""
        return response[7:].strip().replace("\x00", "")[:12]

    def _active_channel(self):
        response = self._command("MC;")
        if (
            len(response) >= 8
            and response.startswith("MC")
            and response[2] in "01"
            and response[3:8].isdigit()
        ):
            return response[2:8]
        return None

    def _memory_tone(self, number, tone_mode):
        previous = self._active_channel()
        try:
            self._command("MC0%05i;" % number)
            sql_type = self._command("CT0;")
            if not sql_type:
                return "", None, None, "NN"
            sql_code = int(sql_type[-1], 16)
            if sql_code not in (1, 2, 3):
                return "", None, None, "NN"
            tone = self._command("CN0;")
            if not tone.startswith("CN") or len(tone) < 3:
                return "", None, None, "NN"
            kind = int(tone[2], 16)
            index = int(tone[4:7], 10)
            if sql_code in (1, 2) and kind == 0 and index < len(CTCSS_TONES):
                value = CTCSS_TONES[index]
                if sql_code == 1:
                    return "Tone", value, None, "NN"
                return "TSQL", value, value, "NN"
            if sql_code == 3 and kind == 1 and index < len(DCS_CODES):
                return "DTCS", None, None, "NN", DCS_CODES[index]
        finally:
            if previous:
                self._command("MC%s;" % previous)
        return "", None, None, "NN"

    def get_memory(self, number):
        if not 1 <= number <= 999:
            raise errors.InvalidMemoryLocation(
                "FTX-1 memory number must be between 1 and 999"
            )
        memory = chirp_common.Memory(number)
        response = self._memory_read(number)
        if response is None:
            memory.empty = True
            return memory

        frequency = int(response[7:16])
        if frequency <= 0:
            memory.empty = True
            return memory

        memory.freq = frequency
        code = response[23]
        memory.mode = RADIO_TO_MODE.get(code, "FM")
        shift = response[-1]
        offset = _standard_offset(frequency)
        if shift in ("1", "2") and offset:
            memory.duplex = "+" if shift == "1" else "-"
            memory.offset = offset
        else:
            memory.duplex = ""
            memory.offset = 0
        memory.name = self._tag_read(number)

        tone_mode = response[25]
        if tone_mode in ("1", "2", "3"):
            tone = self._memory_tone(number, tone_mode)
            if len(tone) == 5:
                memory.tmode, _tx, _rx, memory.dtcs_polarity, dtcs = tone
                memory.dtcs = dtcs
            else:
                memory.tmode, tx_tone, rx_tone, memory.dtcs_polarity = tone
                if tx_tone is not None:
                    memory.rtone = tx_tone
                if rx_tone is not None:
                    memory.ctone = rx_tone
        return memory

    @staticmethod
    def _ctcss_index(tone):
        try:
            index = min(
                range(len(CTCSS_TONES)),
                key=lambda pos: abs(CTCSS_TONES[pos] - float(tone)),
            )
        except (TypeError, ValueError):
            return None
        if abs(CTCSS_TONES[index] - float(tone)) > 0.05:
            return None
        return index

    def _set_memory_tone(self, number, memory):
        previous = self._active_channel()
        try:
            self._command("MC0%05i;" % number)
            if memory.tmode in ("Tone", "TSQL"):
                index = self._ctcss_index(memory.rtone)
                if index is None:
                    raise errors.RadioError(
                        "FTX-1 does not support CTCSS %.1f Hz" % memory.rtone
                    )
                sql_code = 1 if memory.tmode == "Tone" else 2
                self._command("CT0%i;" % sql_code)
                self._command("CN00%03i;" % index)
            elif memory.tmode == "DTCS":
                try:
                    index = DCS_CODES.index(int(memory.dtcs))
                except ValueError as exc:
                    raise errors.RadioError(
                        "FTX-1 does not support DCS %03i" % memory.dtcs
                    ) from exc
                self._command("CT03;")
                self._command("CN01%03i;" % index)
            else:
                self._command("CT00;")
        finally:
            if previous:
                self._command("MC%s;" % previous)

    def set_memory(self, memory):
        number = int(memory.number)
        if not 1 <= number <= 999:
            raise errors.InvalidMemoryLocation(
                "FTX-1 memory number must be between 1 and 999"
            )
        if memory.empty:
            current = self._memory_read(number)
            if current is not None:
                frequency = int(current[7:16])
                if frequency > 0:
                    blank = (
                        "MW%05i%09i+%04i00%s1%s00%s;"
                        % (number, 0, 0, "4", "0", "0")
                    )
                    self._command(
                        blank
                    )
                    self._command("MT%05i;" % number)
            return

        offset = abs(int(memory.offset)) if memory.duplex in ("+", "-") else 0
        shift = "1" if memory.duplex == "+" else (
            "2" if memory.duplex == "-" else "0"
        )
        mode = MODE_TO_RADIO.get(memory.mode, "4")
        tone_mode = {
            "": "0",
            "Tone": "1",
            "TSQL": "2",
            "DTCS": "3",
        }.get(memory.tmode, "0")
        command = (
            "MW%05i%09i+%04i00%s1%s00%s;"
            % (
                number,
                int(memory.freq),
                offset,
                mode,
                tone_mode,
                shift,
            )
        )
        self._command(command)
        tag = str(memory.name).encode("ascii", errors="replace")[:12]
        self._command("MT%05i%s;" % (number, tag.decode("ascii")))
        if tone_mode != "0":
            self._set_memory_tone(number, memory)

    @classmethod
    def match_model(cls, filedata, filename):
        return False
