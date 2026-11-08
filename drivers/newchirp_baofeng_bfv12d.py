# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""CPS-derived BF-V12D transport with fail-closed firmware diagnostics."""

from __future__ import annotations

import time

from chirp import directory, errors
from chirp.drivers import baofeng_common, baofeng_digital


ACK = b"\x06"
UNLOCK_REQUEST = b"\x02ucbfpwd"
UNLOCK_KEY = b"\x10\xc5\xea\x35"
MODEL_TOKEN = b"Q041OTUwMA==\x00\x00\x00\x00"
PROGRAM_REQUEST = b"\x02prOGRAM"
IDENT_ATTEMPTS = 5
IDENT_RETRY_DELAY = 1.0
RESPONSE_TIMEOUT = 1.5


def _set_timeout(pipe, timeout):
    try:
        pipe.timeout = timeout
    except Exception:
        pass


def _read_exact(pipe, size, timeout=RESPONSE_TIMEOUT):
    """Read a fixed response even when the OS splits it into callbacks."""
    deadline = time.monotonic() + timeout
    data = bytearray()
    _set_timeout(pipe, min(0.05, timeout))
    try:
        while len(data) < size and time.monotonic() < deadline:
            chunk = pipe.read(size - len(data))
            if chunk:
                data.extend(chunk)
        return bytes(data)
    finally:
        _set_timeout(pipe, RESPONSE_TIMEOUT)


def _send(pipe, payload):
    try:
        pipe.write(payload)
    except Exception as exc:
        raise errors.RadioError("Could not send a BF-V12D command") from exc


def _send_ack_step(pipe, payload, step):
    _send(pipe, payload)
    response = _read_exact(pipe, 1)
    if response != ACK:
        detail = "no response" if not response else response.hex()
        raise errors.RadioError(
            "BF-V12D %s was not acknowledged (%s)" % (step, detail)
        )


def _official_unlock_sequence(pipe):
    _send_ack_step(pipe, UNLOCK_REQUEST, "unlock request")
    _send_ack_step(pipe, UNLOCK_KEY, "unlock key")
    _send_ack_step(pipe, MODEL_TOKEN, "model token")


directory.enable_reregistrations()


@directory.register
class NewChirpBaofengBFV12D(baofeng_digital.BaofengBFV12D):
    """Baofeng BF-V12D using the serial sequence traced from BF_Series 1.5.1."""

    @classmethod
    def get_prompts(cls):
        prompts = super().get_prompts()
        prompts.experimental = (
            "NewChirp uses the BF-V12D unlock and clone sequence recovered "
            "from Baofeng BF_Series CPS 1.5.1. Original firmware is "
            "experimental. Some newer radios report V1.19 or V2.02 and "
            "reject the same password handshake in both NewChirp/CHIRP and "
            "Baofeng's CPS. Those firmware variants are not yet supported. "
            "Use a standard Baofeng K-type programming cable; FTDI cables "
            "have been reported not to work with this model. Keep an "
            "unedited image before writing."
        )
        prompts.pre_upload = (
            "Save an unedited image first, write one test channel, then read "
            "the radio back and verify it on the radio."
        )
        return prompts

    def _get_radio_id(self):
        last_error = None
        for attempt in range(IDENT_ATTEMPTS):
            try:
                baofeng_common._clean_buffer(self)
                _official_unlock_sequence(self.pipe)
                radio_id = _read_exact(self.pipe, 4)
                if len(radio_id) != 4:
                    raise errors.RadioError(
                        "BF-V12D did not return its four-byte radio ID"
                    )
                return radio_id
            except errors.RadioError as exc:
                last_error = exc
                if attempt + 1 >= IDENT_ATTEMPTS:
                    break
                self._exit_programming()
                time.sleep(IDENT_RETRY_DELAY)

        detail = str(last_error) if last_error else "unknown failure"
        if "no response" in detail.lower():
            raise errors.RadioNoResponse(
                "BF-V12D did not answer the CPS unlock request. Use a "
                "standard Baofeng K-type cable rather than an FTDI cable. "
                "Firmware V1.19 and V2.02 have a newer password handshake "
                "that is unsupported by the current Baofeng CPS and CHIRP. "
                "(%s)" % detail
            )
        raise errors.RadioError(
            "BF-V12D unlock failed after %i attempts: %s"
            % (IDENT_ATTEMPTS, detail)
        )
