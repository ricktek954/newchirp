# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""VX-170/VX-177 override that decodes the split-tone squelch modes.

The memory's ``tmode`` field is 3 bits, but stock CHIRP lists only five
values ("", Tone, TSQL, TSQL-R, DTCS), so a channel stored with one of the
radio's split-tone modes raised ``IndexError`` and the whole read failed
(upstream CHIRP #11624 log: ``ft7800.py`` ``get_memory``
``self.TMODES[_mem.tmode]``; NewChirp ledger ``w-20261122-28ff``).

Evidence for values 5-7, in order:

* VX-170 Operating Manual, Set Mode Item 44 SQL.TYP (printed p. 79):
  OFF / TONE / TSQL / REV TN / DCS, and with Item 43 SPLIT on, the extra
  parameters "D" (DCS encode only), "T DCS" (CTCSS encode, DCS decode) and
  "D TSQL" (DCS encode, CTCSS decode), listed after DCS.
* CHIRP's FT-60 driver, same Yaesu generation and the same ``tmode:3``
  byte layout, maps 5-7 to ``DTCS->``, ``Tone->DTCS`` and ``DTCS->Tone``.

No OEM CPS exists for this radio (only RT Systems ADMS-VX170), so this is
manual- and sibling-driver evidence, not CPS or hardware evidence.
"""

from chirp import directory
from chirp.drivers import vx170


SPLIT_TMODES = ["DTCS->", "Tone->DTCS", "DTCS->Tone"]
BASE_TMODES = ["", "Tone", "TSQL", "TSQL-R", "DTCS"]


class _SplitToneMixin:
    """Raw tmode 0-4 stay with the stock code; 5-7 become CHIRP Cross.

    ``chirp_common.Memory`` rejects "DTCS->" as a tmode, so the stock
    get/set paths only ever see a base mode, and the split value is applied
    to the raw field around them (as CHIRP's FT-60 driver encodes it).
    """

    def get_features(self):
        rf = super().get_features()
        rf.has_cross = True
        rf.valid_tmodes = BASE_TMODES + ["Cross"]
        rf.valid_cross_modes = list(SPLIT_TMODES)
        return rf

    def get_memory(self, number):
        _mem = self._memobj.memory[number - 1]
        raw = int(_mem.tmode)
        if raw < len(BASE_TMODES):
            return super().get_memory(number)
        _mem.tmode = 0
        try:
            mem = super().get_memory(number)
        finally:
            _mem.tmode = raw
        if not mem.empty:
            mem.tmode = "Cross"
            mem.cross_mode = SPLIT_TMODES[raw - len(BASE_TMODES)]
        return mem

    def set_memory(self, mem):
        if mem.empty or mem.tmode != "Cross":
            return super().set_memory(mem)
        base = mem.dupe()
        base.tmode = ""
        result = super().set_memory(base)
        self._memobj.memory[mem.number - 1].tmode = (
            len(BASE_TMODES) + SPLIT_TMODES.index(mem.cross_mode)
        )
        return result


directory.enable_reregistrations()


@directory.register
class VX170Radio(_SplitToneMixin, vx170.VX170Radio):
    """Yaesu VX-170 with split-tone squelch modes."""


@directory.register
class VX177Radio(_SplitToneMixin, vx170.VX177Radio):
    """Yaesu VX-177 with split-tone squelch modes."""
