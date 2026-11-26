# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Quansheng TK11 upload that opens its own session, like the OEM CPS.

Stock CHIRP ``tk11.do_upload`` (pinned 21e42e45) streams 0x200-byte
memory-write frames (type 0x1FD) straight away. Only ``do_download`` sends the
connection request (0x1F4) that tells the radio the session's magic code, so
an upload works only while the radio still remembers a session from an
earlier read. ``memory_write``'s result is also ignored, so a refused block
does not stop the write.

2026-11-26 report (NewChirp 1.0.75, Windows, TK11(8) firmware 5.00.18,
mailbox UID 1044): a read worked; the write four minutes later got no reply
to the first frame, then a reply without the AB CD framing.

OEM evidence: Quansheng TK11(8) CPS ``TK11_EN(2.19).exe`` (official package
"TK11 Firmware+CPS+Upgrade Tool 2025.10.17", Setup Factory payload;
``TK11.exe`` SHA-256 0839e005...a843) picks a random magic code and runs
``main.Login()`` before every read and every write: ``protocol_struct.Link``
sends O_CALMS_CONN_REQ (500) up to three times and needs O_MSCAL_CONN_RSP
(501), whose bytes 20/22 are u8PasswordValid / u8ParamsVersion; a set
password is entered before anything else. ``protocol_struct.Write`` sends
O_CALMS_PARA_WRITE_REQ (509) and requires O_MSCAL_PARA_WRITE_RSP (510); every
CPS write routine stops at the first refused block, and the write ends with
O_CALMS_REBOOT_REQ (1501).

This upload sends the same connection request first, refuses a radio with a
programming password (CHIRP cannot enter it), checks every block's response,
and reboots the radio at the end. Blocks, addresses and the image are
unchanged.
"""

import logging
import time

from chirp import chirp_common, errors
from chirp.drivers import tk11

LOG = logging.getLogger(__name__)

CONNECT_ATTEMPTS = 3          # main.Login(): protocol_struct.Link(3)
PASSWORD_VALID_OFFSET = 20    # MSG_MSCAL_ConnRsp.u8PasswordValid

_current = tk11.do_upload
_original = getattr(_current, "newchirp_original", _current)


def _connect(serial):
    """Open a session the way the CPS does before a write."""
    last_error = None
    for attempt in range(1, CONNECT_ATTEMPTS + 1):
        reset = getattr(serial, "reset_input_buffer", None)
        if reset is not None:
            reset()
        try:
            serial.write(tk11.encapsulate_message(tk11.CONNECTION_REQUEST))
            response = tk11.read_serial(serial, 64)
        except errors.RadioError as exc:
            last_error = exc
            LOG.warning("TK11 connect attempt %i/%i failed: %s",
                        attempt, CONNECT_ATTEMPTS, exc)
            time.sleep(0.2)
            continue
        if tk11.get_response_code(response) != tk11.MessageType.CONNECT_RESPONSE:
            last_error = errors.RadioError(
                "Unexpected answer to the connection request")
            continue
        return response
    raise errors.RadioError(
        "The TK11 did not answer the connection request before the write "
        "(%s). Check the cable and that the radio is on, then try again."
        % last_error)


def do_upload(radio):
    """Upload with a fresh session, checking each block like the CPS."""
    status = chirp_common.Status()
    status.msg = "Connecting to radio"
    radio.status_fn(status)
    serial = radio.pipe

    response = _connect(serial)
    if len(response) > PASSWORD_VALID_OFFSET and response[PASSWORD_VALID_OFFSET] == 1:
        raise errors.RadioError(
            "This TK11 has a programming password set. NewChirp cannot enter "
            "it yet: remove the password in the radio or Quansheng's "
            "software, then write again.")

    memory = radio.get_mmap()
    memory_size = len(memory)
    for address in range(0, memory_size, tk11.MAX_CHUNK_SIZE):
        status.msg = "Uploading data to %s %s" % (radio.VENDOR, radio.MODEL)
        status.cur = address * 100 // memory_size
        status.max = 100
        radio.status_fn(status)
        try:
            accepted = tk11.memory_write(
                serial, address, memory[address:address + tk11.MAX_CHUNK_SIZE])
        except errors.RadioError as exc:
            raise errors.RadioError(
                "The TK11 did not answer the write at 0x%05X: %s"
                % (address, exc)) from exc
        if not accepted:
            raise errors.RadioError(
                "The TK11 refused the write at 0x%05X; the write stopped "
                "there, as Quansheng's software does. Read the radio again "
                "before retrying." % address)
    tk11.reboot(serial)


do_upload.newchirp_original = _original
tk11.do_upload = do_upload
