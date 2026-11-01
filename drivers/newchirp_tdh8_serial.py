# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Read-only serial support for the TD-H8 fourth-generation HAM identity."""

from chirp import directory, errors
from chirp.drivers import tdh8


@directory.register
@directory.detected_by(tdh8.TDH8)
class TIDRadioTDH8FourthGenHAM(tdh8.TDH8_3rd_Gen_HAM):
    """TIDRADIO TD-H8 fourth-generation HAM serial address space."""

    VARIANT = "G4"
    ident_mode = b"TDH84GEH"
    # This generation answers the original H8 query even though its memory
    # layout follows the later 0x1FEF address space.
    _idents = [tdh8.TD_H8]
    _memsize = 0x1FEF
    _ranges_main = [(0x0000, 0x1FEF)]

    def sync_out(self):
        raise errors.RadioError(
            "TD-H8 fourth-generation serial writes are disabled until a "
            "physical read, controlled write, and read-back are validated."
        )
