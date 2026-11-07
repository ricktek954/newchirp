# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""NewChirp Icom IC-E90 / IC-T90A clone transport.

The IC-E90 enters clone mode with [8 SET]+[MR]+power. A read moves the radio
through CL OUT; a write moves it through CL IN. The radio may ignore a control
query while its clone task is still settling, so this driver retries
identification and explicitly waits for clone-in to accept data before sending
the image.

The CS-T90A CPS models these operations as retryable Send/waitAnswer/waitEcho
steps. CHIRP's inherited write path sends clone-in and immediately streams data
without that readiness boundary. This implementation owns the complete
transport and preserves every unedited byte in the downloaded image.
"""

import logging
import struct
import time

from chirp import chirp_common, directory, errors, memmap
from chirp.drivers import icx90


LOG = logging.getLogger(__name__)

MODEL_ID = b"\x25\x07\x00\x01"
END_FRAME = b"Icom Inc."
MEMORY_SIZE = 0x2D40
BLOCK_SIZE = 32

ADDR_PC = 0xEE
ADDR_RADIO = 0xEF
CMD_CLONE_ID = 0xE0
CMD_CLONE_MODEL = 0xE1
CMD_CLONE_OUT = 0xE2
CMD_CLONE_IN = 0xE3
CMD_CLONE_DATA = 0xE4
CMD_CLONE_END = 0xE5
CMD_CLONE_OK = 0xE6

IDENT_ATTEMPTS = 4
IDENT_TIMEOUT = 1.0
IDENT_RETRY_DELAY = 0.20
READ_TIMEOUT = 15.0
READ_POLL = 0.75
WRITE_TURNAROUND = 0.15
ECHO_TIMEOUT = 0.75
WRITE_RESULT_TIMEOUT = 15.0


directory.enable_reregistrations()

_UPSTREAM_GET_MEMORY = icx90.ICx90Radio.get_memory


def _get_memory_with_invisible_guard(self, number):
    if (
        isinstance(number, int)
        and 0 <= number < len(self.memobj.banks)
        and self.memobj.banks[number].invisible_channel
    ):
        memory = chirp_common.Memory()
        memory.number = number
        memory.empty = True
        return memory
    return _UPSTREAM_GET_MEMORY(self, number)


_get_memory_with_invisible_guard.newchirp_invisible_guard = True
icx90.ICx90Radio.get_memory = _get_memory_with_invisible_guard


def _pack_frame(command, payload=b""):
    return (
        b"\xfe\xfe"
        + bytes((ADDR_PC, ADDR_RADIO, command))
        + payload
        + b"\xfd"
    )


def _decode_hex_payload(payload):
    if len(payload) % 2:
        raise errors.InvalidDataError(
            "IC-E90 frame has an odd number of hexadecimal characters"
        )
    try:
        return bytes.fromhex(payload.decode("ascii"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise errors.InvalidDataError(
            "IC-E90 frame contains non-hexadecimal data"
        ) from exc


def _decode_data_payload(payload):
    data = _decode_hex_payload(payload)
    if len(data) < 4:
        raise errors.InvalidDataError("IC-E90 data frame is too short")
    address, length = struct.unpack(">HB", data[:3])
    expected_length = 3 + length + 1
    if len(data) != expected_length:
        raise errors.InvalidDataError(
            "IC-E90 data frame says it has %i bytes but carries %i"
            % (length, max(0, len(data) - 4))
        )
    body = data[3:3 + length]
    checksum = data[-1]
    calculated = (-sum(data[:-1])) & 0xFF
    if checksum != calculated:
        raise errors.InvalidDataError(
            "IC-E90 checksum mismatch at 0x%04X: expected 0x%02X, got 0x%02X"
            % (address, calculated, checksum)
        )
    return address, body


def _is_end_payload(payload):
    if payload.rstrip(b"\x00") == END_FRAME:
        return True
    try:
        return _decode_hex_payload(payload).rstrip(b"\x00") == END_FRAME
    except errors.InvalidDataError:
        return False


def _clone_succeeded(payload):
    return payload[:1] == b"\x00" or payload == b"00"


class _IcfFrame:
    __slots__ = ("source", "destination", "command", "payload", "wire")

    def __init__(self, source, destination, command, payload, wire):
        self.source = source
        self.destination = destination
        self.command = command
        self.payload = payload
        self.wire = wire

    @property
    def is_pc_echo(self):
        return (
            self.source == ADDR_PC
            and self.destination == ADDR_RADIO
        )


class _FrameReader:
    """Assemble ICF frames while retaining unread bytes and deferred frames."""

    def __init__(self, pipe):
        self.pipe = pipe
        self.buffer = bytearray()
        self.pending = []
        self.saw_echo = False

    def clear_input(self):
        self.buffer.clear()
        self.pending.clear()
        try:
            self.pipe.reset_input_buffer()
        except AttributeError:
            pass

    def prepend(self, frames):
        if frames:
            self.pending[0:0] = list(frames)

    def _extract_frame(self):
        while True:
            start = self.buffer.find(b"\xfe\xfe")
            if start < 0:
                if self.buffer:
                    self.buffer[:] = self.buffer[-1:]
                return None
            if start:
                del self.buffer[:start]
            while self.buffer.startswith(b"\xfe\xfe\xfe"):
                del self.buffer[0]
            if len(self.buffer) < 5:
                return None
            end = self.buffer.find(b"\xfd", 5)
            if end < 0:
                if len(self.buffer) > 4096:
                    raise errors.InvalidDataError(
                        "IC-E90 sent an oversized serial frame"
                    )
                return None
            wire = bytes(self.buffer[:end + 1])
            del self.buffer[:end + 1]
            frame = _IcfFrame(
                wire[2],
                wire[3],
                wire[4],
                wire[5:-1],
                wire,
            )
            if frame.is_pc_echo:
                self.saw_echo = True
            return frame

    def read_frame(self, deadline):
        while True:
            if self.pending:
                return self.pending.pop(0)
            frame = self._extract_frame()
            if frame is not None:
                return frame
            if time.monotonic() >= deadline:
                return None
            data = self.pipe.read(1)
            if data:
                self.buffer.extend(data)


def _wait_for_echo(reader, deadline):
    deferred = []
    while True:
        frame = reader.read_frame(deadline)
        if frame is None:
            reader.prepend(deferred)
            return False
        if frame.is_pc_echo:
            reader.prepend(deferred)
            return True
        deferred.append(frame)


@directory.register
class ICx90Radio(icx90.ICx90Radio):
    """Icom IC-E90 with a NewChirp-owned clone transport."""

    ALIASES = icx90.ICx90Radio.ALIASES

    @classmethod
    def get_prompts(cls):
        prompts = super().get_prompts()
        prompts.info = (
            "Put the IC-E90 in clone mode with [8 SET]+[MR]+power. NewChirp "
            "uses the CS-T90A identity/write state machine and retries a "
            "radio that is temporarily slow to answer. Keep an unedited "
            "backup before changing the radio."
        )
        prompts.pre_download = (
            "1. Turn the radio off.\n"
            "2. Hold [8 SET] and [MR], then power on to enter cloning mode.\n"
            "3. Connect the OPC-478 programming cable and start the download.\n\n"
            "The radio normally displays CL OUT while data is read. Do not "
            "start a write from a radio left in that transfer state."
        )
        prompts.pre_upload = (
            "Before writing, power-cycle the radio and enter a fresh cloning "
            "session. The display should begin at CLONE, then change to CL IN "
            "when NewChirp starts the write. If it stays on CLONE or CL OUT, "
            "stop and retry from a new clone-mode session.\n\n"
            "Keep an unedited image downloaded from this radio. After the "
            "write succeeds, power-cycle the radio and read it back to verify "
            "the edited channels."
        )
        return prompts

    def _write_frame(self, command, payload=b""):
        self.pipe.write(_pack_frame(command, payload))
        self.pipe.flush()

    def _identify(self, reader):
        last_error = None
        for attempt in range(IDENT_ATTEMPTS):
            reader.clear_input()
            LOG.debug(
                "IC-E90 identity query attempt %i/%i",
                attempt + 1,
                IDENT_ATTEMPTS,
            )
            self._write_frame(CMD_CLONE_ID, b"\x00\x00\x00\x00")
            deadline = time.monotonic() + IDENT_TIMEOUT
            while True:
                frame = reader.read_frame(deadline)
                if frame is None:
                    break
                if frame.is_pc_echo:
                    continue
                if (
                    frame.source == ADDR_RADIO
                    and frame.destination == ADDR_PC
                    and frame.command == CMD_CLONE_MODEL
                ):
                    if len(frame.payload) < 4:
                        last_error = errors.RadioNoResponse(
                            "The IC-E90 returned incomplete identification data"
                        )
                        break
                    if frame.payload[:4] != MODEL_ID:
                        raise errors.RadioError(
                            "The connected radio identified as %s, not IC-E90/"
                            "IC-T90A"
                            % frame.payload[:4].hex()
                        )
                    return frame.payload
            if attempt + 1 < IDENT_ATTEMPTS:
                time.sleep(IDENT_RETRY_DELAY)
        raise errors.RadioNoResponse(
            "The IC-E90 did not answer the clone identity query after %i "
            "attempts. %s Power-cycle the radio, re-enter clone mode with "
            "[8 SET]+[MR], confirm it displays CLONE, and retry."
            % (
                IDENT_ATTEMPTS,
                str(last_error) if last_error else "",
            )
        )

    def _start_clone(self, reader, command):
        self._write_frame(command, MODEL_ID)
        if reader.saw_echo:
            _wait_for_echo(
                reader,
                time.monotonic() + ECHO_TIMEOUT,
            )
        if command == CMD_CLONE_IN:
            # Do not stream image blocks into the old CL OUT direction while
            # the radio is changing to CL IN.
            time.sleep(WRITE_TURNAROUND)

    def _clone_from_radio(self):
        reader = _FrameReader(self.pipe)
        self._identify(reader)
        self._start_clone(reader, CMD_CLONE_OUT)

        image = bytearray(MEMORY_SIZE)
        next_address = 0
        got_end = False
        complete = False
        last_frame = time.monotonic()
        status = chirp_common.Status()
        status.msg = "Cloning from radio"
        status.max = MEMORY_SIZE

        while not got_end:
            frame = reader.read_frame(time.monotonic() + READ_POLL)
            if frame is None:
                if complete:
                    LOG.info(
                        "IC-E90 image complete at 0x%04X without an end frame",
                        next_address,
                    )
                    break
                if time.monotonic() - last_frame > READ_TIMEOUT:
                    break
                continue

            last_frame = time.monotonic()
            if frame.is_pc_echo:
                continue
            if (
                frame.source != ADDR_RADIO
                or frame.destination != ADDR_PC
            ):
                continue
            if frame.command == CMD_CLONE_DATA:
                address, data = _decode_data_payload(frame.payload)
                if address != next_address:
                    raise errors.InvalidDataError(
                        "IC-E90 image gap: expected 0x%04X, received 0x%04X"
                        % (next_address, address)
                    )
                end = address + len(data)
                if end > MEMORY_SIZE:
                    raise errors.InvalidDataError(
                        "IC-E90 data extends past the 0x%04X image boundary"
                        % MEMORY_SIZE
                    )
                image[address:end] = data
                next_address = end
                complete = next_address == MEMORY_SIZE
            elif frame.command == CMD_CLONE_END:
                if not _is_end_payload(frame.payload):
                    raise errors.InvalidDataError(
                        "IC-E90 returned an unexpected clone-end marker"
                    )
                got_end = True

            if self.status_fn:
                status.cur = min(next_address, MEMORY_SIZE)
                self.status_fn(status)

            if complete and not got_end:
                LOG.info(
                    "IC-E90 image complete at 0x%04X; final end frame not "
                    "required",
                    next_address,
                )
                break

        if not complete:
            raise errors.RadioError(
                "IC-E90 clone download stopped at 0x%04X of 0x%04X bytes"
                % (next_address, MEMORY_SIZE)
            )
        reader.clear_input()
        return memmap.MemoryMapBytes(bytes(image))

    def _clone_to_radio(self):
        image = self.get_mmap().get_packed()
        if len(image) != MEMORY_SIZE:
            raise errors.InvalidDataError(
                "IC-E90 image is %i bytes; expected %i"
                % (len(image), MEMORY_SIZE)
            )

        reader = _FrameReader(self.pipe)
        self._identify(reader)
        self._start_clone(reader, CMD_CLONE_IN)

        status = chirp_common.Status()
        status.msg = "Cloning to radio"
        status.max = MEMORY_SIZE
        for address in range(0, MEMORY_SIZE, BLOCK_SIZE):
            chunk = image[address:address + BLOCK_SIZE]
            framed = struct.pack(">HB", address, len(chunk)) + chunk
            framed += bytes(((-sum(framed)) & 0xFF,))
            self._write_frame(CMD_CLONE_DATA, framed.hex().upper().encode())
            if reader.saw_echo and not _wait_for_echo(
                reader,
                time.monotonic() + ECHO_TIMEOUT,
            ):
                raise errors.RadioNoResponse(
                    "The IC-E90 stopped acknowledging clone data at 0x%04X"
                    % address
                )
            if self.status_fn:
                status.cur = address + len(chunk)
                self.status_fn(status)

        self._write_frame(CMD_CLONE_END, END_FRAME)
        if reader.saw_echo:
            _wait_for_echo(reader, time.monotonic() + ECHO_TIMEOUT)

        result = None
        deadline = time.monotonic() + WRITE_RESULT_TIMEOUT
        while True:
            frame = reader.read_frame(deadline)
            if frame is None:
                break
            if frame.is_pc_echo:
                continue
            if (
                frame.source == ADDR_RADIO
                and frame.destination == ADDR_PC
                and frame.command == CMD_CLONE_OK
            ):
                result = frame
                break

        if result is None:
            raise errors.RadioNoResponse(
                "The IC-E90 accepted clone-in but did not report completion. "
                "The radio must display CL IN. Power-cycle it, re-enter clone "
                "mode, and retry from a freshly downloaded image."
            )
        if not _clone_succeeded(result.payload):
            detail = (
                "0x%02X" % result.payload[0]
                if result.payload
                else "no status"
            )
            raise errors.RadioError(
                "The IC-E90 rejected the clone image (%s)" % detail
            )

    def sync_in(self):
        image = self._clone_from_radio()
        self._mmap = image
        self._memsize = len(self._mmap)
        self._metadata["icom_image_size"] = self._memsize
        self.process_mmap()

    def sync_out(self):
        self.pipe.baudrate = self.BAUD_RATE
        self._clone_to_radio()
