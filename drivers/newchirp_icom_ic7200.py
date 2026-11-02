# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Icom IC-7200 CI-V support with a corrected memory field grammar."""

from chirp import directory
from chirp.drivers import icomciv


directory.enable_reregistrations()

IC7200_MEM_FORMAT = """
bbcd number[2];
u8   unknown:3,
     split:1,
     unknown_0:4;
lbcd freq[5];
u8   unknown2:5,
     mode:3;
u8   filter;
u8   unknown_1:3,
     dig:1,
     unknown_2:4;
"""


class IC7200MemFrame(icomciv.MemFrame):
    """Use valid bitwise continuation punctuation for IC-7200 records."""

    FORMAT = IC7200_MEM_FORMAT


@directory.register
class NewChirpIcom7200Radio(icomciv.Icom7200Radio):
    """Icom IC-7200 using the corrected shared CI-V memory frame."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._classes["mem"] = IC7200MemFrame
