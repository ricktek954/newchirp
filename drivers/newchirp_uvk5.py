# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Retry malformed UV-K5 firmware replies without enabling unsafe writes."""

import time

from chirp import errors
from chirp.drivers import uvk5


HELLO_PACKET = b"\x14\x05\x04\x00\x6a\x39\x57\x64"
HELLO_RETRIES = 5


def _getstring(data: bytes, begin, maxlen):
    """Return printable text, including responses with no trailing NUL."""
    end = min(begin + maxlen + 1, len(data))
    chars = list(data[begin:end])
    for index, value in enumerate(chars):
        if value < ord(" ") or value > ord("~"):
            return "".join(chr(char) for char in chars[:index])
    return "".join(chr(char) for char in chars)


def _sayhello_with_retry(serport):
    last_reply = b""

    for attempt in range(HELLO_RETRIES):
        uvk5._send_command(serport, HELLO_PACKET)
        try:
            reply = uvk5._receive_reply(serport)
        except errors.RadioNoResponse:
            reply = b""
        except errors.RadioError:
            reply = b""

        if reply.startswith(b"\x18\x05"):
            raise errors.RadioError(
                "Radio is in programming mode; restart it into normal mode"
            )
        firmware = _getstring(reply, 4, 24)
        if firmware:
            return firmware
        if reply:
            last_reply = reply
        if attempt < HELLO_RETRIES - 1:
            time.sleep(0.08)

    if last_reply:
        raise errors.RadioError(
            "Unable to determine firmware version after %i attempts "
            "(reply %s). Restart the radio normally, reconnect the cable, "
            "and verify that the exact UV-K5-family model is selected."
            % (HELLO_RETRIES, last_reply[:32].hex(" "))
        )
    raise errors.RadioError(
        "Unable to determine firmware version after %i attempts. "
        "Restart the radio normally and reconnect the programming cable."
        % HELLO_RETRIES
    )


_sayhello_with_retry.newchirp_original = uvk5._sayhello
_getstring.newchirp_uvk5_fixed = True
if not getattr(uvk5._getstring, "newchirp_uvk5_fixed", False):
    uvk5._getstring = _getstring
if not getattr(uvk5._sayhello, "newchirp_hello_retry", False):
    _sayhello_with_retry.newchirp_hello_retry = True
    uvk5._sayhello = _sayhello_with_retry
