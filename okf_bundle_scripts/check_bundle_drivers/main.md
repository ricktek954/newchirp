---
okf_version: "0.2"
type: Function
title: main
resource: check_bundle_drivers.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:check_bundle_drivers.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-28T11:25:53Z"
concept_id: check_bundle_drivers/main
language: python
---

# main

## Signature

```python
def main()
```

## Source
Lines 30–90 in `check_bundle_drivers.py`

## Relationships

| Type | Target |
|------|--------|
| related | [check_bundle_drivers](/check_bundle_drivers.md) |
| calls | [parse_args](/check_linux_release_abi/parse_args.md) |
| calls | [load_chirp](/chirp_bridge/load_chirp.md) |
| calls | [live_models_by_vendor](/chirp_bridge/live_models_by_vendor.md) |
| calls | [_is_newchirp_driver](/chirp_bridge/is_newchirp_driver.md) |
| calls | [_digest](/check_bundle_drivers/digest.md) |
