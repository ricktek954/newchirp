# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Make Kenwood live-mode writes safe on a freshly opened connection.

Stock ``KenwoodLiveRadio.set_memory`` runs ``del self._memcache[number]``
before sending ``ME``/``MW``. NewChirp opens a new radio instance for each
write, so the cache is empty and the first channel raises ``KeyError``.
The error text is just the channel number (``0``), so the user sees
"Reported error: 0" and nothing is written.

Stock ``erase_memory`` returns early for any slot that is not cached. On a
fresh connection, every channel the user deleted was silently left on the
radio. The erase path now reads the slot first and erases it only when the
radio actually holds a memory there.
"""

import logging

from chirp.drivers import kenwood_live


LOG = logging.getLogger(__name__)

_original_set_memory = kenwood_live.KenwoodLiveRadio.set_memory
_original_erase_memory = kenwood_live.KenwoodLiveRadio.erase_memory

_PLACEHOLDER = object()


def _set_memory_without_cache_requirement(self, memory):
    number = memory.number
    inserted = number not in self._memcache
    if inserted:
        # Stock code only needs the key to exist so it can delete it.
        self._memcache[number] = _PLACEHOLDER
    try:
        return _original_set_memory(self, memory)
    finally:
        if self._memcache.get(number) is _PLACEHOLDER:
            # Stock code raised before reaching its delete. Never leave the
            # placeholder where get_memory could return it.
            del self._memcache[number]


def _erase_memory_reading_uncached_slot(self, number):
    if number not in self._memcache:
        current = self.get_memory(number)
        if current is None or current.empty:
            return None
        LOG.info("Erasing uncached Kenwood live memory %s", number)
    return _original_erase_memory(self, number)


if not getattr(
    kenwood_live.KenwoodLiveRadio.set_memory,
    "newchirp_cache_safe",
    False,
):
    _set_memory_without_cache_requirement.newchirp_cache_safe = True
    _erase_memory_reading_uncached_slot.newchirp_cache_safe = True
    kenwood_live.KenwoodLiveRadio.set_memory = (
        _set_memory_without_cache_requirement
    )
    kenwood_live.KenwoodLiveRadio.erase_memory = (
        _erase_memory_reading_uncached_slot
    )
