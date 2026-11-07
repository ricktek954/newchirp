# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Completion-safe Icom IC-E90 / IC-T90A clone download.

Some IC-E90 revisions send every byte of the fixed 0x2D40-byte image but do
not leave CHIRP's clone parser with a recognizable final end frame.  The
radio is otherwise healthy: the reported stream is the expected size for the
legacy hexadecimal ICF payload.  Treat full contiguous image coverage as a
successful download while retaining the normal end-frame path when present.
"""

import logging
import time

from chirp import chirp_common, directory, errors, memmap
from chirp.drivers import icf, icx90


LOG = logging.getLogger(__name__)

CLONE_TIMEOUT = 15


directory.enable_reregistrations()

_UPSTREAM_GET_MEMORY = icx90.ICx90Radio.get_memory


def _get_memory_with_invisible_guard(self, number):
    if (
        isinstance(number, int)
        and 0 <= number < len(self.memobj.banks)
        and self.memobj.banks[number].invisible_channel
    ):
        memory = chirp_common.Memory()
        memory.number = number
        memory.empty = True
        return memory
    return _UPSTREAM_GET_MEMORY(self, number)


_get_memory_with_invisible_guard.newchirp_invisible_guard = True
icx90.ICx90Radio.get_memory = _get_memory_with_invisible_guard


@directory.register
class ICx90Radio(icx90.ICx90Radio):
    """Icom IC-E90 with completion-safe clone download."""

    ALIASES = icx90.ICx90Radio.ALIASES

    @classmethod
    def get_prompts(cls):
        prompts = super().get_prompts()
        prompts.info = (
            "Put the IC-E90 in clone mode before starting a transfer. Power "
            "cycle the radio before a new read or write so it is not left in "
            "the previous CL OUT/CL IN state. If the radio sends the complete "
            "image without a final end frame, NewChirp accepts the download "
            "after every image byte arrives."
        )
        prompts.pre_download = (
            "1. Turn the radio off.\n"
            "2. Hold [8 SET] and [MR], then power on to enter cloning mode.\n"
            "3. Connect the OPC-478 programming cable and start the download.\n\n"
            "The radio normally displays CL OUT while data is read. Do not "
            "start a write from a radio left in that transfer state."
        )
        prompts.pre_upload = (
            "Before writing, turn the radio completely off and back on. "
            "Re-enter cloning mode, connect the programming cable, and start "
            "the write as a new operation.\n\n"
            "The radio must change from CL OUT to CL IN when the write starts. "
            "If it remains on CL OUT, stop the transfer, power-cycle the radio, "
            "and enter cloning mode again before retrying.\n\n"
            "Keep an unedited image downloaded from this radio. After the "
            "write succeeds, power-cycle the radio and read it back to verify "
            "the edited channels."
        )
        return prompts

    def _clone_from_radio(self):
        model_data = icf.get_model_data(
            self,
            mdata=icf._id_query_payload(self),
        )
        if len(model_data) < 4:
            raise errors.RadioNoResponse(
                "The radio returned incomplete Icom identification data"
            )
        if model_data[:4] != self.get_model():
            raise errors.RadioError(
                "Icom model mismatch: expected %s, received %s"
                % (self.get_model().hex(), model_data[:4].hex())
            )

        if self.is_hispeed():
            icf.start_hispeed_clone(self, icf.CMD_CLONE_OUT)
        else:
            icf.send_clone_frame(
                self,
                icf.CMD_CLONE_OUT,
                self.get_model(),
                raw=True,
            )

        stream = icf.RadioStream(self.pipe)
        image = memmap.MemoryMapBytes(bytes(self.get_memsize()))
        contiguous = 0
        complete = False
        got_end = False
        last_frame = time.monotonic()
        status = chirp_common.Status()
        status.msg = "Cloning from radio"
        status.max = self.get_memsize()

        while not got_end:
            frames = stream.get_frames()
            if not frames:
                if complete:
                    LOG.info(
                        "IC-E90 image reached 0x%04X without an end frame; "
                        "accepting complete coverage",
                        contiguous,
                    )
                    break
                if time.monotonic() - last_frame > CLONE_TIMEOUT:
                    break
                continue

            for frame in frames:
                last_frame = time.monotonic()
                if frame.cmd == icf.CMD_CLONE_DAT:
                    start, stop = icf.process_data_frame(self, frame, image)
                    if start > contiguous:
                        # Do not mistake a sparse image for a complete one.
                        contiguous = -1
                    elif contiguous >= 0:
                        contiguous = max(contiguous, stop)
                    complete = contiguous >= self.get_memsize()
                elif frame.cmd == icf.CMD_CLONE_END:
                    image.truncate(contiguous)
                    got_end = True
                    complete = contiguous >= self.get_memsize()

            if self.status_fn:
                status.cur = max(0, contiguous)
                self.status_fn(status)

            if complete and not got_end:
                LOG.info(
                    "IC-E90 image complete at 0x%04X; final end frame not "
                    "required",
                    contiguous,
                )
                break

        if not complete:
            raise errors.RadioError(
                "IC-E90 clone download stopped at 0x%04X of 0x%04X bytes"
                % (max(0, contiguous), self.get_memsize())
            )

        if self._highbit_flip:
            image = memmap.MemoryMapBytes(
                icf.flip_high_order_bit(image.get_packed())
            )
        return image

    def sync_in(self):
        image = self._clone_from_radio()
        self._mmap = image
        self._memsize = len(self._mmap)
        self._metadata["icom_image_size"] = self._memsize
        self.process_mmap()
