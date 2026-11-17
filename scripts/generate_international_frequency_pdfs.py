#!/usr/bin/env python3
"""Generate one-page international frequency-reference PDFs."""

from __future__ import annotations

from pathlib import Path

from generate_gmrs_frs_pdf import (
    GRID,
    HEADER_BG,
    HEADER_FG,
    INK,
    MARGIN,
    MUTED,
    PAGE_H,
    PAGE_W,
    WHITE,
    PdfWriter,
)


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"


MARINE = [
    ("01", "156.050", "Duplex"),
    ("02", "156.100", "Duplex"),
    ("03", "156.150", "Duplex"),
    ("04", "156.200", "Duplex"),
    ("05", "156.250", "Duplex"),
    ("06", "156.300", "Inter-ship"),
    ("07", "156.350", "Duplex"),
    ("08", "156.400", "Inter-ship"),
    ("09", "156.450", "Calling"),
    ("10", "156.500", "Inter-ship"),
    ("11", "156.550", "Inter-ship"),
    ("12", "156.600", "Port operations"),
    ("13", "156.650", "Bridge-to-bridge"),
    ("14", "156.700", "Port operations"),
    ("15", "156.750", "Low power"),
    ("16", "156.800", "Distress / safety / calling"),
    ("17", "156.850", "Low power"),
    ("18", "156.900", "Duplex"),
    ("19", "156.950", "Duplex"),
    ("20", "157.000", "Duplex"),
    ("21", "157.050", "Duplex"),
    ("22", "157.100", "Duplex"),
    ("23", "157.150", "Duplex"),
    ("24", "157.200", "Duplex"),
    ("25", "157.250", "Duplex"),
    ("26", "157.300", "Duplex"),
    ("27", "157.350", "Duplex"),
    ("28", "157.400", "Duplex"),
    ("60", "156.025", "Duplex"),
    ("61", "156.075", "Duplex"),
    ("62", "156.125", "Duplex"),
    ("63", "156.175", "Duplex"),
    ("64", "156.225", "Duplex"),
    ("65", "156.275", "Duplex"),
    ("66", "156.325", "Duplex"),
    ("67", "156.375", "Inter-ship"),
    ("68", "156.425", "Inter-ship"),
    ("69", "156.475", "Inter-ship"),
    ("70", "156.525", "DSC only; no voice"),
    ("71", "156.575", "Inter-ship"),
    ("72", "156.625", "Inter-ship"),
    ("73", "156.675", "Inter-ship"),
    ("74", "156.725", "Inter-ship"),
    ("75", "156.775", "Restrictions may apply"),
    ("76", "156.825", "Restrictions may apply"),
    ("77", "156.875", "Inter-ship"),
    ("78", "156.925", "Duplex"),
    ("79", "156.975", "Duplex"),
    ("80", "157.025", "Duplex"),
    ("81", "157.075", "Duplex"),
    ("82", "157.125", "Duplex"),
    ("83", "157.175", "Duplex"),
    ("84", "157.225", "Duplex"),
    ("85", "157.275", "Duplex"),
    ("86", "157.325", "Duplex"),
    ("87", "157.375", "Duplex"),
    ("88", "157.425", "Duplex"),
]

STANDARD_CB = [
    26.965, 26.975, 26.985, 26.995, 27.005, 27.015, 27.025, 27.055,
    27.065, 27.075, 27.085, 27.105, 27.115, 27.125, 27.135, 27.155,
    27.165, 27.175, 27.185, 27.205, 27.215, 27.225, 27.255, 27.235,
    27.245, 27.265, 27.275, 27.285, 27.295, 27.305, 27.315, 27.325,
    27.335, 27.345, 27.355, 27.365, 27.375, 27.385, 27.395, 27.405,
]


def uhf_rows():
    rows = []
    for channel in range(1, 81):
        frequency = (
            476.425 + (channel - 1) * 0.025
            if channel <= 40
            else 476.4375 + (channel - 41) * 0.025
        )
        if 1 <= channel <= 8:
            note = (
                "Emergency output; input Ch 35"
                if channel == 5
                else "Repeater output; input Ch %02i" % (channel + 30)
            )
        elif 31 <= channel <= 38:
            note = (
                "Emergency input; output Ch 05"
                if channel == 35
                else "Repeater input; output Ch %02i" % (channel - 30)
            )
        elif 41 <= channel <= 48:
            note = (
                "Repeater output; guard caution"
                if channel in (44, 45)
                else "Repeater output; input Ch %02i" % (channel + 30)
            )
        elif 71 <= channel <= 78:
            note = (
                "Repeater input; guard caution"
                if channel in (74, 75)
                else "Repeater input; output Ch %02i" % (channel - 30)
            )
        elif 61 <= channel <= 63:
            note = "Guard channel; receive-only"
        elif channel in (22, 23):
            note = "Data/telemetry only; no voice"
        else:
            note = {
                10: "4WD / off-road / parks",
                11: "Call channel; then move",
                18: "Caravan / camper convoy",
                29: "Road: Pacific / Hume Hwy",
                30: "UHF CB broadcasts / simplex",
                40: "Australia-wide road / truck",
            }.get(channel, "General simplex")
        rows.append((str(channel), f"{frequency:.4f}", note))
    return rows


def draw_table(pdf, *, title, rows, left, top, width):
    columns = [
        ("Ch", 32, "center"),
        ("MHz", 66, "center"),
        ("Use / notes", width - 98, "left"),
    ]
    pdf.text(left, top + 5, title, "F2", 9, MUTED)
    header_top = top - 6
    x = left
    for label, col_width, align in columns:
        pdf.table_cell(
            top=header_top,
            left=x,
            width=col_width,
            height=17,
            text=label,
            font="F2",
            size=7.2,
            color=HEADER_FG,
            fill=HEADER_BG,
            align=align,
        )
        x += col_width
    row_top = header_top - 17
    for channel, frequency, note in rows:
        x = left
        for value, (_label, col_width, align) in zip(
            (channel, frequency, note), columns
        ):
            pdf.table_cell(
                top=row_top,
                left=x,
                width=col_width,
                height=11.4,
                text=value,
                font="F1",
                size=6.4,
                color=INK,
                align=align,
            )
            x += col_width
        row_top -= 11.4
    return row_top


def make_pdf(path, title, subtitle, source, sections):
    pdf = PdfWriter()
    pdf.rect(0, 0, PAGE_W, PAGE_H, (0.965, 0.976, 0.969))
    pdf.rect(
        MARGIN - 10,
        MARGIN - 10,
        PAGE_W - 2 * MARGIN + 20,
        PAGE_H - 2 * MARGIN + 20,
        WHITE,
    )
    pdf.text(MARGIN, 726, title, "F2", 21, HEADER_BG)
    pdf.text(MARGIN, 705, subtitle, "F1", 9.5, MUTED)
    pdf.line(MARGIN, 690, PAGE_W - MARGIN, 690, GRID, 0.6)

    for index, section in enumerate(sections):
        draw_table(
            pdf,
            title=section,
            rows=sections[section],
            left=MARGIN + index * 266,
            top=662,
            width=252,
        )

    pdf.text(MARGIN, 102, "Reference source: " + source, "F1", 7.6, MUTED)
    pdf.text(
        MARGIN,
        87,
        "Reference only. Verify current national rules, permitted modes, "
        "power, and channel restrictions before transmitting.",
        "F3",
        7.6,
        MUTED,
    )
    path.write_bytes(pdf.as_pdf())
    print(path)


def main():
    ASSETS.mkdir(parents=True, exist_ok=True)
    make_pdf(
        ASSETS / "Marine_VHF_Frequency_Reference.pdf",
        "International Marine VHF",
        "ITU Appendix 18 marine voice and DSC channels",
        "ITU Radio Regulations Appendix 18; national rules may differ.",
        {
            "Channels 01-28": MARINE[:29],
            "Channels 60-88": MARINE[29:],
        },
    )

    cb_rows = [
        (
            str(index + 1),
            f"{frequency:.3f}",
            "Emergency / calling"
            if index == 8
            else "Australia: local calling (LSB)"
            if index == 15
            else "Highway / travel"
            if index == 18
            else "Australia: DX calling (LSB)"
            if index == 34
            else "AM/SSB CB",
        )
        for index, frequency in enumerate(STANDARD_CB)
    ]
    uk_rows = [
        (
            str(channel),
            f"{27.60125 + (channel - 1) * 0.01:.5f}",
            "UK 27/81 band",
        )
        for channel in range(1, 41)
    ]
    make_pdf(
        ASSETS / "CB_27MHz_Frequency_Reference.pdf",
        "27 MHz CB",
        "US / Canada / Australia / New Zealand and UK CB channels",
        "FCC 47 CFR Part 95 Subpart D, ISED RSS-210, ACMA CB class licence, "
        "and Ofcom UK CB rules.",
        {
            "40-channel AM/SSB plan": cb_rows,
            "UK CB 27/81 band": uk_rows,
        },
    )

    australian_rows = uhf_rows()
    make_pdf(
        ASSETS / "Australia_UHF_CB_Frequency_Reference.pdf",
        "Australian UHF CB",
        "80-channel 476-477 MHz Australian Citizens Band plan",
        "Australian Communications and Media Authority CB radio class licence.",
        {
            "Channels 1-40": australian_rows[:40],
            "Channels 41-80": australian_rows[40:],
        },
    )


if __name__ == "__main__":
    main()
