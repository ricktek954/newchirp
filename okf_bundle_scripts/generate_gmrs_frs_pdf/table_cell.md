---
okf_version: "0.2"
type: Function
title: table_cell
resource: generate_gmrs_frs_pdf.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:generate_gmrs_frs_pdf.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-08-23T13:43:31Z"
concept_id: generate_gmrs_frs_pdf/table_cell
language: python
---

# table_cell

## Signature

```python
def table_cell(self) -> None
```

## Parameters

| Name | Type | Default |
|------|------|---------|
| `self` | `—` | `—` |

## Returns
`None`

## Source
Lines 129–158 in `generate_gmrs_frs_pdf.py`

## Relationships

| Type | Target |
|------|--------|
| related | [PdfWriter](/generate_gmrs_frs_pdf/PdfWriter.md) |
| calls | [line](/generate_gmrs_frs_pdf/line.md) |
| calls | [text_in_rect](/generate_gmrs_frs_pdf/text_in_rect.md) |
| calls | [rect](/generate_gmrs_frs_pdf/rect.md) |
| called_by | [main](/generate_gmrs_frs_pdf/main.md) |
| called_by | [draw_table](/generate_international_frequency_pdfs/draw_table.md) |
