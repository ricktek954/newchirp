---
description: 'Top-level OKF summary: 1170 concepts across 5 domains and 39 modules'
git_branch: main
git_repo: newchirp
okf_version: '0.2'
timestamp: '2026-11-28T10:36:31Z'
title: okf_bundle — Knowledge Summary
type: Index
---

# okf_bundle — Knowledge Summary

> OKF v0.2 bundle | 1,170 concepts | 5 domains | 39 modules

## Stats

| Type | Count |
|------|-------|
| Function | 1,014 |
| Class | 107 |
| Module | 39 |
| Enum | 10 |

| Language | Concepts |
|----------|----------|
| dart | 1,170 |

## Domain Map

Use these links to navigate the bundle or prime an AI agent with focused context.

### [l10n](l10n/index.md) — 475 concepts

- [l10n/app_localizations](l10n/app_localizations/index.md) (123 concepts)
- [l10n/app_localizations_en](l10n/app_localizations_en/index.md) (117 concepts)
- [l10n/app_localizations_es](l10n/app_localizations_es/index.md) (117 concepts)
- [l10n/app_localizations_fr](l10n/app_localizations_fr/index.md) (117 concepts)
- [l10n/l10n](l10n/l10n/index.md) (1 concepts)

### [main.dart](main.dart/index.md) — 255 concepts

- [main](main/index.md) (255 concepts)

### [models](models/index.md) — 113 concepts

- [models/radio_channel](models/radio_channel/index.md) (45 concepts)
- [models/gm32_channel](models/gm32_channel/index.md) (15 concepts)
- [models/channel_image_baseline](models/channel_image_baseline/index.md) (12 concepts)
- [models/radio_mapping](models/radio_mapping/index.md) (12 concepts)
- [models/frequency_reference](models/frequency_reference/index.md) (9 concepts)
- [models/marine_channels](models/marine_channels/index.md) (7 concepts)
- [models/repeater_search](models/repeater_search/index.md) (7 concepts)
- [models/repeater_regions](models/repeater_regions/index.md) (5 concepts)
- *…and 1 more modules*

### [services](services/index.md) — 262 concepts

- [services/radio_bridge](services/radio_bridge/index.md) (57 concepts)
- [services/module_sandbox](services/module_sandbox/index.md) (36 concepts)
- [services/mygmrs_client](services/mygmrs_client/index.md) (22 concepts)
- [services/chirp_csv](services/chirp_csv/index.md) (17 concepts)
- [services/mototrbo_cps2_xml](services/mototrbo_cps2_xml/index.md) (17 concepts)
- [services/update_checker](services/update_checker/index.md) (17 concepts)
- [services/diagnostic_log](services/diagnostic_log/index.md) (15 concepts)
- [services/channel_list_pdf](services/channel_list_pdf/index.md) (14 concepts)
- *…and 10 more modules*

### [widgets](widgets/index.md) — 65 concepts

- [widgets/radio_model_picker](widgets/radio_model_picker/index.md) (29 concepts)
- [widgets/radio_mapping_dialog](widgets/radio_mapping_dialog/index.md) (15 concepts)
- [widgets/error_report_dialog](widgets/error_report_dialog/index.md) (8 concepts)
- [widgets/file_save_warning_dialog](widgets/file_save_warning_dialog/index.md) (5 concepts)
- [widgets/marine_template_dialog](widgets/marine_template_dialog/index.md) (5 concepts)
- [widgets/channel_library_image_bar](widgets/channel_library_image_bar/index.md) (3 concepts)

## Key Concepts

Highest-value concepts across all domains (Classes and Functions with rich descriptions).

| Concept | Type | Module | Description |
|---------|------|--------|-------------|
| [_installLinuxUpdate](/services/update_installer/installLinuxUpdate.md) | Function | `services/update_installer.dart` | Installs the downloaded .deb/.rpm/etc. through a small helpe… |
| [toString](/services/update_installer/toString.md) | Function | `services/update_installer.dart` | Installs the downloaded .deb/.rpm/etc. through a small helpe… |
| [buildReport](/services/diagnostic_log/buildReport.md) | Function | `services/diagnostic_log.dart` | Text of recent entries for a bug report, newest last, cut to… |
| [_channelFromDefinition](/models/marine_channels/channelFromDefinition.md) | Function | `models/marine_channels.dart` | One marine channel as a radio channel. Receive-only channels… |
| [submit](/services/diagnostic_log/submit.md) | Function | `services/diagnostic_log.dart` | Sends a bug report (with the diagnostic log and, optionally,… |
| [saveForModel](/services/radio_image_store/saveForModel.md) | Function | `services/radio_image_store.dart` | Copies a radio image into the app's image folder as the mode… |
| [_standardCbRows](/models/frequency_reference/standardCbRows.md) | Function | `models/frequency_reference.dart` | US/international 40-channel CB (26.965-27.405 MHz; the list … |
| [_australianUhfNote](/models/frequency_reference/australianUhfNote.md) | Function | `models/frequency_reference.dart` | Usage note for an Australian UHF CB channel (repeater output… |
| [repeaterCountiesForRegion](/models/repeater_regions/repeaterCountiesForRegion.md) | Function | `models/repeater_regions.dart` | Counties to offer for [region]: the built-in list plus any c… |
| [currentUpdatePlatform](/services/update_checker/currentUpdatePlatform.md) | Function | `services/update_checker.dart` | Platform name used by the release API: windows, macos, linux… |
| [normalizeRepeaterCounty](/models/repeater_regions/normalizeRepeaterCounty.md) | Function | `models/repeater_regions.dart` | County name without suffixes like " County" or " census area… |
| [check](/services/update_checker/check.md) | Function | `services/update_checker.dart` | Asks the website for this platform's latest release and comp… |
| [_settingsMessage](/main/settingsMessage.md) | Function | `main.dart` | Centered icon, title, text and optional button for the setti… |
| [load](/services/app_language/load.md) | Function | `services/app_language.dart` | Reads the saved choice; returns "system" when nothing is sav… |
| [_postJson](/services/mygmrs_client/postJson.md) | Function | `services/mygmrs_client.dart` | POSTs [payload] as JSON to the website and returns the JSON … |
| [_remapLocations](/models/radio_mapping/remapLocations.md) | Function | `models/radio_mapping.dart` | Applies [locations] to a list of channel numbers, dropping d… |
| [load](/services/column_layout_store/load.md) | Function | `services/column_layout_store.dart` | Reads the saved channel-table column order and widths; null … |
| [_loadChirpModule](/main/loadChirpModule.md) | Function | `main.dart` | Loads a user-supplied CHIRP driver module (after a warning),… |
| [copy](/models/radio_channel/copy.md) | Function | `models/radio_channel.dart` | The 22 standard GMRS channels as a starter list (repeater ch… |
| [gmrsStarterChannels](/models/radio_channel/gmrsStarterChannels.md) | Function | `models/radio_channel.dart` | The 22 standard GMRS channels as a starter list (repeater ch… |

## Usage with OpenCode

```bash
# Prime full context
RUN cat ./okf_bundle/SUMMARY.md

# Prime specific domain
RUN cat ./okf_bundle/l10n/index.md

# Find a concept
RUN find ./okf_bundle -name '<ConceptName>.md' | xargs cat
```
