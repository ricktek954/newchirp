"""Baofeng GM-21 compatibility for later firmware handshakes."""

from chirp import directory
from chirp.drivers import baofeng_uv17Pro


@directory.register
class BaofengGM21(baofeng_uv17Pro.BaofengGM21):
    """Baofeng GM-21 with GM-5RH-compatible programming firmware."""

    _idents = [
        baofeng_uv17Pro.MSTRING_GM5RH,
        baofeng_uv17Pro.MSTRING_UV17PROGPS,
    ]
