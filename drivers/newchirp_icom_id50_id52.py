# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Experimental Icom ID-50 and ID-52 clone-mode drivers.

The transport was recovered from Icom CS-50 1.03 and CS-52 1.23.  Both
programmers use the standard Icom ``IcomCloneFormat3`` protocol implemented
by CHIRP's ``icf`` module: FE/FD framing with E0 through E6 commands, raw
escaped clone data, and the high-bit transform used by recent Icom radios.

The 500-channel layout was recovered from a physical ID-50 image supplied by
a field tester.  Reads expose frequencies, offsets, channel names, the analog
mode flag, and D-STAR callsigns.  Tones and some channel option bits are still
unvalidated, so writes are disabled and the radio model is checked on every
live transfer.
"""

import logging
import time

from chirp import chirp_common, directory, errors, memmap
from chirp.drivers import icf, id5100


LOG = logging.getLogger(__name__)

# The clone stream reports its actual end address.  This ceiling is only the
# allocation limit while downloading; the saved image is truncated to the
# radio's reported end and uploads use that resulting image length.
MAX_MEMORY_SIZE = 0x80000
END_FRAME = b"Icom Inc."
CLONE_TIMEOUT = 15
CHANNEL_COUNT = 500
CHANNEL_RECORD_SIZE = 51


def _model_hex(model):
    return bytes(model).hex()


class _DynamicIcomCloneMixin:
    """Use the model ID reported by the connected radio."""

    def __init__(self, pipe):
        self._radio_model = None
        self._radio_version = None
        self._icf_data = dict(self._icf_data)
        super().__init__(pipe)

    def get_model(self):
        return self._radio_model or b"\x00\x00\x00\x00"

    def get_endframe(self):
        return END_FRAME

    def get_ranges(self):
        if self._mmap is None:
            return []
        return [(0, len(self._mmap), 32)]

    def _identify_radio(self):
        model_data = icf.get_model_data(self)
        if len(model_data) < 4:
            raise errors.RadioNoResponse(
                "The radio returned incomplete Icom identification data"
            )

        reported = bytes(model_data[:4])
        expected = self._metadata.get("icom_model_id")
        if expected and reported.hex() != expected:
            raise errors.RadioError(
                "Connected radio model %s does not match saved image model %s"
                % (reported.hex(), expected)
            )

        self._radio_model = reported
        self._metadata["icom_model_id"] = _model_hex(reported)
        version = icf.decode_model(model_data)
        if version is not None:
            self._radio_version = version
            self._icf_data["MapRev"] = version
        LOG.info(
            "Icom %s model ID %s, map revision %s",
            self.MODEL,
            reported.hex(),
            self._radio_version,
        )
        return model_data

    def _clone_from_radio(self):
        if self.is_hispeed():
            icf.start_hispeed_clone(self, icf.CMD_CLONE_OUT)
        else:
            icf.send_clone_frame(
                self, icf.CMD_CLONE_OUT, self.get_model(), raw=True
            )

        stream = icf.RadioStream(self.pipe)
        addr = 0
        image = memmap.MemoryMapBytes(bytes(self.get_memsize()))
        last_frame = time.monotonic()
        got_end = False
        status = chirp_common.Status()
        status.msg = "Cloning from radio"
        status.max = self.get_memsize()

        while not got_end:
            frames = stream.get_frames()
            if not frames and time.monotonic() - last_frame > CLONE_TIMEOUT:
                break
            for frame in frames:
                last_frame = time.monotonic()
                if frame.cmd == icf.CMD_CLONE_DAT:
                    _start, addr = icf.process_data_frame(self, frame, image)
                elif frame.cmd == icf.CMD_CLONE_END:
                    image.truncate(addr)
                    got_end = True
            if self.status_fn:
                status.cur = addr
                self.status_fn(status)

        if not got_end:
            raise errors.RadioError(
                "Icom clone download stopped at 0x%05X before the end frame"
                % addr
            )
        return image

    def _clone_to_radio(self):
        stream = icf.RadioStream(self.pipe)
        if self.is_hispeed():
            icf.start_hispeed_clone(self, icf.CMD_CLONE_IN)
        else:
            icf.send_clone_frame(
                self, icf.CMD_CLONE_IN, self.get_model(), raw=True
            )

        for start, stop, block_size in self.get_ranges():
            if not icf.send_mem_chunk(
                self, stream, start, stop, block_size
            ):
                raise errors.RadioError("Icom clone upload stopped early")

        icf.send_clone_frame(
            self, icf.CMD_CLONE_END, self.get_endframe(), raw=True
        )

        frames = []
        deadline = time.monotonic() + CLONE_TIMEOUT
        while time.monotonic() < deadline:
            frames += stream.get_frames(True)
            if frames and frames[-1].cmd == icf.CMD_CLONE_OK:
                break
            time.sleep(0.1)

        if not frames:
            raise errors.RadioNoResponse(
                "The radio did not acknowledge the Icom clone upload"
            )
        result = frames[-1]
        if result.cmd != icf.CMD_CLONE_OK:
            raise errors.RadioError("The radio rejected the Icom clone upload")
        if result.payload[:1] != b"\x00":
            raise errors.RadioError(
                "The radio reported an Icom clone upload failure"
            )
        return True

    def sync_in(self):
        self._identify_radio()
        self._memsize = MAX_MEMORY_SIZE
        image = self._clone_from_radio()
        if self._highbit_flip:
            image = memmap.MemoryMapBytes(
                icf.flip_high_order_bit(image.get_packed())
            )
        self._mmap = image
        self._memsize = len(self._mmap)
        self._metadata["icom_image_size"] = self._memsize
        self.process_mmap()

    def sync_out(self):
        raise errors.RadioError(
            "The ID-50/ID-52 channel and D-STAR map is read-only while the "
            "remaining tone and mode flags are validated."
        )

    def process_mmap(self):
        model = self._metadata.get("icom_model_id")
        if model:
            try:
                self._radio_model = bytes.fromhex(model)
            except ValueError:
                LOG.warning("Ignoring invalid saved Icom model ID %r", model)
        self._memsize = len(self._mmap)


class _IcomId50Id52Base(
    _DynamicIcomCloneMixin,
    id5100.ID4100Radio,
    chirp_common.ExperimentalRadio,
):
    """Shared read-only implementation for the two experimental drivers."""

    VENDOR = "Icom"
    BAUD_RATE = 9600
    _memsize = MAX_MEMORY_SIZE
    _model = b"\x00\x00\x00\x00"
    _endframe = END_FRAME
    _ranges = []
    _raw_frames = True
    _highbit_flip = True
    _can_hispeed = False
    _num_banks = 26

    @classmethod
    def get_prompts(cls):
        prompts = chirp_common.RadioPrompts()
        prompts.experimental = (
            "%s support is experimental. The Icom clone transport is known, "
            "and supplied physical images have established the 500-channel "
            "frequency, name, offset, and D-STAR callsign layout. Tones and "
            "some mode flags remain unvalidated, so uploads are disabled. "
            "Download the radio and keep a saved backup image.\n" % cls.MODEL
        )
        prompts.info = (
            "Connect the radio with its Icom USB programming cable, turn it "
            "on, close CS-50/CS-52, and start the download. The clone "
            "interface uses 9600 baud, 8 data bits, no parity, and one stop "
            "bit."
        )
        prompts.pre_download = (
            "1. Turn the radio on and connect the Icom USB cable.\n"
            "2. Close Icom CS-50/CS-52 and any other program using the port.\n"
            "3. Start the download and leave the radio powered on.\n\n"
            "Save the unedited download as a backup. This driver is "
            "read-only until the remaining tone and mode fields are verified."
        )
        return prompts

    def get_features(self):
        rf = chirp_common.RadioFeatures()
        rf.has_name = True
        rf.has_settings = False
        rf.has_bank = False
        rf.has_ctone = False
        rf.has_rx_dtcs = False
        rf.has_tuning_step = False
        rf.has_cross = False
        rf.can_odd_split = False
        rf.memory_bounds = (1, CHANNEL_COUNT)
        rf.valid_bands = [
            (108000000, 174000000),
            (375000000, 550000000),
        ]
        rf.valid_modes = ["FM", "AM", "DV"]
        rf.valid_duplexes = ["", "+"]
        rf.valid_tmodes = [""]
        rf.valid_name_length = 16
        return rf

    def _channel_record(self, number):
        if not 1 <= number <= CHANNEL_COUNT:
            raise errors.InvalidMemoryLocation(
                "Channel number must be between 1 and %i" % CHANNEL_COUNT
            )
        start = (number - 1) * CHANNEL_RECORD_SIZE
        return self._mmap.get(start, CHANNEL_RECORD_SIZE)

    def get_raw_memory(self, number):
        return repr(self._channel_record(number))

    @staticmethod
    def _decode_name(raw):
        try:
            name = raw.decode("shift_jis")
        except UnicodeDecodeError:
            name = raw.decode("ascii", errors="replace")
        return name.replace("\x00", "").rstrip()

    @staticmethod
    def _decode_call(raw):
        return "".join(
            chr(value) for value in icf.warp_byte_size(raw, 7, 8)
        ).rstrip()

    def get_memory(self, number):
        record = self._channel_record(number)
        memory = chirp_common.DVMemory()
        memory.number = number

        frequency = int.from_bytes(record[0:4], "big")
        if frequency in (0, 0xFFFFFFFF):
            memory.empty = True
            return memory

        memory.freq = frequency
        offset = int.from_bytes(record[4:8], "big")
        if offset:
            memory.duplex = "+"
            memory.offset = offset

        memory.name = self._decode_name(record[12:28])
        mode_flag = record[9]
        if mode_flag == 0x03:
            memory.mode = "AM"
        elif mode_flag == 0x05:
            memory.mode = "DV"
            memory.dv_urcall = self._decode_call(record[30:37])
            memory.dv_rpt1call = self._decode_call(record[37:44])
            memory.dv_rpt2call = self._decode_call(record[44:51])
        else:
            if mode_flag != 0x00:
                LOG.warning(
                    "Unknown Icom %s channel %i mode flag 0x%02X; using FM",
                    self.MODEL,
                    number,
                    mode_flag,
                )
            memory.mode = "FM"
        return memory

    def set_memory(self, memory):
        raise errors.RadioError(
            "The ID-50/ID-52 map is read-only until all tone and mode flags "
            "are independently validated."
        )

    @classmethod
    def match_model(cls, filedata, filename):
        # Saved NewChirp images are selected through their metadata.  OEM
        # ICF detection waits until the model IDs for both radios are known.
        return False


@directory.register
class IcomId50Radio(_IcomId50Id52Base):
    """Icom ID-50 experimental clone-mode driver."""

    MODEL = "ID-50"


@directory.register
class IcomId52Radio(_IcomId50Id52Base):
    """Icom ID-52 experimental clone-mode driver."""

    MODEL = "ID-52"
