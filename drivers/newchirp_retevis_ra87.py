# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Retevis RA87 download identification as the OEM CPS performs it.

Stock CHIRP requires the 8-byte reply to ``0x02`` to start with one of two
captured fingerprints (``FF FF FF FF FF A5 2C FF`` / ``... A5 26 FF``), so a
radio whose other bytes differ fails with "Radio identification failed"
(2026-11-21 report, ledger ``w-20261122-8452``).

OEM evidence: Retevis RA87 CPS ``RunApp.exe`` (VB6, from
``ra87-programming-software_20251104150930_0234.zip``, SHA-256
``54d14be98e42274419946de60ccf998f19114ae47d69b98f347bf02c7fdf8eb0``) drives
the radio with command scripts. Its read handshake is
``TX "PROGRAM" RX 06 TX 02 RX VA VA VA VA VA VA VA VA TX 06 RX 06`` (``VA`` =
any byte), so the CPS accepts any 8-byte reply. It identifies the model by
byte 0x1F05 instead (``TX 52 1F 05 01 RX 57 1F 05 01 <5A|79|A5>``, one value
per band version; A5 is the 400-480 MHz version this driver models). The
8-byte reply is the image's 0x1F00-0x1F07 block (CHIRP's RA87 sample holds
the first fingerprint there), so its byte 5 is that model byte. The stock
upload path already checks 0x1F05 == A5.
"""

import logging

from chirp import errors, util
from chirp.drivers import retevis_ra87

LOG = logging.getLogger(__name__)

UHF_MODEL_BYTE = 0xA5
OTHER_MODEL_BYTES = {
    0x5A: "134-176 MHz",
    0x79: "340-400 MHz",
}

_current = retevis_ra87._enter_programming_mode_download
_stock = getattr(_current, "newchirp_original", _current)


def _identify(ident):
    """Return an error for an ident the OEM CPS would not treat as an RA87."""
    if len(ident) != 8:
        return "Radio identification failed: expected 8 bytes, got %i (%s)." % (
            len(ident),
            ident.hex(" ") or "nothing",
        )
    model = ident[5]
    if model == UHF_MODEL_BYTE:
        return None
    band = OTHER_MODEL_BYTES.get(model)
    if band:
        return (
            "This radio reports the %s RA87 version (model byte %02X). "
            "NewChirp's RA87 driver supports only the 400-480 MHz version "
            "(A5); the radio was not read." % (band, model)
        )
    return "Radio identification failed: model byte %02X, reply %s." % (
        model,
        ident.hex(" "),
    )


def _enter_programming_mode_download(radio):
    serial = radio.pipe
    magic = radio._magic

    try:
        serial.write(magic)
        if radio._echo:
            serial.read(len(magic))  # Chew the echo
        ack = serial.read(1)
    except Exception:
        raise errors.RadioError("Error communicating with radio")

    if not ack:
        raise errors.RadioNoResponse()
    if ack != retevis_ra87.CMD_ACK:
        raise errors.RadioError("Radio refused to enter programming mode")

    try:
        serial.write(b"\x02")
        if radio._echo:
            serial.read(1)  # Chew the echo
        ident = serial.read(8)
    except Exception:
        raise errors.RadioError("Error communicating with radio")

    problem = _identify(ident)
    if problem:
        LOG.debug("RA87 identification reply:\n\n" + util.hexprint(ident))
        raise errors.RadioError(problem)
    if not any(ident.startswith(fp) for fp in radio._fingerprint):
        LOG.info("RA87 reply %s is new; model byte A5 matches", ident.hex(" "))

    # Unchanged from stock: two ACK exchanges (each echoed by the cable).
    try:
        serial.write(retevis_ra87.CMD_ACK)
        if radio._echo:
            serial.read(1)  # Chew the echo
        ack = serial.read(1)
        serial.write(retevis_ra87.CMD_ACK)
        serial.read(1)  # Chew the echo
        ack = serial.read(1)
    except Exception:
        raise errors.RadioError("Error communicating with radio")

    if ack != retevis_ra87.CMD_ACK:
        raise errors.RadioError("Radio refused to enter programming mode")


_enter_programming_mode_download.newchirp_original = _stock
retevis_ra87._enter_programming_mode_download = _enter_programming_mode_download
