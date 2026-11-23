# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Keep FT-70D clone reads aligned on the radio's ID block.

Yaesu ADMS-10 1.0.1.0 (adms10.exe, SerialProtocol.backgroundWorker1_DoWork)
reads 10 ID bytes, rejects them unless they start with "AH51G", sends one
ACK (0x06), then reads 65216 data bytes and one checksum byte. The checksum
is the low byte of the sum of the ID and data bytes, the same range as
CHIRP's YaesuChecksum(0x0000, 0xFEC9).

Stock CHIRP reads the first 10 bytes as the ID without checking them. One
stray byte ahead of the ID (left over from an attempt where [BAND] was
pressed early, for example) shifts the whole image by one byte and the read
ends with "Checksum Failed [0000-FEC9 (@FECA)]". This override discards
stale input before the read and anything received ahead of "AH51G", and it
explains a real checksum failure in terms the operator can act on. The
memory layout, checksum and write path stay stock.
"""

import logging

from chirp import errors, memmap, util
from chirp.drivers import ft70, yaesu_clone


LOG = logging.getLogger(__name__)

ID_PREFIX = b"AH51G"
ID_LENGTH = 10
BODY_LENGTH = 65217  # 65216 data bytes and the checksum byte
MAX_READS = 60  # About 15 s at the bridge's 0.25 s serial timeout
MAX_DISCARD = 64

CHECKSUM_HELP = (
    "The FT-70D image arrived damaged (checksum mismatch), so NewChirp did "
    "not load it. Nothing was written to the radio. Enter ADMS mode from "
    "cold: remove power, then hold [AMS] while reconnecting the battery or "
    "DC plug until \"ADMS\" appears. Start the read in NewChirp and press "
    "[BAND] only after NewChirp says the radio is ready. Use the USB cable "
    "directly on the computer rather than a hub."
)


def _reset_input(pipe):
    reset = getattr(pipe, "reset_input_buffer", None)
    if reset is None:
        reset = getattr(pipe, "flushInput", None)
    if reset is not None:
        try:
            reset()
        except Exception:  # pragma: no cover - transport specific
            LOG.debug("Could not clear the serial input buffer")


def _read_ident(pipe, cmd_ack=yaesu_clone.CMD_ACK):
    buf = b""
    discarded = 0
    had_data = False
    for _attempt in range(MAX_READS):
        need = ID_LENGTH - len(buf) if buf.startswith(ID_PREFIX) else ID_LENGTH
        chunk = pipe.read(max(1, need))
        if not chunk:
            continue
        had_data = True
        buf += chunk
        index = buf.find(ID_PREFIX)
        if index < 0:
            keep = len(ID_PREFIX) - 1
            discarded += max(0, len(buf) - keep)
            buf = buf[-keep:]
        elif index:
            discarded += index
            buf = buf[index:]
        if discarded > MAX_DISCARD:
            raise errors.RadioError(
                "The radio did not send an FT-70D identification block. "
                "Check that the FT-70D model is selected and that the radio "
                "is in ADMS mode."
            )
        if buf.startswith(ID_PREFIX) and len(buf) >= ID_LENGTH:
            if discarded:
                LOG.warning(
                    "Discarded %i byte(s) received before the FT-70D ID block",
                    discarded,
                )
            return buf[:ID_LENGTH], buf[ID_LENGTH:]
    if not had_data:
        raise errors.RadioNoResponse()
    raise errors.RadioError("Timed out reading the FT-70D identification block")


def _clone_in(radio):
    pipe = radio.pipe
    _reset_input(pipe)
    ident, extra = _read_ident(pipe, radio._cmd_ack)
    if extra:
        # The radio waits for the ACK before it sends memory data.
        raise errors.RadioError(
            "The FT-70D sent data before NewChirp acknowledged its ID. "
            "Turn the radio off and start the read again."
        )
    LOG.debug("ID block: %s", util.hexprint(ident))
    pipe.write(bytes([radio._cmd_ack]))
    body = yaesu_clone._chunk_read(
        pipe, BODY_LENGTH, radio.status_fn, radio._cmd_ack
    )
    data = ident + body
    if len(data) != radio.get_memsize():
        raise errors.RadioError("Received incomplete image from radio")
    return memmap.MemoryMapBytes(data)


def _sync_in(self):
    try:
        self._mmap = _clone_in(self)
    except errors.RadioError:
        raise
    except Exception as exc:
        raise errors.RadioError(
            "Failed to communicate with the radio: %s" % exc
        )
    try:
        self.check_checksums()
    except errors.RadioError as exc:
        if "Checksum Failed" not in str(exc):
            raise
        raise errors.RadioError("%s\n\n(%s)" % (CHECKSUM_HELP, exc))
    self.process_mmap()


_sync_in.newchirp_ft70_aligned = True
if not getattr(ft70.FT70Radio.sync_in, "newchirp_ft70_aligned", False):
    ft70.FT70Radio.sync_in = _sync_in
