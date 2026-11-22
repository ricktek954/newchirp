# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""UV-5R Mini download that re-requests a block the radio did not answer.

Stock CHIRP aborts the whole read on the first block that times out. A
2026-11-21 report (ledger ``w-20261122-e807``) read about 75 blocks
normally, then one ``R`` request got no reply and the read failed.

OEM evidence: Baofeng UV-5R Mini CPS v1.0.7
(``Baofeng_UV_5R_Mini_CPS_V1.0.7.zip``, SHA-256
``f96977b15bd9859fc53d0fe432ea48d4c4994074de73555ce8615d3d9e38f607``;
``BF-5RMini_CPS.exe``, ``KDH.Communication.Read``). The CPS sends
``52 <addr hi> <addr lo> 40``, waits for 68 bytes, and on a 1 s timer
resends the same request up to five more times before failing
(``timesOfRetry = 5``). Its address walk is 0x0000-0x803F, 0x9000-0x903F,
0xA000-0xA1BF, the same as CHIRP's ``MEM_STARTS``/``MEM_SIZES``. Reads do
not change the radio, so resending one is safe. The handshake and upload
are unchanged.
"""

import logging

from chirp import chirp_common, errors
from chirp.drivers import baofeng_common as bfc
from chirp.drivers import baofeng_uv17Pro

LOG = logging.getLogger(__name__)

# The CPS sends a block request once, then up to five more times.
BLOCK_ATTEMPTS = 6


def _read_block(radio, addr):
    frame = radio._make_read_frame(addr, radio.BLOCK_SIZE)
    for attempt in range(1, BLOCK_ATTEMPTS + 1):
        radio.pipe.log("Sending request for 0x%04x" % addr)
        bfc._rawsend(radio, frame)
        try:
            return bfc._rawrecv(radio, radio.BLOCK_SIZE + 4)
        except errors.RadioError as exc:
            if attempt == BLOCK_ATTEMPTS:
                raise errors.RadioError(
                    "The UV-5R Mini stopped answering at memory block "
                    "0x%04X after %i requests (%s). The radio was not "
                    "changed. Keep the cable fully inserted, turn off the "
                    "radio's Bluetooth, and read again." % (
                        addr, BLOCK_ATTEMPTS, exc)) from exc
            LOG.warning("No complete reply for block 0x%04x (attempt %i): %s",
                        addr, attempt, exc)
            bfc._clean_buffer(radio)


def _download(radio):
    """Stock ``baofeng_uv17Pro._download`` with the CPS block retry."""
    if radio.MODEL != "UV-5R Mini":
        # UV-5G Mini inherits UV5RMini; its CPS has not been checked.
        return baofeng_uv17Pro._download(radio)
    baofeng_uv17Pro._do_ident(radio)
    data = b""

    status = chirp_common.Status()
    status.cur = 0
    status.max = radio.MEM_TOTAL // radio.BLOCK_SIZE
    status.msg = "Cloning from radio..."
    radio.status_fn(status)

    for start, size in zip(radio.MEM_STARTS, radio.MEM_SIZES):
        for addr in range(start, start + size, radio.BLOCK_SIZE):
            block = _read_block(radio, addr)
            if radio._uses_encr:
                block = baofeng_uv17Pro._crypt(radio._encrsym, block[4:])
            else:
                block = block[4:]
            data += block
            status.cur = len(data) // radio.BLOCK_SIZE
            radio.status_fn(status)
    return data


_download.newchirp_block_retry = True
baofeng_uv17Pro.UV5RMini.download_function = _download
