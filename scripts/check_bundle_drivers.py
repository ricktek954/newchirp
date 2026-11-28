"""Release gate: NewChirp drivers in a built app take precedence over CHIRP's.

Run it with the app's own bundled Python against the built app's resource
folder (the one that contains chirp/ and newchirp_drivers/), for example:

  APP/Contents/Resources/python-arm64/bin/python3.13 -I -B \\
      scripts/check_bundle_drivers.py \\
      --resources APP/Contents/Resources \\
      --bridge APP/Contents/Frameworks/App.framework/Resources/flutter_assets/scripts/chirp_bridge.py \\
      --vendor .../flutter_assets/assets/python/pyserial-3.5-py2.py3-none-any.whl \\
      --expect-drivers drivers

It fails when a newchirp_*.py file sits inside CHIRP's chirp/drivers, when
newchirp_drivers/ is missing or differs from --expect-drivers, or when any
driver ID that a NewChirp driver registers resolves to an upstream driver.
"""

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path


def _digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resources", type=Path, required=True)
    parser.add_argument("--bridge", type=Path, required=True)
    parser.add_argument("--vendor", type=Path, required=True)
    parser.add_argument("--expect-drivers", type=Path)
    args = parser.parse_args()

    problems = []
    chirp_drivers = args.resources / "chirp" / "drivers"
    ours = args.resources / "newchirp_drivers"
    mixed = sorted(path.name for path in chirp_drivers.glob("newchirp_*.py"))
    if mixed:
        problems.append(
            "NewChirp drivers inside chirp/drivers: %s" % ", ".join(mixed))
    if not ours.is_dir():
        problems.append("newchirp_drivers/ is missing")
    elif args.expect_drivers:
        expected = {path.name: _digest(path)
                    for path in args.expect_drivers.glob("*.py")}
        bundled = {path.name: _digest(path) for path in ours.glob("*.py")}
        missing = sorted(set(expected) - set(bundled))
        extra = sorted(set(bundled) - set(expected))
        changed = sorted(name for name in set(expected) & set(bundled)
                         if expected[name] != bundled[name])
        for label, names in (("missing", missing), ("unexpected", extra),
                             ("different from source", changed)):
            if names:
                problems.append("newchirp_drivers %s: %s"
                                % (label, ", ".join(names)))

    spec = importlib.util.spec_from_file_location(
        "newchirp_bundle_bridge", args.bridge)
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    directory = bridge.load_chirp(
        str(args.resources), str(args.vendor),
        str(ours) if ours.is_dir() else None)

    owned = {}
    for radio_class, ident in directory.RADIO_TO_DRV.items():
        if bridge._is_newchirp_driver(radio_class):
            owned[ident] = radio_class
    lost = sorted(
        "%s -> %s" % (ident, directory.DRV_TO_RADIO[ident].__module__)
        for ident in owned
        if not bridge._is_newchirp_driver(directory.DRV_TO_RADIO[ident]))
    if lost:
        problems.append("upstream drivers win: %s" % "; ".join(lost))

    models = bridge.live_models_by_vendor(directory)
    report = {
        "ok": not problems,
        "newchirpDriverIds": len(owned),
        "models": sum(len(items) for items in models.values()),
        "vendors": len(models),
        "problems": problems,
    }
    print(json.dumps(report, indent=2))
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
