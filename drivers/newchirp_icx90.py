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


@directory.register
class ICx90Radio(icx90.ICx90Radio):
    """Icom IC-E90 with completion-safe clone download."""

    ALIASES = icx90.ICx90Radio.ALIASES

    @classmethod
    def get_prompts(cls):
        prompts = super().get_prompts()
        prompts.info = (
            "Put the IC-E90 in clone mode before starting a transfer. If the "
            "radio sends the complete image without a final end frame, "
            "NewChirp accepts the download after every image byte arrives."
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
