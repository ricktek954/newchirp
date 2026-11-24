---
okf_version: "0.2"
type: Function
title: preserve_unloadable_settings
description: Write back settings CHIRP could not load exactly as the radio had them.
resource: chirp_bridge.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:chirp_bridge.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-24T19:23:42Z"
concept_id: chirp_bridge/preserve_unloadable_settings
language: python
---

# preserve_unloadable_settings

Write back settings CHIRP could not load exactly as the radio had them.

## Signature

```python
def preserve_unloadable_settings(settings)
```

## Docstring

Write back settings CHIRP could not load exactly as the radio had them.

A driver's range can be narrower than what a radio really stores, for
example a UV-5R factory squelch calibration of 124 against CHIRP's 0-123.
CHIRP logs "Failed to load ...", leaves the value unset, and the driver's
set_settings then fails on int(None), so no setting can be written
(2026-11-20 UV-5R report, mailbox INBOX:833). The app shows such a value
as unsupported and never changes it. Restore the radio's own stored value
without validation and mark it read-only so drivers that honour
mutability skip it; either way the radio's bytes stay unchanged.
Returns the names of preserved settings.

## Parameters

| Name | Type | Default |
|------|------|---------|
| `settings` | `—` | `—` |

## Source
Lines 1606–1642 in `chirp_bridge.py`

## Relationships

| Type | Target |
|------|--------|
| related | [chirp_bridge](/chirp_bridge.md) |
| called_by | [main](/chirp_bridge/main.md) |
