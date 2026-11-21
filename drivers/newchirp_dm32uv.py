# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""DM-32UV override with bounded retries for the password-state query."""

import time

from chirp import chirp_common, directory, errors
from chirp.drivers import baofeng_dm32uv


AIRBAND = (108_000_000, 136_000_000)

_current_xfer = baofeng_dm32uv._Link.xfer
_original_xfer = getattr(_current_xfer, "newchirp_original", _current_xfer)
_current_query_v = baofeng_dm32uv._Link.query_v
_original_query_v = getattr(
    _current_query_v,
    "newchirp_original",
    _current_query_v,
)
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
    if data == b"SYSINFO" and length == 1:
        last_reply = b""
        last_error = None
        for attempt in range(3):
            try:
                response = _original_xfer(self, data, length, timeout)
            except errors.RadioError as exc:
                last_error = exc
            else:
                if response == b"\x06":
                    return response
                last_reply = response
            if attempt < 2:
                time.sleep(0.08)

        detail = (
            "reply %s" % last_reply.hex()
            if last_reply
            else str(last_error or "no reply")
        )
        raise errors.RadioError(
            "Unexpected reply to SYSINFO after 3 attempts (%s). "
            "Power-cycle the radio, reconnect the programming cable, close "
            "the Baofeng CPS, and try the read again." % detail
        )

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


def _query_v_with_retry(self, cmd):
    """Retry read-only radio information queries with slower fragmentation."""
    last_header = b""
    last_body = b""

    for attempt in range(3):
        self.send(cmd)
        header = self.recv(3, timeout=1.5)
        body = (
            self.recv(header[2], timeout=2.0)
            if len(header) == 3
            else b""
        )
        if (
            len(header) == 3
            and header[0] == 0x56
            and len(body) == header[2]
        ):
            return body
        last_header = header
        last_body = body
        if attempt < 2:
            time.sleep(0.08)

    message = (
        "Bad reply to radio info query %s after 3 attempts "
        "(header %s, body %i bytes)"
        % (cmd.hex(), last_header.hex() or "empty", len(last_body))
    )
    raise baofeng_dm32uv._bad_reply(
        message,
        last_header[:1],
        b"V",
    )


_xfer_with_passsta_retry.newchirp_passsta_retry = True
_xfer_with_passsta_retry.newchirp_original = _original_xfer
_query_v_with_retry.newchirp_query_retry = True
_query_v_with_retry.newchirp_original = _original_query_v
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
if not getattr(
    baofeng_dm32uv._Link.query_v,
    "newchirp_query_retry",
    False,
):
    baofeng_dm32uv._Link.query_v = _query_v_with_retry


def _stored_name(raw):
    """A name as the radio shows it: text up to the first NUL or 0xFF.

    Names written by other software can keep old bytes after the NUL that
    ends them, such as "Channel 1\\x00t Mode" or "RPT 15\\x00 23". The radio
    stops at the NUL; stock CHIRP only stripped trailing padding and showed
    the leftover text (forum file drop 12, 2026-11-20).
    """
    return str(raw).split("\x00")[0].split("\xff")[0].rstrip(" ")


def _zone_get_name(self):
    name = _stored_name(self._zone().name)
    if self.index + 1 > self._model._radio._zone_count() and (
            not name or not name.isprintable()):
        return "New zone"
    return name


_zone_get_name.newchirp_stored_name = True
if not getattr(
    baofeng_dm32uv.DM32UVZone.get_name,
    "newchirp_stored_name",
    False,
):
    baofeng_dm32uv.DM32UVZone.get_name = _zone_get_name


directory.enable_reregistrations()


@directory.register
class DM32UV(baofeng_dm32uv.DM32UV):
    """Baofeng DM-32UV with a retry-safe password-state handshake."""

    def get_features(self):
        features = super().get_features()
        features.valid_bands.insert(0, AIRBAND)
        return features

    def get_memory(self, number):
        mem = super().get_memory(number)
        if not mem.empty:
            mem.name = _stored_name(self._chan(number).name)
        return mem

    def _channel_names(self):
        names = {}
        for number in super()._channel_names():
            names[number] = baofeng_dm32uv._shown(
                _stored_name(self._chan(number).name)
            )
        return names

    def validate_memory(self, memory):
        messages = []
        if (
            AIRBAND[0] <= memory.freq < AIRBAND[1]
            and memory.duplex != "off"
        ):
            messages.append(chirp_common.ValidationError(
                "DM-32UV airband memories must be set to receive-only"
            ))
        return messages + super().validate_memory(memory)

    @classmethod
    def get_prompts(cls):
        prompts = super().get_prompts()
        prompts.info = (
            "Switch the DM-32UV on and connect its programming cable at "
            "115200 baud. Close the Baofeng CPS before reading or writing."
        )
        return prompts

