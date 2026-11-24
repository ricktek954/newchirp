---
okf_version: "0.2"
type: Function
title: rect
resource: generate_gmrs_frs_pdf.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:generate_gmrs_frs_pdf.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-08-23T23:14:49Z"
concept_id: generate_gmrs_frs_pdf/rect
language: python
---

# rect

## Signature

```python
def rect(self, x: float, y: float, width: float, height: float, color: tuple[float, float, float]) -> None
```

## Parameters

| Name | Type | Default |
|------|------|---------|
| `self` | `—` | `—` |

| `x` | `float` | `—` |

| `y` | `float` | `—` |

| `width` | `float` | `—` |

| `height` | `float` | `—` |

| `color` | `tuple[float, float, float]` | `—` |

## Returns
`None`

## Source
Lines 59–70 in `generate_gmrs_frs_pdf.py`

## Relationships

| Type | Target |
|------|--------|
| related | [PdfWriter](/generate_gmrs_frs_pdf/PdfWriter.md) |
| calls | [set_fill](/generate_gmrs_frs_pdf/set_fill.md) |
| called_by | [make_pdf](/generate_international_frequency_pdfs/make_pdf.md) |
