---
description: 'Top-level OKF summary: 93 concepts across 4 domains and 4 modules'
git_branch: main
git_repo: newchirp
okf_version: '0.2'
timestamp: '2026-10-29T11:04:50Z'
title: okf_bundle_scripts — Knowledge Summary
type: Index
---

# okf_bundle_scripts — Knowledge Summary

> OKF v0.2 bundle | 93 concepts | 4 domains | 4 modules

## Stats

| Type | Count |
|------|-------|
| Function | 79 |
| Class | 10 |
| Module | 4 |

| Language | Concepts |
|----------|----------|
| python | 93 |

## Domain Map

Use these links to navigate the bundle or prime an AI agent with focused context.

### [build_macos_dmg.py](build_macos_dmg.py/index.md) — 4 concepts

- [build_macos_dmg](build_macos_dmg/index.md) (4 concepts) — Build a styled NewChirp macOS DMG with a drag-to-Applications window.

### [chirp_bridge.py](chirp_bridge.py/index.md) — 54 concepts

- [chirp_bridge](chirp_bridge/index.md) (54 concepts) — Small JSON boundary between NewChirp and the audited CHIRP driver tree.

### [generate_gmrs_frs_pdf.py](generate_gmrs_frs_pdf.py/index.md) — 15 concepts

- [generate_gmrs_frs_pdf](generate_gmrs_frs_pdf/index.md) (15 concepts) — Generate a single-page color PDF for the US FRS/GMRS channel plan.

### [newchirp_mass_storage.py](newchirp_mass_storage.py/index.md) — 20 concepts

- [newchirp_mass_storage](newchirp_mass_storage/index.md) (20 concepts) — Reusable raw SCSI transport and RAP framing for NewChirp radios.

## Key Concepts

Highest-value concepts across all domains (Classes and Functions with rich descriptions).

| Concept | Type | Module | Description |
|---------|------|--------|-------------|
| [external_memory_owner](/chirp_bridge/external_memory_owner.md) | Function | `chirp_bridge.py` | Return the object that owns metadata for a radio or channel … |
| [set_memory_with_extras](/chirp_bridge/set_memory_with_extras.md) | Function | `chirp_bridge.py` | Write a channel and persist fields CHIRP stores outside radi… |
| [memory_with_extras](/chirp_bridge/memory_with_extras.md) | Function | `chirp_bridge.py` | Load a channel plus CHIRP's metadata-backed fields such as c… |
| [extra_field_doc](/chirp_bridge/extra_field_doc.md) | Function | `chirp_bridge.py` | Return CHIRP's documentation or a concise fallback for commo… |
| [emit_progress](/chirp_bridge/emit_progress.md) | Function | `chirp_bridge.py` | Send structured transfer progress without touching the JSON … |
| [status_progress](/chirp_bridge/status_progress.md) | Function | `chirp_bridge.py` | Translate a CHIRP Status message into a structured progress … |
| [TracedSerial](/chirp_bridge/TracedSerial.md) | Class | `chirp_bridge.py` | Delegate a serial port while recording sanitized CAT transac… |
| [bridge_error_message](/chirp_bridge/bridge_error_message.md) | Function | `chirp_bridge.py` | Add safe, command-specific recovery guidance to bridge failu… |
| [live_channel_context](/chirp_bridge/live_channel_context.md) | Function | `chirp_bridge.py` | Choose a live-radio subdevice without probing every memory s… |
| [nearest_programmable_frequency](/chirp_bridge/nearest_programmable_frequency.md) | Function | `chirp_bridge.py` | Return the closest frequency representable by one of the ste… |
| [headless_live_adapter](/chirp_bridge/headless_live_adapter.md) | Function | `chirp_bridge.py` | Give a live radio the file-backed interfaces NewChirp requir… |
| [emit_read_ready](/chirp_bridge/emit_read_ready.md) | Function | `chirp_bridge.py` | Tell the user when a manual PTT-triggered clone read can beg… |
| [channel_validation_message](/chirp_bridge/channel_validation_message.md) | Function | `chirp_bridge.py` | Add a frequency suggestion to CHIRP's unsupported-step error… |
| [channel_context](/chirp_bridge/channel_context.md) | Function | `chirp_bridge.py` | Return the selected channel owner plus available radio zones… |
| [RadioCommunicationTrace](/chirp_bridge/RadioCommunicationTrace.md) | Class | `chirp_bridge.py` | Keep a bounded, privacy-safe view of recent serial exchanges… |
| [normalize_repeaterbook_query](/chirp_bridge/normalize_repeaterbook_query.md) | Function | `chirp_bridge.py` | Treat location words like "Broward County" as a county name. |
| [RapMassStorageRadio](/newchirp_mass_storage/RapMassStorageRadio.md) | Class | `newchirp_mass_storage.py` | Generic command-response session over a raw SCSI transport. |
| [radio_from_image](/chirp_bridge/radio_from_image.md) | Function | `chirp_bridge.py` | Build a driver instance backed only by a saved radio image. |
| [ScsiPassthrough](/newchirp_mass_storage/ScsiPassthrough.md) | Class | `newchirp_mass_storage.py` | Reusable factory for platform-specific raw SCSI transport. |
| [fetch_repeaterbook_data](/chirp_bridge/fetch_repeaterbook_data.md) | Function | `chirp_bridge.py` | Fetch RepeaterBook's CHIRP-compatible compressed database. |

## Usage with OpenCode

```bash
# Prime full context
RUN cat ./okf_bundle/SUMMARY.md

# Prime specific domain
RUN cat ./okf_bundle/build_macos_dmg.py/index.md

# Find a concept
RUN find ./okf_bundle -name '<ConceptName>.md' | xargs cat
```
