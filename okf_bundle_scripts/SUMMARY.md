---
description: 'Top-level OKF summary: 245 concepts across 12 domains and 12 modules'
git_branch: main
git_repo: newchirp
okf_version: '0.2'
timestamp: '2026-11-28T09:47:29Z'
title: okf_bundle_scripts — Knowledge Summary
type: Index
---

# okf_bundle_scripts — Knowledge Summary

> OKF v0.2 bundle | 245 concepts | 12 domains | 12 modules

## Stats

| Type | Count |
|------|-------|
| Function | 219 |
| Class | 14 |
| Module | 12 |

| Language | Concepts |
|----------|----------|
| python | 245 |

## Domain Map

Use these links to navigate the bundle or prime an AI agent with focused context.

### [build_macos_dmg.py](build_macos_dmg.py/index.md) — 4 concepts

- [build_macos_dmg](build_macos_dmg/index.md) (4 concepts) — Build a styled NewChirp macOS DMG with a drag-to-Applications window.

### [check_linux_release_abi.py](check_linux_release_abi.py/index.md) — 10 concepts

- [check_linux_release_abi](check_linux_release_abi/index.md) (10 concepts) — Reject Linux release payloads built against a newer desktop ABI.

### [check_private_data.py](check_private_data.py/index.md) — 4 concepts

- [check_private_data](check_private_data/index.md) (4 concepts) — Fail when private email addresses or local build paths are tracked.

### [chirp_bridge.py](chirp_bridge.py/index.md) — 92 concepts

- [chirp_bridge](chirp_bridge/index.md) (92 concepts) — Small JSON boundary between NewChirp and the audited CHIRP driver tree.

### [driver_work.py](driver_work.py/index.md) — 32 concepts

- [driver_work](driver_work/index.md) (32 concepts) — Manufacturer/model work ledger for NewChirp radio support.

### [export_radio_catalog.py](export_radio_catalog.py/index.md) — 6 concepts

- [export_radio_catalog](export_radio_catalog/index.md) (6 concepts) — Export the radio model catalog from the pinned CHIRP source.

### [generate_gmrs_frs_pdf.py](generate_gmrs_frs_pdf.py/index.md) — 15 concepts

- [generate_gmrs_frs_pdf](generate_gmrs_frs_pdf/index.md) (15 concepts) — Generate a single-page color PDF for the US FRS/GMRS channel plan.

### [generate_international_frequency_pdfs.py](generate_international_frequency_pdfs.py/index.md) — 5 concepts

- [generate_international_frequency_pdfs](generate_international_frequency_pdfs/index.md) (5 concepts) — Generate one-page international frequency-reference PDFs.

### [generate_repeater_counties.py](generate_repeater_counties.py/index.md) — 6 concepts

- [generate_repeater_counties](generate_repeater_counties/index.md) (6 concepts) — Generate the bundled U.S. county-equivalent list from Census data.

### [newchirp_mass_storage.py](newchirp_mass_storage.py/index.md) — 23 concepts

- [newchirp_mass_storage](newchirp_mass_storage/index.md) (23 concepts) — Reusable raw SCSI transport and RAP framing for NewChirp radios.

### [newchirp_usb_dfu.py](newchirp_usb_dfu.py/index.md) — 27 concepts

- [newchirp_usb_dfu](newchirp_usb_dfu/index.md) (27 concepts) — Minimal libusb DFU transport used by experimental STM32 radios.

### [upstream_review.py](upstream_review.py/index.md) — 21 concepts

- [upstream_review](upstream_review/index.md) (21 concepts) — Review upstream CHIRP changes against NewChirp's pinned commit.

## Key Concepts

Highest-value concepts across all domains (Classes and Functions with rich descriptions).

| Concept | Type | Module | Description |
|---------|------|--------|-------------|
| [preserve_unloadable_settings](/chirp_bridge/preserve_unloadable_settings.md) | Function | `chirp_bridge.py` | Write back settings CHIRP could not load exactly as the radi… |
| [external_memory_owner](/chirp_bridge/external_memory_owner.md) | Function | `chirp_bridge.py` | Return the object that owns metadata for a radio or channel … |
| [live_models_by_vendor](/chirp_bridge/live_models_by_vendor.md) | Function | `chirp_bridge.py` | Return selectable serial/transport radios, excluding file-on… |
| [reported_model_choice](/chirp_bridge/reported_model_choice.md) | Function | `chirp_bridge.py` | Return (vendor, model) when a driver's ID check names a sibl… |
| [set_memory_with_extras](/chirp_bridge/set_memory_with_extras.md) | Function | `chirp_bridge.py` | Write a channel and persist fields CHIRP stores outside radi… |
| [extra_field_doc](/chirp_bridge/extra_field_doc.md) | Function | `chirp_bridge.py` | Return CHIRP's documentation or a concise fallback for commo… |
| [memory_with_extras](/chirp_bridge/memory_with_extras.md) | Function | `chirp_bridge.py` | Load a channel plus CHIRP's metadata-backed fields such as c… |
| [prepare_upload_channels](/chirp_bridge/prepare_upload_channels.md) | Function | `chirp_bridge.py` | Validate and apply imported channels without touching invali… |
| [download_decode_error_message](/chirp_bridge/download_decode_error_message.md) | Function | `chirp_bridge.py` | Explain a post-download map failure without losing the saved… |
| [emit_progress](/chirp_bridge/emit_progress.md) | Function | `chirp_bridge.py` | Send structured transfer progress without touching the JSON … |
| [TracedSerial](/chirp_bridge/TracedSerial.md) | Class | `chirp_bridge.py` | Delegate a serial port while recording sanitized CAT transac… |
| [_allow_driver_specific_modes](/chirp_bridge/allow_driver_specific_modes.md) | Function | `chirp_bridge.py` | Permit declared radio modes rejected by CHIRP's shared memor… |
| [memory_with_new_extras](/chirp_bridge/memory_with_new_extras.md) | Function | `chirp_bridge.py` | Reload a slot after giving it the incoming channel's basic f… |
| [radio_firmware](/chirp_bridge/radio_firmware.md) | Function | `chirp_bridge.py` | Return the best available firmware identity from a radio or … |
| [status_progress](/chirp_bridge/status_progress.md) | Function | `chirp_bridge.py` | Translate a CHIRP Status message into a structured progress … |
| [uvk5_firmware_from_hello](/chirp_bridge/uvk5_firmware_from_hello.md) | Function | `chirp_bridge.py` | Decode the UV-K5 hello reply without trusting non-printable … |
| [verify_live_write](/chirp_bridge/verify_live_write.md) | Function | `chirp_bridge.py` | Read back live memories so a rejected write cannot report su… |
| [apply_mapping_payload](/chirp_bridge/apply_mapping_payload.md) | Function | `chirp_bridge.py` | Apply bank/zone names and memberships to an already loaded i… |
| [fetch_repeaterbook_search](/chirp_bridge/fetch_repeaterbook_search.md) | Function | `chirp_bridge.py` | Query NewChirp's relay without exposing RepeaterBook credent… |
| [live_refusal_message](/chirp_bridge/live_refusal_message.md) | Function | `chirp_bridge.py` | Say which channel a live radio refused and how far the write… |

## Usage with OpenCode

```bash
# Prime full context
RUN cat ./okf_bundle/SUMMARY.md

# Prime specific domain
RUN cat ./okf_bundle/build_macos_dmg.py/index.md

# Find a concept
RUN find ./okf_bundle -name '<ConceptName>.md' | xargs cat
```
