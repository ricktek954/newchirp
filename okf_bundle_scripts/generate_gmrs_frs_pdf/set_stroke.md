---
okf_version: "0.2"
type: Function
title: set_stroke
resource: generate_gmrs_frs_pdf.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:generate_gmrs_frs_pdf.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-08-23T23:14:49Z"
concept_id: generate_gmrs_frs_pdf/set_stroke
language: python
---

# set_stroke

## Signature

```python
def set_stroke(self, color: tuple[float, float, float]) -> None
```

## Parameters

| Name | Type | Default |
|------|------|---------|
| `self` | `—` | `—` |

| `color` | `tuple[float, float, float]` | `—` |

## Returns
`None`

## Source
Lines 56–57 in `generate_gmrs_frs_pdf.py`

## Relationships

| Type | Target |
|------|--------|
| related | [PdfWriter](/generate_gmrs_frs_pdf/PdfWriter.md) |
| calls | [_rgb](/generate_gmrs_frs_pdf/rgb.md) |
| called_by | [line](/generate_gmrs_frs_pdf/line.md) |
