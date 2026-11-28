"""Review upstream CHIRP changes against NewChirp's pinned commit.

Prepares the target commit in build_support/chirp-review-<commit> (with
NewChirp's source patches), compares it with the pinned tree, lists new and
removed radios, flags changed upstream modules that NewChirp drivers patch or
extend, runs the offline test suites against the target, and writes a
Markdown report. It never changes scripts/chirp-source.pin.
"""

import argparse
import datetime
import difflib
import filecmp
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request


ROOT = Path(__file__).resolve().parent.parent
PIN_FILE = ROOT / "scripts/chirp-source.pin"
UPSTREAM = "https://github.com/kk7ds/chirp"
COMPARE_API = "https://api.github.com/repos/kk7ds/chirp/compare/%s...%s"
FLUTTER_CANDIDATES = (
    os.environ.get("NEWCHIRP_FLUTTER", ""),
    shutil.which("flutter") or "",
    "/Volumes/RICKEXT/flutter/bin/flutter",
)


def pinned():
    text = PIN_FILE.read_text(encoding="utf-8")
    commit = re.search(r"^commit ([0-9a-f]{40})$", text, re.MULTILINE)
    digest = re.search(r"^sha256 ([0-9a-f]{64})$", text, re.MULTILINE)
    if not commit or not digest:
        raise SystemExit("scripts/chirp-source.pin is missing commit/sha256")
    return commit.group(1), digest.group(1)


def resolve_target(ref):
    if re.fullmatch(r"[0-9a-f]{40}", ref):
        return ref
    output = subprocess.run(
        ["git", "ls-remote", UPSTREAM, ref],
        check=True, capture_output=True, text=True, timeout=120,
    ).stdout.split()
    if not output or not re.fullmatch(r"[0-9a-f]{40}", output[0]):
        raise SystemExit("Could not resolve upstream ref %r" % ref)
    return output[0]


def prepare_tree(commit):
    env = dict(os.environ, NEWCHIRP_CHIRP_REVIEW_COMMIT=commit)
    result = subprocess.run(
        ["bash", str(ROOT / "scripts/update_chirp.sh")],
        env=env, capture_output=True, text=True, timeout=900,
    )
    if result.returncode != 0:
        raise SystemExit("update_chirp.sh review mode failed:\n%s"
                         % result.stderr)
    path = Path(result.stdout.strip().splitlines()[-1])
    digest = re.search(r"CHIRP archive sha256 ([0-9a-f]{64})", result.stderr)
    warnings = [line for line in result.stderr.splitlines()
                if line.startswith("warning:")]
    return path, digest.group(1) if digest else "", warnings


def pinned_tree(commit):
    path = ROOT / ("build_support/chirp-%s" % commit)
    if not (path / "chirp/directory.py").is_file():
        subprocess.run(["bash", str(ROOT / "scripts/update_chirp.sh")],
                       check=True, capture_output=True, timeout=900)
    return path


def upstream_commits(base, target):
    request = urllib.request.Request(
        COMPARE_API % (base, target),
        headers={"Accept": "application/vnd.github+json",
                 "User-Agent": "newchirp-upstream-review"},
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            data = json.load(response)
    except Exception as exc:
        return None, str(exc)
    commits = [
        {
            "sha": item["sha"],
            "date": item["commit"]["committer"]["date"][:10],
            "author": (item.get("author") or {}).get("login")
            or item["commit"]["author"]["name"],
            "title": item["commit"]["message"].splitlines()[0],
            "message": item["commit"]["message"],
        }
        for item in data.get("commits", [])
    ]
    return {"total": data.get("total_commits", len(commits)),
            "commits": commits}, ""


def changed_files(old_root, new_root):
    def files(root):
        base = root / "chirp"
        return {
            str(path.relative_to(root))
            for path in base.rglob("*")
            if path.is_file() and "__pycache__" not in path.parts
            and path.suffix != ".pyc"
        }

    old_files = files(old_root)
    new_files = files(new_root)
    added = sorted(new_files - old_files)
    removed = sorted(old_files - new_files)
    modified = []
    for name in sorted(old_files & new_files):
        if not filecmp.cmp(old_root / name, new_root / name, shallow=False):
            modified.append(name)
    return added, removed, modified


def line_delta(old_path, new_path):
    def lines(path):
        try:
            return path.read_text(encoding="utf-8", errors="replace").splitlines()
        except FileNotFoundError:
            return []

    plus = minus = 0
    for line in difflib.unified_diff(lines(old_path), lines(new_path),
                                     lineterm="", n=0):
        if line.startswith("+") and not line.startswith("+++"):
            plus += 1
        elif line.startswith("-") and not line.startswith("---"):
            minus += 1
    return plus, minus


def export_catalog(source, out):
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/export_radio_catalog.py"),
         "--source", str(source), "--out", str(out)],
        check=True, capture_output=True, timeout=600,
    )
    data = json.loads(out.read_text(encoding="utf-8"))
    return {
        (vendor["name"], model)
        for vendor in data["vendors"] for model in vendor["models"]
    }


def newchirp_references():
    sources = sorted((ROOT / "drivers").glob("*.py"))
    sources += [ROOT / "scripts/chirp_bridge.py"]
    sources += sorted((ROOT / "scripts").glob("newchirp_*.py"))
    texts = {path: path.read_text(encoding="utf-8", errors="replace")
             for path in sources}
    return texts


def module_users(module, texts):
    patterns = (
        re.compile(r"from\s+chirp\.drivers\s+import\s+[^\n]*\b%s\b"
                   % re.escape(module)),
        re.compile(r"chirp\.drivers\.%s\b" % re.escape(module)),
        re.compile(r"from\s+chirp\s+import\s+[^\n]*\b%s\b"
                   % re.escape(module)),
        re.compile(r"\bchirp\.%s\b" % re.escape(module)),
    )
    users = []
    for path, text in texts.items():
        if any(pattern.search(text) for pattern in patterns):
            users.append(str(path.relative_to(ROOT)))
    return users


def run_python_tests(source):
    env = dict(os.environ, NEWCHIRP_CHIRP_SOURCE=str(source))
    results = []
    for path in sorted((ROOT / "test").glob("*_test.py")):
        try:
            result = subprocess.run(
                [sys.executable, str(path)], cwd=ROOT, env=env,
                capture_output=True, text=True, timeout=900,
            )
            ok = result.returncode == 0
            tail = "\n".join((result.stdout + result.stderr)
                             .strip().splitlines()[-25:])
        except subprocess.TimeoutExpired:
            ok, tail = False, "timed out after 900 s"
        results.append((str(path.relative_to(ROOT)), ok, tail))
    return results


def flutter_binary():
    for candidate in FLUTTER_CANDIDATES:
        if candidate and Path(candidate).is_file():
            return candidate
    return None


def run_dart_tests(source):
    flutter = flutter_binary()
    if not flutter:
        return None
    files = sorted(
        str(path.relative_to(ROOT))
        for path in (ROOT / "test").glob("*_test.dart")
        if "chirp_test_source" in path.read_text(encoding="utf-8")
    )
    if not files:
        return []
    env = dict(os.environ, NEWCHIRP_CHIRP_SOURCE=str(source))
    results = []
    for name in files:
        try:
            result = subprocess.run(
                [flutter, "test", name], cwd=ROOT, env=env,
                capture_output=True, text=True, timeout=1800,
            )
            ok = result.returncode == 0
            tail = "\n".join((result.stdout + result.stderr)
                             .strip().splitlines()[-25:])
        except subprocess.TimeoutExpired:
            ok, tail = False, "timed out after 1800 s"
        results.append((name, ok, tail))
    return results


def module_name(path):
    name = Path(path).stem
    return name


def mentions(commits, module):
    prefix = re.compile(r"^\s*([\w./-]+(?:\s*,\s*[\w./-]+)*)\s*:")
    word = re.compile(r"\b%s\b" % re.escape(module), re.IGNORECASE)
    hits = []
    for commit in commits:
        match = prefix.match(commit["title"])
        subjects = match.group(1) if match else ""
        if word.search(subjects):
            hits.append(commit)
    return hits


def _family(model):
    text = re.sub(r"[^0-9a-z]", "", model.lower().replace(" *", ""))
    return re.sub(r"[a-z]$", "", text) if re.search(r"\d[a-z]$", text) else text


def newchirp_models():
    models = {}
    pattern = re.compile(r"^\s*MODEL\s*=\s*[\"']([^\"']+)[\"']", re.MULTILINE)
    for path in sorted((ROOT / "drivers").glob("*.py")):
        for model in pattern.findall(path.read_text(encoding="utf-8",
                                                     errors="replace")):
            models.setdefault(_family(model), set()).add(
                (model, str(path.relative_to(ROOT))))
    return models


def maintained_collisions(models_added):
    ours = newchirp_models()
    hits = []
    for vendor, model in models_added:
        for our_model, path in sorted(ours.get(_family(model), ())):
            hits.append((vendor, model, our_model, path))
    return hits


def write_report(report, path):
    lines = []
    add = lines.append
    add("# Upstream CHIRP review %s" % report["date"])
    add("")
    add("Generated by `scripts/upstream_review.py`. This review does not "
        "change the pin; adopting the target is a separate, reviewed commit.")
    add("")
    add("| | Commit | Archive SHA-256 |")
    add("|---|---|---|")
    add("| Pinned | `%s` | `%s` |" % (report["pin"], report["pin_sha"]))
    add("| Target | `%s` (%s) | `%s` |" % (
        report["target"], report["ref"], report["target_sha"]))
    add("")
    commits = report["commits"]
    if commits is None:
        add("Upstream commit list unavailable: %s" % report["commits_error"])
    else:
        dates = [c["date"] for c in commits["commits"]]
        add("Upstream commits since the pin: **%i**%s." % (
            commits["total"],
            " (%s to %s)" % (min(dates), max(dates)) if dates else ""))
    add("Changed files under `chirp/`: %i modified, %i added, %i removed." % (
        len(report["modified"]), len(report["added"]), len(report["removed"])))
    add("")

    add("## Verdict")
    add("")
    for line in report["verdict"]:
        add("- %s" % line)
    add("")

    add("## NewChirp source patches")
    add("")
    if report["patch_warnings"]:
        for warning in report["patch_warnings"]:
            add("- **%s**" % warning)
    else:
        add("All `update_chirp.sh` patches applied to the target.")
    add("")

    add("## Radios")
    add("")
    for title, items in (("New in the target", report["models_added"]),
                         ("No longer in the target", report["models_removed"])):
        add("### %s (%i)" % (title, len(items)))
        add("")
        if items:
            for vendor, model in items:
                add("- %s %s" % (vendor, model))
        else:
            add("None.")
        add("")

    add("## New upstream radios NewChirp already maintains")
    add("")
    if report["collisions"]:
        add("Upstream added a driver for a radio NewChirp maintains. Decide "
            "which driver wins and check the registration order.")
        add("")
        for vendor, model, ours, where in report["collisions"]:
            add("- Upstream %s %s vs NewChirp %s (`%s`)" % (
                vendor, model, ours, where))
    else:
        add("None.")
    add("")

    add("## Changed core CHIRP modules")
    add("")
    if report["core"]:
        add("Shared by most NewChirp drivers; the tests below are the main "
            "check.")
        add("")
        for item in report["core"]:
            add("- `%s` (+%i / -%i), used by %i NewChirp files" % (
                item["file"], item["plus"], item["minus"],
                len(item["users"])))
    else:
        add("None.")
    add("")

    add("## Changed upstream drivers that NewChirp code uses")
    add("")
    add("Each needs a decision: our patch is still needed, conflicts, or is "
        "now fixed upstream.")
    add("")
    if report["overlaps"]:
        add("| Upstream file | +/- lines | NewChirp files | Upstream commits mentioning it |")
        add("|---|---|---|---|")
        for item in report["overlaps"]:
            add("| `%s` | +%i / -%i | %s | %s |" % (
                item["file"], item["plus"], item["minus"],
                ", ".join("`%s`" % user for user in item["users"]),
                "; ".join("%s %s" % (c["sha"][:9], c["title"].replace("|", "/"))
                          for c in item["commits"]) or "-",
            ))
    else:
        add("None.")
    add("")

    add("## Other changed files")
    add("")
    others = [item for item in report["other_changes"]]
    if others:
        for name, plus, minus in others:
            add("- `%s` (+%i / -%i)" % (name, plus, minus))
    else:
        add("None.")
    for title, names in (("Added", report["added"]),
                         ("Removed", report["removed"])):
        if names:
            add("")
            add("%s files:" % title)
            add("")
            for name in names:
                add("- `%s`" % name)
    add("")

    add("## Tests against the target")
    add("")
    for title, results in (("Python", report["python_tests"]),
                           ("Dart (CHIRP-dependent)", report["dart_tests"])):
        if results is None:
            add("%s: not run." % title)
            add("")
            continue
        failed = [item for item in results if not item[1]]
        add("%s: %i of %i files passed." % (
            title, len(results) - len(failed), len(results)))
        add("")
        for name, _ok, tail in failed:
            add("<details><summary>FAIL %s</summary>" % name)
            add("")
            add("```text")
            add(tail)
            add("```")
            add("")
            add("</details>")
            add("")

    if commits:
        add("## Upstream commits")
        add("")
        for commit in commits["commits"]:
            add("- %s `%s` %s (%s)" % (
                commit["date"], commit["sha"][:9],
                commit["title"].replace("<", "&lt;"), commit["author"]))
        add("")

    add("## Adopting the target")
    add("")
    add("1. Resolve every overlap and test failure above.")
    add("2. Set `scripts/chirp-source.pin` to:")
    add("")
    add("   ```text")
    add("   commit %s" % report["target"])
    add("   sha256 %s" % report["target_sha"])
    add("   ```")
    add("")
    add("3. Run `bash scripts/update_chirp.sh` and the full test suites.")
    add("4. Run `python3 scripts/export_radio_catalog.py --out "
        "/Volumes/RICKEXT/web/newchirpweb/catalog/chirp-pinned-models.json`, "
        "then `npm run sync:radios` in the website.")
    add("5. Update `docs/DRIVER_STATUS.md` for any NewChirp driver whose "
        "upstream base changed, record the pin change in the driver ledger, "
        "and commit both repositories.")
    add("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ref", default="master",
                        help="upstream branch, tag or 40-hex commit")
    parser.add_argument("--out", type=Path,
                        help="report path (default docs/upstream_reviews/)")
    parser.add_argument("--skip-tests", action="store_true")
    parser.add_argument("--skip-dart", action="store_true")
    args = parser.parse_args()

    pin, pin_sha = pinned()
    target = resolve_target(args.ref)
    today = datetime.date.today().isoformat()
    out = args.out or ROOT / ("docs/upstream_reviews/%s-%s.md"
                              % (today, target[:9]))
    if target == pin:
        print("The pin already matches %s (%s)." % (args.ref, target))
        return

    print("Preparing pinned %s and target %s..." % (pin[:12], target[:12]))
    old_root = pinned_tree(pin)
    new_root, target_sha, patch_warnings = prepare_tree(target)

    commits, commits_error = upstream_commits(pin, target)
    added, removed, modified = changed_files(old_root, new_root)

    with tempfile.TemporaryDirectory() as scratch:
        old_models = export_catalog(old_root, Path(scratch) / "old.json")
        new_models = export_catalog(new_root, Path(scratch) / "new.json")
    models_added = sorted(new_models - old_models)
    models_removed = sorted(old_models - new_models)

    texts = newchirp_references()
    commit_list = commits["commits"] if commits else []
    overlaps = []
    core = []
    other_changes = []
    for name in modified + added + removed:
        plus, minus = line_delta(old_root / name, new_root / name)
        if not name.endswith(".py"):
            other_changes.append((name, plus, minus))
            continue
        module = module_name(name)
        users = module_users(module, texts)
        if users and not name.startswith("chirp/drivers/"):
            core.append({"file": name, "plus": plus, "minus": minus,
                         "users": users})
        elif users:
            overlaps.append({
                "file": name, "plus": plus, "minus": minus, "users": users,
                "commits": mentions(commit_list, module),
            })
        else:
            other_changes.append((name, plus, minus))

    python_tests = dart_tests = None
    if not args.skip_tests:
        print("Running Python tests against the target...")
        python_tests = run_python_tests(new_root)
        if not args.skip_dart:
            print("Running CHIRP-dependent Dart tests against the target...")
            dart_tests = run_dart_tests(new_root)

    verdict = []
    failed = [t for t in (python_tests or []) + (dart_tests or []) if not t[1]]
    if patch_warnings:
        verdict.append("%i NewChirp source patch(es) no longer apply."
                       % len(patch_warnings))
    if python_tests is None:
        verdict.append("Tests were not run.")
    elif failed:
        verdict.append("%i test file(s) fail against the target." % len(failed))
    else:
        verdict.append("All tests that were run pass against the target.")
    collisions = maintained_collisions(models_added)
    if collisions:
        verdict.append("%i new upstream radio(s) collide with NewChirp-"
                       "maintained drivers." % len(collisions))
    verdict.append("%i changed upstream driver(s) are used by NewChirp code "
                   "and need review; %i core module(s) changed."
                   % (len(overlaps), len(core)))
    verdict.append("%i radio model(s) would be added and %i removed."
                   % (len(models_added), len(models_removed)))
    if (not patch_warnings and python_tests is not None and not failed
            and not collisions):
        verdict.append("No blocker found automatically; adopt only after "
                       "reviewing the overlaps.")
    else:
        verdict.append("Do not adopt until the items above are resolved.")

    write_report({
        "date": today, "ref": args.ref, "pin": pin, "pin_sha": pin_sha,
        "target": target, "target_sha": target_sha,
        "commits": commits, "commits_error": commits_error,
        "added": added, "removed": removed, "modified": modified,
        "patch_warnings": patch_warnings,
        "models_added": models_added, "models_removed": models_removed,
        "overlaps": overlaps, "core": core, "collisions": collisions,
        "other_changes": other_changes,
        "python_tests": python_tests, "dart_tests": dart_tests,
        "verdict": verdict,
    }, out)
    print("\n".join(verdict))
    print("Report: %s" % out)


if __name__ == "__main__":
    main()
