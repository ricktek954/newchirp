---
description: 'Top-level OKF summary: 474 concepts across 4 domains and 22 modules'
git_branch: main
git_repo: newchirp
okf_version: '0.2'
timestamp: '2026-10-29T12:07:27Z'
title: okf_bundle — Knowledge Summary
type: Index
---

# okf_bundle — Knowledge Summary

> OKF v0.2 bundle | 474 concepts | 4 domains | 22 modules

## Stats

| Type | Count |
|------|-------|
| Function | 372 |
| Class | 74 |
| Module | 22 |
| Enum | 6 |

| Language | Concepts |
|----------|----------|
| dart | 474 |

## Domain Map

Use these links to navigate the bundle or prime an AI agent with focused context.

### [main.dart](main.dart/index.md) — 186 concepts

- [main](main/index.md) (186 concepts)

### [models](models/index.md) — 70 concepts

- [models/radio_channel](models/radio_channel/index.md) (37 concepts)
- [models/gm32_channel](models/gm32_channel/index.md) (15 concepts)
- [models/channel_image_baseline](models/channel_image_baseline/index.md) (11 concepts)
- [models/repeater_search](models/repeater_search/index.md) (7 concepts)

### [services](services/index.md) — 186 concepts

- [services/radio_bridge](services/radio_bridge/index.md) (46 concepts)
- [services/module_sandbox](services/module_sandbox/index.md) (35 concepts)
- [services/mototrbo_cps2_xml](services/mototrbo_cps2_xml/index.md) (17 concepts)
- [services/update_checker](services/update_checker/index.md) (17 concepts)
- [services/diagnostic_log](services/diagnostic_log/index.md) (14 concepts)
- [services/update_installer](services/update_installer/index.md) (11 concepts)
- [services/chirp_csv](services/chirp_csv/index.md) (10 concepts)
- [services/radio_image_store](services/radio_image_store/index.md) (8 concepts)
- *…and 5 more modules*

### [widgets](widgets/index.md) — 32 concepts

- [widgets/radio_model_picker](widgets/radio_model_picker/index.md) (17 concepts)
- [widgets/error_report_dialog](widgets/error_report_dialog/index.md) (7 concepts)
- [widgets/file_save_warning_dialog](widgets/file_save_warning_dialog/index.md) (5 concepts)
- [widgets/channel_library_image_bar](widgets/channel_library_image_bar/index.md) (3 concepts)

## Key Concepts

Highest-value concepts across all domains (Classes and Functions with rich descriptions).

| Concept | Type | Module | Description |
|---------|------|--------|-------------|
| [isAllowedDownloadUrl](/services/update_checker/isAllowedDownloadUrl.md) | Function | `services/update_checker.dart` | True when [url] is an https link on newchirp.net, with no lo… |
| [ChannelLibraryStatsCache](/models/channel_image_baseline/ChannelLibraryStatsCache.md) | Class | `models/channel_image_baseline.dart` | Remembers the last library snapshot so search and row select… |
| [trustedUpdateArtifactUrl](/services/update_checker/trustedUpdateArtifactUrl.md) | Function | `services/update_checker.dart` | Validated installer URL for [platform], or null when it is n… |
| [MototrboCps2Xml](/services/mototrbo_cps2_xml/MototrboCps2Xml.md) | Class | `services/mototrbo_cps2_xml.dart` | Read-only importer for conventional channels copied from MOT… |
| [trustedDownloadUrl](/services/update_checker/trustedDownloadUrl.md) | Function | `services/update_checker.dart` | Address the Update button may open. Untrusted links use the … |
| [UpdateInstaller](/services/update_installer/UpdateInstaller.md) | Class | `services/update_installer.dart` | Downloads a direct NewChirp installer and starts the native … |
| [_resolvePython](/services/radio_bridge/resolvePython.md) | Function | `services/radio_bridge.dart` | The bundled CHIRP tree uses Python 3.10+ syntax, so prefer a… |
| [ChannelLibraryImageBar](/widgets/channel_library_image_bar/ChannelLibraryImageBar.md) | Class | `widgets/channel_library_image_bar.dart` | Bottom bar on the Channel Library, matching the Radio settin… |
| [ChannelImageBaseline](/models/channel_image_baseline/ChannelImageBaseline.md) | Class | `models/channel_image_baseline.dart` | Fingerprint of the channel list last read from, imported fro… |
| [midlandReceiveChannelIsUnset](/models/radio_channel/midlandReceiveChannelIsUnset.md) | Function | `models/radio_channel.dart` | A new row has no receive channel yet. 146.52 MHz is the old … |
| [install](/services/update_installer/install.md) | Function | `services/update_installer.dart` | Starts the detached native helper that will install after th… |
| [_windowsSerialPortNames](/services/radio_bridge/windowsSerialPortNames.md) | Function | `services/radio_bridge.dart` | Windows: read the live COM ports from the SERIALCOMM registr… |
| [UpdateCheckResult](/services/update_checker/UpdateCheckResult.md) | Class | `services/update_checker.dart` | Outcome of comparing the installed NewChirp version against … |
| [gmrsChannelForHz](/models/radio_channel/gmrsChannelForHz.md) | Function | `models/radio_channel.dart` | GMRS channel 1-22 for a receive frequency, or null when it i… |
| [showsMidlandChannelNumbers](/models/radio_channel/showsMidlandChannelNumbers.md) | Function | `models/radio_channel.dart` | This radio's list uses Midland's channel numbers instead of … |
| [restorePlainMidlandRepeater](/models/radio_channel/restorePlainMidlandRepeater.md) | Function | `models/radio_channel.dart` | Puts the standard GMRS repeater back in this row and clears … |
| [isHidden](/services/file_save_warning_store/isHidden.md) | Function | `services/file_save_warning_store.dart` | True only when the person checked "Do not show me this messa… |
| [DownloadedUpdate](/services/update_installer/DownloadedUpdate.md) | Class | `services/update_installer.dart` | A downloaded installer ready for the platform-specific updat… |
| [midlandReceiveGmrsChannel](/models/radio_channel/midlandReceiveGmrsChannel.md) | Function | `models/radio_channel.dart` | GMRS channel shown for this row. Fixed rows use the slot. Ot… |
| [moduleSandboxRefusal](/services/module_sandbox/moduleSandboxRefusal.md) | Function | `services/module_sandbox.dart` | A message when this operating system cannot sandbox a module… |

## Usage with OpenCode

```bash
# Prime full context
RUN cat ./okf_bundle/SUMMARY.md

# Prime specific domain
RUN cat ./okf_bundle/main.dart/index.md

# Find a concept
RUN find ./okf_bundle -name '<ConceptName>.md' | xargs cat
```
