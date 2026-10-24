#!/usr/bin/env python3
"""Small JSON boundary between NewChirp and the audited CHIRP driver tree."""
import argparse
import builtins
import glob
import importlib.machinery
import importlib.util
import json
import os
import re
import sys
import tempfile
PROGRESS_PREFIX = "__NEWCHIRP_PROGRESS__ "
MANUAL_READ_READY_MESSAGE = (
    "Listening for the radio - hold PTT for one second."
)

# CHIRP normally redirects stdout and stderr to ~/.chirp/debug.log when it is
# launched without a terminal. The bridge owns those streams as its JSON/error
# protocol, so keep them attached to the parent process.
os.environ.setdefault("CHIRP_TESTENV", "1")


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
    if (
        command in ("download", "read-settings")
        and model == "Yaesu_FT-60"
        and "no response from radio" in message.lower()
    ):
        return (
            "No response from the FT-60. Leave the radio on its F8 CLONE "
            "screen, read again, and hold PTT only after the transfer window "
            'says "%s"' % MANUAL_READ_READY_MESSAGE
        )
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
    try:
        spec.loader.exec_module(module)
    except Exception as exc:
        sys.modules.pop(module_name, None)
        raise RuntimeError(
            "Could not load CHIRP module %s: %s"
            % (os.path.basename(module_path), exc)
        ) from exc


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
    if module_path:
        _load_module(os.path.abspath(module_path), directory)
    if newchirp_driver_dir and os.path.isdir(newchirp_driver_dir):
        for driver_path in sorted(
            glob.glob(os.path.join(newchirp_driver_dir, "*.py"))
        ):
            module_name = os.path.splitext(os.path.basename(driver_path))[0]
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
            "kind": kind,
            "value": current,
            "choices": choices,
            "mutable": is_mutable,
        })
    return fields


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
    from chirp.settings import RadioSetting

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
        element.value = change.get("value")


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


def open_serial(radio_class, port):
    import serial

    if "://" in port:
        handle = serial.serial_for_url(port, do_not_open=True)
        handle.timeout = 0.25
        handle.rtscts = radio_class.HARDWARE_FLOW
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


def radio_for(
    directory,
    model,
    port,
    progress_range=(0.0, 1.0),
    image=None,
    detect_serial=True,
):
    radio_class = directory.get_radio(model)
    if image is not None:
        # Writes must use the exact class recorded in the image. The driver's
        # sync_out() owns its programming-mode handshake, like CHIRP's upload
        # dialog, so probing first would make strict drivers handshake twice.
        try:
            radio_class = directory.get_radio_by_image(image).__class__
        except Exception:
            pass
    handle = open_serial(radio_class, port)
    try:
        if detect_serial:
            try:
                radio_class = radio_class.detect_from_serial(handle)
            except NotImplementedError:
                pass
        radio = radio_class(handle)
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
    if "[PTT]" in (getattr(prompts, "pre_download", "") or ""):
        emit_progress(MANUAL_READ_READY_MESSAGE, 0.01)
    else:
        emit_progress("Connecting to radio...", 0.01)


def radio_from_image(directory, model, image):
    """Build a driver instance backed only by a saved radio image."""
    radio = directory.get_radio(model)(None)
    radio.load_mmap(image)
    return radio


def channel_context(radio, zone=None):
    """Return the selected channel owner plus available radio zones."""
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


def settings_payload(radio):
    settings = radio.get_settings()
    return {
        "hasSettings": bool(
            getattr(radio.get_features(), "has_settings", False)
        ),
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
    model_info = sub.add_parser("model-info")
    model_info.add_argument("--model", required=True)
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
        if args.command == "model-info":
            prompts = directory.get_radio(args.model).get_prompts()
            print(json.dumps({
                "info": prompts.info,
                "experimental": prompts.experimental,
                "preDownload": prompts.pre_download,
                "preUpload": prompts.pre_upload,
            }))
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
                    mem = channel_radio.get_memory(location)
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
                    mem = channel_radio.get_memory(location)
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
                        errors = channel_radio.validate_memory(mem)
                        if errors:
                            if locked_fields:
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
                            raise RuntimeError(
                                f"Channel {mem.number}: {errors[0]}")
                        channel_radio.set_memory(mem)
                        if locked_fields or filtered_name != requested_name:
                            adjusted.append({
                                "location": int(item["location"]),
                                "name": filtered_name,
                                "fields": locked_fields,
                                "nameFrom": requested_name,
                                "nameTo": filtered_name,
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
                cleared = [
                    int(part) for part in args.cleared.split(",") if part.strip()
                ]
                for location in cleared:
                    try:
                        mem = channel_radio.get_memory(location)
                        mem.empty = True
                        channel_radio.set_memory(mem)
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
                radio.load_mmap(args.image)
                with open(args.settings, encoding="utf-8") as handle:
                    payload = json.load(handle)
                settings = radio.get_settings()
                if settings is None:
                    raise RuntimeError(
                        "This radio does not expose global settings."
                    )
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
            bridge_error_message(exc, args.command, args.model),
            file=sys.stderr,
        )
        raise SystemExit(1)


if __name__ == "__main__":
    main()
