---
description: 'Top-level OKF summary: 239 concepts across 3 domains and 9 modules'
git_branch: HEAD
git_repo: newchirp
okf_version: '0.2'
timestamp: '2026-10-24T18:24:39Z'
title: okf_bundle — Knowledge Summary
type: Index
---

# okf_bundle — Knowledge Summary

> OKF v0.2 bundle | 239 concepts | 3 domains | 9 modules

## Stats

| Type | Count |
|------|-------|
| Function | 186 |
| Class | 44 |
| Module | 9 |

| Language | Concepts |
|----------|----------|
| dart | 239 |

## Domain Map

Use these links to navigate the bundle or prime an AI agent with focused context.

### [main.dart](main.dart/index.md) — 144 concepts

- [main](main/index.md) (144 concepts)

### [models](models/index.md) — 9 concepts

- [models/radio_channel](models/radio_channel/index.md) (9 concepts)

### [services](services/index.md) — 86 concepts

- [services/radio_bridge](services/radio_bridge/index.md) (36 concepts)
- [services/update_checker](services/update_checker/index.md) (15 concepts)
- [services/chirp_csv](services/chirp_csv/index.md) (10 concepts)
- [services/window_state_store](services/window_state_store/index.md) (7 concepts)
- [services/column_layout_store](services/column_layout_store/index.md) (6 concepts)
- [services/radio_image_store](services/radio_image_store/index.md) (6 concepts)
- [services/radio_selection_store](services/radio_selection_store/index.md) (6 concepts)

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
