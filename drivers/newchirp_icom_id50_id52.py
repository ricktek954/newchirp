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

The memory layout starts from the closely related ID-4100 map.  It remains
provisional for these two radios until physical readback validates every
field.  Reading and writing are intentionally enabled for this experimental
driver so field data can be collected, but the radio model and map revision
are checked on every live transfer.
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
        if self._mmap is None:
            raise errors.RadioError("Read the radio or load an image first")
        self._identify_radio()
        self._memsize = len(self._mmap)
        self.pipe.baudrate = self.BAUD_RATE
        return self._clone_to_radio()

    def process_mmap(self):
        super().process_mmap()
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
    """Shared read/write implementation for the two experimental drivers."""

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
            "but the channel, zone, and D-STAR field map has not yet been "
            "validated on physical hardware. Reading and writing are enabled "
            "at your own risk. Download and save an unedited backup image "
            "before making changes, and do not write if the downloaded "
            "channels do not look correct.\n" % cls.MODEL
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
            "Save the unedited download as a backup. Verify the model ID, "
            "channels, names, tones, zones, and D-STAR callsigns before "
            "using upload."
        )
        prompts.pre_upload = (
            "Experimental write. Keep a known-good backup image and do not "
            "disconnect the cable or turn off the radio. After writing, read "
            "the radio back and verify every field before relying on it."
        )
        return prompts

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
