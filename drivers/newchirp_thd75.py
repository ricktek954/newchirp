# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Kenwood TH-D75 CAT handling for USB adapters that echo commands."""

import time

from chirp import chirp_common, directory
from chirp.drivers import thd74


COMMAND_TIMEOUT = 2.0


@directory.register
class THD75Radio(thd74.THD75Radio):
    """TH-D75 with echo-tolerant and slower CAT responses."""

    @classmethod
    def get_prompts(cls):
        prompts = super().get_prompts()
        prompts.info = (
            "Connect the TH-D75 with its USB programming cable and close the "
            "Kenwood MCP-D75 software before reading or writing."
        )
        return prompts

    def command(self, command, timeout=COMMAND_TIMEOUT):
        """Return the radio response, skipping an echoed command line."""
        deadline = time.monotonic() + max(timeout, COMMAND_TIMEOUT)
        self.pipe.write((command + "\r").encode())
        data = bytearray()
        while time.monotonic() < deadline:
            char = self.pipe.read(1)
            if not char:
                continue
            data.extend(char)
            if not data.endswith(b"\r"):
                continue
            text = data.decode("ascii", errors="replace").strip()
            data.clear()
            if not text:
                continue
            if text == command:
                # Some USB serial adapters and radio CAT settings echo the
                # command. The actual response follows on the next line.
                continue
            return text
        return ""
