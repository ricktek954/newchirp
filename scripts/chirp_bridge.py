#!/usr/bin/env python3
"""Small JSON boundary between NewChirp and the audited CHIRP driver tree."""
import argparse
import builtins
import glob
import importlib.machinery
import importlib.util
import json
import logging
import os
import re
import sys
import tempfile
import time
import urllib.error
import urllib.request
import warnings
PROGRESS_PREFIX = "__NEWCHIRP_PROGRESS__ "
RADIO_TRACE_MARKER = "\n\nRadio communication trace:\n"
_UVK5_HELLO_XOR = bytes.fromhex(
    "16 6c 14 e6 2e 91 0d 40 21 35 d5 40 13 03 e9 80"
)
_FIRMWARE_METADATA_KEYS = (
    "uvk5_firmware",
    "f4hwn_firmware",
    "dm32uv_firmware",
    "tk11_firmware_version",
    "ha1g_firmware",
    "tkx80_ver",
    "firmware",
    "firmware_version",
    "fw_version",
)


def uvk5_firmware_from_hello(reply):
    """Decode the UV-K5 hello reply without trusting non-printable bytes."""
    if (
        not isinstance(reply, (bytes, bytearray))
        or len(reply) < 20
        or bytes(reply[:2]) != b"\xab\xcd"
    ):
        return None
    body_length = int.from_bytes(reply[2:4], "little")
    encoded = bytes(reply[4:4 + body_length])
    if len(encoded) < 12:
        return None
    body = bytes(
        value ^ _UVK5_HELLO_XOR[index % len(_UVK5_HELLO_XOR)]
        for index, value in enumerate(encoded)
    )
    if body[:2] != b"\x15\x05":
        return None
    firmware = body[4:]
    for index, value in enumerate(firmware):
        if value == 0 or value < 0x20 or value > 0x7E:
            firmware = firmware[:index]
            break
    text = firmware.decode("ascii", errors="ignore").strip()
    return text or None


def radio_firmware(radio):
    """Return the best available firmware identity from a radio or image."""
    metadata = getattr(radio, "metadata", None)
    if isinstance(metadata, dict):
        for key in _FIRMWARE_METADATA_KEYS:
            value = metadata.get(key)
            if value is None:
                continue
            if isinstance(value, bytes):
                value = value.decode("ascii", errors="replace")
            elif isinstance(value, int):
                value = "0x%04X" % value
            text = str(value).replace("\x00", "").strip()
            if text:
                return text[:120]

    for name in (
        "_firmware",
        "FIRMWARE_VERSION",
        "F4HWN_FIRMWARE",
    ):
        value = getattr(radio, name, None)
        if value is None:
            continue
        if isinstance(value, bytes):
            value = value.decode("ascii", errors="replace")
        elif isinstance(value, int):
            value = "0x%04X" % value
        text = str(value).replace("\x00", "").strip()
        if text:
            return text[:120]
    return ""
MANUAL_READ_READY_MESSAGE = (
    "Listening for the radio - hold PTT for one second."
)
MANUAL_SEND_READY_MESSAGE = (
    "Radio is ready - press Send on the radio now."
)

# CHIRP normally redirects stdout and stderr to ~/.chirp/debug.log when it is
# launched without a terminal. The bridge owns those streams as its JSON/error
# protocol, so keep them attached to the parent process.
os.environ.setdefault("CHIRP_TESTENV", "1")
warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
    module=r"chirp(\.|$)",
)


ECHO_ONLY_RESULT = "echo of the command only, no radio reply"
ECHO_ONLY_GUIDANCE = (
    "The programming cable sent NewChirp's own command back, but the radio "
    "did not answer. Check that the radio is switched on, the cable is "
    "pushed fully into the radio's programming jack, and the selected "
    "model matches the radio."
)


class RadioCommunicationTrace:
    """Keep a bounded, privacy-safe view of recent serial exchanges."""

    def __init__(self, max_entries=80):
        self.max_entries = max_entries
        self._entries = []
        self._pending = None
        self._protocol = "TYT"

    def set_radio_class(self, radio_class):
        self._protocol = (
            "Icom" if getattr(radio_class, "VENDOR", "") == "Icom" else "TYT"
        )

    def _command_summary(self, data):
        try:
            raw = bytes(data)
        except (TypeError, ValueError):
            return "<invalid serial data>"
        if not raw:
            return "<empty write>"
        if len(raw) >= 5 and raw[:4] == b"\xfe\xfe\xee\xef":
            if self._protocol == "Icom":
                commands = {
                    0xE0: "identify",
                    0xE1: "identify response",
                    0xE2: "clone out/read",
                    0xE3: "clone in/write",
                    0xE4: "clone data",
                    0xE5: "clone end",
                    0xE6: "clone result",
                }
                label = commands.get(raw[4], "command %02x" % raw[4])
                if raw[4] == 0xE4 and len(raw) >= 9:
                    try:
                        decoded = bytes.fromhex(
                            raw[5:-1].decode("ascii")
                        )
                        address = int.from_bytes(decoded[:2], "big")
                        length = decoded[2]
                        label += " addr=0x%04x len=%i" % (address, length)
                    except (UnicodeDecodeError, ValueError, IndexError):
                        pass
                return "Icom %s (%i bytes)" % (label, len(raw))

            commands = {
                0xE0: "handshake",
                0xE2: "enter read",
                0xE3: "enter write",
                0xE4: "write block",
                0xE5: "end session",
                0xE6: "baud switch",
                0xE7: "programming code",
                0xEB: "read block",
            }
            label = commands.get(raw[4], "command %02x" % raw[4])
            if raw[4] in (0xE4, 0xEB) and len(raw) >= 11:
                try:
                    address = int(raw[5:9], 16)
                    length = int(raw[9:11], 16)
                except ValueError:
                    address = int.from_bytes(raw[5:9], "big")
                    length = int.from_bytes(raw[9:11], "big")
                label += " addr=0x%04x len=%i" % (address, length)
            return "TYT %s (%i bytes)" % (label, len(raw))
        if len(raw) >= 6 and raw[:2] == b"\xfe\xfe":
            command = raw[4]
            subcommand = raw[5]
            if command == 0xFA:
                return "CI-V echo probe (%i bytes)" % len(raw)
            label = "CI-V %02x->%02x cmd=%02x" % (
                raw[2],
                raw[3],
                command,
            )
            if subcommand != 0xFD:
                label += "/%02x" % subcommand
            return "%s (%i bytes)" % (label, len(raw))
        if len(raw) >= 4 and raw[:4] == b"\xab\xcd\x08\x00":
            return "UV-K5 hello"
        # Block reads/writes such as R <addr> <addr> <len> are short; show
        # their bytes so a report names the address where a radio stopped
        # (2026-11-21 UV-5R Mini report: 75 blocks read, then silence, at
        # an unknown address). Longer frames stay hidden: they can carry
        # radio passwords.
        if len(raw) == 4 and raw[:1] in (b"R", b"W", b"S") and not (
            raw.rstrip(b"\r\n").isalpha()
        ):
            return self._binary_label(raw)
        try:
            text = raw.decode("cp1252").strip("\r\n")
        except UnicodeDecodeError:
            return self._binary_label(raw)
        body = text.split(";", 1)[0].strip()
        if not body or not all(32 <= ord(char) < 127 for char in body):
            return self._binary_label(raw)
        upper = body.upper()
        memory = re.match(r"^(M[WRA])\s*([01]?),?(\d{3})", upper)
        if memory:
            return "%s memory=%s" % (memory.group(1), memory.group(3))
        token = re.match(r"^[A-Z~]+", upper)
        command = token.group(0) if token else ""
        alinco_block = re.match(r"^AL~(EEP[ED]L)([0-9A-F]{4})([RW])", upper)
        if alinco_block:
            # The hex address can start with a letter (C000), so label it
            # explicitly instead of taking the leading letters.
            return "AL~%s %s %s" % alinco_block.groups()
        if command.startswith("AL~EEP"):
            return command[:8]
        return command[:12] or "<text command>"

    @staticmethod
    def _binary_label(raw):
        if len(raw) <= 4:
            return "<binary command, %i bytes: %s>" % (len(raw), raw.hex(" "))
        return "<binary command, %i bytes>" % len(raw)

    def begin(self, data):
        self._finish_pending()
        try:
            raw = bytes(data)
        except (TypeError, ValueError):
            raw = b""
        self._pending = {
            "command": self._command_summary(data),
            "started": time.monotonic(),
            "response": bytearray(),
            "alinco": raw if raw.startswith(b"AL~") else None,
            "raw": raw,
        }

    def received(self, data):
        if self._pending is None or not data:
            return
        self._pending["response"].extend(data)
        alinco = self._pending["alinco"]
        if alinco is not None:
            # The single-wire Alinco ERW-7 echoes each command before the
            # radio's reply line, so the echo alone is not a response.
            response = bytes(self._pending["response"])
            lines = response.count(b"\r\n")
            if lines >= 2 or (lines == 1 and not response.startswith(alinco)):
                self._finish_pending()
            return
        if any(delimiter in data for delimiter in (b";", b"\r", b"\n")):
            self._finish_pending()

    @staticmethod
    def _alinco_result(command_bytes, command, response):
        echo = command_bytes.rstrip(b"\r\n")
        if not response:
            return "no response (no cable echo)"
        if response.startswith(echo + b"\r\n"):
            rest = response[len(echo) + 2:]
            if not rest:
                return "cable echo only; radio did not answer"
        else:
            rest = response
        reply, separator, _ = rest.partition(b"\r\n")
        if not separator:
            return "incomplete reply (%i bytes after echo)" % len(rest)
        text = reply.decode("ascii", errors="replace")
        if command == "AL~WHO":
            return "radio id=%s" % text[:20]
        if text == "OK":
            return "OK"
        if re.fullmatch(r"[0-9A-Fa-f]{128}", text):
            return "block (64 bytes)"
        return "reply=%s" % text[:40]

    def _finish_pending(self):
        pending = self._pending
        if pending is None:
            return
        self._pending = None
        response = bytes(pending["response"])
        raw = pending.get("raw") or b""
        if pending.get("alinco") is not None:
            result = self._alinco_result(
                pending["alinco"], pending["command"], response,
            )
        elif (
            len(raw) >= 2
            and response == raw
            and any(not 32 <= byte < 127 for byte in raw.rstrip(b"\r\n"))
        ):
            # Only our own binary command came back: a cable that echoes,
            # with no radio answering behind it (2026-11-21 KT7900D report:
            # the 8-byte magic returned 8 bytes, read as "Bad ack"). Text
            # commands are excluded: some radios answer "ID" with "ID".
            result = "%s (%i bytes)" % (ECHO_ONLY_RESULT, len(response))
        elif pending["command"] == "ID":
            text = response.decode("ascii", errors="replace").strip()
            identifier = re.search(
                r"ID\s*([A-Z0-9_-]+)",
                text.upper(),
            )
            if identifier:
                result = "radio id=%s" % identifier.group(1)
            elif text and all(32 <= ord(char) < 127 for char in text):
                result = "reply=%s" % text[:40]
            elif response:
                result = "reply=%s (%i bytes)" % (
                    response[:20].hex(" "),
                    len(response),
                )
            else:
                result = "no response"
        elif pending["command"] == "UV-K5 hello":
            preview = response[:32].hex(" ")
            if len(response) > 32:
                preview += " …"
            firmware = uvk5_firmware_from_hello(response)
            result = (
                "firmware=%s | reply=%s (%i bytes)"
                % (firmware, preview, len(response))
                if firmware
                else "reply=%s (%i bytes)" % (preview, len(response))
            )
        elif response.strip() in (
            b"N;",
            b"?;",
            b"N\r",
            b"?\r",
            b"N\n",
            b"?\n",
        ):
            result = "radio refused"
        elif any(delimiter in response for delimiter in (b";", b"\r", b"\n")):
            result = "response complete"
        elif response:
            if pending["command"] in (
                "PSEARCH",
                "PASSSTA",
                "SYSINFO",
                "PROGRAM",
            ) or pending["command"].startswith("PROGRAM"):
                preview = response[:32].hex(" ")
                if len(response) > 32:
                    preview += " …"
                result = "reply=%s (%i bytes)" % (preview, len(response))
            elif (
                pending["command"].startswith("<binary command")
                and len(response) <= 16
            ):
                # Short binary replies are usually identification strings.
                # Showing them lets a report name an unknown model ID
                # (2026-11-21 RT22 report: 8-byte ID rejected, bytes unseen).
                result = "reply=%s (%i bytes)" % (
                    response.hex(" "),
                    len(response),
                )
            else:
                result = "incomplete response (%i bytes)" % len(response)
        else:
            result = "no response"
        self._entries.append({
            "command": pending["command"],
            "result": result,
            "elapsed": max(0.0, time.monotonic() - pending["started"]),
        })
        if len(self._entries) > self.max_entries:
            del self._entries[: len(self._entries) - self.max_entries]

    def last_reply_was_echo_only(self):
        """True when the last exchange returned only the command's echo."""
        self._finish_pending()
        return bool(self._entries) and self._entries[-1]["result"].startswith(
            ECHO_ONLY_RESULT
        )

    def format(self):
        self._finish_pending()
        if not self._entries:
            return ""
        first = max(0, len(self._entries) - 30)
        lines = []
        for index, entry in enumerate(self._entries[first:], start=first + 1):
            lines.append(
                "%i. %s | %s | %.2fs"
                % (
                    index,
                    entry["command"],
                    entry["result"],
                    entry["elapsed"],
                )
            )
        return "\n".join(lines)


RADIO_TRACE = RadioCommunicationTrace()


class TracedSerial:
    """Delegate a serial port while recording sanitized CAT transactions."""

    def __init__(self, serial_port, trace):
        object.__setattr__(self, "_serial_port", serial_port)
        object.__setattr__(self, "_trace", trace)

    def __getattr__(self, name):
        return getattr(self._serial_port, name)

    def __setattr__(self, name, value):
        if name in ("_serial_port", "_trace"):
            object.__setattr__(self, name, value)
        else:
            setattr(self._serial_port, name, value)

    def write(self, data):
        self._trace.begin(data)
        return self._serial_port.write(data)

    def read(self, size=1):
        data = self._serial_port.read(size)
        self._trace.received(data)
        return data

    def readline(self, size=-1):
        data = self._serial_port.readline(size)
        self._trace.received(data)
        return data

    def readlines(self, hint=-1):
        lines = self._serial_port.readlines(hint)
        self._trace.received(b"".join(lines))
        return lines

    def close(self):
        return self._serial_port.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


def emit_progress(label, fraction=None):
    """Send structured transfer progress without touching the JSON stdout."""
    message = str(label).replace("\r", " ").replace("\n", " ").strip()
    payload = {"label": message or "Working..."}
    if fraction is not None:
        try:
            payload["fraction"] = max(0.0, min(1.0, float(fraction)))
        except (TypeError, ValueError):
            pass
    sys.stderr.write(
        PROGRESS_PREFIX + json.dumps(payload, separators=(",", ":")) + "\n"
    )
    sys.stderr.flush()


def bridge_error_message(exc, command=None, model=None, port=None):
    """Add safe, command-specific recovery guidance to bridge failures."""
    message = str(exc).strip() or exc.__class__.__name__
    if re.fullmatch(r"-?\d+|'[^']*'|\"[^\"]*\"", message):
        # KeyError(1) and similar print only their argument ("1"), which
        # tells the reporter and the maintainer nothing.
        message = "%s: %s" % (exc.__class__.__name__, message)
    lowered_message = message.lower()
    if (
        "cannot configure port" in lowered_message
        or "a device attached to the system is not functioning"
        in lowered_message
    ):
        port_match = re.search(r"port '([^']+)'", message)
        port = port_match.group(1) if port_match else (
            port or "the selected serial port"
        )
        if sys.platform.startswith("linux") or sys.platform == "darwin":
            message = (
                "Could not configure %s. Unplug and replug the programming "
                "cable, reseat the radio plug, and try a different USB port "
                "before retrying." % port
            )
        else:
            message = (
                "Windows could not configure %s because the USB-serial driver "
                "reported a device failure (Windows error 31). Unplug and "
                "replug the cable, use a USB port on the computer itself "
                "rather than a hub, and reseat the radio programming plug. "
                "If the error continues, reinstall the adapter's CH340, "
                "CP210x, or FTDI driver or try a different cable." % port
            )
    elif (
        "permissionerror(13" in lowered_message
        or "access is denied" in lowered_message
        or "permission denied" in lowered_message
    ):
        port_match = re.search(r"port '([^']+)'", message)
        port = port_match.group(1) if port_match else "the selected serial port"
        if sys.platform.startswith("linux"):
            message = (
                "Linux could not open %s because the port is denied or "
                "already in use. Close CHIRP, terminal software, ModemManager, "
                "and any vendor programmer before retrying. If this is a "
                "permissions error, add your user to the dialout group with "
                "`sudo usermod -aG dialout $USER`, then log out and back in "
                "before reconnecting the cable."
                % port
            )
        elif sys.platform == "darwin":
            message = (
                "macOS could not open %s because the port is denied or "
                "already in use. Close CHIRP, terminal software, and any "
                "vendor programmer before retrying. If the error continues, "
                "unplug and reconnect the USB cable, refresh the interface "
                "list, and select the serial device that appears for the "
                "programming cable."
                % port
            )
        else:
            message = (
                "Windows could not open %s because another program or driver "
                "has it reserved. Close Baofeng CPS, CHIRP, terminal software, "
                "and any vendor programmer before retrying. If the error "
                "continues, unplug and reconnect the USB cable, refresh the "
                "interface list, and select the COM port that appears for the "
                "programming cable. Do not rely on an old saved port such as "
                "COM100 if it did not newly appear when the cable was connected."
                % port
            )
    elif (
        "filenotfounderror" in lowered_message
        or "could not open port" in lowered_message
    ):
        port_match = re.search(r"port '([^']+)'", message)
        port = port_match.group(1) if port_match else (
            port or "the selected serial port"
        )
        if sys.platform.startswith("linux"):
            message = (
                "Linux could not open %s because no serial device exists at "
                "that path. Reconnect the programming cable, then refresh the "
                "interface list; USB adapters can reappear under a different "
                "ttyUSB name after being unplugged." % port
            )
        elif sys.platform == "darwin":
            message = (
                "macOS could not open %s because no serial device exists at "
                "that path. Reconnect the programming cable, then refresh the "
                "interface list; the adapter can reappear under a different "
                "/dev/cu.usbmodem name after being unplugged." % port
            )
        else:
            message = (
                "Windows could not open %s because that port is not "
                "available. The cable may be unplugged or using a different "
                "COM port, a USB-serial driver may not be loaded, or the "
                "saved entry may be stale. Unplug and reconnect the cable, "
                "check Device Manager to confirm the COM port appears "
                "without a warning icon, then refresh the interface list "
                "and select that port." % port
            )
    if (
        command in ("download", "read-settings")
        and model == "Yaesu_FT-60"
        and "no response from radio" in message.lower()
    ):
        message = (
            "No response from the FT-60. Leave the radio on its F8 CLONE "
            "screen, read again, and hold PTT only after the transfer window "
            'says "%s"' % MANUAL_READ_READY_MESSAGE
        )
    if (
        command == "download"
        and model == "Yaesu_FT5D_R"
        and "no response from radio" in message.lower()
    ):
        message = (
            "No response from the Yaesu radio. Turn the radio off, connect "
            "the cable to its DATA terminal, then hold [F MENU] while "
            "switching it on so CLONE appears. Start the read again and "
            "press Send on the radio when NewChirp says \"%s\" If it is "
            "already in CLONE mode, select the COM port created by the "
            "Yaesu USB cable and close Yaesu ADMS. COM1 may be a built-in "
            "serial port rather than the programming cable."
            % MANUAL_SEND_READY_MESSAGE
        )
    elif (
        command == "download"
        and model in (
            "Yaesu_FT2D_R",
            "Yaesu_FT2D_Rv2",
            "Yaesu_FT3D_R",
        )
        and "no response from radio" in message.lower()
    ):
        message = (
            "No response from the Yaesu radio. Turn the radio off, connect "
            "the cable to its DATA terminal, then hold DISP while switching "
            "it on so CLONE appears. Start the read again and press Send on "
            "the radio when NewChirp says \"%s\" If it is already in "
            "CLONE mode, select the COM port created by the Yaesu USB cable "
            "and close Yaesu ADMS. COM1 may be a built-in serial port rather "
            "than the programming cable."
            % MANUAL_SEND_READY_MESSAGE
        )
    if (
        command in ("download", "read-settings")
        and model == "AOR_AR8200"
        and "no response from radio" in message.lower()
    ):
        selected_port = str(port or "the selected COM port")
        message = (
            "No response from the AR8200. Use an AOR CC8200-compatible "
            "RS-232 lead fully inserted in the option socket, not a TTL "
            "handheld-radio programming cable. In the radio's CONFIG menu, "
            "set REMOTE BPS to 19200, 9600, or 4800 and set RMT-ID to 00; "
            "NewChirp scans all three baud rates, but nonzero RMT-ID prevents "
            "normal single-radio commands. If command text is merely echoed "
            "back, the radio or adapter is not processing remote commands. "
            "Close other software using %s, power-cycle the radio, and retry."
            % selected_port
        )
    if (
        command in ("download", "read-settings")
        and model == "Retevis_RT1"
        and "no response from radio" in message.lower()
    ):
        message = (
            "No response from the RT1. Confirm that the exact model is "
            "Retevis RT1 and not Retevis RT21: these are different radios "
            "with different protocols. If the label says RT-21, go back and "
            "select Retevis RT21 instead. The RT1 uses 2400 baud and a "
            "PROGRAMa handshake; the RT21 uses 9600 baud and a PRMZUNE "
            "handshake. Close any existing programming software before "
            "retrying."
        )
    if (
        command == "download"
        and model == "Baofeng_BF-F8HP-PRO"
        and "no response from radio" in message.lower()
    ):
        selected_port = str(port or "the selected COM port")
        message = (
            "No response from the BF-F8HP-PRO. Confirm that the radio label "
            "includes PRO. The older BF-F8HP is a different model and uses "
            "the separate Baofeng BF-F8HP entry. For the PRO, fully insert "
            "the two-pin programming cable, turn the radio on to a normal "
            "channel, close the Baofeng CPS, and keep %s selected. "
            "If the Baofeng CPS can read the radio, compare its COM port and "
            "programming-cable driver with NewChirp. NewChirp currently "
            "supports the PRO protocol through firmware v0.52; include the "
            "firmware version shown on the radio in the support report."
            % selected_port
        )
    if (
        command == "download"
        and model == "Baofeng_UV-5R_Mini"
        and "no response from radio" in message.lower()
    ):
        message = (
            "No response from the UV-5R Mini. Confirm the selected port is "
            "the USB programming cable, not a built-in COM1 port: unplug the "
            "cable, refresh interfaces, reconnect it, and select the COM port "
            "that newly appears. Fully insert the two-pin cable, turn the "
            "radio on to a normal channel, and close Baofeng CPS. If using "
            "the radio through a Bluetooth serial port, select that Bluetooth "
            "port instead of COM1. If COM3 disappears and reappears when the "
            "cable is unplugged and reconnected, test the cable once with "
            "Baofeng CPS. If the stock software also cannot read the radio, "
            "replace the cable or install its CH340, CP210x, or FTDI driver. "
            "If the stock software succeeds, report the cable model, COM-port "
            "device name, and driver provider."
        )
    if (
        command in ("download", "read-settings")
        and model == "Baofeng_UV-5RH"
        and "no response from radio" in message.lower()
    ):
        selected_port = str(port or "the selected COM port")
        message = (
            "The radio did not answer the legacy UV-5RH handshake on %s. "
            "If the label says 5RH Pro, UV-5RH Pro, or UV-5RH Plus, go back "
            "and select the matching v2 model. Those radios use a different "
            "encrypted clone protocol and are tested on firmware v2_0_09. "
            "Close the Baofeng CPS before retrying."
            % selected_port
        )
    if (
        command in ("download", "read-settings")
        and model == "Wouxun_KG-UVD1P"
        and (
            "failed to read full block" in lowered_message
            or "no response from radio" in lowered_message
        )
    ):
        message = (
            "The Wouxun KG-UV2D uses the KG-UVD1P radio entry. Fully insert "
            "the programming cable, close Wouxun CPS or any other program "
            "using the COM port, and power the radio off and on before "
            "retrying. A failed clone can leave this radio family in "
            "programming mode and unresponsive. If Windows assigns a new COM "
            "port after reconnecting the cable, refresh the interface list "
            "and select that new port. If it still fails, report whether the "
            "original Wouxun CPS can read the same radio."
        )
    if (
        command == "read-settings"
        and model == "Icom_IC-2730A"
        and (
            "end-of-clone" in lowered_message
            or "clone_end" in lowered_message
            or "data stream stopped" in lowered_message
        )
    ):
        message = (
            "The IC-2730A stopped before completing the clone connection. "
            "After writing channels, turn the radio off and back on to leave "
            "clone mode, then reconnect the cable to the Speaker-2 jack and "
            "try Read settings again. You can also use Load from stored image "
            "to view the settings saved from the completed channel write."
        )
    if (
        command in ("download", "read-settings")
        and model in ("Kenwood_TK-350", "Kenwood_TK-359")
        and (
            "reading the radio identity" in lowered_message
            or "no response from radio" in lowered_message
        )
    ):
        selected_port = str(port or "the selected COM port")
        radio_name = model.split("_", 1)[1]
        cps = "KPG-32D" if model == "Kenwood_TK-359" else "KPG-23D"
        if model == "Kenwood_TK-359":
            # KPG-32D manual, "Connecting the equipment", step 7.
            pc_mode = (
                "put the radio in PC mode: switch it off, connect the cable, "
                "hold [LMP] and [CALL] while switching it on, and wait until "
                "\"-PC-\" appears"
            )
        else:
            # The KPG-23D files document no PC-mode key combination; the
            # radio enters PC mode when a read starts from normal power-on.
            pc_mode = (
                "switch the radio on normally with the cable connected, "
                "without holding any keys"
            )
        message = (
            "The %s did not answer its identity request on %s. Use a "
            "KPG-8 or KPG-22 compatible programming cable, close %s, CHIRP, "
            "and any terminal program, then %s. If the display shows "
            "\"PROG\" (flashing), the radio is in firmware-loading mode and "
            "will not answer programming software: switch it off and start "
            "again. Then select the COM port created by the cable and read "
            "again. If the OEM %s software can read the radio with the same "
            "cable and port, report that result with the cable model."
            % (radio_name, selected_port, cps, pc_mode, cps)
        )
    if (
        command == "download"
        and model
        and message.strip().lower() == "no response from radio"
    ):
        key = manual_send_key_for_model(model)
        if key and key.lower() != "[send]":
            message = (
                "No response from the radio. Leave it in CLONE mode, start "
                "the read again, and press %s on the radio only after "
                "NewChirp says \"%s\" A key pressed earlier sends the image "
                "before NewChirp is listening, and the radio then waits. If "
                "it still fails, select the COM port created by the "
                "programming cable." % (key, manual_send_ready_message(key))
            )
    if RADIO_TRACE.last_reply_was_echo_only():
        message = "%s\n\n%s" % (ECHO_ONLY_GUIDANCE, message)
    trace = RADIO_TRACE.format()
    if trace:
        message += RADIO_TRACE_MARKER + trace
    return message


def manual_send_key_for_model(model):
    """The send key from a registered driver's read prompt, if loaded."""
    try:
        from chirp import directory

        radio_class = directory.get_radio(model)
        pre_download = radio_class.get_prompts().pre_download or ""
    except Exception:
        return None
    if "[PTT]" in pre_download:
        return None
    return manual_send_key(pre_download)


def status_progress(status, start=0.0, end=1.0):
    """Translate a CHIRP Status message into a structured progress event."""
    label = getattr(status, "msg", None) or str(status)
    raw = None
    current = getattr(status, "cur", None)
    maximum = getattr(status, "max", None)
    if isinstance(current, (int, float)) and isinstance(maximum, (int, float)):
        if maximum > 0:
            raw = float(current) / float(maximum)
    if raw is None:
        match = re.search(r"(\d+(?:\.\d+)?)\s*%", str(status))
        if match:
            raw = float(match.group(1)) / 100.0
    if raw is None:
        emit_progress(label)
    else:
        raw = max(0.0, min(1.0, raw))
        emit_progress(label, start + (end - start) * raw)


def _load_module(module_path, directory):
    if not os.path.isfile(module_path):
        raise RuntimeError(
            "CHIRP module file was not found: %s" % module_path
        )
    directory.enable_reregistrations()
    module_name = "newchirp.loaded.%s" % os.path.splitext(
        os.path.basename(module_path)
    )[0]
    loader = importlib.machinery.SourceFileLoader(module_name, module_path)
    spec = importlib.util.spec_from_file_location(
        module_name, module_path, loader=loader
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Invalid or unsupported CHIRP module file")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    old_log_level = directory.LOG.level
    directory.LOG.setLevel(logging.ERROR)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:
        sys.modules.pop(module_name, None)
        if isinstance(exc, ModuleNotFoundError) and exc.name == "wx":
            try:
                with open(module_path, encoding="utf-8",
                          errors="replace") as handle:
                    is_f4hwn = "F4HWN" in handle.read()
            except OSError:
                is_f4hwn = False
            if is_f4hwn:
                # F4HWN's module needs wx; NewChirp has the same v6.3 map
                # built in and opens that module's saved images.
                raise RuntimeError(
                    "Could not load %s: F4HWN's CHIRP module needs the wx "
                    "GUI toolkit, which NewChirp does not include. You do "
                    "not need it: choose the built-in \"Quansheng UV-K1 "
                    "(F4HWN 6.3)\" radio to read the radio, or open an image "
                    "saved by F4HWN's module directly."
                    % os.path.basename(module_path)
                ) from exc
            raise RuntimeError(
                "Could not load CHIRP module %s: this module depends on the "
                "wx GUI toolkit, which is not available in NewChirp's "
                "headless driver runtime. Ask the module author for a "
                "driver-only version, or use the built-in radio driver."
                % os.path.basename(module_path)
            ) from exc
        raise RuntimeError(
            "Could not load CHIRP module %s: %s"
            % (os.path.basename(module_path), exc)
        ) from exc
    finally:
        directory.LOG.setLevel(old_log_level)


def _allow_driver_specific_modes():
    """Permit declared radio modes rejected by CHIRP's shared memory map."""
    from chirp import chirp_common

    valid = tuple(chirp_common.Memory._valid_map["mode"])
    extra = tuple(mode for mode in ("DR", "R-CW") if mode not in valid)
    if extra:
        chirp_common.Memory._valid_map["mode"] = valid + extra


def load_chirp(
    source, vendor, newchirp_driver_dir=None, module_path=None
):
    # pyserial is shipped as a pure-Python wheel inside NewChirp. Python can
    # import it directly without pip or a user-level installation.
    sys.path.insert(0, vendor)
    sys.path.insert(0, source)
    # Driver prompt/error strings use CHIRP's process-wide translation hook.
    # The headless bridge keeps the original English strings.
    builtins._ = lambda message: message
    try:
        import serial  # noqa: F401
    except ImportError as exc:
        raise RuntimeError(
            "NewChirp's bundled serial backend could not be loaded. "
            "Reinstall NewChirp so its support files are restored."
        ) from exc
    from chirp import directory

    # Some packaged builds install NewChirp overrides beside CHIRP's own
    # drivers. Reregistration must therefore be enabled before the initial
    # directory scan, or an override such as TIDRADIO_TD-H3 collides with the
    # upstream class while it is being imported.
    old_log_level = directory.LOG.level
    directory.LOG.setLevel(logging.ERROR)
    try:
        directory.enable_reregistrations()
        directory.import_drivers()
        _allow_driver_specific_modes()
    finally:
        directory.LOG.setLevel(old_log_level)
    # chirp.drivers resets DeprecationWarning handling while it imports, so
    # apply NewChirp's filter again before loading overrides or image data.
    warnings.filterwarnings(
        "ignore",
        category=DeprecationWarning,
        module=r"chirp(\.|$)",
    )
    if module_path:
        _load_module(os.path.abspath(module_path), directory)
    if newchirp_driver_dir and os.path.isdir(newchirp_driver_dir):
        # NewChirp drivers may intentionally replace a bundled CHIRP driver
        # while preserving its stable model identifier.
        installed_driver_dir = os.path.realpath(
            os.path.join(source, "chirp", "drivers")
        )
        requested_driver_dir = os.path.realpath(newchirp_driver_dir)
        if requested_driver_dir == installed_driver_dir:
            # The initial directory scan already loaded the overrides.
            return directory
        old_log_level = directory.LOG.level
        directory.LOG.setLevel(logging.ERROR)
        try:
            for driver_path in sorted(
                glob.glob(os.path.join(newchirp_driver_dir, "*.py"))
            ):
                module_name = os.path.splitext(
                    os.path.basename(driver_path)
                )[0]
                if module_name.startswith("_"):
                    continue
                full_name = "newchirp.drivers.%s" % module_name
                spec = importlib.util.spec_from_file_location(
                    full_name, driver_path
                )
                if spec is None or spec.loader is None:
                    raise RuntimeError(
                        "Could not load NewChirp driver %s" % driver_path
                    )
                module = importlib.util.module_from_spec(spec)
                sys.modules[full_name] = module
                spec.loader.exec_module(module)
        finally:
            directory.LOG.setLevel(old_log_level)
    return directory


def live_models_by_vendor(directory):
    """Return selectable serial/transport radios, excluding file-only models."""
    from chirp import chirp_common

    models_by_vendor = {}
    for identifier, radio_class in directory.DRV_TO_RADIO.items():
        if (
            issubclass(radio_class, chirp_common.FileBackedRadio)
            and not issubclass(radio_class, chirp_common.CloneModeRadio)
        ):
            continue
        models_by_vendor.setdefault(
            str(radio_class.VENDOR), []
        ).append(identifier)
    return models_by_vendor


def memory_json(mem):
    return {
        "location": mem.number,
        "name": mem.name,
        "frequency": mem.freq / 1_000_000,
        "duplex": mem.duplex,
        "offset": mem.offset / 1_000_000,
        "tone": mem.tmode,
        "txTone": mem.rtone,
        "rxTone": mem.ctone,
        "dtcs": mem.dtcs,
        "dtcsPolarity": mem.dtcs_polarity,
        "rxDtcs": mem.rx_dtcs,
        "crossMode": mem.cross_mode,
        "mode": mem.mode,
        "step": mem.tuning_step,
        "skip": mem.skip,
        "power": str(mem.power or ""),
        "comment": mem.comment,
        "extras": extra_fields_json(mem),
    }


def external_memory_owner(radio):
    """Return the object that owns metadata for a radio or channel subdevice."""
    from chirp import chirp_common

    if not isinstance(radio, chirp_common.ExternalMemoryProperties):
        return None
    if hasattr(radio, "_metadata"):
        return radio
    parent = getattr(radio, "_parent", None)
    if (
        isinstance(parent, chirp_common.ExternalMemoryProperties)
        and hasattr(parent, "_metadata")
    ):
        return parent
    return None


def memory_with_extras(radio, number):
    """Load a channel plus CHIRP's metadata-backed fields such as comments."""
    memory = radio.get_memory(number)
    owner = external_memory_owner(radio)
    if owner is not None:
        memory = owner.get_memory_extra(memory)
    return memory


def repair_uninitialized_extras(memory):
    """Give extras that failed to load a valid default before writing.

    A slot written by other software can hold a byte outside a driver's
    option table (for example Baofeng 5RM PTT-ID 0xFF). CHIRP then logs
    "Failed to load ... out of range", leaves the value unset, and the
    driver's set_memory fails with "x not in list", blocking the whole
    upload. The stored byte was invalid, so the first valid option is the
    safe replacement. Returns the names of repaired settings.
    """
    from chirp.settings import (
        RadioSetting,
        RadioSettingValueBoolean,
        RadioSettingValueFloat,
        RadioSettingValueInteger,
        RadioSettingValueList,
        RadioSettingValueString,
    )

    repaired = []
    extra = getattr(memory, "extra", None)
    if not extra:
        return repaired
    for setting in extra.walk() if hasattr(extra, "walk") else extra:
        if not isinstance(setting, RadioSetting):
            continue
        for value in setting.values():
            if value.initialized:
                continue
            try:
                if isinstance(value, RadioSettingValueList):
                    value.set_value(value.get_options()[0])
                elif isinstance(value, RadioSettingValueBoolean):
                    value.set_value(False)
                elif isinstance(value, (RadioSettingValueInteger,
                                        RadioSettingValueFloat)):
                    value.set_value(value.get_min())
                elif isinstance(value, RadioSettingValueString):
                    value.set_value("")
                else:
                    continue
            except Exception:
                continue
            repaired.append(setting.get_name())
    if repaired:
        logging.getLogger("newchirp.bridge").warning(
            "Channel %s: reset invalid stored value(s) for %s",
            getattr(memory, "number", "?"),
            ", ".join(repaired),
        )
    return repaired


def set_memory_with_extras(radio, memory):
    """Write a channel and persist fields CHIRP stores outside radio memory."""
    repair_uninitialized_extras(memory)
    radio.set_memory(memory)
    owner = external_memory_owner(radio)
    if owner is not None:
        owner.set_memory_extra(memory)


def erase_memory_with_extras(radio, number):
    """Erase a channel and remove its metadata-backed fields."""
    radio.erase_memory(number)
    owner = external_memory_owner(radio)
    if owner is not None:
        owner.erase_memory_extra(number)


def extra_fields_json(mem):
    from chirp.settings import (
        RadioSettingValueBoolean,
        RadioSettingValueFloat,
        RadioSettingValueInteger,
        RadioSettingValueList,
    )

    fields = []
    for setting in mem.extra:
        value = setting.value
        if not value.initialized:
            try:
                value.initialize()
            except Exception:
                pass
        current = value.get_value()
        choices = []
        if current is None:
            kind = "unsupported"
            current = None
            is_mutable = False
        elif isinstance(value, RadioSettingValueBoolean):
            kind = "boolean"
            current = bool(current)
            is_mutable = value.get_mutable()
        elif isinstance(value, RadioSettingValueList):
            kind = "choice"
            choices = [str(option) for option in value.get_options()]
            current = str(current)
            is_mutable = value.get_mutable()
        elif isinstance(value, RadioSettingValueInteger):
            kind = "integer"
            current = int(current)
            is_mutable = value.get_mutable()
        elif isinstance(value, RadioSettingValueFloat):
            kind = "number"
            current = float(current)
            is_mutable = value.get_mutable()
        else:
            kind = "string"
            current = str(current).rstrip()
            is_mutable = value.get_mutable()
        fields.append({
            "name": setting.get_name(),
            "label": setting.get_shortname(),
            "documentation": extra_field_doc(setting),
            "kind": kind,
            "value": current,
            "choices": choices,
            "mutable": is_mutable,
        })
    return fields


_EXTRA_FIELD_DOCS = {
    "bcl": (
        "Busy Channel Lockout. Prevents transmitting when the channel is "
        "already in use; the radio sounds an alert instead of transmitting."
    ),
    "bclo": (
        "Busy Channel Lockout. Prevents transmitting when the channel is "
        "already in use; the radio sounds an alert instead of transmitting."
    ),
    "pttid": (
        "PTT ID. Controls when the radio sends its programmed station ID: "
        "at the beginning (BOT), end (EOT), both, or not at all."
    ),
    "pttidcode": (
        "PTT ID Code. Selects which programmed station-identification code "
        "this channel transmits."
    ),
    "scode": (
        "S-CODE. Selects which stored signaling or PTT-ID code this channel "
        "uses. The code text is configured in the radio's signaling settings."
    ),
    "rxdtmf": (
        "RX DTMF. Controls whether incoming DTMF signaling is decoded on "
        "this channel."
    ),
    "fhss": (
        "Frequency-hopping spread spectrum. Changes frequency rapidly to "
        "reduce interference; only supported by compatible radios."
    ),
    "scramble": (
        "Voice inversion scrambling. Obscures analog voice; another compatible "
        "radio or scanner must use the same scramble setting."
    ),
    "compander": (
        "Compander. Compresses loud audio before transmission and expands it "
        "on receive to reduce level differences."
    ),
    "talkaround": (
        "Talkaround. Transmits on the receive frequency, bypassing the "
        "repeater input offset."
    ),
}


def extra_field_doc(setting):
    """Return CHIRP's documentation or a concise fallback for common terms."""
    documentation = setting_doc(setting)
    if documentation:
        return documentation
    for value in (setting.get_shortname(), setting.get_name()):
        key = re.sub(r"[^a-z0-9]+", "", str(value).lower())
        if key in _EXTRA_FIELD_DOCS:
            return _EXTRA_FIELD_DOCS[key]
    return None


def features_json(radio):
    features = radio.get_features()
    memory_start, memory_end = features.memory_bounds
    return {
        "duplexes": list(features.valid_duplexes),
        "toneModes": list(features.valid_tmodes),
        "crossModes": list(features.valid_cross_modes),
        "modes": list(features.valid_modes),
        "steps": list(features.valid_tuning_steps),
        "skips": list(features.valid_skips),
        "powers": [str(level) for level in features.valid_power_levels],
        "tones": list(features.valid_tones),
        "dtcsCodes": list(features.valid_dtcs_codes),
        "memoryStart": memory_start,
        "memoryEnd": memory_end,
        "nameLength": features.valid_name_length,
        "validCharacters": features.valid_characters,
        "validBands": [
            {
                "startMhz": start / 1_000_000,
                "endMhz": end / 1_000_000,
            }
            for start, end in features.valid_bands
        ],
        "hasTuningStep": features.has_tuning_step,
        "hasNostepTuning": features.has_nostep_tuning,
    }


def setting_doc(element):
    doc = getattr(element, "__doc__", None)
    if not isinstance(doc, str):
        return None
    doc = doc.strip()
    if not doc or doc == element.get_name():
        return None
    return doc


def setting_value_json(setting):
    from chirp.settings import (
        RadioSettingValueBoolean,
        RadioSettingValueFloat,
        RadioSettingValueInteger,
        RadioSettingValueList,
        RadioSettingValueString,
    )

    value = setting.value
    if not value.initialized:
        try:
            value.initialize()
        except Exception:
            pass
    current = value.get_value()
    options = []
    minimum = None
    maximum = None
    step = None
    min_length = None
    max_length = None
    if current is None:
        kind = "unsupported"
        current = None
        mutable = False
    elif isinstance(value, RadioSettingValueBoolean):
        kind = "boolean"
        current = bool(current)
        mutable = value.get_mutable()
    elif isinstance(value, RadioSettingValueList):
        kind = "choice"
        options = [str(option) for option in value.get_options()]
        current = str(current)
        mutable = value.get_mutable()
    elif isinstance(value, RadioSettingValueInteger):
        kind = "integer"
        current = int(current)
        minimum = int(value.get_min())
        maximum = int(value.get_max())
        step = int(value.get_step())
        mutable = value.get_mutable()
    elif isinstance(value, RadioSettingValueFloat):
        kind = "number"
        current = float(current)
        minimum_value = value.get_min()
        maximum_value = value.get_max()
        if maximum_value is None:
            maximum_value = getattr(value, "_max", None)
        if minimum_value is not None:
            minimum = float(minimum_value)
        if maximum_value is not None:
            maximum = float(maximum_value)
        mutable = value.get_mutable()
    else:
        kind = "string"
        current = str(current).rstrip()
        if isinstance(value, RadioSettingValueString):
            min_length = int(value.minlength)
            max_length = int(value.maxlength)
        mutable = value.get_mutable()
    return {
        "kind": kind,
        "value": current,
        "options": options,
        "mutable": bool(mutable),
        "min": minimum,
        "max": maximum,
        "step": step,
        "minLength": min_length,
        "maxLength": max_length,
    }


def settings_tree_json(elements, prefix=()):
    from chirp.settings import RadioSetting, RadioSettingGroup

    result = []
    for index, element in enumerate(elements):
        path = list(prefix + (index,))
        base = {
            "id": path,
            "name": element.get_name(),
            "shortName": element.get_shortname(),
            "documentation": setting_doc(element),
        }
        if isinstance(element, RadioSetting):
            if len(element) != 1:
                result.append({
                    **base,
                    "kind": "unsupported",
                    "value": None,
                    "options": [],
                    "mutable": False,
                    "min": None,
                    "max": None,
                    "step": None,
                    "minLength": None,
                    "maxLength": None,
                })
                continue
            result.append({**base, **setting_value_json(element)})
        elif isinstance(element, RadioSettingGroup):
            result.append({
                **base,
                "kind": "group",
                "value": None,
                "options": [],
                "mutable": False,
                "min": None,
                "max": None,
                "step": None,
                "minLength": None,
                "maxLength": None,
                "children": settings_tree_json(element, tuple(path)),
            })
    return result


def coerce_setting_value(element, value):
    """Match JSON values to labels or native option values.

    Some drivers expose numeric RadioSettingValueList options such as
    0-8. JSON serializes those as strings, but CHIRP expects the original
    integer when applying the value.
    """
    from chirp.settings import RadioSettingValueList

    if not isinstance(element.value, RadioSettingValueList):
        return value
    for option in element.value.get_options():
        if option == value or str(option) == str(value):
            return option
    return value


def preserve_unloadable_settings(settings):
    """Write back settings CHIRP could not load exactly as the radio had them.

    A driver's range can be narrower than what a radio really stores, for
    example a UV-5R factory squelch calibration of 124 against CHIRP's 0-123.
    CHIRP logs "Failed to load ...", leaves the value unset, and the driver's
    set_settings then fails on int(None), so no setting can be written
    (2026-11-20 UV-5R report, mailbox INBOX:833). The app shows such a value
    as unsupported and never changes it. Restore the radio's own stored value
    without validation and mark it read-only so drivers that honour
    mutability skip it; either way the radio's bytes stay unchanged.
    Returns the names of preserved settings.
    """
    from chirp.settings import RadioSetting

    preserved = []
    if not settings:
        return preserved
    for group in settings:
        for setting in group.walk() if hasattr(group, "walk") else [group]:
            if not isinstance(setting, RadioSetting):
                continue
            for value in setting.values():
                if value.initialized:
                    continue
                raw = getattr(value, "_preinit_current", None)
                if raw is None or isinstance(raw, Exception):
                    continue
                value._current = raw
                value._preinit_current = None
                value.set_mutable(False)
                preserved.append(setting.get_name())
    if preserved:
        logging.getLogger("newchirp.bridge").info(
            "Preserving radio values CHIRP could not load: %s",
            ", ".join(preserved))
    return preserved


def apply_setting_changes(settings, changes):
    from chirp.settings import RadioSetting, RadioSettingValueList

    for change in changes:
        path = change.get("id")
        if not isinstance(path, list) or not path:
            raise RuntimeError("A radio setting change was missing its path.")
        element = settings
        try:
            for index in path:
                element = list(element)[int(index)]
        except (IndexError, TypeError, ValueError) as exc:
            raise RuntimeError(
                "A radio setting change no longer matches the image."
            ) from exc
        if not isinstance(element, RadioSetting) or len(element) != 1:
            raise RuntimeError(
                "A radio setting change targeted an unsupported value."
            )
        if not element.value.get_mutable():
            continue
        value = coerce_setting_value(element, change.get("value"))
        try:
            element.value = value
        except Exception as exc:
            label = element.get_shortname() or element.get_name()
            raise RuntimeError(
                "Radio setting %r rejected value %r: %s"
                % (label, value, exc)
            ) from exc


def apply_json(radio, mem, item):
    from chirp import chirp_common

    fields = {
        "name": "name", "duplex": "duplex", "tone": "tmode",
        "txTone": "rtone", "rxTone": "ctone", "dtcs": "dtcs",
        "dtcsPolarity": "dtcs_polarity", "rxDtcs": "rx_dtcs",
        "crossMode": "cross_mode", "mode": "mode", "step": "tuning_step",
        "skip": "skip", "comment": "comment",
    }
    skipped_fields = []

    def set_mem(name, value):
        if name in mem.immutable:
            if getattr(mem, name, None) != value:
                skipped_fields.append(name)
            return
        setattr(mem, name, value)

    set_mem("number", int(item["location"]))
    set_mem("freq", int(round(float(item["frequency"]) * 1_000_000)))
    set_mem("offset", int(round(float(item["offset"]) * 1_000_000)))
    for source, target in fields.items():
        value = item[source]
        if (target == "cross_mode" and item.get("tone") != "Cross"
                and value not in chirp_common.CROSS_MODES):
            # Only Cross channels use the cross mode. A CSV with a blank
            # CrossMode cell must not stop the write of an ordinary channel
            # (2026-11-20 UV-32 report, mailbox INBOX:828).
            continue
        set_mem(target, value)
    if item.get("power"):
        for level in radio.get_features().valid_power_levels:
            if str(level) == item["power"]:
                set_mem("power", level)
                break
    extra_values = {
        field["name"]: field.get("value")
        for field in item.get("extras", [])
    }
    for setting in mem.extra:
        if setting.get_name() in extra_values and setting.value.get_mutable():
            setting.value = coerce_setting_value(
                setting, extra_values[setting.get_name()]
            )
    set_mem("empty", False)
    return skipped_fields


def nearest_programmable_frequency(frequency_hz, steps_khz):
    """Return the closest frequency representable by one of the steps."""
    nearest = None
    nearest_distance = None
    for step_khz in steps_khz:
        if abs(float(step_khz) - 8.33) < 0.001:
            continue
        step_hz = int(round(float(step_khz) * 1000))
        if step_hz <= 0:
            continue
        candidate = int(round(frequency_hz / step_hz)) * step_hz
        distance = abs(candidate - frequency_hz)
        if nearest_distance is None or distance < nearest_distance:
            nearest = candidate
            nearest_distance = distance
    return nearest


def channel_validation_message(memory, errors, steps_khz):
    """Add a frequency suggestion to CHIRP's unsupported-step error."""
    message = str(errors[0])
    if message.startswith("Unable to find a supported tuning step for "):
        nearest = nearest_programmable_frequency(memory.freq, steps_khz)
        if nearest is not None:
            message += (
                "\nNearest frequency supported by this radio: %.6f MHz."
                % (nearest / 1_000_000)
            )
    return message


def normalize_upload_memory(radio, memory):
    """Apply safe coercions advertised by CHIRP validation warnings.

    CHIRP distinguishes fatal errors from warnings that describe values the
    driver will coerce. NewChirp used to abort on both, which made custom
    receive-only GMRS and MURS channels impossible to upload.
    """
    from chirp import chirp_common

    messages = radio.validate_memory(memory)
    warnings, errors = chirp_common.split_validation_msgs(messages)
    changed_fields = []
    notes = []

    for warning in warnings:
        text = str(warning)
        if (
            text == 'Duplex must be "off" for this frequency'
            and memory.duplex != "off"
        ):
            memory.duplex = "off"
            memory.offset = 0
            changed_fields.extend(("duplex", "offset"))
            notes.append(
                "frequency is outside the radio's transmit plan; "
                "duplex was changed to TX off"
            )
        elif (
            text == "Only simplex or +5 MHz offset allowed on GMRS"
            and memory.offset != 5_000_000
        ):
            memory.offset = 5_000_000
            changed_fields.append("offset")
            notes.append("repeater offset was changed to +5 MHz")

    if changed_fields:
        messages = radio.validate_memory(memory)
        warnings, errors = chirp_common.split_validation_msgs(messages)

    return errors, warnings, sorted(set(changed_fields)), notes


def memory_with_new_extras(radio, location, item):
    """Reload a slot after giving it the incoming channel's basic fields.

    A channel's extra fields describe the channel that was in the slot. When
    inserting or moving shifts a channel into a slot that held a different
    kind (an analog channel onto a DMR one, for example), some drivers offer
    different choices for the same field, so the incoming value is rejected
    ("Allow TX is not valid for this setting", 2026-11-21 DM-32UV report,
    mailbox INBOX:863). Writing the basic fields first lets the driver switch
    the slot's kind; the reloaded memory then lists the matching choices.
    """
    mem = radio.get_memory(location)
    apply_json(radio, mem, dict(item, extras=[]))
    radio.set_memory(mem)
    return radio.get_memory(location)


def prepare_upload_channels(radio, items, progress_callback=None):
    """Validate and apply imported channels without touching invalid slots."""
    from chirp import chirp_common
    from chirp.settings import InvalidValueError

    start, end = radio.get_features().memory_bounds
    skipped = []
    adjusted = []
    written = 0

    for index, source_item in enumerate(items):
        item = dict(source_item)
        raw_location = item.get("location")
        try:
            location = int(raw_location)
        except (TypeError, ValueError):
            skipped.append({
                "location": raw_location,
                "name": str(item.get("name", "")),
                "reason": (
                    "Channel location must be a whole number between "
                    "%s and %s." % (start, end)
                ),
                "skipped": True,
            })
            location = None

        if location is not None and not start <= location <= end:
            filtered_name = radio.filter_name(str(item.get("name", "")))
            skipped.append({
                "location": location,
                "name": filtered_name,
                "reason": (
                    "Location %s is outside this radio's supported range "
                    "%s-%s." % (location, start, end)
                ),
                "skipped": True,
            })
            location = None

        if location is not None:
            requested_name = str(item.get("name", ""))
            filtered_name = radio.filter_name(requested_name)
            item["location"] = location
            item["name"] = filtered_name
            try:
                mem = radio.get_memory(location)
            except Exception as exc:
                skipped.append({
                    "location": location,
                    "name": filtered_name,
                    "reason": (
                        "The selected driver could not load channel %s: %s"
                        % (location, exc)
                    ),
                    "skipped": True,
                })
                location = None

        if location is not None:
            try:
                try:
                    locked_fields = apply_json(radio, mem, item)
                except InvalidValueError:
                    mem = memory_with_new_extras(radio, location, item)
                    locked_fields = apply_json(radio, mem, item)
                (
                    errors,
                    warnings,
                    normalized_fields,
                    normalization_notes,
                ) = normalize_upload_memory(radio, mem)
                if (errors or warnings) and locked_fields:
                    skipped.append({
                        "location": location,
                        "name": filtered_name,
                        "reason": (
                            "locked field(s): %s left a required value "
                            "unchanged" % ", ".join(locked_fields)
                        ),
                        "skipped": True,
                    })
                elif errors:
                    skipped.append({
                        "location": location,
                        "name": filtered_name,
                        "reason": channel_validation_message(
                            mem,
                            errors,
                            radio.get_features().valid_tuning_steps,
                        ),
                        "skipped": True,
                    })
                else:
                    set_memory_with_extras(radio, mem)
                    written += 1
                    if (
                        locked_fields
                        or normalized_fields
                        or filtered_name != requested_name
                    ):
                        fields = sorted(
                            set(locked_fields + normalized_fields)
                        )
                        adjusted.append({
                            "location": location,
                            "name": filtered_name,
                            "fields": fields,
                            "nameFrom": requested_name,
                            "nameTo": filtered_name,
                            "reason": (
                                "; ".join(normalization_notes)
                                if normalization_notes
                                else None
                            ),
                        })
            except chirp_common.ImmutableValueError as exc:
                skipped.append({
                    "location": location,
                    "name": filtered_name,
                    "reason": str(exc),
                    "skipped": True,
                })
            except Exception as exc:
                raise RuntimeError(
                    "Could not prepare channel %s (%s): %s"
                    % (location, filtered_name, exc)
                ) from exc

        if progress_callback is not None:
            progress_callback(index, len(items))

    return skipped, adjusted, written


def serial_read_timeout(radio_class):
    # Legacy Wouxun radios can take longer than CHIRP's 250 ms default to
    # finish the first 64-byte memory page. A one-byte-late response otherwise
    # appears as "Failed to read full block (67!=68)".
    if getattr(radio_class, "MODEL", "") == "KG-UVD1P":
        return 1.0
    return 0.25


def open_serial(radio_class, port):
    import serial

    software_flow = getattr(radio_class, "XON_XOFF", False)
    timeout = serial_read_timeout(radio_class)
    stopbits = getattr(radio_class, "SERIAL_STOPBITS", None)
    if "://" in port:
        handle = serial.serial_for_url(port, do_not_open=True)
        handle.timeout = timeout
        if stopbits is not None:
            handle.stopbits = stopbits
        handle.rtscts = radio_class.HARDWARE_FLOW
        handle.xonxoff = software_flow
        handle.rts = radio_class.WANTS_RTS
        handle.dtr = radio_class.WANTS_DTR
        handle.open()
        handle.baudrate = radio_class.BAUD_RATE
    else:
        # Configure baud and modem-control lines before opening the device.
        # This mirrors CHIRP's clone dialog and avoids a pulse at the radio.
        kwargs = dict(
            baudrate=radio_class.BAUD_RATE,
            rtscts=radio_class.HARDWARE_FLOW,
            xonxoff=software_flow,
            timeout=timeout,
        )
        if stopbits is not None:
            kwargs["stopbits"] = stopbits
        handle = serial.Serial(**kwargs)
        handle.rts = radio_class.WANTS_RTS
        handle.dtr = radio_class.WANTS_DTR
        handle.port = port
        handle.open()
    # Some modern CHIRP drivers annotate the GUI's SerialTrace stream. The
    # headless bridge does not need a trace file, but it must expose the same
    # interface as CHIRP's serial wrapper.
    handle.log = lambda message: None
    return handle


def headless_live_adapter(live_radio):
    """Give a live radio the file-backed interfaces NewChirp requires."""
    from chirp import chirp_common, errors
    from chirp.drivers import generic_csv

    class HeadlessLiveAdapter(generic_csv.CSVRadio):
        FILE_EXTENSION = "img"

        def __init__(self, radio):
            bounds = radio.get_features().memory_bounds
            super().__init__(None, max_memory=bounds[1])
            self._live_radio = radio
            self.VENDOR = radio.VENDOR
            self.MODEL = radio.MODEL
            self.VARIANT = getattr(radio, "VARIANT", "")
            self.BAUD_RATE = radio.BAUD_RATE
            self.HARDWARE_FLOW = radio.HARDWARE_FLOW
            self.SERIAL_STOPBITS = getattr(radio, "SERIAL_STOPBITS", 1)
            self.pipe = radio.pipe
            self._features = radio.get_features()

        def get_features(self):
            return self._features

        def get_prompts(self):
            return self._live_radio.get_prompts()

        def set_pipe(self, pipe):
            self.pipe = pipe
            self._live_radio.pipe = pipe

        def sync_in(self):
            start, end = self._features.memory_bounds
            for number in range(start, end + 1):
                self.set_memory(self._live_radio.get_memory(number))
                if self.status_fn:
                    status = chirp_common.Status()
                    status.cur = number
                    status.max = end
                    status.msg = "Reading from radio"
                    self.status_fn(status)

        def sync_out(self):
            start, end = self._features.memory_bounds
            written = []
            for number in range(start, end + 1):
                memory = self.get_memory(number)
                if memory.empty:
                    self._live_radio.erase_memory(number)
                else:
                    self._live_radio.set_memory(memory)
                    written.append(memory.dupe())
                if self.status_fn:
                    status = chirp_common.Status()
                    status.cur = number
                    status.max = end
                    status.msg = "Writing to radio"
                    self.status_fn(status)
            verify_live_write(self._live_radio, written, [])

        def load_mmap(self, filename):
            try:
                return super().load_mmap(filename)
            except errors.InvalidDataError as exc:
                if str(exc) != "No channels found":
                    raise
                # Live radios are persisted as CSV snapshots. A freshly reset
                # radio legitimately produces a header-only snapshot. Grow the
                # CSV map to its full bounds so an upload can fill selected
                # channels and erase the remaining slots.
                self._grow(self._features.memory_bounds[1])

        def get_settings(self):
            return self._live_radio.get_settings()

        def set_settings(self, settings):
            return self._live_radio.set_settings(settings)

    return HeadlessLiveAdapter(live_radio)


def live_memory_matches(expected, actual):
    """Compare fields that every live radio must retain after a write."""
    if actual is None:
        return False
    if expected.empty or actual.empty:
        return expected.empty == actual.empty
    if (
        int(expected.freq) != int(actual.freq)
        or expected.mode != actual.mode
        or expected.duplex != actual.duplex
        or str(expected.name).rstrip() != str(actual.name).rstrip()
    ):
        return False
    if expected.duplex in ("+", "-", "split"):
        if int(expected.offset) != int(actual.offset):
            return False
    if expected.tmode != actual.tmode:
        return False
    if expected.tmode in ("Tone", "TSQL", "Cross"):
        if abs(float(expected.rtone) - float(actual.rtone)) > 0.05:
            return False
    if expected.tmode in ("TSQL", "Cross"):
        if abs(float(expected.ctone) - float(actual.ctone)) > 0.05:
            return False
    if expected.tmode == "Cross" and expected.cross_mode != actual.cross_mode:
        return False
    if expected.tmode == "DTCS":
        if (
            int(expected.dtcs) != int(actual.dtcs)
            or expected.dtcs_polarity != actual.dtcs_polarity
        ):
            return False
    return True


def verify_live_write(live_radio, memories, cleared):
    """Read back live memories so a rejected write cannot report success."""
    failures = []
    for expected in memories:
        actual = live_radio.get_memory(expected.number)
        if not live_memory_matches(expected, actual):
            failures.append("channel %i" % expected.number)
    for number in cleared:
        if not live_radio.get_memory(number).empty:
            failures.append("channel %i was not cleared" % number)
    if failures:
        detail = ", ".join(failures[:8])
        if len(failures) > 8:
            detail += " and %i more" % (len(failures) - 8)
        raise RuntimeError(
            "The radio acknowledged the transfer but did not retain the "
            "changes: %s" % detail
        )


def live_channel_context(radio, zone=None):
    """Choose a live-radio subdevice without probing every memory slot."""
    from chirp import chirp_common

    if not isinstance(radio, chirp_common.LiveRadio):
        return radio, [], None
    features = radio.get_features()
    if not features.has_sub_devices:
        return radio, [], None
    subdevices = radio.get_sub_devices()
    if not subdevices:
        return radio, [], None

    zones = []
    for index, subdevice in enumerate(subdevices):
        start, end = subdevice.get_features().memory_bounds
        name = str(getattr(subdevice, "VARIANT", "")).strip()
        zones.append({
            "index": index,
            "name": name or "Zone %i" % (index + 1),
            "channelCount": max(0, end - start + 1),
        })
    selected = zone if zone is not None and 0 <= zone < len(subdevices) else 0
    return subdevices[selected], zones, selected


def radio_for(
    directory,
    model,
    port,
    progress_range=(0.0, 1.0),
    image=None,
    detect_serial=True,
    channel_zone=None,
):
    from chirp import chirp_common

    radio_class = directory.get_radio(model)
    RADIO_TRACE.set_radio_class(radio_class)
    if image is not None and not issubclass(
        radio_class, chirp_common.LiveRadio
    ):
        # Writes must use the exact class recorded in the image. The driver's
        # sync_out() owns its programming-mode handshake, like CHIRP's upload
        # dialog, so probing first would make strict drivers handshake twice.
        try:
            radio_class = directory.get_radio_by_image(image).__class__
        except Exception:
            pass
    transport_kind = getattr(radio_class, "NEWCHIRP_TRANSPORT", None)
    if transport_kind == "scsi_rap":
        from newchirp_mass_storage import ScsiPassthrough

        handle = ScsiPassthrough(port)
    elif transport_kind == "usb_dfu":
        from newchirp_usb_dfu import DfuTransport

        handle = DfuTransport(port)
    else:
        handle = TracedSerial(open_serial(radio_class, port), RADIO_TRACE)
    try:
        if detect_serial and transport_kind is None:
            try:
                radio_class = radio_class.detect_from_serial(handle)
                RADIO_TRACE.set_radio_class(radio_class)
            except NotImplementedError:
                pass
        radio = radio_class(handle)
        if isinstance(radio, chirp_common.LiveRadio):
            if channel_zone is None:
                radio = headless_live_adapter(radio)
            else:
                channel_radio, zones, selected_zone = live_channel_context(
                    radio, channel_zone
                )
                radio = headless_live_adapter(channel_radio)
                if zones:
                    radio._newchirp_zone_context = (
                        channel_radio,
                        zones,
                        selected_zone,
                    )
        # CHIRP's status callbacks become structured progress events on
        # stderr, leaving stdout available for the final JSON response.
        radio.status_fn = lambda status: status_progress(
            status, *progress_range
        )
        return radio
    except Exception:
        handle.close()
        raise


def download_decode_error_message(model, image, exc):
    """Explain a post-download map failure without losing the saved image."""
    detail = str(exc).strip() or exc.__class__.__name__
    return (
        "The radio image downloaded successfully and was saved to:\n"
        "%s\n\n"
        "NewChirp could not decode the %s channel map: %s\n\n"
        "Do not write this image back to the radio. Send the saved .img "
        "file with a bug report so the memory map can be corrected."
        % (image, model, detail)
    )


# The radio-side key in a clone prompt's "After clicking OK, press [KEY]"
# step (FT-1D "[BAND]", FT-817 "[A]", FT-8800 "left" [V/M], ...).
_SEND_KEY_STEP = re.compile(
    r'after\s+clicking\s+(?:OK|"[^"]+")(?:\s+here)?,\s*'
    r'press(?:\s+the)?(?:\s+"[^"]+")?\s+(\[[^\]]+\](?:\([^)]*\))?)',
    re.IGNORECASE,
)


def manual_send_key(pre_download):
    """Return the key a clone prompt says to press after OK, if any."""
    text = re.sub(r"<[^>]+>", "", pre_download or "")
    match = _SEND_KEY_STEP.search(text)
    return match.group(1) if match else None


def manual_send_ready_message(key):
    """Ready cue for a radio that starts the clone from its own key."""
    if key.lower() == "[send]":
        return MANUAL_SEND_READY_MESSAGE
    return "Radio is ready - press %s on the radio now." % key


def emit_read_ready(radio):
    """Tell the user when a manually triggered clone read can begin.

    The bridge opens the port only after the user confirms the prompt, so a
    radio key pressed before this message sends the image to a closed port.
    The radio then waits for an ACK that never comes (2026-11-21 FT-1D
    report: ID block lost, then "No response from radio").
    """
    prompts = radio.get_prompts()
    pre_download = getattr(prompts, "pre_download", "") or ""
    key = manual_send_key(pre_download)
    if "[PTT]" in pre_download:
        emit_progress(MANUAL_READ_READY_MESSAGE, 0.01)
    elif key:
        emit_progress(manual_send_ready_message(key), 0.01)
    elif "[Send]" in pre_download:
        emit_progress(MANUAL_SEND_READY_MESSAGE, 0.01)
    else:
        emit_progress("Connecting to radio...", 0.01)


def radio_from_image(directory, model, image):
    """Build a driver instance backed only by a saved radio image."""
    radio = directory.get_radio(model)(None)
    radio.load_mmap(image)
    return radio


def channel_context(radio, zone=None):
    """Return the selected channel owner plus available radio zones."""
    live_context = getattr(radio, "_newchirp_zone_context", None)
    if live_context is not None:
        return live_context
    features = radio.get_features()
    if not features.has_sub_devices:
        return radio, [], None
    subdevices = radio.get_sub_devices()
    if not subdevices:
        return radio, [], None
    zones = []
    populated = []
    for index, subdevice in enumerate(subdevices):
        start, end = subdevice.get_features().memory_bounds
        count = 0
        for location in range(start, end + 1):
            try:
                if not subdevice.get_memory(location).empty:
                    count += 1
            except Exception:
                continue
        name = str(getattr(subdevice, "VARIANT", "")).strip()
        zones.append({
            "index": index,
            "name": name or "Zone %i" % (index + 1),
            "channelCount": count,
        })
        if count:
            populated.append(index)
    selected = zone if zone is not None and 0 <= zone < len(subdevices) else None
    if selected is None:
        selected = populated[0] if populated else 0
    return subdevices[selected], zones, selected


def channel_radio_for(radio, zone=None):
    """Return the radio object that owns channel memories."""
    return channel_context(radio, zone)[0]


def _mapping_index_key(index):
    return str(index)


def display_mapping_name(value):
    """Return a safe display name for a CHIRP bank or zone."""
    text = str(value).split("\x00", 1)[0].replace("\xff", "").strip()
    return "".join(
        character if character.isprintable() else "?" for character in text
    )


def mapping_payload(radio):
    """Describe CHIRP's bank/zone models for an image or channel owner."""
    from chirp import chirp_common

    models_json = []
    for model_index, model in enumerate(radio.get_mapping_models()):
        try:
            editable = (
                not isinstance(model, chirp_common.StaticBankModel)
                and model.__class__.add_memory_to_mapping
                is not chirp_common.MappingModel.add_memory_to_mapping
                and model.__class__.remove_memory_from_mapping
                is not chirp_common.MappingModel.remove_memory_from_mapping
            )
            mappings_json = []
            for mapping in model.get_mappings():
                members = model.get_mapping_memories(mapping)
                locations = [int(memory.number) for memory in members]
                mappings_json.append({
                    "index": _mapping_index_key(mapping.get_index()),
                    "name": display_mapping_name(mapping.get_name()),
                    "channelLocations": list(dict.fromkeys(locations)),
                    "nameEditable": (
                        editable
                        and callable(getattr(mapping, "set_name", None))
                    ),
                })
        except Exception:
            # A partial bank model is unsafe to edit: saving it could erase
            # memberships that could not be read.
            continue
        models_json.append({
            "index": model_index,
            "name": str(model.get_name()),
            "editable": editable,
            "multiple": isinstance(model, chirp_common.MTOBankModel),
            "mappings": mappings_json,
        })
    return models_json


def _mapping_models_by_index(radio):
    return {
        str(index): model
        for index, model in enumerate(radio.get_mapping_models())
    }


def _mapping_entries_by_index(model):
    return {
        _mapping_index_key(mapping.get_index()): mapping
        for mapping in model.get_mappings()
    }


def apply_mapping_payload(radio, requested_models, active_locations):
    """Apply bank/zone names and memberships to an already loaded image.

    The client sends the complete state for each model. Unchanged models are
    left alone so writing channels cannot accidentally reorder unrelated
    banks. Removing memberships happens before additions, which also supports
    one-bank-per-channel models when a channel moves between banks.
    """
    from chirp import chirp_common, errors

    active_locations = {int(location) for location in active_locations}
    models = _mapping_models_by_index(radio)
    for requested_model in requested_models:
        model_index = str(requested_model.get("index"))
        model = models.get(model_index)
        if model is None:
            raise RuntimeError(
                "The selected bank model is no longer available."
            )

        current_entries = _mapping_entries_by_index(model)
        requested_entries = requested_model.get("mappings", [])
        requested_by_index = {
            _mapping_index_key(entry.get("index")): entry
            for entry in requested_entries
        }
        current_state = mapping_payload(radio)[int(requested_model["index"])]
        current_by_index = {
            entry["index"]: entry for entry in current_state["mappings"]
        }
        changed = set(current_by_index) != set(requested_by_index)
        if not changed:
            for key, current_entry in current_by_index.items():
                requested_entry = requested_by_index[key]
                if (
                    str(requested_entry.get("name", current_entry["name"]))
                    != current_entry["name"]
                    or [
                        int(location)
                        for location in requested_entry.get(
                            "channelLocations", []
                        )
                    ]
                    != current_entry["channelLocations"]
                ):
                    changed = True
                    break
        if not changed:
            continue
        if not current_state["editable"]:
            # Fixed zones follow channel numbers and cannot be edited, so a
            # different membership list only reflects channels the user
            # added, moved or removed. The radio derives the real zones.
            logging.getLogger("newchirp.bridge").info(
                "Ignoring membership changes to fixed %s", current_state["name"]
            )
            continue

        desired = {}
        for key, entry in requested_by_index.items():
            mapping = current_entries.get(key)
            if mapping is None:
                raise RuntimeError(
                    "Bank %s is no longer available; reopen the radio image."
                    % key
                )
            requested_locations = [
                int(location)
                for location in entry.get("channelLocations", [])
            ]
            if len(requested_locations) != len(set(requested_locations)):
                raise RuntimeError(
                    "Bank %s contains a duplicate channel." % entry.get("name")
                )
            locations = requested_locations
            for location in locations:
                if location not in active_locations:
                    raise RuntimeError(
                        "Channel %i is empty and cannot be placed in a bank."
                        % location
                    )
                try:
                    memory = radio.get_memory(location)
                except Exception as exc:
                    raise RuntimeError(
                        "Could not load channel %i for bank %s."
                        % (location, entry.get("name"))
                    ) from exc
                if memory.empty:
                    raise RuntimeError(
                        "Channel %i is empty and cannot be placed in a bank."
                        % location
                    )
            desired[key] = {
                "mapping": mapping,
                "locations": locations,
                "name": str(entry.get("name", mapping.get_name())),
            }

        if not current_state["multiple"]:
            seen_locations = set()
            for entry in desired.values():
                overlap = seen_locations.intersection(entry["locations"])
                if overlap:
                    location = sorted(overlap)[0]
                    raise RuntimeError(
                        "Channel %i can be in only one %s."
                        % (location, current_state["name"].lower())
                    )
                seen_locations.update(entry["locations"])

        for key, entry in desired.items():
            mapping = entry["mapping"]
            current_locations = {
                int(memory.number)
                for memory in model.get_mapping_memories(mapping)
            }
            removed_locations = current_locations - set(entry["locations"])
            for location in sorted(removed_locations):
                model.remove_memory_from_mapping(
                    radio.get_memory(location), mapping
                )

        for key, entry in desired.items():
            mapping = entry["mapping"]
            current_locations = {
                int(memory.number)
                for memory in model.get_mapping_memories(mapping)
            }
            for location in entry["locations"]:
                if location not in current_locations:
                    try:
                        model.add_memory_to_mapping(
                            radio.get_memory(location), mapping
                        )
                    except errors.RadioError as exc:
                        message = str(exc)
                        if " is full" not in message:
                            raise
                        name = display_mapping_name(mapping.get_name())
                        capacity = re.search(
                            r"\((\d+) channels\)", message
                        )
                        limit = (
                            "This radio allows at most %s channels per zone."
                            % capacity.group(1)
                            if capacity
                            else "This radio limits the channels in each zone."
                        )
                        raise RuntimeError(
                            "Zone %r is full. %s Remove at least one channel "
                            "from this zone or place the additional channels "
                            "in another zone, then try the write again."
                            % (name, limit)
                        ) from exc

        for key, entry in desired.items():
            mapping = entry["mapping"]
            if (
                entry["name"] != display_mapping_name(mapping.get_name())
                and callable(getattr(mapping, "set_name", None))
            ):
                mapping.set_name(entry["name"])

    return mapping_payload(radio)


REPEATERBOOK_BROKER_MAX_RESPONSE_BYTES = 4 * 1024 * 1024


def fetch_repeaterbook_search(
    country,
    state,
    service,
    query="",
    latitude=None,
    longitude=None,
    distance=None,
    fm_only=False,
    open_only=False,
    limit=200,
):
    """Query NewChirp's relay without exposing RepeaterBook credentials."""
    base = os.environ.get(
        "REPEATERBOOK_BROKER_BASE",
        "https://newchirp.net",
    ).rstrip("/")
    payload = json.dumps({
        "country": country,
        "state": state,
        "service": service,
        "query": query,
        "latitude": latitude,
        "longitude": longitude,
        "distance": distance,
        "fmOnly": bool(fm_only),
        "openOnly": bool(open_only),
        "limit": int(limit),
    }).encode("utf-8")
    request = urllib.request.Request(
        base + "/api/repeaters/repeaterbook/search",
        data=payload,
        method="POST",
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "NewChirp repeater relay client",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            body = response.read(REPEATERBOOK_BROKER_MAX_RESPONSE_BYTES + 1)
    except urllib.error.HTTPError as exc:
        detail = ""
        try:
            error_body = exc.read(4096)
            parsed = json.loads(error_body.decode("utf-8"))
            detail = str(parsed.get("error") or "").strip()
        except Exception:
            pass
        message = "RepeaterBook search service returned HTTP %s" % exc.code
        if detail:
            message += ": " + detail[:300]
        raise RuntimeError(message) from exc
    except Exception as exc:
        raise RuntimeError(
            "Could not reach NewChirp's RepeaterBook search service: %s" % exc
        ) from exc
    if len(body) > REPEATERBOOK_BROKER_MAX_RESPONSE_BYTES:
        raise RuntimeError(
            "RepeaterBook search returned an unexpectedly large response."
        )
    try:
        data = json.loads(body)
    except (TypeError, ValueError) as exc:
        raise RuntimeError("RepeaterBook search returned invalid JSON.") from exc
    if not isinstance(data, dict) or not isinstance(data.get("results"), list):
        raise RuntimeError("RepeaterBook search returned an unexpected response.")
    return data


def repeaterbook_tone(value):
    from chirp import chirp_common

    value = str(value or "").strip()
    if value.startswith("D"):
        return "DTCS", chirp_common.DTCS_CODES[int(value[1:])], "N"
    if "." in value:
        return "Tone", float(value), "N"
    return "", None, "N"


def repeaterbook_item_to_channel(item, number):
    from chirp import chirp_common, errors

    memory = chirp_common.Memory()
    memory.number = number
    memory.empty = False
    memory.freq = chirp_common.parse_freq(item.get("Frequency") or "0")
    try:
        memory.tuning_step = chirp_common.required_step(memory.freq)
    except errors.InvalidDataError:
        memory.tuning_step = 5.0
    tx_frequency = chirp_common.parse_freq(item.get("Input Freq") or "0")
    if tx_frequency:
        chirp_common.split_to_offset(memory, memory.freq, tx_frequency)
    else:
        memory.duplex = "off"
        memory.offset = 0
    chirp_common.split_tone_decode(
        memory,
        repeaterbook_tone(item.get("PL")),
        repeaterbook_tone(item.get("TSQ")),
    )
    if item.get("FM Analog") == "Yes":
        memory.mode = "FM"
    elif item.get("DMR") == "Yes":
        memory.mode = "DMR"
    elif item.get("D-Star") == "Yes":
        memory.mode = "DV"
    elif item.get("System Fusion") == "Yes":
        memory.mode = "DN"
    else:
        memory.mode = "FM"
    memory.name = str(item.get("Landmark") or item.get("Callsign") or "")
    location = ", ".join(
        part
        for part in (
            item.get("Nearest City"),
            item.get("County") and "%s County" % item.get("County"),
            item.get("State") or item.get("Region"),
        )
        if part
    )
    comment = "RepeaterBook: %s" % (
        item.get("Callsign") or "Unknown callsign"
    )
    if location:
        comment += " - %s" % location
    if item.get("Use"):
        comment += " - %s" % item.get("Use")
    if item.get("Notes"):
        comment += " - %s" % item.get("Notes")
    memory.comment = comment
    return memory_json(memory)


def repeaterbook_api_tone(tone):
    if not isinstance(tone, dict):
        return "", None, "N"
    mode = str(tone.get("mode") or "").lower()
    try:
        value = int(tone["value"]) if mode == "dtcs" else float(tone["value"])
    except (KeyError, TypeError, ValueError):
        return "", None, "N"
    if mode == "dtcs":
        polarity = "R" if str(tone.get("polarity")).upper() == "R" else "N"
        return "DTCS", value, polarity
    if mode == "ctcss":
        return "Tone", value, "N"
    return "", None, "N"


def repeaterbook_api_result_to_channel(result, number):
    from chirp import chirp_common, errors

    memory = chirp_common.Memory()
    memory.number = number
    memory.empty = False
    memory.freq = int(result["rxFrequency"])
    try:
        memory.tuning_step = chirp_common.required_step(memory.freq)
    except errors.InvalidDataError:
        memory.tuning_step = 5.0
    tx_frequency = (
        int(result["txFrequency"])
        if result.get("txFrequency") not in (None, "")
        else None
    )
    if tx_frequency:
        chirp_common.split_to_offset(memory, memory.freq, tx_frequency)
    else:
        memory.duplex = "off"
        memory.offset = 0
    chirp_common.split_tone_decode(
        memory,
        repeaterbook_api_tone(result.get("txTone")),
        repeaterbook_api_tone(result.get("rxTone")),
    )
    memory.mode = "NFM" if result.get("mode") == "NFM" else "FM"
    memory.name = str(
        result.get("name") or result.get("callsign") or ""
    ).strip()
    location = ", ".join(
        part
        for part in (
            str(result.get("city") or "").strip(),
            (
                "%s County" % str(result.get("county")).strip()
                if str(result.get("county") or "").strip()
                else ""
            ),
            str(result.get("state") or "").strip(),
        )
        if part
    )
    service = str(result.get("service") or "Amateur").strip()
    comment = "RepeaterBook %s: %s" % (
        service,
        str(result.get("callsign") or "Unknown callsign").strip(),
    )
    if location:
        comment += " - %s" % location
    use = str(result.get("use") or "").strip()
    if use:
        comment += " - %s" % use
    notes = str(result.get("notes") or "").strip()
    if notes:
        comment += " - %s" % notes
    memory.comment = comment
    return memory_json(memory)


US_ZIP_PATTERN = re.compile(r"^\d{5}(?:-\d{4})?$")
REPEATERBOOK_DEFAULT_ZIP_RADIUS_KM = 50.0
ZIP_LOOKUP_MAX_AGE_SECONDS = 30 * 86400


def zip_lookup_cache_path(zip_code):
    cache_dir = os.path.join(tempfile.gettempdir(), "newchirp-zipcodes")
    os.makedirs(cache_dir, exist_ok=True)
    return os.path.join(cache_dir, "%s.json" % zip_code)


def resolve_us_zip_code(zip_code):
    """Resolve a US ZIP code to a representative latitude and longitude."""
    requested_zip = str(zip_code or "").strip()
    if not US_ZIP_PATTERN.fullmatch(requested_zip):
        raise RuntimeError("Enter a valid 5-digit US ZIP code.")
    lookup_zip = requested_zip[:5]
    cache_path = zip_lookup_cache_path(lookup_zip)

    def cached_result():
        try:
            with open(cache_path, encoding="utf-8") as handle:
                cached = json.load(handle)
            latitude = float(cached["latitude"])
            longitude = float(cached["longitude"])
            state = str(cached["state"]).strip()
            city = str(cached.get("city") or "").strip()
            if not state:
                return None
            return {
                "zip": lookup_zip,
                "city": city,
                "state": state,
                "latitude": latitude,
                "longitude": longitude,
            }
        except (OSError, KeyError, TypeError, ValueError):
            return None

    cache_age = (
        time.time() - os.path.getmtime(cache_path)
        if os.path.exists(cache_path)
        else None
    )
    if cache_age is not None and cache_age < ZIP_LOOKUP_MAX_AGE_SECONDS:
        result = cached_result()
        if result is not None:
            return result

    emit_progress("Resolving ZIP code...", 0.06)
    url = "https://api.zippopotam.us/us/%s" % lookup_zip
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "NewChirp repeater search"},
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            payload = json.load(response)
        places = payload.get("places") or []
        if not places:
            raise ValueError("ZIP lookup returned no places")
        place = places[0]
        result = {
            "zip": lookup_zip,
            "city": str(place.get("place name") or "").strip(),
            "state": str(place.get("state") or "").strip(),
            "latitude": float(place["latitude"]),
            "longitude": float(place["longitude"]),
        }
        if not result["state"]:
            raise ValueError("ZIP lookup returned no state")
        if not -90 <= result["latitude"] <= 90:
            raise ValueError("ZIP lookup returned an invalid latitude")
        if not -180 <= result["longitude"] <= 180:
            raise ValueError("ZIP lookup returned an invalid longitude")
        with open(cache_path + ".tmp", "w", encoding="utf-8") as handle:
            json.dump(result, handle)
        os.replace(cache_path + ".tmp", cache_path)
        return result
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise RuntimeError(
                "Could not resolve ZIP code %s. Check the ZIP code and try "
                "again." % lookup_zip
            ) from exc
        failure = str(exc)
    except Exception as exc:
        failure = str(exc)

    result = cached_result()
    if result is not None:
        emit_progress("Using cached ZIP location.", 0.07)
        return result
    raise RuntimeError(
        "Could not resolve ZIP code %s (%s). Try again, or enter latitude "
        "and longitude instead." % (lookup_zip, failure)
    )


def normalize_repeaterbook_query(query):
    """Treat location words like "Broward County" as a county name."""
    normalized = re.sub(
        r"\b(?:county|parish)\b",
        " ",
        str(query or ""),
        flags=re.IGNORECASE,
    )
    return re.sub(r"\s+", " ", normalized).strip().lower()


def search_repeaterbook(
    country,
    state,
    service="amateur",
    query="",
    latitude=None,
    longitude=None,
    distance=None,
    fm_only=False,
    open_only=False,
    limit=200,
):
    if country != "United States":
        service = "amateur"
    if (latitude is None) != (longitude is None):
        raise RuntimeError("Enter both latitude and longitude, or neither.")
    query_text = str(query or "").strip()
    zip_search = US_ZIP_PATTERN.fullmatch(query_text)
    if zip_search:
        if country != "United States":
            raise RuntimeError(
                "ZIP-code repeater searches are available for the United "
                "States. Choose United States or enter latitude and longitude."
            )
        if latitude is not None:
            raise RuntimeError(
                "Use either a ZIP code or latitude and longitude, not both."
            )
        zip_location = resolve_us_zip_code(query_text)
        if (
            state
            and str(state).strip().lower() != "all"
            and str(state).strip().casefold()
            != zip_location["state"].strip().casefold()
        ):
            raise RuntimeError(
                "ZIP code %s is in %s, but Region is %s. Choose %s or enter "
                "the correct ZIP code."
                % (
                    query_text[:5],
                    zip_location["state"],
                    state,
                    zip_location["state"],
                )
            )
        latitude = zip_location["latitude"]
        longitude = zip_location["longitude"]
        if distance is None:
            distance = REPEATERBOOK_DEFAULT_ZIP_RADIUS_KM
        query = ""
    else:
        query = normalize_repeaterbook_query(query_text)
    data = fetch_repeaterbook_search(
        country=country,
        state=state,
        service=service,
        query=query,
        latitude=latitude,
        longitude=longitude,
        distance=distance,
        fm_only=fm_only,
        open_only=open_only,
        limit=limit,
    )
    results = []
    for index, item in enumerate(data.get("results", [])[:limit]):
        try:
            channel = repeaterbook_api_result_to_channel(item, index + 1)
        except Exception:
            continue
        results.append({
            "channel": channel,
            "callsign": item.get("callsign") or "",
            "city": item.get("city") or "",
            "county": item.get("county") or "",
            "state": item.get("state") or "",
            "use": item.get("use") or "",
            "service": item.get("service") or "Amateur",
            "latitude": item.get("latitude"),
            "longitude": item.get("longitude"),
            "distanceKm": item.get("distanceKm"),
        })
    total_matches = data.get("totalMatches")
    return {
        "source": "RepeaterBook",
        "sourceUrl": "https://repeaterbook.com",
        "totalMatches": (
            int(total_matches)
            if total_matches is not None
            else len(results)
        ),
        "results": results,
    }


def has_global_settings(radio):
    return bool(getattr(radio.get_features(), "has_settings", False))


def settings_payload(radio):
    if not has_global_settings(radio):
        return {"hasSettings": False, "settings": []}
    settings = radio.get_settings()
    return {
        "hasSettings": True,
        "settings": settings_tree_json(settings or []),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--vendor", required=True)
    parser.add_argument("--newchirp-driver-dir")
    parser.add_argument(
        "--module",
        help="Load a session-scoped CHIRP .py or .mod module",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list-models")
    sub.add_parser("list-interfaces")
    model_info = sub.add_parser("model-info")
    model_info.add_argument("--model", required=True)
    repeaterbook = sub.add_parser("repeaterbook-search")
    repeaterbook.add_argument("--country", default="United States")
    repeaterbook.add_argument("--state", required=True)
    repeaterbook.add_argument(
        "--service", choices=("amateur", "gmrs", "all"), default="all"
    )
    repeaterbook.add_argument("--filter", default="")
    repeaterbook.add_argument("--latitude", type=float)
    repeaterbook.add_argument("--longitude", type=float)
    repeaterbook.add_argument("--distance", type=float)
    repeaterbook.add_argument("--fm-only", action="store_true")
    repeaterbook.add_argument("--open-only", action="store_true")
    repeaterbook.add_argument("--limit", type=int, default=200)
    read_image = sub.add_parser("read-image")
    read_image.add_argument("--image", required=True)
    read_image.add_argument("--metadata-only", action="store_true")
    read_image.add_argument("--zone", type=int)
    for name in ("download", "upload"):
        command = sub.add_parser(name)
        command.add_argument("--model", required=True)
        command.add_argument("--port", required=True)
        command.add_argument("--zone", type=int)
        if name == "upload":
            command.add_argument("--image", required=True)
            command.add_argument("--channels", required=True)
            command.add_argument("--cleared", default="")
            command.add_argument("--mappings")
    read_settings = sub.add_parser("read-settings")
    read_settings.add_argument("--model", required=True)
    settings_source = read_settings.add_mutually_exclusive_group(required=True)
    settings_source.add_argument("--image")
    settings_source.add_argument("--port")
    write_settings = sub.add_parser("write-settings")
    write_settings.add_argument("--model", required=True)
    write_settings.add_argument("--port", required=True)
    write_settings.add_argument("--image", required=True)
    write_settings.add_argument("--settings", required=True)
    args = parser.parse_args()
    try:
        directory = load_chirp(
            args.source,
            args.vendor,
            args.newchirp_driver_dir,
            args.module,
        )
        if args.command == "list-models":
            models_by_vendor = live_models_by_vendor(directory)
            vendors = [
                {
                    "name": vendor,
                    "models": sorted(identifiers),
                }
                for vendor, identifiers in sorted(
                    models_by_vendor.items(),
                    key=lambda item: item[0].casefold(),
                )
            ]
            print(json.dumps({
                "models": sorted(
                    identifier
                    for identifiers in models_by_vendor.values()
                    for identifier in identifiers
                ),
                "vendors": vendors,
            }))
            return
        if args.command == "list-interfaces":
            interfaces = []
            try:
                from newchirp_mass_storage import list_devices

                interfaces.extend(list_devices())
            except Exception:
                pass
            try:
                from newchirp_usb_dfu import list_devices as list_dfu_devices

                interfaces.extend(list_dfu_devices())
            except Exception:
                pass
            print(json.dumps({"interfaces": interfaces}))
            return
        if args.command == "model-info":
            from chirp import chirp_common

            radio_class = directory.get_radio(args.model)
            prompts = radio_class.get_prompts()
            print(json.dumps({
                "info": prompts.info,
                "experimental": prompts.experimental,
                "preDownload": prompts.pre_download,
                "preUpload": prompts.pre_upload,
                # Drivers that always refuse uploads declare it so the app
                # can say so before a write starts (RT-950 Pro report,
                # 2026-11-19: the refusal surfaced only on channel 1).
                "writeDisabled": bool(
                    getattr(radio_class, "NEWCHIRP_WRITE_DISABLED", False)
                ),
                # Live (CI-V style) radios keep no clone image. Their saved
                # snapshot holds only the band that was read, so switching
                # bands must read that band from the radio (2026-11-19
                # IC-9700 report, mailbox INBOX:825).
                "liveRadio": issubclass(radio_class, chirp_common.LiveRadio),
            }))
            return
        if args.command == "repeaterbook-search":
            emit_progress("Searching RepeaterBook...", 0.04)
            print(json.dumps(search_repeaterbook(
                country=args.country,
                state=args.state,
                service=args.service,
                query=args.filter,
                latitude=args.latitude,
                longitude=args.longitude,
                distance=args.distance,
                fm_only=args.fm_only,
                open_only=args.open_only,
                limit=max(1, min(args.limit, 500)),
            )))
            emit_progress("RepeaterBook search complete.", 1.0)
            return
        if args.command == "read-image":
            image_path = os.path.abspath(args.image)
            radio = directory.get_radio_by_image(image_path)
            try:
                model = directory.get_driver(radio.__class__)
            except Exception:
                model = directory.radio_class_id(radio.__class__)
            channel_radio, zones, selected_zone = channel_context(radio, args.zone)
            channels = []
            if not args.metadata_only:
                start, end = channel_radio.get_features().memory_bounds
                for location in range(start, end + 1):
                    mem = memory_with_extras(channel_radio, location)
                    if not mem.empty:
                        channels.append(memory_json(mem))
            print(json.dumps({
                "model": model,
                "firmware": radio_firmware(radio),
                "channels": channels,
                "imagePath": image_path,
                "zones": zones,
                "zone": selected_zone,
                "mappings": mapping_payload(channel_radio),
                "features": features_json(channel_radio),
            }))
            return
        if args.command == "read-settings":
            if args.port is not None:
                radio = radio_for(
                    directory,
                    args.model,
                    args.port,
                    progress_range=(0.02, 0.97),
                )
                try:
                    if not has_global_settings(radio):
                        emit_progress(
                            "This radio does not expose global settings.",
                            1.0,
                        )
                        print(json.dumps(settings_payload(radio)))
                        return
                    emit_read_ready(radio)
                    radio.sync_in()
                    fd, image = tempfile.mkstemp(
                        prefix="newchirp-", suffix=".img"
                    )
                    os.close(fd)
                    radio.save_mmap(image)
                    payload = settings_payload(radio)
                    payload["imagePath"] = image
                    payload["firmware"] = radio_firmware(radio)
                    emit_progress("Radio settings read.", 1.0)
                    print(json.dumps(payload))
                finally:
                    radio.pipe.close()
            else:
                radio = radio_from_image(directory, args.model, args.image)
                payload = settings_payload(radio)
                payload["firmware"] = radio_firmware(radio)
                print(json.dumps(payload))
            return
        if args.command == "download":
            progress_range = (0.02, 0.92)
        elif args.command == "upload":
            progress_range = (0.10, 0.98)
        else:
            progress_range = (0.12, 0.97)
        is_write = args.command in ("upload", "write-settings")
        radio = radio_for(
            directory,
            args.model,
            args.port,
            progress_range=progress_range,
            image=args.image if is_write else None,
            detect_serial=not is_write,
            channel_zone=(
                (args.zone if args.zone is not None else 0)
                if args.command in ("download", "upload")
                else None
            ),
        )
        try:
            if args.command == "download":
                emit_read_ready(radio)
                radio.sync_in()
                emit_progress("Saving the radio image...", 0.93)
                fd, image = tempfile.mkstemp(prefix="newchirp-", suffix=".img")
                os.close(fd)
                radio.save_mmap(image)
                try:
                    channel_radio, zones, selected_zone = channel_context(
                        radio, args.zone
                    )
                    start, end = channel_radio.get_features().memory_bounds
                    locations = list(range(start, end + 1))
                    channels = []
                    for index, location in enumerate(locations):
                        mem = memory_with_extras(channel_radio, location)
                        if not mem.empty:
                            channels.append(memory_json(mem))
                        if locations and (
                            index % 20 == 0 or index == len(locations) - 1
                        ):
                            emit_progress(
                                "Building the channel list...",
                                0.94 + 0.05 * (index + 1) / len(locations),
                            )
                except Exception as exc:
                    raise RuntimeError(
                        download_decode_error_message(
                            args.model,
                            image,
                            exc,
                        )
                    ) from exc
                emit_progress("Read complete.", 1.0)
                print(json.dumps({
                    "firmware": radio_firmware(radio),
                    "channels": channels,
                    "imagePath": image,
                    "zones": zones,
                    "zone": selected_zone,
                    "mappings": mapping_payload(channel_radio),
                    "features": features_json(channel_radio),
                }))
            elif args.command == "upload":
                emit_progress("Preparing channels...", 0.02)
                radio.load_mmap(args.image)
                channel_radio, zones, selected_zone = channel_context(
                    radio, args.zone
                )
                with open(args.channels, encoding="utf-8") as handle:
                    items = json.load(handle)
                def channel_progress(index, total):
                    if total and (index % 10 == 0 or index == total - 1):
                        emit_progress(
                            "Preparing channels...",
                            0.03 + 0.06 * (index + 1) / total,
                        )

                skipped, adjusted, written = prepare_upload_channels(
                    channel_radio,
                    items,
                    channel_progress,
                )
                if items and written == 0:
                    detail = (
                        " First incompatible channel: %s."
                        % skipped[0]["reason"]
                        if skipped
                        else ""
                    )
                    raise RuntimeError(
                        "None of the selected channels is compatible with "
                        "this radio.%s" % detail
                    )
                cleared = [
                    int(part) for part in args.cleared.split(",") if part.strip()
                ]
                for location in cleared:
                    try:
                        erase_memory_with_extras(channel_radio, location)
                    except Exception:
                        continue
                mappings = None
                if args.mappings:
                    with open(args.mappings, encoding="utf-8") as handle:
                        requested_mappings = json.load(handle)
                    start, end = channel_radio.get_features().memory_bounds
                    active_locations = set()
                    for location in range(start, end + 1):
                        try:
                            if not channel_radio.get_memory(location).empty:
                                active_locations.add(location)
                        except Exception:
                            continue
                    emit_progress("Preparing banks and zones...", 0.09)
                    mappings = apply_mapping_payload(
                        channel_radio,
                        requested_mappings,
                        active_locations,
                    )
                emit_progress("Writing the image to the radio...", 0.10)
                radio.sync_out()
                emit_progress("Saving the updated image...", 0.99)
                radio.save_mmap(args.image)
                emit_progress("Write complete.", 1.0)
                print(json.dumps({
                    "ok": True,
                    "firmware": radio_firmware(radio),
                    "skipped": skipped,
                    "adjusted": adjusted,
                    "mappings": (
                        mappings
                        if mappings is not None
                        else mapping_payload(channel_radio)
                    ),
                }))
            else:
                emit_progress("Preparing radio settings...", 0.02)
                if not has_global_settings(radio):
                    raise RuntimeError(
                        "This radio does not expose global settings."
                    )
                radio.load_mmap(args.image)
                with open(args.settings, encoding="utf-8") as handle:
                    payload = json.load(handle)
                settings = radio.get_settings()
                preserve_unloadable_settings(settings)
                changes = payload.get("changes", [])
                apply_setting_changes(settings, changes)
                emit_progress("Applying settings...", 0.10)
                radio.set_settings(settings)
                emit_progress("Writing settings to the radio...", 0.12)
                radio.sync_out()
                emit_progress("Saving the updated image...", 0.99)
                radio.save_mmap(args.image)
                emit_progress("Settings write complete.", 1.0)
                print(json.dumps({
                    "ok": True,
                    "firmware": radio_firmware(radio),
                    "changed": len(changes),
                }))
        finally:
            radio.pipe.close()
    except Exception as exc:
        print(
            bridge_error_message(
                exc,
                getattr(args, "command", None),
                getattr(args, "model", None),
                getattr(args, "port", None),
            ),
            file=sys.stderr,
        )
        raise SystemExit(1)


if __name__ == "__main__":
    main()
