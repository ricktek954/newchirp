# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Experimental, read-only AnyTone AT-D878UVII Plus driver.

The D878UVII Plus uses the same AnyTone serial session as the D578UV
(PROGRAM -> QX06, 02 -> "I" model[7] bands version 06, 16-byte R/W frames,
END) and the same conventional channel and zone map. Evidence:

- Official AnyTone package "D878UVII PLUS V4.00 official release 250815"
  (BridgeCom; ZIP SHA-256
  5ba14d88cebef105365e8977529a5817d1d163a9e9eccc5156ccd9575be500e6), CPS
  D878UVII.exe (SHA-256
  4e7f8b4d6e119b8b9ef0a4ffd82aef2bd83d1887d11e5651596b86f371711005): holds
  the "D878UV2" model string and the channel-bitmap (0x024C1500),
  zone-bitmap (0x024C1300) and zone-name (0x02540000) addresses as
  constants.
- QDMR commit fb9c96af53f646c0706fa360209b2e0e6cd79a08: anytone_interface.cc
  maps "D878UV2" to the D878UVII; D878UV2Codeplug inherits the D878UV and
  D868UV channel/zone layout (128 channels per 0x40000 bank, 64-byte
  records whose bytes 0x00-0x33 match the D578UV fields read here).

Read-only until a physical read and a controlled write/read-back are
compared with the official CPS (ledger w-20261123-2772).
"""

import importlib
import sys

from chirp import chirp_common, directory, errors

try:
    _BASE = sys.modules["newchirp.drivers.newchirp_anytone_d578uviii"]
except KeyError:
    try:
        _BASE = importlib.import_module(
            "newchirp.drivers.newchirp_anytone_d578uviii")
    except ModuleNotFoundError:
        _BASE = importlib.import_module(
            ".newchirp_anytone_d578uviii", __package__)


D878_POWER_LEVELS = [
    chirp_common.PowerLevel("Low", watts=1),
    chirp_common.PowerLevel("Mid", watts=2.5),
    chirp_common.PowerLevel("High", watts=5),
    chirp_common.PowerLevel("Turbo", watts=7),
]


@directory.register
class AnyToneD878UVIIPlusRadio(_BASE.AnyToneD578UVIIIPlusRadio):
    """AnyTone AT-D878UVII Plus dual-band DMR handheld (read-only)."""

    MODEL = "AT-D878UVII Plus"
    _model = "D878UV2"
    _model_ids = ("D878UV2",)
    _family = "D878UVII"
    # Read-only until a physical write/read-back is validated; the app
    # explains this before a write starts.
    NEWCHIRP_WRITE_DISABLED = True

    @classmethod
    def get_prompts(cls):
        prompts = super().get_prompts()
        prompts.experimental = (
            "The AnyTone AT-D878UVII Plus driver is experimental and "
            "read-only. It reads conventional channels and zones over the "
            "AnyTone serial protocol confirmed in the official D878UVII "
            "CPS 4.00 and QDMR. Writing is disabled until a read and a "
            "write/read-back have been checked on a real radio; keep using "
            "the AnyTone CPS to program it."
        )
        prompts.pre_upload = (
            "Writing to the AT-D878UVII Plus is not enabled yet."
        )
        return prompts

    def get_features(self):
        rf = super().get_features()
        rf.valid_power_levels = list(D878_POWER_LEVELS)
        rf.valid_bands = [
            (136000000, 174000000),
            (400000000, 480000000),
        ]
        return rf

    def get_memory(self, number):
        memory = super().get_memory(number)
        if not memory.empty:
            # Read the level from the record: the base list has High and
            # Turbo at the same wattage, so mapping by value is ambiguous.
            level = _BASE._bit(self._channel_record(number)[8], 2, 2)
            memory.power = D878_POWER_LEVELS[min(level, 3)]
        return memory

    def sync_out(self):
        raise errors.RadioError(
            "Writing to the AnyTone AT-D878UVII Plus is not enabled yet; "
            "nothing was sent to the radio."
        )
