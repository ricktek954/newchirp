# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Allow simplex or repeater operation on UV-5G Mini GMRS channels 15-22."""

from chirp.drivers import baofeng_uv17Pro


_ORIGINAL_GET_MEMORY = baofeng_uv17Pro.UV5GMini.get_memory


def _get_memory(self, number):
    if not 15 <= number <= 22:
        return _ORIGINAL_GET_MEMORY(self, number)

    presets = getattr(baofeng_uv17Pro, "UV5G_GMRS_PRESETS", ())
    if number > len(presets):
        return _ORIGINAL_GET_MEMORY(self, number)

    # The upstream UV-5G Mini path forces these eight GMRS output
    # frequencies to +5 MHz and marks both duplex and offset immutable.
    # Decode the stored transmit frequency through the parent implementation
    # instead so simplex and repeater assignments survive a write/read cycle.
    mem = baofeng_uv17Pro.UV5RMini.get_memory(self, number)
    mem.freq = presets[number - 1]
    mem.immutable = ["freq"]
    return mem


_get_memory.newchirp_uv5g_mini_duplex = True
if not getattr(
    baofeng_uv17Pro.UV5GMini.get_memory,
    "newchirp_uv5g_mini_duplex",
    False,
):
    baofeng_uv17Pro.UV5GMini.get_memory = _get_memory
