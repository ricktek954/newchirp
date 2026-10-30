#!/usr/bin/env python3
"""Small JSON boundary between NewChirp and the audited CHIRP driver tree."""
import argparse
import builtins
import glob
import importlib.machinery
import importlib.util
import json
import logging
import lzma
import math
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


class RadioCommunicationTrace:
    """Keep a bounded, privacy-safe view of recent serial exchanges."""

    def __init__(self, max_entries=80):
        self.max_entries = max_entries
        self._entries = []
        self._pending = None

    @staticmethod
    def _command_summary(data):
        try:
            raw = bytes(data)
        except (TypeError, ValueError):
            return "<invalid serial data>"
        if not raw:
            return "<empty write>"
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
        try:
            text = raw.decode("cp1252").strip("\r\n")
        except UnicodeDecodeError:
            return "<binary command, %i bytes>" % len(raw)
        body = text.split(";", 1)[0].strip()
        if not body or not all(32 <= ord(char) < 127 for char in body):
            return "<binary command, %i bytes>" % len(raw)
        upper = body.upper()
        memory = re.match(r"^(M[WRA])\s*([01]?),?(\d{3})", upper)
        if memory:
            return "%s memory=%s" % (memory.group(1), memory.group(3))
        token = re.match(r"^[A-Z~]+", upper)
        command = token.group(0) if token else ""
        if command.startswith("AL~EEPEL"):
            return "AL~EEPEL"
        return command[:12] or "<text command>"

    def begin(self, data):
        self._finish_pending()
        self._pending = {
            "command": self._command_summary(data),
            "started": time.monotonic(),
            "response": bytearray(),
        }

    def received(self, data):
        if self._pending is None or not data:
            return
        self._pending["response"].extend(data)
        if any(delimiter in data for delimiter in (b";", b"\r", b"\n")):
            self._finish_pending()

    def _finish_pending(self):
        pending = self._pending
        if pending is None:
            return
        self._pending = None
        response = bytes(pending["response"])
        if pending["command"] == "ID":
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
            result = "reply=%s (%i bytes)" % (preview, len(response))
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
            ):
                preview = response[:32].hex(" ")
                if len(response) > 32:
                    preview += " …"
                result = "reply=%s (%i bytes)" % (preview, len(response))
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


def bridge_error_message(exc, command=None, model=None):
    """Add safe, command-specific recovery guidance to bridge failures."""
    message = str(exc).strip() or exc.__class__.__name__
    lowered_message = message.lower()
    if (
        "permissionerror(13)" in lowered_message
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
        and model in (
            "Yaesu_FT2D_R",
            "Yaesu_FT2D_Rv2",
            "Yaesu_FT3D_R",
            "Yaesu_FT5D_R",
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
        message = (
            "No response from the AR8200. Use an AOR CC8200-compatible "
            "RS-232 lead in the option socket, not a TTL handheld-radio "
            "programming cable. In the radio's CONFIG menu, set REMOTE BPS "
            "to 19200, 9600, or 4800 and set RMT-ID to 00; NewChirp scans "
            "all three baud rates, but nonzero RMT-ID prevents normal "
            "single-radio commands. Close other software using COM6, power "
            "cycle the radio, and retry."
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
        message = (
            "No response from the BF-F8HP-PRO. Confirm that the radio label "
            "includes PRO. The older BF-F8HP is a different model and uses "
            "the separate Baofeng BF-F8HP entry. For the PRO, fully insert "
            "the two-pin programming cable, turn the radio on to a normal "
            "channel, close the Baofeng CPS, and keep COM4 selected. "
            "NewChirp currently supports the PRO protocol through firmware "
            "v0.52; if the radio has newer firmware, include the firmware "
            "version shown on the radio in the support report."
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
    trace = RADIO_TRACE.format()
    if trace:
        message += RADIO_TRACE_MARKER + trace
    return message


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
    directory.import_drivers()
    _allow_driver_specific_modes()
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
        directory.enable_reregistrations()
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
    return radio


def memory_with_extras(radio, number):
    """Load a channel plus CHIRP's metadata-backed fields such as comments."""
    memory = radio.get_memory(number)
    owner = external_memory_owner(radio)
    if owner is not None:
        memory = owner.get_memory_extra(memory)
    return memory


def set_memory_with_extras(radio, memory):
    """Write a channel and persist fields CHIRP stores outside radio memory."""
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
        value = change.get("value")
        if isinstance(element.value, RadioSettingValueList):
            for option in element.value.get_options():
                if option == value:
                    break
                if str(option) == str(value):
                    value = option
                    break
        try:
            element.value = value
        except Exception as exc:
            label = element.get_shortname() or element.get_name()
            raise RuntimeError(
                "Radio setting %r rejected value %r: %s"
                % (label, value, exc)
            ) from exc


def apply_json(radio, mem, item):
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
        set_mem(target, item[source])
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
            setting.value = extra_values[setting.get_name()]
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


def open_serial(radio_class, port):
    import serial

    software_flow = getattr(radio_class, "XON_XOFF", False)
    if "://" in port:
        handle = serial.serial_for_url(port, do_not_open=True)
        handle.timeout = 0.25
        handle.rtscts = radio_class.HARDWARE_FLOW
        handle.xonxoff = software_flow
        handle.rts = radio_class.WANTS_RTS
        handle.dtr = radio_class.WANTS_DTR
        handle.open()
        handle.baudrate = radio_class.BAUD_RATE
    else:
        # Configure baud and modem-control lines before opening the device.
        # This mirrors CHIRP's clone dialog and avoids a pulse at the radio.
        handle = serial.Serial(
            baudrate=radio_class.BAUD_RATE,
            rtscts=radio_class.HARDWARE_FLOW,
            xonxoff=software_flow,
            timeout=0.25,
        )
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
    from chirp import chirp_common
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
            for number in range(start, end + 1):
                memory = self.get_memory(number)
                if memory.empty:
                    self._live_radio.erase_memory(number)
                else:
                    self._live_radio.set_memory(memory)
                if self.status_fn:
                    status = chirp_common.Status()
                    status.cur = number
                    status.max = end
                    status.msg = "Writing to radio"
                    self.status_fn(status)

        def get_settings(self):
            return self._live_radio.get_settings()

        def set_settings(self, settings):
            return self._live_radio.set_settings(settings)

    return HeadlessLiveAdapter(live_radio)


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
    else:
        handle = TracedSerial(open_serial(radio_class, port), RADIO_TRACE)
    try:
        if detect_serial and transport_kind != "scsi_rap":
            try:
                radio_class = radio_class.detect_from_serial(handle)
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


def emit_read_ready(radio):
    """Tell the user when a manual PTT-triggered clone read can begin."""
    prompts = radio.get_prompts()
    pre_download = getattr(prompts, "pre_download", "") or ""
    if "[PTT]" in pre_download:
        emit_progress(MANUAL_READ_READY_MESSAGE, 0.01)
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


def repeaterbook_resource_name(service, country, state):
    country = str(country).strip()
    state = str(state).strip()
    if country not in ("United States", "Canada", "Mexico"):
        state = "all"
    service = (
        "gmrs"
        if country == "United States" and str(service).lower() == "gmrs"
        else ""
    )
    country_key = str(country).strip().lower().replace(" ", "_")
    state_key = str(state).strip().lower().replace(" ", "_")
    return "rb%s-%s-%s.json" % (service, country_key, state_key)


def repeaterbook_cache_path(resource):
    cache_dir = os.path.join(tempfile.gettempdir(), "newchirp-repeaterbook")
    os.makedirs(cache_dir, exist_ok=True)
    return os.path.join(cache_dir, resource)


def fetch_repeaterbook_data(service, country, state):
    """Fetch RepeaterBook's CHIRP-compatible compressed database."""
    resource = repeaterbook_resource_name(service, country, state)
    cache_path = repeaterbook_cache_path(resource)
    cache_age = (
        time.time() - os.path.getmtime(cache_path)
        if os.path.exists(cache_path)
        else None
    )
    if cache_age is not None and cache_age < 30 * 86400:
        with open(cache_path, encoding="utf-8") as handle:
            return json.load(handle)

    emit_progress("Downloading RepeaterBook data...", 0.08)
    url = "https://data.chirpmyradio.com/rb/%s.xz" % resource
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "CHIRP/py3dev Python %s %s"
            % (".".join(str(part) for part in sys.version_info[:3]), sys.platform)
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            compressed = response.read()
        payload = lzma.decompress(compressed)
        data = json.loads(payload)
        with open(cache_path + ".tmp", "wb") as handle:
            handle.write(json.dumps(data).encode("utf-8"))
        os.replace(cache_path + ".tmp", cache_path)
        return data
    except Exception as exc:
        if os.path.exists(cache_path):
            emit_progress("Using cached RepeaterBook data.", 0.12)
            with open(cache_path, encoding="utf-8") as handle:
                return json.load(handle)
        raise RuntimeError(
            "Could not download RepeaterBook data for %s, %s: %s"
            % (state, country, exc)
        ) from exc


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
    query = normalize_repeaterbook_query(query)
    has_origin = latitude is not None and longitude is not None
    matches = []
    requested_services = (
        ("amateur", "gmrs") if service == "all" else (service,)
    )
    for service_name in requested_services:
        data = fetch_repeaterbook_data(service_name, country, state)
        for item in data.get("results", []):
            if not item or item.get("Operational Status") != "On-air":
                continue
            if open_only and item.get("Use") != "OPEN":
                continue
            if query:
                fields = (
                    "County",
                    "State",
                    "Landmark",
                    "Nearest City",
                    "Callsign",
                    "Region",
                    "Notes",
                )
                haystack = " ".join(
                    str(item.get(key) or "") for key in fields
                )
                if query not in haystack.lower():
                    continue
            if fm_only and item.get("FM Analog") != "Yes":
                continue
            item_lat = item.get("Lat")
            item_lon = item.get("Long")
            distance_km = None
            if has_origin and item_lat and item_lon:
                lat1, lon1 = math.radians(latitude), math.radians(longitude)
                lat2, lon2 = math.radians(float(item_lat)), math.radians(
                    float(item_lon)
                )
                value = (
                    math.sin((lat2 - lat1) / 2) ** 2
                    + math.cos(lat1)
                    * math.cos(lat2)
                    * math.sin((lon2 - lon1) / 2) ** 2
                )
                distance_km = 6371 * 2 * math.atan2(
                    math.sqrt(value), math.sqrt(1 - value)
                )
            if distance is not None and distance_km is not None:
                if distance_km > distance:
                    continue
            elif distance is not None:
                continue
            matches.append((distance_km, item, service_name))
    if has_origin:
        matches.sort(
            key=lambda match: (
                match[0] is None,
                match[0] if match[0] is not None else float("inf"),
            )
        )
    results = []
    for index, (distance_km, item, service_name) in enumerate(matches[:limit]):
        try:
            channel = repeaterbook_item_to_channel(item, index + 1)
        except Exception:
            continue
        item_lat = item.get("Lat")
        item_lon = item.get("Long")
        channel["comment"] = channel["comment"].replace(
            "RepeaterBook:",
            "RepeaterBook %s:" % service_name.title(),
            1,
        )
        results.append({
            "channel": channel,
            "callsign": item.get("Callsign") or "",
            "city": item.get("Nearest City") or "",
            "county": item.get("County") or "",
            "state": item.get("State") or item.get("Region") or "",
            "use": item.get("Use") or "",
            "service": "GMRS" if service_name == "gmrs" else "Amateur",
            "latitude": (
                float(item_lat) if item_lat not in (None, "") else None
            ),
            "longitude": (
                float(item_lon) if item_lon not in (None, "") else None
            ),
            "distanceKm": (
                round(distance_km, 1) if distance_km is not None else None
            ),
        })
    return {
        "source": "RepeaterBook",
        "sourceUrl": "https://repeaterbook.com",
        "totalMatches": len(matches),
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
            print(json.dumps({"models": sorted(directory.DRV_TO_RADIO.keys())}))
            return
        if args.command == "list-interfaces":
            try:
                from newchirp_mass_storage import list_devices

                interfaces = list_devices()
            except Exception:
                interfaces = []
            print(json.dumps({"interfaces": interfaces}))
            return
        if args.command == "model-info":
            prompts = directory.get_radio(args.model).get_prompts()
            print(json.dumps({
                "info": prompts.info,
                "experimental": prompts.experimental,
                "preDownload": prompts.pre_download,
                "preUpload": prompts.pre_upload,
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
                "channels": channels,
                "imagePath": image_path,
                "zones": zones,
                "zone": selected_zone,
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
                    emit_progress("Radio settings read.", 1.0)
                    print(json.dumps(payload))
                finally:
                    radio.pipe.close()
            else:
                radio = radio_from_image(directory, args.model, args.image)
                print(json.dumps(settings_payload(radio)))
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
                emit_progress("Read complete.", 1.0)
                print(json.dumps({
                    "channels": channels,
                    "imagePath": image,
                    "zones": zones,
                    "zone": selected_zone,
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
                from chirp import chirp_common
                skipped = []
                adjusted = []
                written = 0
                for index, item in enumerate(items):
                    requested_name = str(item.get("name", ""))
                    filtered_name = channel_radio.filter_name(requested_name)
                    item = dict(item)
                    item["name"] = filtered_name
                    try:
                        mem = channel_radio.get_memory(int(item["location"]))
                    except Exception:
                        mem = chirp_common.Memory()
                    try:
                        locked_fields = apply_json(channel_radio, mem, item)
                        (
                            errors,
                            warnings,
                            normalized_fields,
                            normalization_notes,
                        ) = normalize_upload_memory(channel_radio, mem)
                        if (errors or warnings) and locked_fields:
                            skipped.append({
                                "location": int(item["location"]),
                                "name": filtered_name,
                                "reason": (
                                    "locked field(s): %s left a required "
                                    "value unchanged" % ", ".join(locked_fields)
                                ),
                                "skipped": True,
                            })
                            continue
                        if errors:
                            skipped.append({
                                "location": int(item["location"]),
                                "name": filtered_name,
                                "reason": channel_validation_message(
                                    mem,
                                    errors,
                                    channel_radio.get_features()
                                    .valid_tuning_steps,
                                ),
                                "skipped": True,
                            })
                            continue
                        set_memory_with_extras(channel_radio, mem)
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
                                "location": int(item["location"]),
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
                            "location": int(item["location"]),
                            "name": filtered_name,
                            "reason": str(exc),
                            "skipped": True,
                        })
                    if items and (
                        index % 10 == 0 or index == len(items) - 1
                    ):
                        emit_progress(
                            "Preparing channels...",
                            0.03 + 0.06 * (index + 1) / len(items),
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
                emit_progress("Writing the image to the radio...", 0.10)
                radio.sync_out()
                emit_progress("Saving the updated image...", 0.99)
                radio.save_mmap(args.image)
                emit_progress("Write complete.", 1.0)
                print(json.dumps({
                    "ok": True,
                    "skipped": skipped,
                    "adjusted": adjusted,
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
                changes = payload.get("changes", [])
                apply_setting_changes(settings, changes)
                emit_progress("Applying settings...", 0.10)
                radio.set_settings(settings)
                emit_progress("Writing settings to the radio...", 0.12)
                radio.sync_out()
                emit_progress("Saving the updated image...", 0.99)
                radio.save_mmap(args.image)
                emit_progress("Settings write complete.", 1.0)
                print(json.dumps({"ok": True, "changed": len(changes)}))
        finally:
            radio.pipe.close()
    except Exception as exc:
        print(
            bridge_error_message(
                exc,
                getattr(args, "command", None),
                getattr(args, "model", None),
            ),
            file=sys.stderr,
        )
        raise SystemExit(1)


if __name__ == "__main__":
    main()
