---
okf_version: "0.2"
type: Function
title: as_pdf
resource: generate_gmrs_frs_pdf.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:generate_gmrs_frs_pdf.py"
  - "git:branch:HEAD"
  - "git:repo:newchirp"
timestamp: "2026-08-23T23:14:49Z"
concept_id: generate_gmrs_frs_pdf/as_pdf
language: python
---

# as_pdf

## Signature

```python
def as_pdf(self) -> bytes
```

## Parameters

| Name | Type | Default |
|------|------|---------|
| `self` | `—` | `—` |

## Returns
`bytes`

## Source
Lines 160–210 in `generate_gmrs_frs_pdf.py`

## Relationships

| Type | Target |
|------|--------|
| related | [PdfWriter](/generate_gmrs_frs_pdf/PdfWriter.md) |
| called_by | [make_pdf](/generate_international_frequency_pdfs/make_pdf.md) |
