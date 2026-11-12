# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Correct the Yaesu FTM-7250D transmit-power encoding.

The pinned CHIRP driver correctly decodes this model's stored power codes as
1=Low, 2=Mid, 3=High, but inherited an encoder that writes the inverse values.
Selecting Low therefore wrote the code the radio displays as High.
"""

from chirp import directory
from chirp.drivers import ftm7250d


directory.enable_reregistrations()


@directory.register
class NewChirpFTM7250Radio(ftm7250d.FTM7250Radio):
    """Yaesu FTM-7250D with CPS-compatible power encoding."""

    def _encode_power_level(self, mem):
        if mem.power is None:
            return 1
        return ftm7250d.POWER_LEVELS.index(mem.power) + 1
