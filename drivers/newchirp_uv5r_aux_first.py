# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""UV-5R family download that reads the settings block before the channels.

Stock CHIRP ``uv5r._do_download`` (pinned 21e42e45) handshakes, reads the
firmware version from 0x1E80/0x1EC0/0x1FC0, reads the channels 0x0000-0x17FF,
then jumps back to 0x1EC0 for the settings block 0x1EC0-0x1FFF. A
2026-11-25 report (NewChirp 1.0.73, macOS, INBOX:985) shows a radio that
answers the 50 BB FF 20 12 07 25 handshake (ident AA 30 76 04 00 05 20 DD),
the firmware-version reads and every channel block, then sends nothing for
0x1EC0. It failed the same way in five tries as UV-5R, BF-F8HP and UV-5RX3.

OEM evidence: the Baofeng UV-5RX CPS 20231124 (the same handshake,
``WriFreq.hSTable1``) reads channels 0x0000-0x17C0 in one session
(``ReadCHData``, stops at eepAddr 6080) and reads 0x1FC0 and 0x1EC0 only at the
start of a separate session (``ReadConfigData``). It never asks for the
settings block after the channels in one session.

This download keeps the same handshake, addresses, block sizes and image
layout (ident + 0x0000-0x17FF + 0x1EC0-0x1FFF), but reads the settings block
right after the firmware-version read, while the radio is still answering in
that area, then reads the channels. 0x1FC0 -> 0x0000 is the jump stock
already makes, and the report shows this radio accepts it. Reads do not
change the radio. BJ-UV55 and radios without the settings block keep the
stock download. Uploads are unchanged.
"""

import logging

from chirp import memmap
from chirp.drivers import uv5r

LOG = logging.getLogger(__name__)

_current = uv5r._do_download
_original = getattr(_current, "newchirp_original", _current)


def _read_aux(radio, has_dropped_byte):
    data = b""
    if has_dropped_byte:
        # Same as stock: 0x40 blocks, then 0x10 blocks for the last 0x40
        # bytes, which these radios garble when read in one 0x40 block.
        for addr in range(0x1EC0, 0x1FC0, 0x40):
            data += uv5r._read_block(radio, addr, 0x40, False)
        for addr in range(0x1FC0, 0x2000, 0x10):
            data += uv5r._read_block(radio, addr, 0x10, False)
    else:
        for addr in range(0x1EC0, 0x2000, 0x40):
            data += uv5r._read_block(radio, addr, 0x40, False)
    return data


def _do_download_aux_first(radio):
    if not radio._aux_block or radio.MODEL == "BJ-UV55":
        return _original(radio)

    data = uv5r._ident_radio(radio)
    radio_version, has_dropped_byte = uv5r._get_radio_firmware_version(radio)
    LOG.info("Radio Version is %s" % repr(radio_version))
    LOG.info("Radio has dropped byte issue: %s" % repr(has_dropped_byte))

    LOG.debug("downloading aux block before the main block...")
    aux = _read_aux(radio, has_dropped_byte)

    LOG.debug("downloading main block...")
    for addr in range(0, 0x1800, 0x40):
        data += uv5r._read_block(radio, addr, 0x40, False)
        uv5r._do_status(radio, "from", addr)
    uv5r._do_status(radio, "from", radio.get_memsize())
    LOG.debug("done.")
    return memmap.MemoryMapBytes(data + aux)


_do_download_aux_first.newchirp_original = _original
uv5r._do_download = _do_download_aux_first
