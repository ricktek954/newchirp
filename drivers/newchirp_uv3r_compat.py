# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Report the real UV-3R handshake error instead of a Python error.

Stock CHIRP ``baofeng_uv3r.uv3r_prep`` (pinned 21e42e45 and upstream
kk7ds/chirp master as of 2026-11-25) retries the handshake ten times and
then runs ``raise e``. Python 3 clears ``e`` when its ``except`` block ends,
so a radio that never answers shows "Failed to communicate with radio:
cannot access local variable 'e' where it is not associated with a value"
(2026-11-25 report, INBOX:985). This keeps the same ten tries and one-second
pause and raises the last handshake error.
"""

import time

from chirp import errors
from chirp.drivers import baofeng_uv3r

PREP_ATTEMPTS = 10


def uv3r_prep(radio):
    """Do the UV3R identification dance"""
    last = None
    for _attempt in range(PREP_ATTEMPTS):
        try:
            return baofeng_uv3r._uv3r_prep(radio)
        except errors.RadioError as exc:
            last = exc
            time.sleep(1)
    raise last


baofeng_uv3r.uv3r_prep = uv3r_prep
