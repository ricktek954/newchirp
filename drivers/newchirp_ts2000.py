# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Kenwood TS-2000 live driver with longer write-command tolerance."""

import time

from chirp import directory
from chirp.drivers import kenwood_live
from chirp.drivers.ts2000 import TS2000Radio as ChirpTS2000Radio


directory.enable_reregistrations()


@directory.register
class TS2000Radio(ChirpTS2000Radio):
    """Kenwood TS-2000 with NewChirp write timing safeguards."""

    READ_COMMAND_TIMEOUT = 1.0
    WRITE_COMMAND_TIMEOUT = 5.0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.pipe:
            self.pipe.timeout = 0.25

    def _command(self, ser, cmd, *args):
        """Run a CAT command without the stock one-second write cutoff.

        The generic Kenwood live driver allows only one second for every
        response. Reads from a TS-2000 complete within that window, but some
        units take longer to commit MW/MC memory writes. The protocol still
        validates the echoed command, so a longer bounded wait cannot turn a
        rejected write into a successful one.
        """
        start = time.time()
        timeout = (
            self.WRITE_COMMAND_TIMEOUT
            if cmd.startswith(("MW", "MC"))
            else self.READ_COMMAND_TIMEOUT
        )

        if args:
            cmd += self.LAST_DELIMITER[1] + self.LAST_DELIMITER[1].join(args)
        cmd += self.LAST_DELIMITER[0]

        kenwood_live.LOG.debug("PC->RADIO: %s", cmd.strip())
        ser.write(cmd.encode("cp1252"))

        result = ""
        while not result.endswith(self.LAST_DELIMITER[0]):
            result += ser.read(8).decode("cp1252")
            if time.time() - start > timeout:
                kenwood_live.LOG.error(
                    "TS-2000 command timed out after %.1f seconds",
                    timeout,
                )
                break

        if result.endswith(self.LAST_DELIMITER[0]):
            kenwood_live.LOG.debug("RADIO->PC: %r", result.strip())
            result = result[:-1]
        else:
            kenwood_live.LOG.error("TS-2000 gave up waiting for a response")

        return result.strip()
