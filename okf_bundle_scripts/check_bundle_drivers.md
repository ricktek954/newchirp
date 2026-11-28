---
okf_version: "0.2"
type: Module
title: check_bundle_drivers
description: "Release gate: NewChirp drivers in a built app take precedence over CHIRP's."
resource: check_bundle_drivers.py
tags:
  - "lang:python"
  - "type:Module"
  - "module:check_bundle_drivers.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-28T11:25:53Z"
concept_id: check_bundle_drivers
language: python
---

# check_bundle_drivers

Release gate: NewChirp drivers in a built app take precedence over CHIRP's.

## Docstring

Release gate: NewChirp drivers in a built app take precedence over CHIRP's.

Run it with the app's own bundled Python against the built app's resource
folder (the one that contains chirp/ and newchirp_drivers/), for example:

  APP/Contents/Resources/python-arm64/bin/python3.13 -I -B \
      scripts/check_bundle_drivers.py \
      --resources APP/Contents/Resources \
      --bridge APP/Contents/Frameworks/App.framework/Resources/flutter_assets/scripts/chirp_bridge.py \
      --vendor .../flutter_assets/assets/python/pyserial-3.5-py2.py3-none-any.whl \
      --expect-drivers drivers

It fails when a newchirp_*.py file sits inside CHIRP's chirp/drivers, when
newchirp_drivers/ is missing or differs from --expect-drivers, or when any
driver ID that a NewChirp driver registers resolves to an upstream driver.

## Relationships

| Type | Target |
|------|--------|
| related | [_digest](/check_bundle_drivers/digest.md) |
| related | [main](/check_bundle_drivers/main.md) |
