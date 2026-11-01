# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Accept a completed Yaesu clone read after a slow final data chunk."""

import time

from chirp import chirp_common, errors
from chirp.drivers import ft1d, ft2d, ft4, yaesu_clone


IDLE_TIMEOUT = 5.0


def _chunk_read(
    pipe,
    count,
    status_fn,
    cmd_ack=yaesu_clone.CMD_ACK,
    clock=time.monotonic,
):
    """Read a clone block without rejecting a late, complete final chunk."""
    timer = clock()
    block = 32
    data = b""
    had_data = False
    while len(data) < count:
        chunk_size = min(block, count - len(data))
        chunk = pipe.read(chunk_size)
        if chunk:
            timer = clock()
            had_data = True
            data += chunk
            if data[0] == cmd_ack:
                data = data[1:]  # Chew an echo'd ACK from a 2-pin cable.

        # Completion must win over the idle timeout. The radio can take more
        # than the old two-second limit to deliver the final chunk.
        if len(data) == count:
            break
        if clock() - timer > IDLE_TIMEOUT:
            if not had_data:
                raise errors.RadioNoResponse()
            raise errors.RadioError("Timed out reading from radio")
        status = chirp_common.Status()
        status.msg = "Cloning from radio"
        status.max = count
        status.cur = len(data)
        status_fn(status)
    return data


_chunk_read.newchirp_completion_first = True
if not getattr(
    yaesu_clone._chunk_read,
    "newchirp_completion_first",
    False,
):
    yaesu_clone._chunk_read = _chunk_read


class _MTOYaesuSC35BankModel(
    ft4.YaesuSC35GenericBankModel,
    chirp_common.MTOBankModel,
):
    """Describe the FT-1/2/3/5 bitmask banks as multi-bank mappings."""


_OriginalFT1BankModel = ft1d.FT1BankModel
_OriginalFT2BankModel = ft2d.FT2BankModel


class _MTOFT1BankModel(
    _OriginalFT1BankModel,
    chirp_common.MTOBankModel,
):
    """Describe the FT-1/2/3/5 ordered bank lists as multi-bank mappings."""

    def __init__(self, radio, name="Banks"):
        chirp_common.BankModel.__init__(self, radio, name)
        self._bank_mappings = []
        for index, _bank in enumerate(self._radio._memobj.bank_info):
            bank = ft1d.FT1Bank(self, "%i" % index, "BANK-%i" % index)
            bank.index = index
            self._bank_mappings.append(bank)


class _MTOFT2BankModel(
    _OriginalFT2BankModel,
    chirp_common.MTOBankModel,
):
    """Describe the FT-2/5 ordered bank lists as multi-bank mappings."""

    def __init__(self, radio, name="Banks"):
        chirp_common.BankModel.__init__(self, radio, name)
        self._bank_mappings = []
        for index, _bank in enumerate(self._radio._memobj.bank_info):
            bank = ft2d.FT2Bank(self, "%i" % index, "BANK-%i" % index)
            bank.index = index
            self._bank_mappings.append(bank)


ft4.YaesuSC35GenericBankModel = _MTOYaesuSC35BankModel
ft1d.FT1BankModel = _MTOFT1BankModel
ft2d.FT2BankModel = _MTOFT2BankModel

