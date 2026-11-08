# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Serial support for the fourth-generation TIDRADIO TD-H8 family."""

import struct

from chirp import directory, errors
from chirp.drivers import tdh8


# ODMaster 2.6.4 writes these 32-byte pages for all three G4 regional
# profiles. Pages outside this map are read but never written. The first
# interval spans channel memory; the remaining intervals contain settings,
# startup data, VFO state, and the final configuration page.
TDH8_G4_WRITE_RANGES = (
    (0x0000, 0x1380),
    (0x1800, 0x18E0),
    (0x1900, 0x1980),
    (0x1C00, 0x1C40),
    (0x1F20, 0x1F40),
)

TDH8_G4_BLOCK_SIZE = 0x20
# CHIRP images begin with the eight-byte radio identity. Memory address zero
# is therefore stored at image offset eight.
TDH8_G4_IMAGE_PREFIX = 8
TDH8_G4_IMAGE_SIZE = 0x1FEF

# The official G4 protocol enters programming mode with the TD-H3 magic.
# G4 identities are new and are returned by the subsequent ``02`` query.
TDH8_G4_WRITE_MAGIC = tdh8.TD_H3


def _validate_write_image(radio):
    image = radio.get_mmap()
    if len(image) < TDH8_G4_IMAGE_SIZE:
        raise errors.RadioError(
            "TD-H8 fourth-generation image is incomplete; refusing to write"
        )

    last_address = TDH8_G4_WRITE_RANGES[-1][1]
    if len(image) < TDH8_G4_IMAGE_PREFIX + last_address:
        raise errors.RadioError(
            "TD-H8 fourth-generation image does not contain every official "
            "write page; refusing to write"
        )


def _write_page(radio, address):
    start = TDH8_G4_IMAGE_PREFIX + address
    stop = start + TDH8_G4_BLOCK_SIZE
    payload = radio.get_mmap()[start:stop]
    if len(payload) != TDH8_G4_BLOCK_SIZE:
        raise errors.RadioError(
            "TD-H8 fourth-generation page 0x%04X is incomplete" % address
        )

    header = struct.pack(">cHB", b"W", address, TDH8_G4_BLOCK_SIZE)
    checksum = bytes([sum(payload) & 0xFF])
    radio.pipe.write(header + payload + checksum)

    ack = radio.pipe.read(1)
    if ack != b"\x06":
        raise errors.RadioError(
            "Radio refused TD-H8 fourth-generation page 0x%04X" % address
        )


def _do_g4_upload(radio):
    _validate_write_image(radio)

    radio_ident = tdh8._do_ident(radio.pipe, TDH8_G4_WRITE_MAGIC)
    if radio_ident != radio.ident_mode:
        raise errors.RadioError(
            "TD-H8 fourth-generation model mismatch: expected %r, received %r"
            % (radio.ident_mode, radio_ident)
        )

    for start_address, end_address in TDH8_G4_WRITE_RANGES:
        for address in range(
            start_address, end_address, TDH8_G4_BLOCK_SIZE
        ):
            _write_page(radio, address)
            tdh8._do_status(radio, address)


class _TDH8FourthGenMixin:
    """Common discovery and write behavior for all G4 regional profiles."""

    VARIANT = "G4"
    _memsize = TDH8_G4_IMAGE_SIZE
    _ranges_main = [(0x0000, TDH8_G4_IMAGE_SIZE)]
    # Read detection remains on the magic observed by NewChirp reporters.
    # Upload uses the G4 magic recovered from ODMaster.
    _idents = [tdh8.TD_H8]

    def sync_out(self):
        try:
            _do_g4_upload(self)
        except errors.RadioError:
            raise
        except Exception as exc:
            raise errors.RadioError(
                "Failed to communicate with radio: %s" % exc
            )


@directory.register
@directory.detected_by(tdh8.TDH8)
class TIDRadioTDH8FourthGenHAM(
    _TDH8FourthGenMixin, tdh8.TDH8_3rd_Gen_HAM
):
    """TIDRADIO TD-H8 fourth-generation HAM serial profile."""

    ident_mode = b"TDH84GEH"


@directory.register
@directory.detected_by(tdh8.TDH8)
class TIDRadioTDH8FourthGen(_TDH8FourthGenMixin, tdh8.TDH8_3rd_Gen):
    """TIDRADIO TD-H8 fourth-generation generic serial profile."""

    ident_mode = b"TDH84GEN"


@directory.register
@directory.detected_by(tdh8.TDH8)
class TIDRadioTDH8FourthGenGMRS(
    _TDH8FourthGenMixin, tdh8.TDH8_3rd_Gen_GMRS
):
    """TIDRADIO TD-H8 fourth-generation GMRS serial profile."""

    ident_mode = b"TDH84GEG"
