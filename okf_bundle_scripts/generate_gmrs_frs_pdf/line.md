---
okf_version: "0.2"
type: Function
title: line
resource: generate_gmrs_frs_pdf.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:generate_gmrs_frs_pdf.py"
  - "git:branch:HEAD"
  - "git:repo:newchirp"
timestamp: "2026-08-23T23:14:49Z"
concept_id: generate_gmrs_frs_pdf/line
language: python
---

# line

## Signature

```python
def line(self, x1: float, y1: float, x2: float, y2: float, color: tuple[float, float, float], width: float = 0.5) -> None
```

## Parameters

| Name | Type | Default |
|------|------|---------|
| `self` | `—` | `—` |

| `x1` | `float` | `—` |

| `y1` | `float` | `—` |

| `x2` | `float` | `—` |

| `y2` | `float` | `—` |

| `color` | `tuple[float, float, float]` | `—` |

| `width` | `float` | `0.5` |

## Returns
`None`

## Source
Lines 72–85 in `generate_gmrs_frs_pdf.py`

## Relationships

| Type | Target |
|------|--------|
| related | [PdfWriter](/generate_gmrs_frs_pdf/PdfWriter.md) |
| calls | [set_stroke](/generate_gmrs_frs_pdf/set_stroke.md) |
| called_by | [make_pdf](/generate_international_frequency_pdfs/make_pdf.md) |
