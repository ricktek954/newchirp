---
okf_version: "0.2"
type: Function
title: __exit__
resource: chirp_bridge.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:chirp_bridge.py"
  - "git:branch:fix/email-triage-20261030"
  - "git:repo:newchirp"
timestamp: "2026-10-30T23:31:36Z"
concept_id: chirp_bridge/exit
language: python
---

# __exit__

## Signature

```python
def __exit__(self, exc_type, exc_value, traceback)
```

## Parameters

| Name | Type | Default |
|------|------|---------|
| `self` | `—` | `—` |

| `exc_type` | `—` | `—` |

| `exc_value` | `—` | `—` |

| `traceback` | `—` | `—` |

## Source
Lines 228–229 in `chirp_bridge.py`

## Relationships

| Type | Target |
|------|--------|
| related | [TracedSerial](/chirp_bridge/TracedSerial.md) |
| calls | [close](/chirp_bridge/close.md) |
