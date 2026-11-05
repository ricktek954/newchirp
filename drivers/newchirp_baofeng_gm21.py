"""Baofeng GM-21 compatibility for later firmware handshakes."""

import logging

from chirp import directory, errors
from chirp.drivers import baofeng_common as bfc
from chirp.drivers import baofeng_uv17Pro


LOG = logging.getLogger(__name__)

_IDENT_PROFILES = (
    (
        baofeng_uv17Pro.MSTRING_GM5RH,
        baofeng_uv17Pro.GM5RH._magics,
    ),
    (
        baofeng_uv17Pro.MSTRING_UV17PROGPS,
        baofeng_uv17Pro.UV17ProGPS._magics,
    ),
)
_ORIGINAL_DO_IDENT = baofeng_uv17Pro._do_ident


def _do_ident(radio):
    if getattr(radio, "MODEL", "") != "GM-21":
        return _ORIGINAL_DO_IDENT(radio)

    saw_data = False
    for ident, magics in _IDENT_PROFILES:
        bfc._clean_buffer(radio)
        LOG.debug("Sending GM-21 ident profile: %r", ident)
        try:
            ack = baofeng_uv17Pro._sendmagic(
                radio,
                ident,
                len(radio._fingerprint),
            )
        except errors.RadioError:
            continue
        if ack:
            saw_data = True
        if not ack.startswith(radio._fingerprint):
            continue
        for magic, response_len in magics:
            baofeng_uv17Pro._sendmagic(radio, magic, response_len)
        return True

    if saw_data:
        raise errors.RadioError("Unexpected response from radio")
    raise errors.RadioNoResponse()


_do_ident.newchirp_gm21_paired_handshake = True
if not getattr(
    baofeng_uv17Pro._do_ident,
    "newchirp_gm21_paired_handshake",
    False,
):
    baofeng_uv17Pro._do_ident = _do_ident


@directory.register
class BaofengGM21(baofeng_uv17Pro.BaofengGM21):
    """Baofeng GM-21 with GM-5RH-compatible programming firmware."""

    _idents = [
        baofeng_uv17Pro.MSTRING_GM5RH,
        baofeng_uv17Pro.MSTRING_UV17PROGPS,
    ]
