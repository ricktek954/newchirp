# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Radioddity DB25-G transport recovered from the official GMRS CPS."""

import struct
import time

from chirp import directory, errors
from chirp.drivers import btech


IDENT_SIZE = 50
IDENT_ATTEMPTS = 4
IDENT_TIMEOUT = 4.0
READ_TIMEOUT = 2.0
RETRY_DELAY = 0.75
WRITE_BLOCK_SIZE = 16


def _reset_input(pipe):
    reset_input = getattr(pipe, "reset_input_buffer", None)
    if reset_input is not None:
        reset_input()


def _send(radio, payload):
    try:
        radio.pipe.write(bytes(payload))
    except Exception as exc:
        raise errors.RadioError(
            "Could not send the DB25-G programming command."
        ) from exc


def _read_exact(radio, size, timeout):
    deadline = time.monotonic() + timeout
    response = bytearray()
    while len(response) < size:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        chunk = radio.pipe.read(size - len(response))
        if not chunk:
            break
        response.extend(chunk)
    return bytes(response)


def _identify(radio):
    """Send the CPS eight-byte programming request and retry if it is silent."""
    radio.pipe.baudrate = 9600
    radio.pipe.parity = "N"
    radio.pipe.timeout = min(float(radio._timeout), IDENT_TIMEOUT)

    last_reply = b""
    for attempt in range(IDENT_ATTEMPTS):
        if attempt:
            time.sleep(RETRY_DELAY)
        _reset_input(radio.pipe)
        _send(radio, btech.MSTRING_KT8900D)
        reply = _read_exact(radio, IDENT_SIZE, IDENT_TIMEOUT)
        last_reply = reply
        if (
            len(reply) == IDENT_SIZE
            and reply[0] == btech.ACK_CMD
            and any(fingerprint in reply for fingerprint in radio._fileid)
        ):
            return reply
        if reply and reply[0] != btech.ACK_CMD:
            raise errors.RadioError(
                "The DB25-G returned an unexpected handshake reply: %s."
                % reply[:8].hex()
            )

    detail = (
        "last reply was %i bytes" % len(last_reply)
        if last_reply
        else "no bytes were received"
    )
    raise errors.RadioNoResponse(
        "The DB25-G did not answer the CPS programming handshake after "
        "%i attempts (%s). The official CPS retries this same eight-byte "
        "request. Turn the radio off and on, close Radioddity CPS and every "
        "other program using the COM port, reconnect the programming cable, "
        "then try the read again." % (IDENT_ATTEMPTS, detail)
    )


def _read_block(radio, address, length):
    _send(radio, btech._make_frame("S", address, length))
    response = _read_exact(radio, length + 5, READ_TIMEOUT)
    if len(response) != length + 5:
        raise errors.RadioError(
            "Short reply from the DB25-G reading block 0x%04x: expected "
            "%i bytes, received %i."
            % (address, length + 5, len(response))
        )
    if response[0] not in b"\x06\x05":
        raise errors.RadioError(
            "The DB25-G did not acknowledge read block 0x%04x: %s."
            % (address, response[:1].hex() or "no data")
        )
    command, returned_address, returned_length = struct.unpack(
        ">BHB", response[1:5]
    )
    if (
        command != ord("X")
        or returned_address != address
        or returned_length != length
    ):
        raise errors.RadioError(
            "The DB25-G returned a mismatched block header for 0x%04x "
            "(command %02x, address 0x%04x, length %i)."
            % (address, command, returned_address, returned_length)
        )
    return response[5:]


def _write_block(radio, address, payload):
    frame = (
        b"\x06X"
        + struct.pack(">HB", address, len(payload))
        + bytes(payload)
    )
    _send(radio, frame)
    response = _read_exact(radio, 1, READ_TIMEOUT)
    if response != b"\x06":
        detail = response.hex() if response else "no response"
        raise errors.RadioError(
            "The DB25-G did not acknowledge write block 0x%04x (%s)."
            % (address, detail)
        )


directory.enable_reregistrations()


@directory.register
class DB25G(btech.DB25G):
    """Radioddity DB25-G with the OEM CPS connection sequence."""

    _timeout = 1.5
    # Radioddity CPS leaves MSComm DTREnable and RTSEnable at their defaults.
    WANTS_DTR = False
    WANTS_RTS = False
    XON_XOFF = False

    @classmethod
    def get_prompts(cls):
        prompts = super().get_prompts()
        prompts.experimental = (
            "This NewChirp DB25-G driver uses the connection sequence "
            "recovered from Radioddity DB25-G GMRS CPS 20250903. It retries "
            "the initial programming handshake and writes in 16-byte blocks "
            "like the official CPS. Keep an unmodified read image as a backup "
            "before writing."
        )
        prompts.pre_download = (
            "Keep the radio on a normal channel, connect the programming "
            "cable, close Radioddity CPS and any other program using the COM "
            "port, and click Read from radio."
        )
        return prompts

    def sync_in(self):
        status = btech.chirp_common.Status()
        status.msg = "Connecting to DB25-G..."
        status.cur = 0
        status.max = 1
        self.status_fn(status)

        _identify(self)
        data = bytearray()
        total_blocks = btech.MEM_SIZE // self._block_size
        for block_index, address in enumerate(
            range(0, btech.MEM_SIZE, self._block_size),
            start=1,
        ):
            data.extend(_read_block(self, address, self._block_size))
            status.cur = block_index
            status.max = total_blocks
            status.msg = "Cloning from DB25-G..."
            self.status_fn(status)

        self._mmap = btech.memmap.MemoryMapBytes(bytes(data))
        self.process_mmap()

    def sync_out(self):
        status = btech.chirp_common.Status()
        status.msg = "Connecting to DB25-G..."
        status.cur = 0
        status.max = 1
        self.status_fn(status)

        _identify(self)
        image = self.get_mmap().get_byte_compatible()
        upload_size = min(len(image), self.UPLOAD_MEM_SIZE)
        if upload_size < self.UPLOAD_MEM_SIZE:
            raise errors.RadioError(
                "The DB25-G image is too short to write: expected at least "
                "%i bytes, received %i."
                % (self.UPLOAD_MEM_SIZE, len(image))
            )

        total_blocks = self.UPLOAD_MEM_SIZE // WRITE_BLOCK_SIZE
        for block_index, address in enumerate(
            range(0, self.UPLOAD_MEM_SIZE, WRITE_BLOCK_SIZE),
            start=1,
        ):
            _write_block(
                self,
                address,
                image[address:address + WRITE_BLOCK_SIZE],
            )
            status.cur = block_index
            status.max = total_blocks
            status.msg = "Cloning to DB25-G..."
            self.status_fn(status)
