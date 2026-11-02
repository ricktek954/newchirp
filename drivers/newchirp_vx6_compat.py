# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Keep VX-6 reads usable when one stored frequency is not programmable.

The VX-6 memory flags can retain a record whose stored frequency is not on a
supported tuning step. Upstream CHIRP raises while decoding that one slot,
which discards an otherwise complete radio read. Treat only slots that fail
CHIRP's frequency correction as empty; the original image bytes remain
untouched.
"""

from chirp import chirp_common, errors
from chirp.drivers import vx6


_ORIGINAL_GET_MEMORY = vx6.VX6Radio.get_memory
_ROUNDING_ERROR = "Unable to correct rounded frequency"


def _get_memory(self, number):
    try:
        return _ORIGINAL_GET_MEMORY(self, number)
    except errors.InvalidDataError as exc:
        if _ROUNDING_ERROR not in str(exc):
            raise

    memory = chirp_common.Memory(number=number, empty=True)
    memory.power = vx6.POWER_LEVELS[0]
    return memory


_get_memory.newchirp_tolerant_frequency = True
if not getattr(
    vx6.VX6Radio.get_memory,
    "newchirp_tolerant_frequency",
    False,
):
    vx6.VX6Radio.get_memory = _get_memory
