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

"""Keep UV-17ProGPS reads usable when a stored CTCSS value is malformed.

Some firmware stores a nonstandard or reserved CTCSS value in an active
channel record. Upstream CHIRP decodes that word as a large tone frequency and
then rejects the whole channel. Preserve the channel and bytes while exposing
the field as no tone until the user deliberately selects a valid CTCSS value.
"""

import logging

from chirp import chirp_common
from chirp.drivers import baofeng_uv17Pro


LOG = logging.getLogger(__name__)
_ORIGINAL_DECODE_TONE = baofeng_uv17Pro.UV17Pro.decode_tone
_ORIGINAL_SET_MEMORY = baofeng_uv17Pro.UV17ProGPS.set_memory
_TONE_FIELDS = ("tmode", "rtone", "ctone", "dtcs", "rx_dtcs",
                "cross_mode", "dtcs_polarity")


def _invalid_ctcss(value):
    try:
        return int(value) not in chirp_common.TONES
    except (TypeError, ValueError):
        return True


def _decode_tone(self, value):
    try:
        mode, decoded, polarity = _ORIGINAL_DECODE_TONE(self, value)
    except (IndexError, TypeError, ValueError):
        return "", 0, "N"
    if mode == "Tone" and _invalid_ctcss(decoded):
        LOG.warning(
            "Treating malformed UV-17ProGPS CTCSS value %r as no tone",
            decoded,
        )
        return "", 0, "N"
    return mode, decoded, polarity


_decode_tone.newchirp_uv17progps_malformed_ctcss = True


def _has_invalid_stored_ctcss(self, value):
    try:
        mode, decoded, _polarity = _ORIGINAL_DECODE_TONE(self, value)
    except (IndexError, TypeError, ValueError):
        return False
    return mode == "Tone" and _invalid_ctcss(decoded)


def _tone_state(memory):
    return tuple(getattr(memory, field, None) for field in _TONE_FIELDS)


def _set_memory(self, memory):
    raw_memory = self._get_raw_memory(memory.number)
    original_tx_tone = int(raw_memory.txtone)
    original_rx_tone = int(raw_memory.rxtone)
    baseline = chirp_common.Memory()
    baseline.number = memory.number
    if not memory.empty:
        self.get_memory_common(raw_memory, raw_memory.name, baseline)
    original_tone_state = _tone_state(baseline)
    empty = bool(memory.empty)

    _ORIGINAL_SET_MEMORY(self, memory)

    if empty or _tone_state(memory) != original_tone_state:
        return
    if _has_invalid_stored_ctcss(self, original_tx_tone):
        raw_memory.txtone.set_value(original_tx_tone)
    if _has_invalid_stored_ctcss(self, original_rx_tone):
        raw_memory.rxtone.set_value(original_rx_tone)


_set_memory.newchirp_uv17progps_malformed_ctcss = True


if not getattr(
    baofeng_uv17Pro.UV17ProGPS.decode_tone,
    "newchirp_uv17progps_malformed_ctcss",
    False,
):
    baofeng_uv17Pro.UV17ProGPS.decode_tone = _decode_tone

if not getattr(
    baofeng_uv17Pro.UV17ProGPS.set_memory,
    "newchirp_uv17progps_malformed_ctcss",
    False,
):
    baofeng_uv17Pro.UV17ProGPS.set_memory = _set_memory
