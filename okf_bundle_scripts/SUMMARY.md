---
description: 'Top-level OKF summary: 39 concepts across 3 domains and 3 modules'
git_branch: main
git_repo: newchirp
okf_version: '0.2'
timestamp: '2026-10-24T18:37:52Z'
title: okf_bundle_scripts — Knowledge Summary
type: Index
---

# okf_bundle_scripts — Knowledge Summary

> OKF v0.2 bundle | 39 concepts | 3 domains | 3 modules

## Stats

| Type | Count |
|------|-------|
| Function | 35 |
| Module | 3 |
| Class | 1 |

| Language | Concepts |
|----------|----------|
| python | 39 |

## Domain Map

Use these links to navigate the bundle or prime an AI agent with focused context.

### [build_macos_dmg.py](build_macos_dmg.py/index.md) — 4 concepts

- [build_macos_dmg](build_macos_dmg/index.md) (4 concepts) — Build a styled NewChirp macOS DMG with a drag-to-Applications window.

### [chirp_bridge.py](chirp_bridge.py/index.md) — 20 concepts

- [chirp_bridge](chirp_bridge/index.md) (20 concepts) — Small JSON boundary between NewChirp and the audited CHIRP driver tree.

### [generate_gmrs_frs_pdf.py](generate_gmrs_frs_pdf.py/index.md) — 15 concepts

- [generate_gmrs_frs_pdf](generate_gmrs_frs_pdf/index.md) (15 concepts) — Generate a single-page color PDF for the US FRS/GMRS channel plan.

## Key Concepts

Highest-value concepts across all domains (Classes and Functions with rich descriptions).

| Concept | Type | Module | Description |
|---------|------|--------|-------------|
| [emit_progress](/chirp_bridge/emit_progress.md) | Function | `chirp_bridge.py` | Send structured transfer progress without touching the JSON … |
| [status_progress](/chirp_bridge/status_progress.md) | Function | `chirp_bridge.py` | Translate a CHIRP Status message into a structured progress … |
| [channel_context](/chirp_bridge/channel_context.md) | Function | `chirp_bridge.py` | Return the selected channel owner plus available radio zones… |
| [radio_from_image](/chirp_bridge/radio_from_image.md) | Function | `chirp_bridge.py` | Build a driver instance backed only by a saved radio image. |
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
