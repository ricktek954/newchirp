---
description: 'Top-level OKF summary: 50 concepts across 3 domains and 3 modules'
git_branch: main
git_repo: newchirp
okf_version: '0.2'
timestamp: '2026-10-25T00:47:09Z'
title: okf_bundle_scripts — Knowledge Summary
type: Index
---

# okf_bundle_scripts — Knowledge Summary

> OKF v0.2 bundle | 50 concepts | 3 domains | 3 modules

## Stats

| Type | Count |
|------|-------|
| Function | 46 |
| Module | 3 |
| Class | 1 |

| Language | Concepts |
|----------|----------|
| python | 50 |

## Domain Map

Use these links to navigate the bundle or prime an AI agent with focused context.

### [build_macos_dmg.py](build_macos_dmg.py/index.md) — 4 concepts

- [build_macos_dmg](build_macos_dmg/index.md) (4 concepts) — Build a styled NewChirp macOS DMG with a drag-to-Applications window.

### [chirp_bridge.py](chirp_bridge.py/index.md) — 31 concepts

- [chirp_bridge](chirp_bridge/index.md) (31 concepts) — Small JSON boundary between NewChirp and the audited CHIRP driver tree.

### [generate_gmrs_frs_pdf.py](generate_gmrs_frs_pdf.py/index.md) — 15 concepts

- [generate_gmrs_frs_pdf](generate_gmrs_frs_pdf/index.md) (15 concepts) — Generate a single-page color PDF for the US FRS/GMRS channel plan.

## Key Concepts

Highest-value concepts across all domains (Classes and Functions with rich descriptions).

| Concept | Type | Module | Description |
|---------|------|--------|-------------|
| [extra_field_doc](/chirp_bridge/extra_field_doc.md) | Function | `chirp_bridge.py` | Return CHIRP's documentation or a concise fallback for commo… |
| [emit_progress](/chirp_bridge/emit_progress.md) | Function | `chirp_bridge.py` | Send structured transfer progress without touching the JSON … |
| [status_progress](/chirp_bridge/status_progress.md) | Function | `chirp_bridge.py` | Translate a CHIRP Status message into a structured progress … |
| [bridge_error_message](/chirp_bridge/bridge_error_message.md) | Function | `chirp_bridge.py` | Add safe, command-specific recovery guidance to bridge failu… |
| [headless_live_adapter](/chirp_bridge/headless_live_adapter.md) | Function | `chirp_bridge.py` | Give a live radio the file-backed interfaces NewChirp requir… |
| [emit_read_ready](/chirp_bridge/emit_read_ready.md) | Function | `chirp_bridge.py` | Tell the user when a manual PTT-triggered clone read can beg… |
| [channel_context](/chirp_bridge/channel_context.md) | Function | `chirp_bridge.py` | Return the selected channel owner plus available radio zones… |
| [normalize_repeaterbook_query](/chirp_bridge/normalize_repeaterbook_query.md) | Function | `chirp_bridge.py` | Treat location words like "Broward County" as a county name. |
| [radio_from_image](/chirp_bridge/radio_from_image.md) | Function | `chirp_bridge.py` | Build a driver instance backed only by a saved radio image. |
| [fetch_repeaterbook_data](/chirp_bridge/fetch_repeaterbook_data.md) | Function | `chirp_bridge.py` | Fetch RepeaterBook's CHIRP-compatible compressed database. |
| [channel_radio_for](/chirp_bridge/channel_radio_for.md) | Function | `chirp_bridge.py` | Return the radio object that owns channel memories. |

## Usage with OpenCode

```bash
# Prime full context
RUN cat ./okf_bundle/SUMMARY.md

# Prime specific domain
RUN cat ./okf_bundle/build_macos_dmg.py/index.md

# Find a concept
RUN find ./okf_bundle -name '<ConceptName>.md' | xargs cat
```
