---
okf_version: "0.2"
type: Function
title: make_pdf
resource: generate_international_frequency_pdfs.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:generate_international_frequency_pdfs.py"
  - "git:branch:feature/driver-work-ledger"
  - "git:repo:newchirp"
timestamp: "2026-11-17T12:40:24Z"
concept_id: generate_international_frequency_pdfs/make_pdf
language: python
---

# make_pdf

## Signature

```python
def make_pdf(path, title, subtitle, source, sections)
```

## Parameters

| Name | Type | Default |
|------|------|---------|
| `path` | `—` | `—` |

| `title` | `—` | `—` |

| `subtitle` | `—` | `—` |

| `source` | `—` | `—` |

| `sections` | `—` | `—` |

## Source
Lines 189–224 in `generate_international_frequency_pdfs.py`

## Relationships

| Type | Target |
|------|--------|
| related | [generate_international_frequency_pdfs](/generate_international_frequency_pdfs.md) |
| calls | [PdfWriter](/generate_gmrs_frs_pdf/PdfWriter.md) |
| calls | [rect](/generate_gmrs_frs_pdf/rect.md) |
| calls | [text](/generate_gmrs_frs_pdf/text.md) |
| calls | [line](/generate_gmrs_frs_pdf/line.md) |
| calls | [draw_table](/generate_international_frequency_pdfs/draw_table.md) |
| calls | [as_pdf](/generate_gmrs_frs_pdf/as_pdf.md) |
| called_by | [main](/generate_international_frequency_pdfs/main.md) |
