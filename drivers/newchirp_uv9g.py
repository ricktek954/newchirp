# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Keep UV-9G service calibration values readable and unchanged.

Some radios store service-only squelch calibration bytes above the upstream
driver's 0-123 display range. The values are not user settings, but they
cannot be resolved from the downloaded image. Clamp them temporarily while
loading the settings UI and leave the resulting values read-only so a settings
upload preserves the original bytes.
"""

from chirp.drivers import baofeng_wp970i
from chirp.settings import RadioSetting


MAX_SERVICE_SQUELCH = 123
_ORIGINAL_GET_SETTINGS = baofeng_wp970i.UV9G.get_settings


def _find_setting(group, name):
    for element in group:
        if isinstance(element, RadioSetting):
            if element.get_name() == name:
                return element
        else:
            match = _find_setting(element, name)
            if match is not None:
                return match
    return None


def _get_settings(self):
    invalid = {}
    for band in ("vhf", "uhf"):
        squelch = getattr(self._memobj.squelch, band)
        for index in range(10):
            field = "sql%i" % index
            value = int(getattr(squelch, field))
            if value > MAX_SERVICE_SQUELCH:
                key = "squelch.%s.%s" % (band, field)
                invalid[key] = value
                setattr(squelch, field, MAX_SERVICE_SQUELCH)

    try:
        settings = _ORIGINAL_GET_SETTINGS(self)
    finally:
        for key, value in invalid.items():
            _, band, field = key.split(".")
            setattr(getattr(self._memobj.squelch, band), field, value)

    for key in invalid:
        setting = _find_setting(settings, key)
        if setting is None:
            raise RuntimeError("UV-9G service setting %s was not loaded" % key)
        setting.value.set_mutable(False)

    return settings


_get_settings.newchirp_uv9g_service_squelch = True
if not getattr(
    baofeng_wp970i.UV9G.get_settings,
    "newchirp_uv9g_service_squelch",
    False,
):
    baofeng_wp970i.UV9G.get_settings = _get_settings
