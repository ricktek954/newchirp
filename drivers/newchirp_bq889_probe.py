# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Read-only transport probe for the Binqi BQ-889 analog subsystem.

The BQ-889 uses a Beken BK4819 UHF transceiver. The OEM tool family used by
the related KSUN POC radios contains a read-only "Read Simulation" operation
backed by these AT commands:

    AT
    AT*READVER
    AT+CGMR
    AT+HSQ=R
    AT+HXTO=R
    AT+HCHDATA=R

NewChirp has not recovered the response framing or channel-record format for
the BQ-889, and the radio may not expose this interface at all. This driver is
therefore a selectable diagnostic target only. It cannot write the radio.
"""

from __future__ import annotations

import os
from pathlib import Path
import tempfile
import time

from chirp import chirp_common, directory, errors


BAUD_CANDIDATES = (115200, 9600, 38400, 57600, 19200, 230400)
PROBE_COMMANDS = (
    ("basic modem", b"AT"),
    ("firmware", b"AT*READVER"),
    ("modem version", b"AT+CGMR"),
    ("analog settings", b"AT+HSQ=R"),
    ("analog band", b"AT+HXTO=R"),
    ("analog channels", b"AT+HCHDATA=R"),
)
READ_COMMANDS = {command for _label, command in PROBE_COMMANDS}
MAX_MESSAGE_BYTES = 640


def _format_bytes(data, limit=MAX_MESSAGE_BYTES):
    """Return a bounded, one-line representation of serial data."""
    data = bytes(data)
    omitted = max(0, len(data) - limit)
    visible = data[:limit]
    escaped = "".join(
        chr(value) if 32 <= value <= 126 else "\\x%02x" % value
        for value in visible
    )
    if omitted:
        escaped += "... (%i bytes omitted)" % omitted
    return escaped


def _write_transcript(lines):
    fd, path = tempfile.mkstemp(
        prefix="newchirp-bq889-probe-",
        suffix=".txt",
    )
    os.close(fd)
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


@directory.register
class BQ889AnalogProbeRadio(
    chirp_common.CloneModeRadio,
    chirp_common.ExperimentalRadio,
):
    """Selectable read-only BQ-889 USB/AT transport probe."""

    VENDOR = "Binqi"
    MODEL = "BQ-889 Analog Probe"
    BAUD_RATE = 115200
    HARDWARE_FLOW = False
    XON_XOFF = False
    WANTS_DTR = False
    WANTS_RTS = False

    @classmethod
    def get_prompts(cls):
        prompts = chirp_common.RadioPrompts()
        prompts.experimental = (
            "This is a read-only transport probe, not yet a channel driver. "
            "It checks whether the BQ-889 exposes the AT interface used by "
            "related POC radios and captures the replies for driver work. "
            "It never sends a write command."
        )
        prompts.info = (
            "Connect the BQ-889 with a USB-C data cable, power it on, close "
            "KSUN POC software and any other serial program, select the "
            "radio's COM/tty port, and start Download From Radio."
        )
        prompts.pre_download = (
            "The probe will send only these read commands:\n"
            "AT, AT*READVER, AT+CGMR, AT+HSQ=R, AT+HXTO=R, AT+HCHDATA=R.\n\n"
            "It will finish with a diagnostic message and save a transcript. "
            "No frequencies or radio settings will be changed."
        )
        return prompts

    def get_features(self):
        features = chirp_common.RadioFeatures()
        features.has_settings = False
        features.has_name = False
        features.has_tuning_step = False
        features.memory_bounds = (1, 1)
        features.valid_bands = [(400000000, 480000000)]
        features.valid_modes = ["FM", "NFM"]
        return features

    def get_memory(self, number):
        if number != 1:
            raise errors.InvalidMemoryLocation(
                "The BQ-889 transport probe has only one placeholder channel."
            )
        memory = chirp_common.Memory()
        memory.number = number
        memory.empty = True
        return memory

    def _reset_input(self):
        reset = getattr(self.pipe, "reset_input_buffer", None)
        if reset is not None:
            reset()

    def _set_timeout(self, timeout):
        try:
            self.pipe.timeout = timeout
        except Exception:
            pass

    def _read_until_quiet(self, timeout=2.0, quiet=0.25):
        data = bytearray()
        deadline = time.monotonic() + timeout
        last_received = None
        self._set_timeout(0.05)
        try:
            while time.monotonic() < deadline:
                chunk = self.pipe.read(256)
                if chunk:
                    data.extend(chunk)
                    last_received = time.monotonic()
                elif (
                    last_received is not None
                    and time.monotonic() - last_received >= quiet
                ):
                    break
                else:
                    time.sleep(0.01)
        finally:
            self._set_timeout(0.25)
        return bytes(data)

    def _send_read(self, command, timeout=2.0):
        if command not in READ_COMMANDS:
            raise AssertionError(
                "The BQ-889 probe is read-only; refusing %r" % command
            )
        self._reset_input()
        self.pipe.write(command + b"\r")
        flush = getattr(self.pipe, "flush", None)
        if flush is not None:
            flush()
        return self._read_until_quiet(timeout=timeout)

    def _probe_at(self):
        original_baud = getattr(self.pipe, "baudrate", BAUD_CANDIDATES[0])
        attempts = []
        for baud in BAUD_CANDIDATES:
            try:
                self.pipe.baudrate = baud
                response = self._send_read(b"AT", timeout=0.9)
            except Exception as exc:
                attempts.append((baud, b"", "%s: %s" % (
                    exc.__class__.__name__,
                    exc,
                )))
                continue
            attempts.append((baud, response, ""))
            if response:
                return baud, attempts
        try:
            self.pipe.baudrate = original_baud
        except Exception:
            pass
        return None, attempts

    def sync_in(self):
        lines = [
            "NewChirp BQ-889 analog transport probe",
            "Read-only commands: %s" % ", ".join(
                command.decode("ascii")
                for _label, command in PROBE_COMMANDS
            ),
            "",
        ]
        found_baud, attempts = self._probe_at()
        for baud, response, error in attempts:
            lines.append(
                "%i TX: AT" % baud
            )
            if error:
                lines.append("       error: %s" % error)
            else:
                lines.append(
                    "       RX: %s" % (
                        _format_bytes(response) if response else "<no data>"
                    )
                )

        if found_baud is None:
            transcript = _write_transcript(lines)
            raise errors.RadioNoResponse(
                "The BQ-889 did not answer a basic AT request at any tested "
                "baud rate. No radio write was attempted. Confirm that the "
                "USB-C cable carries data, select the newly-created COM/tty "
                "port rather than a built-in serial port, close all POC "
                "software, and send the transcript at %s." % transcript
            )

        lines.extend(("", "AT responded at %i baud." % found_baud, ""))
        responses = {}
        for label, command in PROBE_COMMANDS[1:]:
            status = chirp_common.Status()
            status.msg = "Probing BQ-889 %s" % label
            status.cur = len(responses) + 1
            status.max = len(PROBE_COMMANDS) - 1
            self.status_fn(status)
            try:
                response = self._send_read(command)
                responses[command] = response
                lines.append(
                    "TX: %s" % command.decode("ascii")
                )
                lines.append(
                    "RX: %s" % (
                        _format_bytes(response) if response else "<no data>"
                    )
                )
            except Exception as exc:
                responses[command] = b""
                lines.append("TX: %s" % command.decode("ascii"))
                lines.append(
                    "RX error: %s: %s" % (
                        exc.__class__.__name__,
                        exc,
                    )
                )
            lines.append("")

        transcript = _write_transcript(lines)
        answered = [
            command.decode("ascii")
            for command, response in responses.items()
            if response
        ]
        detail = (
            "%i baud. Read commands with data: %s."
            % (
                found_baud,
                ", ".join(answered) if answered else "none",
            )
        )
        channel_response = responses.get(b"AT+HCHDATA=R", b"")
        if channel_response:
            detail += (
                " First channel response bytes: %s."
                % _format_bytes(channel_response)
            )
        raise errors.RadioError(
            "BQ-889 read-only probe completed at %s No radio write was "
            "attempted. Full transcript: %s\n\n"
            "This build does not yet decode or save analog channels. Send "
            "the transcript with a bug report so the response framing and "
            "channel format can be implemented."
            % (detail, transcript)
        )

    def sync_out(self):
        raise errors.RadioError(
            "The Binqi BQ-889 analog driver is read-only. Uploads are "
            "disabled until the AT response framing and channel record "
            "format have been validated on physical hardware."
        )
