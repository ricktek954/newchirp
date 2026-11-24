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

5RX and UV-S9X3: the official Baofeng UV-5RX CPS 20231124 (baofengradio.com;
ZIP SHA-256 4848128a68dcb0d2ddfa54c65ad43591718d8e9e3b62112691ff6cd60926590a,
BF_5R_ThreeBand.exe, identity 50 BB FF 20 12 07 25 = CHIRP MSTRING_UVS9X3)
writes record byte 14 as 0 for High and 1 for Low (WriFreq.GetCHTxPower) and
reads Low from bit 0 (WriFreq.GetCHOtherImf). Stock CHIRP writes Low as 2,
which that CPS reads as High. These two models now decode and encode power
the CPS way.

Other radios: what an unrecognised value means is not known, so the channel
is shown at the first (High) level, the fallback stock CHIRP intended.

In both cases a channel whose power is not edited keeps its original raw
value on write, so opening and saving never changes the radio's setting.

Tones: stock decodes any tone word >= 0x0258 as CTCSS value/10 and indexes
DTCS_CODES for smaller ones, so a corrupt word fails the whole download. A
2026-11-24 5RX report (NewChirp 1.0.71, INBOX:969) stopped at "`6532.8' is
not a valid value for `ctone'" (rxtone 0xFF30). The Baofeng UV-5RX CPS
(WriFreq.CaculateCTCSS_HexToStr) treats a word as off only when its low byte
is 0x00 or 0xFF and would show this one as 6532.8 too, so it is bad data in
that channel, not another encoding. Such a word is now shown as no tone and
its raw value is written back unless the channel's tones are edited.
"""

import logging

from chirp import chirp_common
from chirp.drivers import baofeng_common, baofeng_wp970i


LOG = logging.getLogger(__name__)

_Base = baofeng_common.BaofengCommonHT
_current_get = _Base.get_memory
_original_get = getattr(_current_get, "newchirp_original", _current_get)
_current_set = _Base.set_memory
_original_set = getattr(_current_set, "newchirp_original", _current_set)


CPS_LOW_BIT = 0x01


def _uses_cps_power(radio):
    return getattr(type(radio), "_newchirp_cps_power", False)


def _power_known(radio, value):
    if _uses_cps_power(radio):
        return True
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


def _tone_known(radio, raw):
    if raw in (0, 0xFFFF):
        return True
    if raw >= 0x0258:
        return raw / 10.0 in chirp_common.TONES
    index = raw - 0x6A if raw >= 0x6A else raw - 1
    return 0 <= index < len(radio.DTCS_CODES)


def _unknown_tones(radio):
    store = getattr(radio, "_newchirp_unknown_tones", None)
    if store is None:
        store = {}
        radio._newchirp_unknown_tones = store
    return store


def _tone_state(mem):
    return (mem.tmode, mem.rtone, mem.ctone, mem.dtcs, mem.rx_dtcs,
            mem.dtcs_polarity, mem.cross_mode)


def _get_memory_keeping_power(self, number):
    _mem = self._memobj.memory[number]
    if _mem.get_raw()[:1] == b"\xff":
        return _original_get(self, number)
    bad = {field: int(getattr(_mem, field))
           for field in ("txtone", "rxtone")
           if not _tone_known(self, int(getattr(_mem, field)))}
    if not bad:
        _unknown_tones(self).pop(number, None)
        return _get_memory_power(self, number)
    for field in bad:
        setattr(_mem, field, 0)
    try:
        mem = _get_memory_power(self, number)
    finally:
        for field, raw in bad.items():
            setattr(_mem, field, raw)
    _unknown_tones(self)[number] = (bad, _tone_state(mem))
    LOG.warning(
        "%s channel %i: invalid tone word(s) %s shown as no tone and kept "
        "unchanged unless the tones are edited", self.MODEL, number,
        ", ".join("%s=0x%04X" % item for item in sorted(bad.items())))
    return mem


def _get_memory_power(self, number):
    _mem = self._memobj.memory[number]
    raw = int(_mem.lowpower)
    if _uses_cps_power(self):
        shown = (baofeng_common.TXPOWER_LOW if raw & CPS_LOW_BIT
                 else baofeng_common.TXPOWER_HIGH)
    elif _power_known(self, raw):
        _unknown_powers(self).pop(number, None)
        return _original_get(self, number)
    else:
        shown = baofeng_common.TXPOWER_HIGH
    _mem.lowpower = shown
    try:
        mem = _original_get(self, number)
    finally:
        _mem.lowpower = raw
    _unknown_powers(self)[number] = (raw, mem.power)
    if _uses_cps_power(self):
        return mem
    LOG.warning(
        "%s channel %i: unrecognised power value %i shown as %s and kept "
        "unchanged unless the power is edited",
        self.MODEL, number, raw, mem.power)
    return mem


def _set_memory_keeping_power(self, mem):
    tones = _unknown_tones(self).pop(mem.number, None)
    result = _set_memory_power(self, mem)
    if tones is not None and not mem.empty:
        bad, state = tones
        if _tone_state(mem) == state:        # tones not edited
            _mem = self._memobj.memory[mem.number]
            for field, raw in bad.items():
                setattr(_mem, field, raw)
            _unknown_tones(self)[mem.number] = tones
    return result


def _set_memory_power(self, mem):
    kept = _unknown_powers(self).get(mem.number)
    result = _original_set(self, mem)
    if mem.empty:
        _unknown_powers(self).pop(mem.number, None)
        return result
    _mem = self._memobj.memory[mem.number]
    if kept is not None and mem.power is not None and mem.power == kept[1]:
        _mem.lowpower = kept[0]          # power not edited: keep the radio's
        return result
    _unknown_powers(self).pop(mem.number, None)
    if _uses_cps_power(self):
        # CPS GetCHTxPower: High 0, Low 1
        _mem.lowpower = (CPS_LOW_BIT
                         if int(_mem.lowpower) == baofeng_common.TXPOWER_LOW
                         else 0)
    return result


_get_memory_keeping_power.newchirp_original = _original_get
_set_memory_keeping_power.newchirp_original = _original_set
_Base.get_memory = _get_memory_keeping_power
_Base.set_memory = _set_memory_keeping_power

baofeng_wp970i.BF5RXRadio._newchirp_cps_power = True
baofeng_wp970i.UVS9X3._newchirp_cps_power = True
