---
okf_version: "0.2"
type: Function
title: text
resource: generate_gmrs_frs_pdf.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:generate_gmrs_frs_pdf.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-08-23T13:43:31Z"
concept_id: generate_gmrs_frs_pdf/text
language: python
---

# text

## Signature

```python
def text(self, x: float, y: float, text: str, font: str, size: float, color: tuple[float, float, float]) -> None
```

## Parameters

| Name | Type | Default |
|------|------|---------|
| `self` | `—` | `—` |

| `x` | `float` | `—` |

| `y` | `float` | `—` |

| `text` | `str` | `—` |

| `font` | `str` | `—` |

| `size` | `float` | `—` |

| `color` | `tuple[float, float, float]` | `—` |

## Returns
`None`

## Source
Lines 87–100 in `generate_gmrs_frs_pdf.py`

## Relationships

| Type | Target |
|------|--------|
| related | [PdfWriter](/generate_gmrs_frs_pdf/PdfWriter.md) |
| calls | [set_fill](/generate_gmrs_frs_pdf/set_fill.md) |
| calls | [_esc](/generate_gmrs_frs_pdf/esc.md) |
| called_by | [build_background](/build_macos_dmg/build_background.md) |
| called_by | [main](/generate_gmrs_frs_pdf/main.md) |
| called_by | [text_in_rect](/generate_gmrs_frs_pdf/text_in_rect.md) |
| called_by | [draw_table](/generate_international_frequency_pdfs/draw_table.md) |
| called_by | [make_pdf](/generate_international_frequency_pdfs/make_pdf.md) |
