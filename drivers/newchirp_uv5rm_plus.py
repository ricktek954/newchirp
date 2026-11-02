# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Match the UV-5RM Plus CPS handshake retry policy.

The official T6UV CPS retries ``PROGRAMBFNORMALU`` once per second, up to
five times, when the radio returns a stray byte instead of the required 0x06.
Upstream CHIRP aborts immediately after the first unexpected byte. Keep the
protocol unchanged while matching the OEM recovery behavior for this model.
"""

import time

from chirp import errors
from chirp.drivers import baofeng_uv17Pro


HANDSHAKE_RETRIES = 5
RETRY_DELAY = 1.0
UNEXPECTED_RESPONSE = "Unexpected response from radio"
_ORIGINAL_DO_IDENT = baofeng_uv17Pro._do_ident


def _do_ident(radio):
    if getattr(radio, "MODEL", "") != "UV-5RM Plus":
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
