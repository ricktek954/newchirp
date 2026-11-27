# channel_list_pdf

## Classs

- [ChannelListColumn](ChannelListColumn.md) — One printed column: header text, relative width, and right alignment.

## Functions

- [_crossSummary](crossSummary.md) — Tone text for a Cross-mode channel, e.g. "TX 100.0 / RX D023N".
- [_dcs](dcs.md) — DCS code as printed, e.g. "D023N".
- [_fit](fit.md) — Shortens [text] with "..." until it fits [maxWidth] points.
- [_mhz](mhz.md) — Frequency text for the PDF: up to six decimals, never fewer than three.
- [_pdfText](pdfText.md) — Escapes text for a PDF string: backslash and parentheses are escaped,
- [_textWidth](textWidth.md) — Width of [text] in points using Helvetica's built-in metrics (1/1000 em per
- [buildChannelListPdf](buildChannelListPdf.md) — Build a landscape PDF listing [rows] under [title] and [subtitle].
- [cellOps](cellOps.md) — PDF drawing commands for one table cell (left- or right-aligned text).
- [channelListRows](channelListRows.md) — The printed cells for each active channel, in location order.
- [channelToneSummary](channelToneSummary.md) — Human-readable squelch summary for one channel.
- [side](side.md) — Tone text for one side (transmit or receive) of a Cross mode.
- [write](write.md)
