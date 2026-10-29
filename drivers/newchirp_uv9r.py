# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Baofeng UV-9R upload retry for newer write-timing variants."""

import struct
import time

from chirp import directory, errors
from chirp.drivers import baofeng_common, baofeng_wp970i


ACK = b"\x06"
WRITE_ATTEMPTS = 3


def _write_block_address(frame):
    if len(frame) < 4 or frame[:1] != b"X":
        return None
    try:
        command, address, length = struct.unpack(">BHB", frame[:4])
    except struct.error:
        return None
    if command != ord("X"):
        return None
    return address


def _read_write_ack(radio, frame, send, receive):
    """Read an upload ACK, resending the identical block when needed."""
    address = _write_block_address(frame)
    if address is None:
        return receive(radio, 1)

    last_error = None
    for attempt in range(WRITE_ATTEMPTS):
        try:
            ack = receive(radio, 1)
        except errors.RadioNoContactLikelyK1 as exc:
            last_error = exc
            ack = b""
        if ack == ACK:
            return ack
        if attempt + 1 < WRITE_ATTEMPTS:
            time.sleep(0.15)
            send(radio, frame)
            time.sleep(0.10)

    detail = "no response" if not ack else "reply %s" % ack.hex()
    raise errors.RadioError(
        "Radio did not acknowledge write block 0x%04x after %i attempts "
        "(%s).%s"
        % (
            address,
            WRITE_ATTEMPTS,
            detail,
            " %s" % last_error if last_error else "",
        )
    )


directory.enable_reregistrations()


@directory.register
class UV9R(baofeng_wp970i.UV9R):
    """Baofeng UV-9R with resumable write acknowledgment handling."""

    @classmethod
    def get_prompts(cls):
        prompts = super().get_prompts()
        prompts.experimental = (
            "This UV-9R upload path retries an unacknowledged 16-byte block "
            "for newer radio revisions. The memory layout is unchanged. "
            "Keep an unmodified read image as a backup before writing."
        )
        return prompts

    def sync_out(self):
        original_send = baofeng_common._rawsend
        original_receive = baofeng_common._rawrecv
        last_write = b""

        def tracking_send(radio, data):
            nonlocal last_write
            last_write = bytes(data)
            return original_send(radio, data)

        def retrying_receive(radio, amount):
            if amount == 1 and _write_block_address(last_write) is not None:
                return _read_write_ack(
                    radio,
                    last_write,
                    original_send,
                    original_receive,
                )
            return original_receive(radio, amount)

        baofeng_common._rawsend = tracking_send
        baofeng_common._rawrecv = retrying_receive
        try:
            return super().sync_out()
        finally:
            baofeng_common._rawsend = original_send
            baofeng_common._rawrecv = original_receive

