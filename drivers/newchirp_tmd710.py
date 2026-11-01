# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Accept the TM-D710GP regional identity in the TM-D710G clone driver."""

import logging

from chirp import errors
from chirp.drivers import tmd710


LOG = logging.getLogger(__name__)

_original_connect_radio = tmd710._connect_radio


def accepts_d710gp_identity(radio, exc):
    return (
        radio.SHORT == "G"
        and "Radio responded as D710GP, not D710G." in str(exc)
    )


def _connect_radio_accepting_regional_identity(radio):
    try:
        return _original_connect_radio(radio)
    except errors.RadioError as exc:
        if accepts_d710gp_identity(radio, exc):
            LOG.info("Accepting TM-D710GP regional clone identity")
            return None
        raise


if not getattr(
    tmd710._connect_radio,
    "newchirp_accepts_d710gp",
    False,
):
    _connect_radio_accepting_regional_identity.newchirp_accepts_d710gp = True
    tmd710._connect_radio = _connect_radio_accepting_regional_identity
