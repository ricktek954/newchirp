# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Icom IC-746PRO support using the shared IC-746 CI-V memory format."""

from chirp import chirp_common, directory
from chirp.drivers import icomciv


directory.enable_reregistrations()


@directory.register
class Icom746ProRadio(
    icomciv.Icom746Radio,
    chirp_common.ExperimentalRadio,
):
    """Icom IC-746PRO.

    The IC-746PRO is a distinct CI-V model: the original IC-746 uses
    address 0x56, while the PRO uses address 0x66. Selecting IC-746 against
    an IC-746PRO sends commands to the wrong address and leaves the radio
    silent even when the cable is working.
    """

    MODEL = "IC-746PRO"
    BAUD_RATE = 9600
    _model = "\x66"

    @classmethod
    def get_prompts(cls):
        prompts = super().get_prompts()
        prompts.info = (
            "Select Icom IC-746PRO for the PRO model. Its CI-V address is "
            "66h; the original IC-746 uses 56h. Connect the radio with a "
            "supported CI-V cable, turn CI-V Transceive off, and close any "
            "other radio-control application using the same port."
        )
        prompts.pre_download = (
            "Confirm that the radio is an IC-746PRO, not an original IC-746. "
            "This driver sends CI-V commands to address 66h. Read the radio "
            "and save an unedited image before editing."
        )
        return prompts
