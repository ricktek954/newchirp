---
okf_version: "0.2"
type: Function
title: set_fill
resource: generate_gmrs_frs_pdf.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:generate_gmrs_frs_pdf.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-08-23T13:43:31Z"
concept_id: generate_gmrs_frs_pdf/set_fill
language: python
---

# set_fill

## Signature

```python
def set_fill(self, color: tuple[float, float, float]) -> None
```

## Parameters

| Name | Type | Default |
|------|------|---------|
| `self` | `—` | `—` |

| `color` | `tuple[float, float, float]` | `—` |

## Returns
`None`

## Source
Lines 53–54 in `generate_gmrs_frs_pdf.py`

## Relationships

| Type | Target |
|------|--------|
| related | [PdfWriter](/generate_gmrs_frs_pdf/PdfWriter.md) |
| calls | [_rgb](/generate_gmrs_frs_pdf/rgb.md) |
| called_by | [rect](/generate_gmrs_frs_pdf/rect.md) |
| called_by | [text](/generate_gmrs_frs_pdf/text.md) |
