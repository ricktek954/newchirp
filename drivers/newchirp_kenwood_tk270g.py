# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Normalize unprogrammed TK-270G bank indexes during channel decoding."""

from chirp.drivers import tk760g


_ORIGINAL_GET_MEMORY = tk760g.TK270G_Radios.get_memory


def _get_memory(self, number):
    _mem = self._memobj.memory[number - 1]
    if int(_mem.bnumb) > 127:
        # Match the driver's existing defaults for a channel whose bank
        # metadata was never assigned.
        _mem.bnumb = number - 1
        _mem.bank = 1
    return _ORIGINAL_GET_MEMORY(self, number)


_get_memory.newchirp_tk270g_bank_index = True
if not getattr(
    tk760g.TK270G_Radios.get_memory,
    "newchirp_tk270g_bank_index",
    False,
):
    tk760g.TK270G_Radios.get_memory = _get_memory
