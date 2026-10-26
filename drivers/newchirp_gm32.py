# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Experimental Baofeng GM-32 support.

The GM-32 uses the UV-32 protocol and memory map exposed by Baofeng's
BF-UVs Pro CPS v1.4.7.  The stock UV-32 driver intentionally hides the ten
bank-name slots, so this profile enables them and keeps the shared transport,
channel, and settings implementation from CHIRP.
"""

from chirp import directory
from chirp.drivers.baofeng_uv17Pro import UV32


@directory.register
class BaofengGM32(UV32):
    """Baofeng GM-32."""

    VENDOR = "Baofeng"
    MODEL = "GM-32"

    # The vendor CPS asserts both modem-control lines before opening the
    # port, while CHIRP's UV-32 class leaves them deasserted in NewChirp.
    WANTS_DTR = True
    WANTS_RTS = True
    HARDWARE_FLOW = False
    XON_XOFF = False

    # CPS offsets 0xA200-0xA27F hold ten 16-byte bank names.  The shared
    # UV-32 memory map already places these at image offset 0x8280.
    _has_support_for_banknames = True

    @classmethod
    def get_prompts(cls):
        prompts = super().get_prompts()
        prompts.experimental = (
            "The Baofeng GM-32 profile is experimental. Its transport, "
            "32-byte channel records, settings, and ten bank-name slots were "
            "recovered from Baofeng's UV-32 CPS v1.4.7, but a complete "
            "physical read/edit/upload/read-back test is still required.\n\n"
            "Save an unedited image after the first successful download. "
            "Before uploading, make a backup and verify that channel names, "
            "bank names, and radio settings survive a read-back."
        )
        prompts.pre_download = (
            "1. Turn the radio off and connect its programming cable.\n"
            "2. Turn the radio on and close any other programming software.\n"
            "3. Start the download and leave the radio powered on.\n\n"
            "Save an unedited image immediately after the first successful "
            "download, then report whether channel names, bank names, and "
            "settings appear correctly."
        )
        return prompts
