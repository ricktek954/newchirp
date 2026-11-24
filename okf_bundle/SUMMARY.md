---
description: 'Top-level OKF summary: 1155 concepts across 5 domains and 39 modules'
git_branch: main
git_repo: newchirp
okf_version: '0.2'
timestamp: '2026-11-24T13:54:22Z'
title: okf_bundle — Knowledge Summary
type: Index
---

# okf_bundle — Knowledge Summary

> OKF v0.2 bundle | 1,155 concepts | 5 domains | 39 modules

## Stats

| Type | Count |
|------|-------|
| Function | 1,000 |
| Class | 106 |
| Module | 39 |
| Enum | 10 |

| Language | Concepts |
|----------|----------|
| dart | 1,155 |

## Domain Map

Use these links to navigate the bundle or prime an AI agent with focused context.

### [l10n](l10n/index.md) — 467 concepts

- [l10n/app_localizations](l10n/app_localizations/index.md) (121 concepts)
- [l10n/app_localizations_en](l10n/app_localizations_en/index.md) (115 concepts)
- [l10n/app_localizations_es](l10n/app_localizations_es/index.md) (115 concepts)
- [l10n/app_localizations_fr](l10n/app_localizations_fr/index.md) (115 concepts)
- [l10n/l10n](l10n/l10n/index.md) (1 concepts)

### [main.dart](main.dart/index.md) — 253 concepts

- [main](main/index.md) (253 concepts)

### [models](models/index.md) — 112 concepts

- [models/radio_channel](models/radio_channel/index.md) (45 concepts)
- [models/gm32_channel](models/gm32_channel/index.md) (15 concepts)
- [models/channel_image_baseline](models/channel_image_baseline/index.md) (12 concepts)
- [models/radio_mapping](models/radio_mapping/index.md) (12 concepts)
- [models/frequency_reference](models/frequency_reference/index.md) (8 concepts)
- [models/marine_channels](models/marine_channels/index.md) (7 concepts)
- [models/repeater_search](models/repeater_search/index.md) (7 concepts)
- [models/repeater_regions](models/repeater_regions/index.md) (5 concepts)
- *…and 1 more modules*

### [services](services/index.md) — 259 concepts

- [services/radio_bridge](services/radio_bridge/index.md) (55 concepts)
- [services/module_sandbox](services/module_sandbox/index.md) (36 concepts)
- [services/mygmrs_client](services/mygmrs_client/index.md) (22 concepts)
- [services/chirp_csv](services/chirp_csv/index.md) (17 concepts)
- [services/mototrbo_cps2_xml](services/mototrbo_cps2_xml/index.md) (17 concepts)
- [services/update_checker](services/update_checker/index.md) (17 concepts)
- [services/channel_list_pdf](services/channel_list_pdf/index.md) (14 concepts)
- [services/diagnostic_log](services/diagnostic_log/index.md) (14 concepts)
- *…and 10 more modules*

### [widgets](widgets/index.md) — 64 concepts

- [widgets/radio_model_picker](widgets/radio_model_picker/index.md) (29 concepts)
- [widgets/radio_mapping_dialog](widgets/radio_mapping_dialog/index.md) (15 concepts)
- [widgets/error_report_dialog](widgets/error_report_dialog/index.md) (7 concepts)
- [widgets/file_save_warning_dialog](widgets/file_save_warning_dialog/index.md) (5 concepts)
- [widgets/marine_template_dialog](widgets/marine_template_dialog/index.md) (5 concepts)
- [widgets/channel_library_image_bar](widgets/channel_library_image_bar/index.md) (3 concepts)

## Key Concepts

Highest-value concepts across all domains (Classes and Functions with rich descriptions).

| Concept | Type | Module | Description |
|---------|------|--------|-------------|
| [ChannelLibraryStatsCache](/models/channel_image_baseline/ChannelLibraryStatsCache.md) | Class | `models/channel_image_baseline.dart` | Remembers the last library snapshot so search and row select… |
| [isAllowedDownloadUrl](/services/update_checker/isAllowedDownloadUrl.md) | Function | `services/update_checker.dart` | True when [url] is an https link on newchirp.net, with no lo… |
| [trustedUpdateArtifactUrl](/services/update_checker/trustedUpdateArtifactUrl.md) | Function | `services/update_checker.dart` | Validated installer URL for [platform], or null when it is n… |
| [uiTheDestinationRangeThroughContainsChannels](/l10n/app_localizations/uiTheDestinationRangeThroughContainsChannels.md) | Function | `l10n/app_localizations.dart` | No description provided for @uiTheDestinationRangeThroughCon… |
| [MototrboCps2Xml](/services/mototrbo_cps2_xml/MototrboCps2Xml.md) | Class | `services/mototrbo_cps2_xml.dart` | Read-only importer for conventional channels copied from MOT… |
| [trustedDownloadUrl](/services/update_checker/trustedDownloadUrl.md) | Function | `services/update_checker.dart` | Address the Update button may open. Untrusted links use the … |
| [UpdateInstaller](/services/update_installer/UpdateInstaller.md) | Class | `services/update_installer.dart` | Downloads a direct NewChirp installer and starts the native … |
| [uiReferenceSourceVerifyCurrentNationalRules](/l10n/app_localizations/uiReferenceSourceVerifyCurrentNationalRules.md) | Function | `l10n/app_localizations.dart` | No description provided for @uiReferenceSourceVerifyCurrentN… |
| [ChannelImageBaseline](/models/channel_image_baseline/ChannelImageBaseline.md) | Class | `models/channel_image_baseline.dart` | Fingerprint of the channel list last read from, imported fro… |
| [_resolvePython](/services/radio_bridge/resolvePython.md) | Function | `services/radio_bridge.dart` | The bundled CHIRP tree uses Python 3.10+ syntax, so prefer a… |
| [ChannelLibraryImageBar](/widgets/channel_library_image_bar/ChannelLibraryImageBar.md) | Class | `widgets/channel_library_image_bar.dart` | Bottom bar on the Channel Library, matching the Radio settin… |
| [clearedLocationsForUpload](/models/channel_image_baseline/clearedLocationsForUpload.md) | Function | `models/channel_image_baseline.dart` | All radio locations that must be blank for the current libra… |
| [midlandReceiveChannelIsUnset](/models/radio_channel/midlandReceiveChannelIsUnset.md) | Function | `models/radio_channel.dart` | A new row has no receive channel yet. 146.52 MHz is the old … |
| [receiveOnlyWriteNote](/models/radio_channel/receiveOnlyWriteNote.md) | Function | `models/radio_channel.dart` | Write-confirmation note naming the receive-only channels, or… |
| [radioMappingsSignature](/models/radio_mapping/radioMappingsSignature.md) | Function | `models/radio_mapping.dart` | Fixed (non-editable) zone models are derived from channel nu… |
| [install](/services/update_installer/install.md) | Function | `services/update_installer.dart` | Starts the detached native helper that will install after th… |
| [uiNoMatchingRepeatersWereFoundCoordinates](/l10n/app_localizations/uiNoMatchingRepeatersWereFoundCoordinates.md) | Function | `l10n/app_localizations.dart` | No description provided for @uiNoMatchingRepeatersWereFoundC… |
| [_windowsSerialPortNames](/services/radio_bridge/windowsSerialPortNames.md) | Function | `services/radio_bridge.dart` | Windows: read the live COM ports from the SERIALCOMM registr… |
| [UpdateCheckResult](/services/update_checker/UpdateCheckResult.md) | Class | `services/update_checker.dart` | Outcome of comparing the installed NewChirp version against … |
| [gmrsChannelForHz](/models/radio_channel/gmrsChannelForHz.md) | Function | `models/radio_channel.dart` | GMRS channel 1-22 for a receive frequency, or null when it i… |

## Usage with OpenCode

```bash
# Prime full context
RUN cat ./okf_bundle/SUMMARY.md

# Prime specific domain
RUN cat ./okf_bundle/l10n/index.md

# Find a concept
RUN find ./okf_bundle -name '<ConceptName>.md' | xargs cat
```
