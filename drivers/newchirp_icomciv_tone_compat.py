# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Tolerate unset CTCSS tones in CHIRP's live Icom CI-V drivers.

``icomciv`` decodes a channel's tone with ``mem.rtone = value / 10``. An
Icom that has never had a tone set on a channel reports 0, so the decode
raises ``'0.0' is not a valid value for 'rtone'``. CHIRP's GUI shows that one
channel as an error, but NewChirp reads every channel in one pass, so the
whole IC-910 read stopped (2026-11-19 report, mailbox INBOX:810).

Every memory frame's parsed object is wrapped so that a tone field holding
a value that is not a standard CTCSS tone reads as 88.5 Hz, CHIRP's default.
The tone is unused on such a channel. Writes still go to the real frame.
"""

from chirp import chirp_common
from chirp.drivers import icomciv


_TONE_FIELDS = frozenset(("rtone", "ctone", "rtone_tx", "ctone_tx"))
_DEFAULT_TONE = 885  # tenths of a hertz


class _ToneSafeMemory:
    """Delegate to a bitwise memory object, sanitizing tone reads."""

    __slots__ = ("_newchirp_obj",)

    def __init__(self, obj):
        object.__setattr__(self, "_newchirp_obj", obj)

    def __getattr__(self, name):
        value = getattr(self._newchirp_obj, name)
        if name in _TONE_FIELDS:
            try:
                if int(value) / 10.0 not in chirp_common.TONES:
                    return _DEFAULT_TONE
            except (TypeError, ValueError):
                return _DEFAULT_TONE
        return value

    def __setattr__(self, name, value):
        setattr(self._newchirp_obj, name, value)

    def __getitem__(self, key):
        return self._newchirp_obj[key]

    def __repr__(self):
        return repr(self._newchirp_obj)


def _wrap(get_obj):
    def get_tone_safe_obj(self):
        return _ToneSafeMemory(get_obj(self))

    get_tone_safe_obj.newchirp_tone_safe = True
    return get_tone_safe_obj


def _frame_classes(root):
    pending = [root]
    while pending:
        cls = pending.pop()
        yield cls
        pending.extend(cls.__subclasses__())


def _patch():
    # Includes NewChirp's own frame classes (IC-7200, IC-9700), which load
    # before this module.
    for cls in _frame_classes(icomciv.MemFrame):
        own = cls.__dict__.get("get_obj")
        if own is not None and not getattr(own, "newchirp_tone_safe", False):
            cls.get_obj = _wrap(own)


_patch()
