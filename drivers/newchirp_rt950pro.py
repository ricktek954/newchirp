# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Experimental read-only driver for the Radtel RT-950 Pro.

The Pro shares the RT-950/BT-9000 handshake and channel encoding, but uses a
larger CPS memory map. The Pro model remains separate so a successful base
RT-950 profile can never silently select the wrong block layout.
"""

from __future__ import annotations

import importlib
import logging
import sys

from chirp import chirp_common, directory, errors, memmap


LOG = logging.getLogger(__name__)

try:
    _BASE = sys.modules["newchirp.drivers.newchirp_rt950"]
except KeyError:
    try:
        _BASE = importlib.import_module("newchirp.drivers.newchirp_rt950")
    except ModuleNotFoundError:
        # Packaged overrides are colocated inside CHIRP's driver package.
        _BASE = importlib.import_module(".newchirp_rt950", __package__)


PRO_MEM_SIZE = 0xD300
PRO_MODEL_PREFIXES = (b"RT-950", b"RT950", b"BT-9000")
PRO_INITIAL_ACK_TIMEOUT = 3.0

# command, source address, length, destination address in the CHIRP image.
# The final 0x54/0x55-only block is APRS data; it is retained at 0xC000 so the
# saved image remains lossless without pretending it is a normal address read.
PRO_SEGMENTS = (
    (0x52, 0x0000, 0x7800, 0x0000),
    (0x52, 0x8000, 0x0100, 0x8000),
    (0x52, 0x9000, 0x0100, 0x9000),
    (0x52, 0xA000, 0x0200, 0xA000),
    (0x52, 0xB000, 0x0200, 0xB000),
    (0x52, 0xD000, 0x0300, 0xD000),
    (0x54, 0x0000, 0x0080, 0xC000),
)


def _pro_read_blocks():
    for command, source, length, target in PRO_SEGMENTS:
        for offset in range(0, length, _BASE.BLOCK_SIZE):
            yield command, source + offset, target + offset


@directory.register
class RT950ProRadio(_BASE.RT950Radio):
    """Radtel RT-950 Pro experimental read-only driver."""

    VENDOR = "Radtel"
    MODEL = "RT-950 Pro"
    BAUD_RATE = 115200
    INITIAL_ACK_TIMEOUT = PRO_INITIAL_ACK_TIMEOUT
    _memsize = PRO_MEM_SIZE

    @classmethod
    def get_prompts(cls):
        prompts = chirp_common.RadioPrompts()
        prompts.experimental = (
            "NewChirp RT-950 Pro support is experimental and read-only. "
            "The Pro uses the RT-950/BT-9000 handshake with a larger CPS "
            "memory map. Uploads remain disabled until a complete physical "
            "read and controlled read-back have been validated."
        )
        prompts.info = (
            "Use the RT-950 Pro programming cable, power the radio on "
            "normally, and close Radtel CPS before connecting. The interface "
            "uses 115200 baud, 8N1, with RTS and DTR asserted and no hardware "
            "or XON/XOFF flow control."
        )
        prompts.pre_download = (
            "1. Restore or confirm the CPS backup if the radio was recently "
            "edited.\n"
            "2. Close Radtel CPS and any other serial software.\n"
            "3. Connect the cable directly and start the read while the "
            "radio is powered on.\n\n"
            "This driver is read-only. Do not attempt an upload."
        )
        return prompts

    def get_features(self):
        rf = super().get_features()
        rf.valid_bands = [
            (18_000_000, 64_000_000),
            (70_000_000, 137_000_000),
            (136_000_000, 174_000_000),
            (174_000_000, 400_000_000),
            (400_000_000, 480_000_000),
            (480_000_000, 580_000_000),
        ]
        rf.has_settings = False
        return rf

    def _handshake_once(self):
        if hasattr(self.pipe, "reset_input_buffer"):
            self.pipe.reset_input_buffer()

        self.pipe.write(_BASE.HANDSHAKE)
        if self._read_exact(
            1, timeout=self.INITIAL_ACK_TIMEOUT
        ) != _BASE.ACK:
            raise errors.RadioNoResponse(
                "The RT-950 Pro did not acknowledge programming mode "
                "within %.1f seconds." % self.INITIAL_ACK_TIMEOUT
            )

        self.pipe.write(b"F")
        self._read_exact(16)

        self.pipe.write(b"M")
        model = self._read_exact(12).replace(b"\x00", b"").strip()
        if not model:
            raise errors.RadioError(
                "The RT-950 Pro returned an empty model identifier."
            )
        if not any(model.startswith(prefix) for prefix in PRO_MODEL_PREFIXES):
            raise errors.RadioError(
                "RT-950 Pro driver received unrecognized model code %r"
                % model
            )
        self._pro_model = model
        LOG.debug("RT-950 Pro model code: %s", model.decode("ascii", "replace"))

        send_packet, self._encryption_symbol = _BASE._send_packet_and_symbol()
        self.pipe.write(send_packet)
        if self._read_exact(1) != _BASE.ACK:
            raise errors.RadioNoResponse(
                "The RT-950 Pro did not acknowledge data encryption."
            )

    def _read_pro_block(self, command, address):
        request = bytes(
            (command, address >> 8, address & 0xFF, _BASE.BLOCK_SIZE)
        )
        self.pipe.write(request)
        reply = self._read_exact(4 + _BASE.BLOCK_SIZE)
        if reply[1:3] != request[1:3]:
            raise errors.RadioError(
                "RT-950 Pro returned the wrong block address for 0x%04x: %r"
                % (address, reply[1:3])
            )
        return _BASE._decode_payload(reply[4:], self._encryption_symbol)

    def sync_in(self):
        session_started = False
        try:
            self._handshake()
            session_started = True

            memory = memmap.MemoryMapBytes(b"\xff" * PRO_MEM_SIZE)
            blocks = tuple(_pro_read_blocks())
            for current, (command, address, target) in enumerate(blocks, 1):
                status = chirp_common.Status()
                status.cur = current
                status.max = len(blocks)
                status.msg = (
                    "Reading RT-950 Pro channels"
                    if command == 0x52 and address < 0x7800
                    else "Reading RT-950 Pro settings"
                )
                self.status_fn(status)
                memory.set(
                    target,
                    self._read_pro_block(command, address),
                )
        except errors.RadioError:
            raise
        except Exception as exc:
            raise errors.RadioError(
                "Failed to communicate with the RT-950 Pro: %s" % exc
            ) from exc
        finally:
            if session_started:
                try:
                    self.pipe.write(b"E")
                except Exception:
                    pass

        self._mmap = memory
        self.process_mmap()

    def sync_out(self):
        raise errors.RadioError(
            "The experimental RT-950 Pro driver is read-only; uploads are "
            "disabled until the larger CPS map and write read-back are "
            "physically validated."
        )

    def set_memory(self, memory):
        raise errors.RadioError(
            "The experimental RT-950 Pro driver is read-only; channel writes "
            "are not enabled."
        )
