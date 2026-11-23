# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Keep unexpected channel power values from failing Baofeng reads.

Stock CHIRP ``BaofengCommonHT.get_memory`` (pinned 21e42e45 and upstream
kk7ds/chirp as of 2026-11-23) handles a power field it does not recognise by
logging ``_mem.power``, a field that does not exist. The log line itself
raises "No attribute power in struct memory", so one channel with an
unexpected value fails the whole download. Tri-band radios (5RX, UV-S9X3,
BF-A58S) only expect 0 (High) and 2 (Low); other radios expect an index
into their power list. A 2026-11-23 5RX report (NewChirp 1.0.68, INBOX:922)
hit this after a successful read.

What the radio means by the other values is not known yet (no CPS or image
from that radio), so this override does not guess. The channel is shown at
the first (High) power level, the fallback stock CHIRP intended, and the
original raw value is written back unless the user changes the power.
"""

import logging

from chirp.drivers import baofeng_common


LOG = logging.getLogger(__name__)

_Base = baofeng_common.BaofengCommonHT
_current_get = _Base.get_memory
_original_get = getattr(_current_get, "newchirp_original", _current_get)
_current_set = _Base.set_memory
_original_set = getattr(_current_set, "newchirp_original", _current_set)


def _power_known(radio, value):
    if radio._tri_band:
        return value in (baofeng_common.TXPOWER_HIGH,
                         baofeng_common.TXPOWER_LOW)
    return value < len(radio.POWER_LEVELS)


def _unknown_powers(radio):
    store = getattr(radio, "_newchirp_unknown_power", None)
    if store is None:
        store = {}
        radio._newchirp_unknown_power = store
    return store


def _get_memory_keeping_power(self, number):
    _mem = self._memobj.memory[number]
    if _mem.get_raw()[:1] == b"\xff":
        return _original_get(self, number)
    raw = int(_mem.lowpower)
    if _power_known(self, raw):
        _unknown_powers(self).pop(number, None)
        return _original_get(self, number)
    _mem.lowpower = baofeng_common.TXPOWER_HIGH
    try:
        mem = _original_get(self, number)
    finally:
        _mem.lowpower = raw
    _unknown_powers(self)[number] = raw
    LOG.warning(
        "%s channel %i: unrecognised power value %i shown as %s and kept "
        "unchanged unless the power is edited",
        self.MODEL, number, raw, mem.power)
    return mem


def _set_memory_keeping_power(self, mem):
    raw = _unknown_powers(self).get(mem.number)
    result = _original_set(self, mem)
    if raw is not None:
        if (not mem.empty and mem.power is not None
                and mem.power == self.POWER_LEVELS[0]):
            self._memobj.memory[mem.number].lowpower = raw
        else:
            _unknown_powers(self).pop(mem.number, None)
    return result


_get_memory_keeping_power.newchirp_original = _original_get
_set_memory_keeping_power.newchirp_original = _original_set
_Base.get_memory = _get_memory_keeping_power
_Base.set_memory = _set_memory_keeping_power
