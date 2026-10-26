# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Baofeng GM-32 GMRS driver.

The GM-32 answers the same clone handshake as the Baofeng UV-32
(PROGRAMCOLORPROU / UV32PRO) and uses that radio's memory map. This
driver keeps the UV-32 memories, bank names, and settings, then limits
transmit to GMRS.
"""

from chirp import chirp_common
from chirp import directory
from chirp.drivers import baofeng_uv17Pro as uv17


def _gmrs_channel(freq):
    """Return GMRS channel 1-22 for an exact receive frequency in Hz."""
    freq = int(freq)
    if 462562500 <= freq <= 462712500 and (freq - 462562500) % 25000 == 0:
        return 1 + (freq - 462562500) // 25000
    if 467562500 <= freq <= 467712500 and (freq - 467562500) % 25000 == 0:
        return 8 + (freq - 467562500) // 25000
    if 462550000 <= freq <= 462725000 and (freq - 462550000) % 25000 == 0:
        return 15 + (freq - 462550000) // 25000
    return None


def _is_repeater_input(freq):
    """True for the eight GMRS repeater inputs, 467.550 through 467.725."""
    freq = int(freq)
    if freq < 467550000 or freq > 467725000:
        return False
    return (freq - 467550000) % 25000 == 0


def legalize_gm32_memory(radio, mem):
    """Snap one memory to the GM-32 GMRS transmit rules.

    Channels 1-7 and 15-22 stay on the normal GMRS choices. Channels
    8-14 stay simplex, narrow, and on the radio's Low step, because
    those interstitial channels may transmit. Any other receive
    frequency is receive-only, except the eight repeater inputs, which
    may also be simplex.
    """
    if mem.empty or mem.freq <= 0:
        mem.empty = True
        return mem

    channel = _gmrs_channel(mem.freq)
    if channel is None:
        if _is_repeater_input(mem.freq) and mem.duplex != "off":
            mem.duplex = ""
        else:
            mem.duplex = "off"
        mem.offset = 0
        return mem

    if channel <= 7:
        mem.duplex = ""
        mem.offset = 0
    elif channel <= 14:
        if mem.duplex != "off":
            mem.duplex = ""
        mem.offset = 0
        mem.mode = "NFM"
        mem.power = radio.POWER_LEVELS[radio._low_power_index]
    elif mem.duplex == "+":
        mem.offset = 5000000
    elif mem.duplex == "off":
        mem.offset = 0
    else:
        mem.duplex = ""
        mem.offset = 0
    return mem


@directory.register
class GM32Radio(uv17.UV32, chirp_common.ExperimentalRadio):
    """Baofeng GM-32 GMRS handheld."""

    VENDOR = "Baofeng"
    MODEL = "GM-32"
    _low_power_index = 1

    @classmethod
    def get_prompts(cls):
        rp = chirp_common.RadioPrompts()
        rp.experimental = (
            "The Baofeng GM-32 driver is experimental. It uses the UV-32 "
            "programming link and keeps memories, bank names, and settings. "
            "Transmit stays on GMRS channels. A channel that is not GMRS "
            "is stored receive-only. Keep a backup image before every write. "
            "A read and a write have been tested on a radio."
        )
        rp.pre_download = (
            "1. Turn off the radio.\n"
            "2. Connect the programming cable.\n"
            "3. Turn the radio on.\n"
            "4. Start the download when the radio is on."
        )
        rp.pre_upload = (
            "Keep a backup image before writing.\n"
            "1. Turn off the radio.\n"
            "2. Connect the programming cable.\n"
            "3. Turn the radio on.\n"
            "4. Start the upload when the radio is on."
        )
        return rp

    def get_features(self):
        rf = super().get_features()
        rf.has_settings = True
        rf.has_bank = True
        rf.valid_duplexes = ["", "+", "off"]
        return rf

    def validate_memory(self, mem):
        # A new row has no frequency yet. Let the write continue and store
        # that slot empty. Check every other row after the GMRS rules, so a
        # spreadsheet cannot leave a non-GMRS transmit in the image.
        if mem.empty or int(mem.freq) <= 0:
            return []
        trial = mem.dupe()
        legalize_gm32_memory(self, trial)
        return super().validate_memory(trial)

    def set_memory(self, mem):
        legalize_gm32_memory(self, mem)
        super().set_memory(mem)
