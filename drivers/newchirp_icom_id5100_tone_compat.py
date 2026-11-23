# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Decode every ID-4100/ID-5100 tone mode instead of aborting the read.

The radios store a 4-bit tone mode. Upstream CHIRP's table names value 8
"DTCS-T" (DTCS encode only, the radio's "DTCS(T)" setting) and values 2 and 4
"2??"/"4??" (TSQL and DTCS with pocket beep). None of those is a CHIRP tone
mode, so one channel set that way fails the whole read with
"`DTCS-T' is not in valid list".

- DTCS-T is CHIRP's cross mode "DTCS->" (DTCS on transmit, open receive).
- Pocket-beep TSQL/DTCS show as TSQL/DTCS, and an unchanged channel keeps
  its pocket-beep value when written back.
- TSQL-R and DTCS-R, which the radio already stored and CHIRP decoded, are
  offered for editing too.
"""

from chirp.drivers import id5100


_ENCODE = list(id5100.TMODES)
_ENCODE[8] = "DTCS->"
_DECODE = list(_ENCODE)
_DECODE[2] = "TSQL"
_DECODE[4] = "DTCS"
_DECODE += [""] * (16 - len(_DECODE))  # Undefined values read as no tone.
_POCKET_BEEP = {"TSQL": 2, "DTCS": 4}

_ORIGINAL_GET_MEMORY = id5100.ID4100Radio.get_memory
_ORIGINAL_SET_MEMORY = id5100.ID4100Radio.set_memory
_ORIGINAL_GET_FEATURES = id5100.ID4100Radio.get_features


def _with_tmodes(table, func, *args):
    saved = id5100.TMODES
    id5100.TMODES = table
    try:
        return func(*args)
    finally:
        id5100.TMODES = saved


def _get_memory(self, number):
    return _with_tmodes(_DECODE, _ORIGINAL_GET_MEMORY, self, number)


def _set_memory(self, mem):
    _num, raw = self._get_raw_memory(mem.number)
    previous = int(raw.tmode)
    _with_tmodes(_ENCODE, _ORIGINAL_SET_MEMORY, self, mem)
    if mem.empty:
        return
    beep = _POCKET_BEEP.get(mem.tmode)
    if beep is not None and previous == beep:
        raw.tmode = beep


def _get_features(self):
    rf = _with_tmodes(_ENCODE, _ORIGINAL_GET_FEATURES, self)
    for mode in ("TSQL-R", "DTCS-R"):
        if mode not in rf.valid_tmodes:
            rf.valid_tmodes.insert(rf.valid_tmodes.index("Cross"), mode)
    return rf


_get_memory.newchirp_id5100_tones = True
if not getattr(id5100.ID4100Radio.get_memory, "newchirp_id5100_tones", False):
    id5100.ID4100Radio.get_memory = _get_memory
    id5100.ID4100Radio.set_memory = _set_memory
    id5100.ID4100Radio.get_features = _get_features
