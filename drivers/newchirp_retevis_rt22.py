# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Retevis RT22 identification as Retevis's own programmer performs it.

Stock CHIRP requires the 8-byte reply to ``02`` to contain one of four
captured IDs, so newer (2025) RT22 units that Retevis's software programs
fail with "Radio identification failed" (2026-11-21 report, ledger
``w-20261121-badb``; upstream CHIRP #6747 open since 2019).

OEM evidence: Retevis RT22 programming software V1.05
(``RT22-Programming-Software.zip``, SHA-256
``acefd8d334c55ec34edd0b05de4dc74c115d5ab70073084c9bc2d52b2f08f68d``; the
installer's main program, MFC, SHA-256 recorded in DRIVER_STATUS.md).
Its handshake at 0x4022CC sends ``PROGRGS`` (up to 10 tries for ``06``),
sends ``02``, reads 8 bytes with a 500 ms timeout and fails only if nothing
or fewer than 8 bytes arrive; it then sends ``06`` and reads memory. The
8-byte buffer is overwritten by the first ``R`` reply before any comparison,
so the ID is never checked. Its write loop covers ``W <addr> 10`` up to
0x3F0, the same 0x400-byte memory as CHIRP's RT22 driver.

Only the plain RT22 model is relaxed; the other RT22-family models keep
CHIRP's ID list. Everything after identification is the stock sequence.
"""

import logging
import time

from chirp import errors, util
from chirp.drivers import retevis_rt22

LOG = logging.getLogger(__name__)

OEM_ANY_ID_MODELS = {"RT22"}

_current = retevis_rt22._rt22_enter_programming_mode
_stock = getattr(_current, "newchirp_original", _current)


def _rt22_enter_programming_mode(radio):
    if getattr(radio, "MODEL", "") not in OEM_ANY_ID_MODELS:
        return _stock(radio)

    serial = radio.pipe
    magic = b"PROGRGS"
    ack = b""
    for _attempt in range(5):
        for j in range(len(magic)):
            time.sleep(0.005)
            serial.write(magic[j:j + 1])
        ack = serial.read(1)
        if ack == retevis_rt22.CMD_ACK:
            break
    else:
        if not ack:
            raise errors.RadioNoResponse()
        raise errors.RadioError(
            "The radio did not accept program mode after five tries.\n"
            "Check you interface cable and power cycle your radio.")

    try:
        serial.write(b"\x02")
        ident = serial.read(8)
    except Exception:
        retevis_rt22._rt22_exit_programming_mode(radio)
        raise errors.RadioError("Error communicating with radio")

    if len(ident) != 8:
        retevis_rt22._rt22_exit_programming_mode(radio)
        raise errors.RadioError(
            "Radio identification failed: expected 8 bytes, got %i (%s)." % (
                len(ident), ident.hex(" ") or "nothing"))
    if not any(fp in ident for fp in radio._fileid):
        LOG.info("RT22 ID %s is not in CHIRP's list; accepted as the "
                 "Retevis software does", ident.hex(" "))
        LOG.debug(util.hexprint(ident))

    try:
        serial.write(retevis_rt22.CMD_ACK)
        ack = serial.read(1)
    except Exception:
        retevis_rt22._rt22_exit_programming_mode(radio)
        raise errors.RadioError("Error communicating with radio")
    if ack != retevis_rt22.CMD_ACK:
        retevis_rt22._rt22_exit_programming_mode(radio)
        raise errors.RadioError("Radio refused to enter programming mode")

    try:
        serial.write(b"\x07")
        ack = serial.read(1)
    except Exception:
        retevis_rt22._rt22_exit_programming_mode(radio)
        raise errors.RadioError("Error communicating with radio")
    if ack != b"\x4E":
        retevis_rt22._rt22_exit_programming_mode(radio)
        raise errors.RadioError("Radio refused to enter programming mode")

    return ident


_rt22_enter_programming_mode.newchirp_original = _stock
retevis_rt22._rt22_enter_programming_mode = _rt22_enter_programming_mode
