# chirp_bridge

## Classs

- [RadioCommunicationTrace](RadioCommunicationTrace.md) — Keep a bounded, privacy-safe view of recent serial exchanges.
- [TracedSerial](TracedSerial.md) — Delegate a serial port while recording sanitized CAT transactions.

## Functions

- [__enter__](enter.md)
- [__exit__](exit.md)
- [__getattr__](getattr.md)
- [__init__](init.md)
- [__setattr__](setattr.md)
- [_command_summary](command_summary.md)
- [_finish_pending](finish_pending.md)
- [_load_module](load_module.md)
- [apply_json](apply_json.md)
- [apply_setting_changes](apply_setting_changes.md)
- [begin](begin.md)
- [bridge_error_message](bridge_error_message.md) — Add safe, command-specific recovery guidance to bridge failures.
- [channel_context](channel_context.md) — Return the selected channel owner plus available radio zones.
- [channel_radio_for](channel_radio_for.md) — Return the radio object that owns channel memories.
- [channel_validation_message](channel_validation_message.md) — Add a frequency suggestion to CHIRP's unsupported-step error.
- [close](close.md)
- [emit_progress](emit_progress.md) — Send structured transfer progress without touching the JSON stdout.
- [emit_read_ready](emit_read_ready.md) — Tell the user when a manual PTT-triggered clone read can begin.
- [erase_memory_with_extras](erase_memory_with_extras.md) — Erase a channel and remove its metadata-backed fields.
- [external_memory_owner](external_memory_owner.md) — Return the object that owns metadata for a radio or channel subdevice.
- [extra_field_doc](extra_field_doc.md) — Return CHIRP's documentation or a concise fallback for common terms.
- [extra_fields_json](extra_fields_json.md)
- [features_json](features_json.md)
- [fetch_repeaterbook_data](fetch_repeaterbook_data.md) — Fetch RepeaterBook's CHIRP-compatible compressed database.
- [format](format.md)
- [has_global_settings](has_global_settings.md)
- [headless_live_adapter](headless_live_adapter.md) — Give a live radio the file-backed interfaces NewChirp requires.
- [live_channel_context](live_channel_context.md) — Choose a live-radio subdevice without probing every memory slot.
- [load_chirp](load_chirp.md)
- [main](main.md)
- [memory_json](memory_json.md)
- [memory_with_extras](memory_with_extras.md) — Load a channel plus CHIRP's metadata-backed fields such as comments.
- [nearest_programmable_frequency](nearest_programmable_frequency.md) — Return the closest frequency representable by one of the steps.
- [normalize_repeaterbook_query](normalize_repeaterbook_query.md) — Treat location words like "Broward County" as a county name.
- [normalize_upload_memory](normalize_upload_memory.md) — Apply safe coercions advertised by CHIRP validation warnings.
- [open_serial](open_serial.md)
- [radio_for](radio_for.md)
- [radio_from_image](radio_from_image.md) — Build a driver instance backed only by a saved radio image.
- [read](read.md)
- [readline](readline.md)
- [readlines](readlines.md)
- [received](received.md)
- [repeaterbook_cache_path](repeaterbook_cache_path.md)
- [repeaterbook_item_to_channel](repeaterbook_item_to_channel.md)
- [repeaterbook_resource_name](repeaterbook_resource_name.md)
- [repeaterbook_tone](repeaterbook_tone.md)
- [search_repeaterbook](search_repeaterbook.md)
- [set_memory_with_extras](set_memory_with_extras.md) — Write a channel and persist fields CHIRP stores outside radio memory.
- [setting_doc](setting_doc.md)
- [setting_value_json](setting_value_json.md)
- [settings_payload](settings_payload.md)
- [settings_tree_json](settings_tree_json.md)
- [status_progress](status_progress.md) — Translate a CHIRP Status message into a structured progress event.
- [write](write.md)
