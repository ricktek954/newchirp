# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Make CHIRP's fixed-zone (StaticBankModel) radios report their zones.

Stock ``StaticBankModel.get_mapping_memories`` sizes each bank with ``/``,
so ``range()`` receives a float (100.0) and raises ``TypeError``. NewChirp's
bridge treats a failing bank model as unsafe and drops it, so radios whose
zones are fixed blocks of channels (BF-F8HP-PRO, UV-17ProGPS family, GM-32,
RT-910 and others) never showed which zone a channel belongs to
(2026-11-19 BF-F8HP-PRO forum report). Zones stay read-only: a channel's
zone is set by its channel number.
"""

from chirp import chirp_common


_ORIGINAL_INIT = chirp_common.StaticBankModel.__init__


def _init(self, radio, name="Banks", banks=10):
    _ORIGINAL_INIT(self, radio, name="Zones" if name == "Banks" else name,
                   banks=banks)
    # Every radio using this model (Baofeng, Radioddity, Radtel and Bajeton
    # fixed-block radios) calls each block a zone in its vendor software.
    self._banks = [
        chirp_common.StaticBank(self, index + 1, "Zone %i" % (index + 1))
        for index in range(self._num_banks)
    ]


def _bank_span(model):
    low, high = model._rf.memory_bounds
    return low, (high - low + 1) // model._num_banks


def _get_mapping_memories(self, bank):
    low, count = _bank_span(self)
    first = low + (bank.get_index() - 1) * count
    return [self._radio.get_memory(first + offset) for offset in range(count)]


def _get_memory_mappings(self, memory):
    low, count = _bank_span(self)
    index = (memory.number - low) // count
    if 0 <= index < len(self._banks):
        return [self._banks[index]]
    return []


if not getattr(chirp_common.StaticBankModel, "newchirp_integer_spans", False):
    chirp_common.StaticBankModel.newchirp_integer_spans = True
    chirp_common.StaticBankModel.__init__ = _init
    chirp_common.StaticBankModel.get_mapping_memories = _get_mapping_memories
    chirp_common.StaticBankModel.get_memory_mappings = _get_memory_mappings
