# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""DM-32UV override with bounded retries for the password-state query."""

import time

from chirp import directory, errors
from chirp.drivers import baofeng_dm32uv


_current_xfer = baofeng_dm32uv._Link.xfer
_original_xfer = getattr(_current_xfer, "newchirp_original", _current_xfer)
_current_construct = baofeng_dm32uv._Link.__init__
_original_construct = getattr(
    _current_construct,
    "newchirp_original",
    _current_construct,
)


def _link_init_with_fixed_timeout(self, pipe):
    _original_construct(self, pipe)
    # FTDI adapters on Windows can misbehave when timeout is changed before
    # every read. Use one short platform-supported timeout and enforce the
    # command deadline in recv() instead.
    self.pipe.timeout = 0.05


def _recv_with_deadline(self, length, timeout=0.5):
    deadline = time.monotonic() + timeout
    response = bytearray()
    while len(response) < length:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        chunk = self.pipe.read(length - len(response))
        if chunk:
            response.extend(chunk)
    return bytes(response)


def _xfer_with_passsta_retry(self, data, length, timeout=0.5):
    if data != b"PASSSTA" or length != 3:
        return _original_xfer(self, data, length, timeout)

    last_reply = b""
    last_error = None
    for attempt in range(3):
        try:
            response = _original_xfer(self, data, length, timeout)
        except errors.RadioError as exc:
            last_error = exc
        else:
            if response and response[0] == ord("P"):
                return response
            last_reply = response
        if attempt < 2:
            time.sleep(0.08)

    if last_reply and last_reply[0] & 0x7F == ord("P"):
        raise baofeng_dm32uv._garbled(
            "Garbled password-state reply from the DM-32UV"
        )
    detail = (
        "reply %s" % last_reply.hex()
        if last_reply
        else str(last_error or "no reply")
    )
    raise errors.RadioError(
        "Unexpected reply to PASSSTA after 3 attempts (%s). Power-cycle the "
        "radio, reconnect the programming cable, close the Baofeng CPS, and "
        "try the read again." % detail
    )


_xfer_with_passsta_retry.newchirp_passsta_retry = True
_xfer_with_passsta_retry.newchirp_original = _original_xfer
_link_init_with_fixed_timeout.newchirp_fixed_timeout = True
_link_init_with_fixed_timeout.newchirp_original = _original_construct
_recv_with_deadline.newchirp_deadline_read = True
if not getattr(baofeng_dm32uv._Link.__init__, "newchirp_fixed_timeout", False):
    baofeng_dm32uv._Link.__init__ = _link_init_with_fixed_timeout
if not getattr(baofeng_dm32uv._Link.recv, "newchirp_deadline_read", False):
    baofeng_dm32uv._Link.recv = _recv_with_deadline
if not getattr(
    baofeng_dm32uv._Link.xfer,
    "newchirp_passsta_retry",
    False,
):
    baofeng_dm32uv._Link.xfer = _xfer_with_passsta_retry


directory.enable_reregistrations()


@directory.register
class DM32UV(baofeng_dm32uv.DM32UV):
    """Baofeng DM-32UV with a retry-safe password-state handshake."""

    @classmethod
    def get_prompts(cls):
        prompts = super().get_prompts()
        prompts.info = (
            "Switch the DM-32UV on and connect its programming cable at "
            "115200 baud. Close the Baofeng CPS before reading or writing."
        )
        return prompts

