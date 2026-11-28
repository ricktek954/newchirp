---
okf_version: "0.2"
type: Module
title: upstream_review
description: "Review upstream CHIRP changes against NewChirp's pinned commit."
resource: upstream_review.py
tags:
  - "lang:python"
  - "type:Module"
  - "module:upstream_review.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-28T09:47:28Z"
concept_id: upstream_review
language: python
---

# upstream_review

Review upstream CHIRP changes against NewChirp's pinned commit.

## Docstring

Review upstream CHIRP changes against NewChirp's pinned commit.

Prepares the target commit in build_support/chirp-review-<commit> (with
NewChirp's source patches), compares it with the pinned tree, lists new and
removed radios, flags changed upstream modules that NewChirp drivers patch or
extend, runs the offline test suites against the target, and writes a
Markdown report. It never changes scripts/chirp-source.pin.

## Relationships

| Type | Target |
|------|--------|
| related | [pinned](/upstream_review/pinned.md) |
| related | [resolve_target](/upstream_review/resolve_target.md) |
| related | [prepare_tree](/upstream_review/prepare_tree.md) |
| related | [pinned_tree](/upstream_review/pinned_tree.md) |
| related | [upstream_commits](/upstream_review/upstream_commits.md) |
| related | [changed_files](/upstream_review/changed_files.md) |
| related | [line_delta](/upstream_review/line_delta.md) |
| related | [export_catalog](/upstream_review/export_catalog.md) |
| related | [newchirp_references](/upstream_review/newchirp_references.md) |
| related | [module_users](/upstream_review/module_users.md) |
| related | [run_python_tests](/upstream_review/run_python_tests.md) |
| related | [flutter_binary](/upstream_review/flutter_binary.md) |
| related | [run_dart_tests](/upstream_review/run_dart_tests.md) |
| related | [module_name](/upstream_review/module_name.md) |
| related | [mentions](/upstream_review/mentions.md) |
| related | [_family](/upstream_review/family.md) |
| related | [newchirp_models](/upstream_review/newchirp_models.md) |
| related | [maintained_collisions](/upstream_review/maintained_collisions.md) |
| related | [write_report](/upstream_review/write_report.md) |
| related | [main](/upstream_review/main.md) |
