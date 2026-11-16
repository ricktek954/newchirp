# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""Keep KG-UV8D maps readable when a DCS word uses reserved code bits.

The stock decoder converts every DCS word into an octal code before assigning
it to CHIRP's Memory object. A stored word with all eleven code bits set
becomes invalid code 3777 and aborts the complete channel-map decode. Preserve
the word in the image while exposing that side of the channel as no tone.
"""

import logging

from chirp import chirp_common
from chirp.drivers import kguv8d


LOG = logging.getLogger(__name__)

_DCS_BASE = 0x2800
_DCS_CODE_MASK = 0x07FF
_NO_TONE = 0xFFFF
_ORIGINAL_GET_MEMORY = kguv8d.KGUV8DRadio.get_memory
_ORIGINAL_SET_MEMORY = kguv8d.KGUV8DRadio.set_memory
_TONE_FIELDS = (
    "tmode",
    "rtone",
    "ctone",
    "dtcs",
    "rx_dtcs",
    "cross_mode",
    "dtcs_polarity",
)


def _invalid_dcs_word(value):
    value = int(value)
    if value in (0, _NO_TONE):
        return False
    if (value & _DCS_BASE) != _DCS_BASE:
        return False
    code = int("%03o" % (value & _DCS_CODE_MASK))
    return code not in chirp_common.ALL_DTCS_CODES


def _invalid_tone_words(raw_memory):
    invalid = {}
    for field in ("txtone", "rxtone"):
        value = int(getattr(raw_memory, field))
        if _invalid_dcs_word(value):
            invalid[field] = value
            getattr(raw_memory, field).set_value(_NO_TONE)
    return invalid


def _restore_tone_words(raw_memory, invalid):
    for field, value in invalid.items():
        getattr(raw_memory, field).set_value(value)


def _get_memory(self, number):
    raw_memory = self._memobj.memory[number]
    invalid = _invalid_tone_words(raw_memory)
    try:
        return _ORIGINAL_GET_MEMORY(self, number)
    finally:
        _restore_tone_words(raw_memory, invalid)


_get_memory.newchirp_kg_uv8d_reserved_dcs = True


def _tone_state(memory):
    return tuple(getattr(memory, field, None) for field in _TONE_FIELDS)


def _set_memory(self, memory):
    raw_memory = self._memobj.memory[memory.number]
    invalid = {}
    baseline_state = None
    if not memory.empty:
        invalid = _invalid_tone_words(raw_memory)
        try:
            baseline_state = _tone_state(_get_memory(self, memory.number))
        finally:
            _restore_tone_words(raw_memory, invalid)

    _ORIGINAL_SET_MEMORY(self, memory)

    if (
        not memory.empty
        and baseline_state is not None
        and _tone_state(memory) == baseline_state
    ):
        _restore_tone_words(raw_memory, invalid)


_set_memory.newchirp_kg_uv8d_reserved_dcs = True


if not getattr(
    kguv8d.KGUV8DRadio.get_memory,
    "newchirp_kg_uv8d_reserved_dcs",
    False,
):
    kguv8d.KGUV8DRadio.get_memory = _get_memory

if not getattr(
    kguv8d.KGUV8DRadio.set_memory,
    "newchirp_kg_uv8d_reserved_dcs",
    False,
):
    kguv8d.KGUV8DRadio.set_memory = _set_memory
