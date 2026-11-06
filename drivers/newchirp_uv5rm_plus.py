# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Match the UV-17-family CPS handshake retry policy.

The official T6UV CPS retries ``PROGRAMBFNORMALU`` once per second, up to
five times, when the radio returns a stray byte instead of the required 0x06.
Upstream CHIRP aborts immediately after the first unexpected byte. Keep the
protocol unchanged while matching the OEM recovery behavior for models that
have shown the same startup mismatch.
"""

import time

from chirp import errors
from chirp.drivers import baofeng_uv17Pro


HANDSHAKE_RETRIES = 5
RETRY_DELAY = 1.0
UNEXPECTED_RESPONSE = "Unexpected response from radio"
RETRY_MODELS = {"UV-5RH", "UV-5RM Plus"}
_ORIGINAL_DO_IDENT = baofeng_uv17Pro._do_ident
_ORIGINAL_GET_MEMORY = baofeng_uv17Pro.BaofengUV5RMPlus.get_memory


def _do_ident(radio):
    if getattr(radio, "MODEL", "") not in RETRY_MODELS:
        return _ORIGINAL_DO_IDENT(radio)

    last_error = None
    for attempt in range(HANDSHAKE_RETRIES):
        try:
            return _ORIGINAL_DO_IDENT(radio)
        except errors.RadioError as exc:
            if str(exc) != UNEXPECTED_RESPONSE:
                raise
            last_error = exc
            if attempt < HANDSHAKE_RETRIES - 1:
                time.sleep(RETRY_DELAY)
    raise last_error


_do_ident.newchirp_uv5rm_plus_retry = True
if not getattr(
    baofeng_uv17Pro._do_ident,
    "newchirp_uv5rm_plus_retry",
    False,
):
    baofeng_uv17Pro._do_ident = _do_ident


def _get_memory(self, number):
    """Expose an unprogrammed PTT-ID byte as a valid Off setting."""
    _mem = self._get_raw_memory(number)
    pttid = int(_mem.pttid)
    if pttid < len(self.PTTID_LIST):
        return _ORIGINAL_GET_MEMORY(self, number)

    # 0xFF is an unprogrammed channel byte, not a selectable PTT-ID mode.
    # Normalize it while decoding so upload can replace it with a valid value.
    _mem.pttid = 0
    return _ORIGINAL_GET_MEMORY(self, number)


_get_memory.newchirp_uv5rm_plus_invalid_pttid = True
if not getattr(
    baofeng_uv17Pro.BaofengUV5RMPlus.get_memory,
    "newchirp_uv5rm_plus_invalid_pttid",
    False,
):
    baofeng_uv17Pro.BaofengUV5RMPlus.get_memory = _get_memory
