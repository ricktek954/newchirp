# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""NewChirp transport for the newer Radioddity GA-510 V2 hardware."""

from __future__ import annotations

import time

from chirp import chirp_common, directory, errors
from chirp.drivers import ga510


ACK = b"\x06"
BAUD_RATE = 57600
BLOCK_SIZE = 0x40
INFO_BLOCKS = (0, 0x10, 0x20)
BLOCK_ORDER = (2, 4, 6, 16, 24)
IMAGE_SIZE = len(BLOCK_ORDER) * 0x1000
DESCRIPTOR_ADDRESSES = (0x1FFF, 0x2FFF, 0x3FFF, 0x4FFF, 0x5FFF, 0x6FFF)
COMMAND_TIMEOUT = 0.5
DATA_TIMEOUT = 2.0

HOST_ACK = bytes((0x06,))
HOST_UNLOCK = b"\xFF\xFF\xFF\xFF\x0C"
PSEARCH = b"PSEARCH"
PASSSTA = b"PASSSTA"
PASWORD = b"PASWORD"
SYSINFO = b"SYSINFO"
DMR1702 = b"DMR1702"


def _set_timeout(pipe, timeout):
    try:
        pipe.timeout = timeout
    except Exception:
        pass


def _drain(pipe):
    _set_timeout(pipe, 0.005)
    try:
        pipe.read(256)
    finally:
        _set_timeout(pipe, 0.25)


def _send(pipe, payload):
    try:
        pipe.write(bytes(payload))
        pipe.flush()
    except Exception as exc:
        raise errors.RadioError(
            "Could not send a GA-510 V2 programming command."
        ) from exc


def _read_exact(pipe, size, timeout):
    deadline = time.monotonic() + timeout
    data = bytearray()
    _set_timeout(pipe, min(0.05, timeout))
    try:
        while len(data) < size:
            if time.monotonic() >= deadline:
                break
            chunk = pipe.read(size - len(data))
            if chunk:
                data.extend(chunk)
            else:
                remaining = deadline - time.monotonic()
                if remaining > 0:
                    time.sleep(min(0.005, remaining))
    finally:
        _set_timeout(pipe, 0.25)
    return bytes(data)


def _send_and_read(pipe, command, size, timeout=COMMAND_TIMEOUT):
    _send(pipe, command)
    return _read_exact(pipe, size, timeout)


def _send_ack(pipe):
    _send(pipe, HOST_ACK)
    if _read_exact(pipe, 1, COMMAND_TIMEOUT) != ACK:
        raise errors.RadioError("The GA-510 V2 did not acknowledge the command.")


def _identify(pipe):
    for _attempt in range(3):
        response = _send_and_read(pipe, PSEARCH, 8)
        if len(response) == 8 and response[:1] == ACK:
            return response[1:]
    raise errors.RadioNoResponse(
        "The GA-510 V2 did not answer PSEARCH. Power-cycle the radio, "
        "close CHIRP or Radioddity CPS, and confirm the selected COM port."
    )


def _protocol_handshake(pipe, writing):
    response = _send_and_read(pipe, PASSSTA, 3)
    if len(response) != 3 or response[:1] != b"P":
        detail = response.hex() if response else "no data"
        raise errors.RadioError(
            "The GA-510 V2 rejected the programming status request (%s)."
            % detail
        )

    password_marker = response[2] if writing else response[1]
    if password_marker == 0xA5:
        if _send_and_read(pipe, PASWORD, 1) != ACK:
            raise errors.RadioError(
                "The GA-510 V2 rejected the OEM programming unlock."
            )

    response = _send_and_read(pipe, SYSINFO, 1)
    if response == b"\x15":
        raise errors.RadioError(
            "The GA-510 V2 reported that it is busy. Power-cycle it and retry."
        )
    if response != ACK:
        raise errors.RadioError(
            "The GA-510 V2 did not acknowledge SYSINFO (%s)."
            % (response.hex() if response else "no data")
        )

    _dmr_handshake(pipe)


def _dmr_handshake(pipe):
    response = _send_and_read(pipe, DMR1702, 1)
    if response != ACK:
        raise errors.RadioError(
            "The GA-510 V2 did not acknowledge the DMR1702 identity stage."
        )
    identity = _send_and_read(pipe, b"\x02", 8)
    if len(identity) != 8 or identity[:1] != ACK:
        raise errors.RadioError(
            "The connected radio did not return the GA-510 V2 DMR1702 mark."
        )
    _send_ack(pipe)


def _send_info_query(pipe, address):
    command = (
        bytes((0x56,))
        + bytes(((address >> 8) & 0x0F, address & 0xFF, 0x0A, 0x0D))
    )
    header = _send_and_read(pipe, command, 3)
    if len(header) != 3 or header[0] != 0x56:
        raise errors.RadioError("The GA-510 V2 returned invalid memory info.")
    size = header[2]
    if size > BLOCK_SIZE:
        raise errors.RadioError(
            "The GA-510 V2 returned an invalid memory-info length of %i." % size
        )
    payload = _read_exact(pipe, size, COMMAND_TIMEOUT)
    if len(payload) != size:
        raise errors.RadioError("The GA-510 V2 returned short memory info.")
    _send_ack(pipe)
    return payload


def _query_memory_layout(pipe):
    for address in INFO_BLOCKS:
        _send_info_query(pipe, address)

    command = bytes((0x56, 0x00, 0x00, 0x00, 0x0A))
    header = _send_and_read(pipe, command, 3)
    if len(header) != 3 or header[0] != 0x56:
        raise errors.RadioError("The GA-510 V2 returned invalid memory-size data.")
    size = header[2]
    if size > BLOCK_SIZE:
        raise errors.RadioError(
            "The GA-510 V2 returned an invalid memory-size length."
        )
    payload = _read_exact(pipe, size, COMMAND_TIMEOUT)
    if len(payload) != size:
        raise errors.RadioError("The GA-510 V2 returned short memory-size data.")
    _send_ack(pipe)

    _send(pipe, HOST_UNLOCK)
    _dmr_handshake(pipe)


def _read_block(pipe, address, size):
    command = (
        bytes((0x52,))
        + address.to_bytes(3, "little")
        + bytes((size,))
    )
    response = _send_and_read(
        pipe,
        command,
        size + 5,
        timeout=DATA_TIMEOUT,
    )
    if len(response) != size + 5:
        raise errors.RadioError(
            "Short GA-510 V2 read at 0x%04X: expected %i bytes, got %i."
            % (address, size + 5, len(response))
        )
    if response[:5] != command:
        raise errors.RadioError(
            "The GA-510 V2 returned a mismatched read header at 0x%04X."
            % address
        )
    _send_ack(pipe)
    return response[5:]


def _write_block(pipe, address, data):
    command = (
        bytes((0x57,))
        + address.to_bytes(3, "little")
        + bytes((len(data),))
    )
    _send(pipe, command + bytes(data))
    response = _read_exact(pipe, 1, COMMAND_TIMEOUT)
    if response == b"\x15":
        raise errors.RadioError(
            "The GA-510 V2 rejected write address 0x%04X as busy." % address
        )
    if response != ACK:
        raise errors.RadioError(
            "The GA-510 V2 did not acknowledge write address 0x%04X (%s)."
            % (address, response.hex() if response else "no data")
        )


def _decode_page_number(value):
    high = (value >> 4) & 0x0F
    low = value & 0x0F
    if high > 9 or low > 9:
        return None
    return high * 10 + low


def _encode_page_number(number):
    return ((number // 10) << 4) | (number % 10)


def _memory_map(pipe):
    pages = []
    for address in DESCRIPTOR_ADDRESSES:
        value = _read_block(pipe, address, 1)[0]
        page = _decode_page_number(value)
        if page is not None:
            pages.append(page)
    missing = [number for number in BLOCK_ORDER if number not in pages]
    if missing:
        raise errors.RadioError(
            "The GA-510 V2 memory map is missing block%s %s. Do not write "
            "an image until the radio has been recovered with Radioddity CPS."
            % (
                "" if len(missing) == 1 else "s",
                ", ".join(str(number) for number in missing),
            )
        )
    return pages


def _enter_programming_mode(radio, writing=False):
    pipe = radio.pipe
    pipe.baudrate = BAUD_RATE
    pipe.parity = "N"
    pipe.stopbits = 1
    pipe.bytesize = 8
    _drain(pipe)
    _identify(pipe)
    _protocol_handshake(pipe, writing)
    _query_memory_layout(pipe)
    pipe._newchirp_ga510_ready = True


def _session_ready(radio):
    ready = bool(getattr(radio.pipe, "_newchirp_ga510_ready", False))
    radio.pipe._newchirp_ga510_ready = False
    return ready


def _download(radio):
    if not _session_ready(radio):
        _enter_programming_mode(radio)

    pages = _memory_map(radio.pipe)
    status = chirp_common.Status()
    status.msg = "Downloading GA-510 V2"
    status.cur = 0
    status.max = len(BLOCK_ORDER) * 0x1000 // BLOCK_SIZE

    image = bytearray()
    for destination, block_number in enumerate(BLOCK_ORDER):
        physical_page = pages.index(block_number) + 1
        start = physical_page * 0x1000
        logical = destination * 0x1000
        for offset in range(0, 0x1000, BLOCK_SIZE):
            image.extend(_read_block(radio.pipe, start + offset, BLOCK_SIZE))
            status.cur = (len(image) // BLOCK_SIZE)
            radio.status_fn(status)
        if len(image) != logical + 0x1000:
            raise errors.RadioError("Internal GA-510 V2 image assembly error.")
    return bytes(image)


def _upload(radio):
    _enter_programming_mode(radio, writing=True)
    pages = _memory_map(radio.pipe)
    image = radio._mmap.get_packed()
    status = chirp_common.Status()
    status.msg = "Uploading GA-510 V2"
    status.cur = 0
    status.max = len(BLOCK_ORDER) * 0x1000 // BLOCK_SIZE

    for source, block_number in enumerate(BLOCK_ORDER):
        physical_page = pages.index(block_number) + 1
        start = physical_page * 0x1000
        logical = source * 0x1000
        for offset in range(0, 0x1000, BLOCK_SIZE):
            payload = bytearray(
                image[logical + offset:logical + offset + BLOCK_SIZE]
            )
            if offset == 0x1000 - BLOCK_SIZE:
                payload[-1] = _encode_page_number(block_number)
            _write_block(radio.pipe, start + offset, payload)
            status.cur = (source * 0x1000 + offset) // BLOCK_SIZE + 1
            radio.status_fn(status)


directory.enable_reregistrations()


@directory.register
class RadioddityGA510V2(
    ga510.RadioddityGA510v2,
    chirp_common.ExperimentalRadio,
):
    """GA-510 V2 with the exact transport traced from CPS v1.00.36."""

    @classmethod
    def get_prompts(cls):
        prompts = super().get_prompts()
        prompts.experimental = (
            "NewChirp GA-510 V2 support uses a transport reconstructed from "
            "Radioddity CPS v1.00.36. It fixes detection and programming "
            "behavior that differs from stock CHIRP on some radios. Keep an "
            "unedited CPS backup and verify the first write by reading it "
            "back."
        )
        prompts.info = (
            "Close Radioddity CPS and CHIRP, power-cycle the GA-510, and "
            "select the COM port created by the programming cable. This "
            "driver is for the newer GA-510 V2 at 57,600 baud."
        )
        prompts.pre_upload = (
            "Save an unedited image from Radioddity CPS before writing. "
            "After the upload, read the radio back and verify the edited "
            "channel before relying on the radio."
        )
        return prompts

    @classmethod
    def detect_from_serial(cls, pipe):
        radio = cls(pipe)
        try:
            _enter_programming_mode(radio)
        except Exception:
            if hasattr(pipe, "_newchirp_ga510_ready"):
                del pipe._newchirp_ga510_ready
            raise
        return cls

    def sync_in(self):
        self._mmap = ga510.memmap.MemoryMapBytes(_download(self))
        self.process_mmap()

    def sync_out(self):
        if len(self._mmap.get_packed()) != IMAGE_SIZE:
            raise errors.RadioError(
                "The GA-510 V2 image is %i bytes; expected %i."
                % (len(self._mmap.get_packed()), IMAGE_SIZE)
            )
        _upload(self)


@directory.register
class RadioddityGA510(ga510.RadioddityGA510Radio):
    """GA-510 selector that prefers the CPS-derived V2 transport."""

    @classmethod
    def get_prompts(cls):
        prompts = super().get_prompts()
        prompts.info = (
            "NewChirp checks for the newer GA-510 V2 protocol first at "
            "57,600 baud, then falls back to the legacy 9,600-baud protocol. "
            "Close CHIRP or Radioddity CPS and use the COM port created by "
            "the programming cable."
        )
        return prompts

    @classmethod
    def detect_from_serial(cls, pipe):
        v2_radio = RadioddityGA510V2(pipe)
        try:
            _enter_programming_mode(v2_radio)
            return RadioddityGA510V2
        except (errors.RadioError, OSError):
            pass

        pipe.baudrate = cls.BAUD_RATE
        pipe.parity = "N"
        pipe.stopbits = 1
        pipe.bytesize = 8
        _drain(pipe)
        legacy_radio = ga510.RadioddityGA510Radio(pipe)
        ga510.start_program(legacy_radio)
        return ga510.RadioddityGA510Radio
