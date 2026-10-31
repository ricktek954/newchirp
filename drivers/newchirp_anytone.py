# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Compatibility fixes for CHIRP's AnyTone 5888UV driver."""

import warnings

from chirp.drivers import anytone


class _SafeSqlModes(list):
    """Keep unknown three-bit SQL values readable as Off."""

    def __getitem__(self, index):
        try:
            return super().__getitem__(index)
        except (IndexError, TypeError):
            return "Off"


anytone.SQL_MODES = _SafeSqlModes(anytone.SQL_MODES)

_original_get_memory = anytone.AnyTone5888UVRadio.get_memory


def _get_memory_without_setting_warning(self, number):
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message="RadioSettingValueList should be provided with current_index",
            category=FutureWarning,
            module=r"chirp\.drivers\.anytone$",
        )
        return _original_get_memory(self, number)


anytone.AnyTone5888UVRadio.get_memory = _get_memory_without_setting_warning
