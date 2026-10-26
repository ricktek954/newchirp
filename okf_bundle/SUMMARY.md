---
description: 'Top-level OKF summary: 287 concepts across 4 domains and 11 modules'
git_branch: main
git_repo: newchirp
okf_version: '0.2'
timestamp: '2026-10-26T07:01:40Z'
title: okf_bundle — Knowledge Summary
type: Index
---

# okf_bundle — Knowledge Summary

> OKF v0.2 bundle | 287 concepts | 4 domains | 11 modules

## Stats

| Type | Count |
|------|-------|
| Function | 223 |
| Class | 52 |
| Module | 11 |
| Enum | 1 |

| Language | Concepts |
|----------|----------|
| dart | 287 |

## Domain Map

Use these links to navigate the bundle or prime an AI agent with focused context.

### [main.dart](main.dart/index.md) — 159 concepts

- [main](main/index.md) (159 concepts)

### [models](models/index.md) — 16 concepts

- [models/radio_channel](models/radio_channel/index.md) (9 concepts)
- [models/repeater_search](models/repeater_search/index.md) (7 concepts)

### [services](services/index.md) — 95 concepts

- [services/radio_bridge](services/radio_bridge/index.md) (45 concepts)
- [services/update_checker](services/update_checker/index.md) (15 concepts)
- [services/chirp_csv](services/chirp_csv/index.md) (10 concepts)
- [services/window_state_store](services/window_state_store/index.md) (7 concepts)
- [services/column_layout_store](services/column_layout_store/index.md) (6 concepts)
- [services/radio_image_store](services/radio_image_store/index.md) (6 concepts)
- [services/radio_selection_store](services/radio_selection_store/index.md) (6 concepts)

### [widgets](widgets/index.md) — 17 concepts

- [widgets/radio_model_picker](widgets/radio_model_picker/index.md) (17 concepts)

## Key Concepts

Highest-value concepts across all domains (Classes and Functions with rich descriptions).

| Concept | Type | Module | Description |
|---------|------|--------|-------------|
| [isAllowedDownloadUrl](/services/update_checker/isAllowedDownloadUrl.md) | Function | `services/update_checker.dart` | True when [url] is an https link on newchirp.net, with no lo… |
| [trustedDownloadUrl](/services/update_checker/trustedDownloadUrl.md) | Function | `services/update_checker.dart` | Address the Update button may open. Untrusted links use the … |
| [_resolvePython](/services/radio_bridge/resolvePython.md) | Function | `services/radio_bridge.dart` | The bundled CHIRP tree uses Python 3.10+ syntax, so prefer a… |
| [_windowsSerialPortNames](/services/radio_bridge/windowsSerialPortNames.md) | Function | `services/radio_bridge.dart` | Windows: read the live COM ports from the SERIALCOMM registr… |
| [UpdateCheckResult](/services/update_checker/UpdateCheckResult.md) | Class | `services/update_checker.dart` | Outcome of comparing the installed NewChirp version against … |
| [compareVersions](/services/update_checker/compareVersions.md) | Function | `services/update_checker.dart` | Compares two dotted version strings, ignoring any `+build` m… |
| [check](/services/update_checker/check.md) | Function | `services/update_checker.dart` | Opens a newchirp.net download page in the default browser. |
| [openExternalUrl](/services/update_checker/openExternalUrl.md) | Function | `services/update_checker.dart` | Opens a newchirp.net download page in the default browser. |
| [_parseManifest](/services/update_checker/parseManifest.md) | Function | `services/update_checker.dart` | Opens a newchirp.net download page in the default browser. |
| [toString](/services/update_checker/toString.md) | Function | `services/update_checker.dart` | Opens a newchirp.net download page in the default browser. |

## Usage with OpenCode

```bash
# Prime full context
RUN cat ./okf_bundle/SUMMARY.md

# Prime specific domain
RUN cat ./okf_bundle/main.dart/index.md

# Find a concept
RUN find ./okf_bundle -name '<ConceptName>.md' | xargs cat
```
