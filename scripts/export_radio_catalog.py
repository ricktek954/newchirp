"""Export the radio model catalog from the pinned CHIRP source.

The website's radio list is built from this file instead of CHIRP's wiki, so
it lists exactly the radios that NewChirp's pinned CHIRP code can program.
"""

import argparse
import builtins
import json
import logging
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parent.parent
PIN_FILE = ROOT / "scripts/chirp-source.pin"


def pinned_commit():
    text = PIN_FILE.read_text(encoding="utf-8")
    match = re.search(r"^commit ([0-9a-f]{40})$", text, re.MULTILINE)
    if not match:
        raise SystemExit("scripts/chirp-source.pin has no commit line")
    return match.group(1)


def _yaml_scalar(text):
    text = text.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "'\"":
        return text[1:-1]
    return text


def load_alias_map(source):
    path = source / "chirp/share/model_alias_map.yaml"
    entries = []
    vendor = None
    alias = None

    def finish():
        if alias is None:
            return
        if "model" not in alias or "alt" not in alias:
            raise SystemExit("%s: incomplete alias %r" % (path, alias))
        entries.append((
            vendor,
            "%s (%suse %s)" % (
                alias["model"], alias.get("variant", ""), alias["alt"]),
        ))

    for number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        field = re.fullmatch(r"(- |  )(alt|model|variant): (.*)", line)
        if field:
            if field.group(1) == "- ":
                finish()
                alias = {}
            if vendor is None or alias is None:
                raise SystemExit("%s:%i: alias outside a vendor" % (
                    path, number))
            alias[field.group(2)] = _yaml_scalar(field.group(3))
            continue
        heading = re.fullmatch(r"([^\s#-][^:]*):", line)
        if heading:
            finish()
            alias = None
            vendor = _yaml_scalar(heading.group(1))
            continue
        raise SystemExit("%s:%i: unexpected line %r" % (path, number, line))
    finish()
    return entries


def collect(source):
    for wheel in sorted((ROOT / "assets/python").glob("*.whl")):
        sys.path.insert(0, str(wheel))
    sys.path.insert(0, str(source))
    if not hasattr(builtins, "_"):
        builtins._ = str
    from chirp import directory

    logging.disable(logging.CRITICAL)
    directory.import_drivers()
    logging.disable(logging.NOTSET)

    from chirp import chirp_common

    vendors = {}

    def add(vendor, model, untested=False):
        models = vendors.setdefault(str(vendor).strip(), {})
        model = str(model).strip()
        models[model] = models.get(model, True) and untested

    untested_ids = {
        line.strip()
        for line in (source / "tests/py3-untested-drivers.txt").read_text(
            encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    }

    for identifier, radio_class in directory.DRV_TO_RADIO.items():
        if (
            issubclass(radio_class, chirp_common.FileBackedRadio)
            and not issubclass(radio_class, chirp_common.CloneModeRadio)
        ):
            continue
        untested = identifier in untested_ids
        add(radio_class.VENDOR, radio_class.MODEL, untested)
        for alias in getattr(radio_class, "ALIASES", []):
            add(alias.VENDOR, alias.MODEL, untested)
    for vendor, model in load_alias_map(source):
        add(vendor, model)
    return [
        {
            "name": name,
            "models": sorted(
                ("%s *" % model if untested else model
                 for model, untested in models.items()),
            ),
        }
        for name, models in sorted(vendors.items())
    ]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        help="Extracted CHIRP tree (default: build_support/chirp-<pin>)",
    )
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    commit = pinned_commit()
    source = args.source or ROOT / ("build_support/chirp-%s" % commit)
    if not (source / "chirp/directory.py").is_file():
        raise SystemExit(
            "Pinned CHIRP source not found at %s; run scripts/update_chirp.sh"
            % source
        )
    vendors = collect(source.resolve())
    payload = {
        "generatedBy": "scripts/export_radio_catalog.py (NewChirp desktop)",
        "chirpCommit": commit,
        "totalModels": sum(len(vendor["models"]) for vendor in vendors),
        "vendors": vendors,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print("Wrote %i models across %i brands from CHIRP %s to %s" % (
        payload["totalModels"], len(vendors), commit[:12], args.out))


if __name__ == "__main__":
    main()
