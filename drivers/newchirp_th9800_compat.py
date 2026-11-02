# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Keep TH-9800 reads usable when an unused tone field is malformed.

Some TH-9800-family images contain active channel records whose CTCSS field
holds a reserved value even though the channel does not use a tone. Upstream
CHIRP assigns that field unconditionally, and the Memory validator aborts the
whole read. Preserve the channel and use the default tone value when the
stored value cannot be represented safely.
"""

from chirp import chirp_common
from chirp.drivers import th9800


_ORIGINAL_GET_MEMORY = th9800.TYTTH9800Base.get_memory
_DEFAULT_TONE = 88.5
_CTONE_ERROR = "is not a valid value for `ctone'"


def _get_memory(self, number):
    try:
        return _ORIGINAL_GET_MEMORY(self, number)
    except ValueError as exc:
        if _CTONE_ERROR not in str(exc):
            raise

    # Temporarily bypass the two tone validators so the upstream decoder can
    # finish constructing the rest of the memory. The unsupported value is
    # replaced with NewChirp's conservative default immediately afterwards.
    old_rtone = chirp_common.Memory._valid_map["rtone"]
    old_ctone = chirp_common.Memory._valid_map["ctone"]
    chirp_common.Memory._valid_map["rtone"] = lambda _value: True
    chirp_common.Memory._valid_map["ctone"] = lambda _value: True
    try:
        memory = _ORIGINAL_GET_MEMORY(self, number)
    finally:
        chirp_common.Memory._valid_map["rtone"] = old_rtone
        chirp_common.Memory._valid_map["ctone"] = old_ctone

    if not chirp_common.VALIDTONE(memory.ctone):
        memory.rtone = _DEFAULT_TONE
        memory.ctone = _DEFAULT_TONE
    return memory


_get_memory.newchirp_tolerant_tone = True
if not getattr(
    th9800.TYTTH9800Base.get_memory,
    "newchirp_tolerant_tone",
    False,
):
    th9800.TYTTH9800Base.get_memory = _get_memory
