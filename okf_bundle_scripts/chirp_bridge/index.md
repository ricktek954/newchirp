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
- [close](close.md)
- [emit_progress](emit_progress.md) — Send structured transfer progress without touching the JSON stdout.
- [emit_read_ready](emit_read_ready.md) — Tell the user when a manual PTT-triggered clone read can begin.
- [extra_field_doc](extra_field_doc.md) — Return CHIRP's documentation or a concise fallback for common terms.
- [extra_fields_json](extra_fields_json.md)
- [features_json](features_json.md)
- [fetch_repeaterbook_data](fetch_repeaterbook_data.md) — Fetch RepeaterBook's CHIRP-compatible compressed database.
- [format](format.md)
- [has_global_settings](has_global_settings.md)
- [headless_live_adapter](headless_live_adapter.md) — Give a live radio the file-backed interfaces NewChirp requires.
- [load_chirp](load_chirp.md)
- [main](main.md)
- [memory_json](memory_json.md)
- [normalize_repeaterbook_query](normalize_repeaterbook_query.md) — Treat location words like "Broward County" as a county name.
- [open_serial](open_serial.md)
- [radio_for](radio_for.md)
- [radio_from_image](radio_from_image.md) — Build a driver instance backed only by a saved radio image.
- [read](read.md)
- [received](received.md)
- [repeaterbook_cache_path](repeaterbook_cache_path.md)
- [repeaterbook_item_to_channel](repeaterbook_item_to_channel.md)
- [repeaterbook_resource_name](repeaterbook_resource_name.md)
- [repeaterbook_tone](repeaterbook_tone.md)
- [search_repeaterbook](search_repeaterbook.md)
- [setting_doc](setting_doc.md)
- [setting_value_json](setting_value_json.md)
- [settings_payload](settings_payload.md)
- [settings_tree_json](settings_tree_json.md)
- [status_progress](status_progress.md) — Translate a CHIRP Status message into a structured progress event.
- [write](write.md)
