# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Read-only capture profile for the Icom IC-F50V / IC-F60V.

No public memory map exists for these land-mobile handhelds, and Icom's
CS-F50V programmer is dealer software. Related Icom land-mobile radios in
CHIRP (``icf520.py``, IC-F621-2) use Icom's standard clone protocol: a
CLONE_ID (0xE0) query answered by a 4-byte model ID, then CLONE_OUT (0xE2)
answered by 16-byte data frames and an "Icom Inc." end frame.

This profile reads with that protocol without knowing the model ID or the
image size in advance. It asks the radio for its ID, clones out everything
the radio sends up to the end frame, and saves it. It decodes no channels
and can never write. Owners' captures are the evidence a real driver needs.
"""

import logging

from chirp import chirp_common, directory, errors, util
from chirp.drivers import icf


LOG = logging.getLogger(__name__)

# Largest image that still uses the 2-byte frame addresses of the related
# IC-F621 family; the image is truncated to what the radio actually sends.
CAPTURE_LIMIT = 0xFFFF
MODEL_KEY = "icom_capture_model_id"


@directory.register
class IcomF50VCapture(icf.IcomCloneModeRadio, chirp_common.ExperimentalRadio):
    """Icom IC-F50V / IC-F60V read-only capture."""

    VENDOR = "Icom"
    MODEL = "IC-F50V/F60V"
    VARIANT = "Capture"
    NEWCHIRP_WRITE_DISABLED = True
    BAUD_RATE = 9600

    _model = "\x00\x00\x00\x00"
    _memsize = CAPTURE_LIMIT
    _endframe = "Icom Inc."
    _ranges = []
    _can_hispeed = False

    @classmethod
    def get_prompts(cls):
        prompts = chirp_common.RadioPrompts()
        prompts.experimental = (
            "This profile only captures the radio's memory so NewChirp can "
            "learn the IC-F50V/F60V layout. It shows no channels and never "
            "writes to the radio. Save the image after reading and send it "
            "to the NewChirp team."
        )
        prompts.pre_download = (
            "1. Turn the radio off.\n"
            "2. Connect the Icom OPC-966 cable.\n"
            "3. Turn the radio on.\n"
            "4. Click OK to read, then save the image (File > Save).\n"
        )
        return prompts

    def get_features(self):
        rf = chirp_common.RadioFeatures()
        rf.memory_bounds = (1, 1)
        rf.has_bank = False
        rf.has_settings = False
        rf.has_name = False
        rf.has_ctone = False
        rf.has_tuning_step = False
        rf.valid_modes = ["FM"]
        rf.valid_tmodes = [""]
        rf.valid_duplexes = [""]
        rf.valid_bands = [(136000000, 470000000)]
        return rf

    @classmethod
    def match_model(cls, filedata, filename):
        # Only images saved by this profile (identified by metadata).
        return False

    def sync_in(self):
        model_data = icf.get_model_data(self)
        model_id = bytes(model_data[0:4])
        if len(model_id) != 4:
            raise errors.RadioError(
                "The radio answered the Icom identity query with %i bytes; "
                "expected a 4-byte model ID." % len(model_id)
            )
        LOG.info("Icom model data: %s", util.hexprint(model_data))
        # Clone out with the radio's own ID. Each bridge command runs in its
        # own process, so setting it on the class affects only this read.
        type(self)._model = model_id.decode("latin1")
        try:
            super().sync_in()
        except errors.RadioError as exc:
            raise errors.RadioError(
                "The radio identified as Icom model %s but the memory read "
                "failed: %s" % (model_id.hex(" ").upper(), exc)
            )
        self._metadata[MODEL_KEY] = model_id.hex(" ").upper()
        self._metadata["icom_capture_model_data"] = bytes(model_data).hex()
        self._metadata["icom_capture_size"] = len(self._mmap.get_packed())
        self.process_mmap()

    def process_mmap(self):
        model_id = self._metadata.get(MODEL_KEY) if self._metadata else None
        size = len(self._mmap.get_packed()) if self._mmap else 0
        self._firmware = (
            "Icom model ID %s, %i-byte capture" % (model_id, size)
            if model_id else "Icom capture, %i bytes" % size
        )

    def get_memory(self, number):
        mem = chirp_common.Memory()
        mem.number = number
        mem.empty = True
        return mem

    def set_memory(self, mem):
        raise errors.RadioError(
            "The IC-F50V/F60V capture profile is read-only."
        )

    def sync_out(self):
        raise errors.RadioError(
            "The IC-F50V/F60V capture profile is read-only."
        )
