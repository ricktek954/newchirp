# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Keep TH-9800 reads usable when an unused tone field is malformed.

Some TH-9800-family images contain active channel records whose CTCSS field
or DTCS field holds a reserved value even though the channel does not use that
tone mode. Upstream CHIRP assigns both fields unconditionally, and the Memory
validator aborts the whole read. Preserve the channel and use a safe default
when the stored value cannot be represented.
"""

from chirp import chirp_common
from chirp.drivers import th9800


_ORIGINAL_GET_MEMORY = th9800.TYTTH9800Base.get_memory
_DEFAULT_TONE = 88.5
_DEFAULT_DTCS = 23
_TONE_FIELDS = ("rtone", "ctone", "dtcs")
_TONE_VALIDATION_ERRORS = (
    "is not a valid value for `ctone'",
    "is not a valid value for `dtcs'",
)


def _is_malformed_tone_error(self, number, exc):
    message = str(exc)
    if any(fragment in message for fragment in _TONE_VALIDATION_ERRORS):
        return True
    if not message.startswith("`") or "' is not in valid list:" not in message:
        return False

    value = message[1:message.index("'")]
    mem = self._memobj.memory[number - 1]
    expected = {
        str(int(mem.ctcss) / 10.0),
        str(int(mem.dtcs)),
    }
    return value in expected


def _get_memory(self, number):
    try:
        return _ORIGINAL_GET_MEMORY(self, number)
    except ValueError as exc:
        if not _is_malformed_tone_error(self, number, exc):
            raise

    # Temporarily bypass the tone validators so the upstream decoder can finish
    # constructing the rest of the memory. Unsupported values are replaced with
    # safe defaults immediately afterwards while the original image bytes stay
    # untouched.
    old_validators = {
        field: chirp_common.Memory._valid_map[field] for field in _TONE_FIELDS
    }
    for field in _TONE_FIELDS:
        chirp_common.Memory._valid_map[field] = lambda _value: True
    try:
        memory = _ORIGINAL_GET_MEMORY(self, number)
    finally:
        for field, validator in old_validators.items():
            chirp_common.Memory._valid_map[field] = validator

    if not chirp_common.VALIDTONE(memory.ctone):
        memory.rtone = _DEFAULT_TONE
        memory.ctone = _DEFAULT_TONE
    if memory.dtcs not in chirp_common.ALL_DTCS_CODES:
        memory.dtcs = _DEFAULT_DTCS
    return memory


_get_memory.newchirp_tolerant_tone = True
if not getattr(
    th9800.TYTTH9800Base.get_memory,
    "newchirp_tolerant_tone",
    False,
):
    th9800.TYTTH9800Base.get_memory = _get_memory
