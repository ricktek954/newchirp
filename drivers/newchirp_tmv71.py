# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Kenwood TM-V71A/E clone-mode driver derived from Kenwood MCP-2A 3.22.

MCP-2A uses one shared memory map for the TM-V71, TM-D710 and RC-D710. The
transceiver body occupies 0x0000-0x7EFF. 0x7F00 (``MemAdr_Adjust_START``)
starts the factory adjustment area, which MCP-2A never reads or writes.
0x8000 and above belong to the RC-D710/TM-D710 control head. MCP-2A reads
only the body range from a TM-V71, so this driver reuses the TM-D710 body
layout from pinned CHIRP and drops the head-only Sky Command structure.

Transport contract (see docs/KENWOOD_TMV71_PROTOCOL.md):

    connect   ID\\r                 -> "ID TM-V71\\r" (baud probed)
    program   0M PROGRAM\\r         -> "0M\\r"   ("N" = refused)
    read      R hi lo 00           -> W hi lo 00 + 256 payload bytes
              06                   -> 06
    exit      E                    -> 06

Writes are disabled until a physical TM-V71 read and a controlled
write/read-back have been validated.
"""

import logging
import struct

from chirp import bitwise, chirp_common, directory, errors, memmap
from chirp.drivers import kenwood_live, tmd710
from chirp.settings import RadioSettings


LOG = logging.getLogger(__name__)

ACK = b"\x06"
BLOCK_SIZE = 0x100
BODY_END = 0x7F00          # MCP-2A MemAdr_Adjust_START; never read
MODEL_ID = "TM-V71"
PROGRAM_CMD = b"0M PROGRAM\r"
PROGRAM_ACK = b"0M\r"

_SKY_COMMAND_SEEK = "#seekto 0x08660;"
_D710_FORMAT = tmd710.KenwoodTMD710Radio.MEM_FORMAT
if _SKY_COMMAND_SEEK not in _D710_FORMAT:
    raise ImportError(
        "Pinned CHIRP TM-D710 layout changed; re-derive the TM-V71 body map."
    )
MEM_FORMAT = _D710_FORMAT.split(_SKY_COMMAND_SEEK)[0]

# Sky Command is stored in the RC-D710 head at 0x8660. A TM-V71 body has no
# such storage. This blank stand-in lets the inherited settings code run;
# the group it feeds is removed before settings reach the user.
_SKY_COMMAND_FORMAT = """
struct {
char cmdr[10];
char tptr[10];
u8  skytone;
} skycmd;
"""


def _read_exact(pipe, count, what):
    data = pipe.read(count)
    if len(data) != count:
        raise errors.RadioError(
            "TM-V71 %s: expected %i bytes, received %i."
            % (what, count, len(data))
        )
    return data


def read_block(pipe, address):
    """Read one 256-byte body block using the MCP-2A contract."""
    if address % BLOCK_SIZE or not 0 <= address < BODY_END:
        raise ValueError("Address 0x%04X is outside the TM-V71 body" % address)
    request = b"R" + struct.pack(">HB", address, 0)
    pipe.write(request)
    header = _read_exact(pipe, 4, "block 0x%04X header" % address)
    if header != b"W" + request[1:]:
        raise errors.RadioError(
            "TM-V71 block 0x%04X: unexpected header %s."
            % (address, header.hex(" "))
        )
    payload = _read_exact(pipe, BLOCK_SIZE, "block 0x%04X data" % address)
    pipe.write(ACK)
    ack = _read_exact(pipe, 1, "block 0x%04X acknowledgement" % address)
    if ack != ACK:
        raise errors.RadioError(
            "TM-V71 block 0x%04X: radio answered %s instead of ACK."
            % (address, ack.hex())
        )
    return payload


def enter_program_mode(pipe):
    pipe.write(PROGRAM_CMD)
    reply = _read_exact(pipe, 3, "program-mode reply")
    if reply != PROGRAM_ACK:
        raise errors.RadioError(
            "TM-V71 refused clone mode (reply %r)." % reply
        )


def exit_program_mode(pipe):
    try:
        pipe.write(b"E")
        reply = pipe.read(1)
        if reply != ACK:
            LOG.warning("TM-V71 exit reply was %r, not ACK", reply)
    except Exception:  # pragma: no cover - best-effort cleanup
        LOG.exception("TM-V71 exit command failed")


def check_identity(pipe):
    radio_id = kenwood_live.KenwoodLiveRadio(None).get_id(pipe)
    # MCP-2A prefix-matches the model name returned after "ID ".
    if not str(radio_id).startswith(MODEL_ID):
        if str(radio_id).startswith(("TM-D710", "RC-D710")):
            raise errors.RadioError(
                "The radio identifies as %s. Select the Kenwood TM-D710 "
                "clone-mode driver instead." % radio_id
            )
        raise errors.RadioError(
            "Radio identified as %s, not a TM-V71." % radio_id
        )
    # Clone responses need more than the 0.1 s live-mode timeout.
    pipe.timeout = 1
    return radio_id


def download(radio):
    status = chirp_common.Status()
    status.msg = "Reading TM-V71 memory"
    status.max = BODY_END // BLOCK_SIZE
    status.cur = 0
    data = bytearray()
    enter_program_mode(radio.pipe)
    try:
        for address in range(0, BODY_END, BLOCK_SIZE):
            data += read_block(radio.pipe, address)
            status.cur += 1
            if radio.status_fn:
                radio.status_fn(status)
    finally:
        exit_program_mode(radio.pipe)
    return bytes(data)


@directory.register
class KenwoodTMV71CloneRadio(
    tmd710.KenwoodTMD710Radio,
    chirp_common.ExperimentalRadio,
):
    """Kenwood TM-V71A/E transceiver body, programmed like MCP-2A."""

    VENDOR = "Kenwood"
    MODEL = "TM-V71_CloneMode"
    SHORT = ""
    BAUD_RATE = 9600
    HARDWARE_FLOW = True
    MEM_FORMAT = MEM_FORMAT
    _memsize = BODY_END
    _num_blocks = 1
    _num_packets = [BODY_END // BLOCK_SIZE]

    @classmethod
    def get_prompts(cls):
        rp = chirp_common.RadioPrompts()
        rp.experimental = (
            "TM-V71 clone-mode support is experimental and read-only. The "
            "transport and memory map were recovered from Kenwood MCP-2A "
            "3.22. Uploads stay disabled until a physical read and a "
            "controlled write/read-back are validated."
        )
        rp.pre_download = (
            "Connect the programming cable to the PC port on the back of "
            "the TM-V71 body and close MCP-2A before reading."
        )
        return rp

    def get_features(self):
        rf = super().get_features()
        # Matches the pinned CHIRP TM-V71 live driver: names are uppercase.
        rf.valid_characters = "".join(
            c for c in rf.valid_characters
            if not (c.isalpha() and c.islower())
        )
        return rf

    def sync_in(self):
        try:
            check_identity(self.pipe)
            data = download(self)
        except errors.RadioError:
            raise
        except Exception as exc:
            LOG.exception("Unexpected error during TM-V71 download")
            raise errors.RadioError(
                "Unexpected error communicating with the TM-V71: %s" % exc
            ) from exc
        self._mmap = memmap.MemoryMapBytes(data)
        self.process_mmap()

    def sync_out(self):
        raise errors.RadioError(
            "TM-V71 clone-mode support is read-only until a physical read "
            "and a controlled write/read-back are validated."
        )

    def get_settings(self):
        body = self._memobj
        sky = bitwise.parse(
            _SKY_COMMAND_FORMAT, memmap.MemoryMapBytes(b"\x00" * 21)
        ).skycmd

        class _BodyWithBlankSkyCommand:
            def __getattr__(self, name):
                if name == "skycmd":
                    return sky
                return getattr(body, name)

        self._memobj = _BodyWithBlankSkyCommand()
        try:
            settings = super().get_settings()
        finally:
            self._memobj = body
        return RadioSettings(*[
            group for group in settings if group.get_name() != "skyk"
        ])

    @classmethod
    def match_model(cls, filedata, filename):
        return False
