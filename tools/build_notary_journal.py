"""Build the printable Cincinnati Document Services notary journal."""

from __future__ import annotations

import argparse
from pathlib import Path

from reportlab.lib.colors import Color, HexColor, white
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

PAGE_WIDTH, PAGE_HEIGHT = LETTER
MARGIN = 36
MAROON = HexColor("#660c1a")
GOLD = HexColor("#c49a2a")
CHARCOAL = HexColor("#1a1816")
MARBLE = HexColor("#938d85")
PARCHMENT = HexColor("#f3e8d6")
LIGHT_GREY = HexColor("#ece9e4")
RELEASE_DATE = "October 20, 2026"
ENTRY_PAGE_COUNT = 8


def wrap_text(text: str, font: str, size: float, width: float) -> list[str]:
    """Wrap a short passage to a width using ReportLab font metrics."""
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if current and stringWidth(candidate, font, size) > width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def draw_wrapped(
    pdf: canvas.Canvas,
    text: str,
    x: float,
    y: float,
    width: float,
    *,
    font: str = "Helvetica",
    size: float = 9,
    leading: float = 12,
    color: Color = CHARCOAL,
) -> float:
    """Draw wrapped text and return the y position below it."""
    pdf.setFillColor(color)
    pdf.setFont(font, size)
    for line in wrap_text(text, font, size, width):
        pdf.drawString(x, y, line)
        y -= leading
    return y


def draw_checkbox(pdf: canvas.Canvas, x: float, y: float, label: str, size: float = 7.2) -> float:
    """Draw one empty checkbox and return the next x position."""
    box = 8
    pdf.setStrokeColor(CHARCOAL)
    pdf.setLineWidth(0.7)
    pdf.rect(x, y - 1, box, box, stroke=1, fill=0)
    pdf.setFillColor(CHARCOAL)
    pdf.setFont("Helvetica", size)
    pdf.drawString(x + box + 3, y, label)
    return x + box + 3 + stringWidth(label, "Helvetica", size) + 12


def line_field(
    pdf: canvas.Canvas,
    label: str,
    x: float,
    y: float,
    width: float,
    *,
    label_size: float = 7.2,
) -> None:
    """Draw a label followed by a handwriting line."""
    pdf.setFillColor(CHARCOAL)
    pdf.setFont("Helvetica-Bold", label_size)
    pdf.drawString(x, y, label)
    start = x + stringWidth(label, "Helvetica-Bold", label_size) + 4
    pdf.setStrokeColor(MARBLE)
    pdf.setLineWidth(0.55)
    pdf.line(start, y - 2, x + width, y - 2)


def draw_brand_header(pdf: canvas.Canvas, title: str, subtitle: str = "") -> None:
    pdf.setFillColor(MAROON)
    pdf.rect(0, PAGE_HEIGHT - 62, PAGE_WIDTH, 62, stroke=0, fill=1)
    pdf.setFillColor(white)
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(MARGIN, PAGE_HEIGHT - 34, title)
    if subtitle:
        pdf.setFont("Helvetica", 8.5)
        pdf.drawRightString(PAGE_WIDTH - MARGIN, PAGE_HEIGHT - 34, subtitle)
    pdf.setFillColor(GOLD)
    pdf.rect(0, PAGE_HEIGHT - 66, PAGE_WIDTH, 4, stroke=0, fill=1)


def draw_footer(pdf: canvas.Canvas, page_number: int) -> None:
    pdf.setStrokeColor(MARBLE)
    pdf.setLineWidth(0.4)
    pdf.line(MARGIN, 30, PAGE_WIDTH - MARGIN, 30)
    pdf.setFillColor(CHARCOAL)
    pdf.setFont("Helvetica", 6.5)
    pdf.drawString(
        MARGIN, 19, "Traditional in-person notarizations only - secure completed journals."
    )
    pdf.drawRightString(PAGE_WIDTH - MARGIN, 19, f"CDS-NJ-001 | Page {page_number}")


def draw_cover(pdf: canvas.Canvas) -> None:
    draw_brand_header(pdf, "CINCINNATI DOCUMENT SERVICES")
    pdf.setFillColor(CHARCOAL)
    pdf.setFont("Times-Bold", 28)
    pdf.drawString(MARGIN, 665, "Ohio Traditional Notary Journal")
    pdf.setFillColor(MAROON)
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(MARGIN, 642, "PRINTABLE WORKING RECORD | TRADITIONAL IN-PERSON NOTARIZATIONS")

    pdf.setFillColor(PARCHMENT)
    pdf.roundRect(MARGIN, 532, PAGE_WIDTH - (2 * MARGIN), 84, 5, stroke=0, fill=1)
    pdf.setFillColor(MAROON)
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(MARGIN + 16, 591, "Purpose and scope")
    notice = (
        "Ohio law does not require a journal for traditional notarizations. The Ohio "
        "Secretary of State strongly recommends logging every notarial act as a best "
        "practice. This paper journal is not an electronic journal and does not satisfy "
        "the electronic-journal requirements for online notarizations."
    )
    draw_wrapped(
        pdf, notice, MARGIN + 16, 573, PAGE_WIDTH - (2 * MARGIN) - 32, size=8.8, leading=12
    )

    pdf.setFillColor(CHARCOAL)
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(MARGIN, 500, "Notary record")
    line_field(pdf, "Notary name", MARGIN, 476, 260)
    line_field(pdf, "Commission number", 316, 476, 260)
    line_field(pdf, "Commission expiration", MARGIN, 448, 260)
    line_field(pdf, "Primary county", 316, 448, 260)
    line_field(pdf, "Journal volume or date range", MARGIN, 420, PAGE_WIDTH - (2 * MARGIN))

    pdf.setFillColor(CHARCOAL)
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(MARGIN, 380, "Use each entry to")
    instructions = [
        "Record one signer and one notarial act per entry, promptly after the act.",
        "Describe the document without copying sensitive contents into the journal.",
        "Record the identification method. For an ID, note type, issuer, and expiration only.",
        "Keep the notarial fee separate from any agreed mobile travel fee.",
        "Secure the completed journal from unauthorized access, loss, or alteration.",
    ]
    y = 358
    for instruction in instructions:
        pdf.setFillColor(GOLD)
        pdf.circle(MARGIN + 4, y + 3, 2.2, stroke=0, fill=1)
        y = draw_wrapped(
            pdf, instruction, MARGIN + 14, y, PAGE_WIDTH - (2 * MARGIN) - 14, size=8.5, leading=13
        )

    pdf.setFillColor(LIGHT_GREY)
    pdf.roundRect(MARGIN, 190, PAGE_WIDTH - (2 * MARGIN), 70, 5, stroke=0, fill=1)
    pdf.setFillColor(CHARCOAL)
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(MARGIN + 14, 239, "Privacy-minded recordkeeping")
    privacy = (
        "Do not record Social Security numbers, account numbers, access codes, full driver "
        "license or ID numbers, or detailed document contents. Follow any retention, access, "
        "and disposal duties that apply to your practice."
    )
    draw_wrapped(
        pdf, privacy, MARGIN + 14, 221, PAGE_WIDTH - (2 * MARGIN) - 28, size=8.5, leading=12
    )

    pdf.setFillColor(CHARCOAL)
    pdf.setFont("Helvetica-Bold", 8)
    pdf.drawString(MARGIN, 156, "Sources checked for this edition")
    source_lines = [
        "Ohio Secretary of State, Notary Resources and Frequently Asked Questions",
        "ohiosos.gov/notary/become-a-notary-in-ohio/resources-and-frequently-asked-questions",
        "Ohio Revised Code sections 147.08 (fees) and 147.65 (online-notary journals)",
        "codes.ohio.gov/ohio-revised-code/chapter-147",
    ]
    y = 142
    for source in source_lines:
        pdf.setFont("Helvetica", 6.8)
        pdf.drawString(MARGIN, y, source)
        y -= 10

    pdf.setFont("Helvetica-Oblique", 6.8)
    pdf.drawString(
        MARGIN, 88, f"Edition date: {RELEASE_DATE}. Check current Ohio law and guidance before use."
    )
    pdf.drawString(
        MARGIN,
        77,
        "This organizational tool is not legal advice and is not issued by the State of Ohio.",
    )
    draw_footer(pdf, 1)


def draw_entry(pdf: canvas.Canvas, x: float, top: float, width: float, entry_number: int) -> None:
    height = 318
    bottom = top - height
    pdf.setStrokeColor(CHARCOAL)
    pdf.setLineWidth(0.8)
    pdf.roundRect(x, bottom, width, height, 4, stroke=1, fill=0)

    pdf.setFillColor(MAROON)
    pdf.roundRect(x, top - 23, width, 23, 4, stroke=0, fill=1)
    pdf.rect(x, top - 23, width, 6, stroke=0, fill=1)
    pdf.setFillColor(white)
    pdf.setFont("Helvetica-Bold", 9)
    pdf.drawString(x + 9, top - 15, "JOURNAL ENTRY")
    pdf.drawRightString(x + width - 9, top - 15, f"Entry {entry_number:02d}")

    left = x + 9
    right = x + width - 9
    y = top - 40
    line_field(pdf, "Date", left, y, 126)
    line_field(pdf, "Time", left + 136, y, 112)
    line_field(pdf, "Ohio county / location", left + 258, y, width - 276)

    y -= 28
    line_field(pdf, "Document title or brief description", left, y, width - 18)
    y -= 15
    line_field(pdf, "Document date (if shown)", left, y, 250)
    line_field(pdf, "Pages", left + 264, y, 92)
    line_field(pdf, "Capacity claimed", left + 368, y, width - 386)

    y -= 26
    pdf.setFont("Helvetica-Bold", 7.2)
    pdf.drawString(left, y, "Notarial act")
    next_x = draw_checkbox(pdf, left + 70, y - 1, "Acknowledgment")
    next_x = draw_checkbox(pdf, next_x, y - 1, "Jurat / oath / affirmation")
    draw_checkbox(pdf, next_x, y - 1, "Other certificate")

    y -= 25
    line_field(pdf, "Signer full name", left, y, 270)
    line_field(pdf, "Address (optional)", left + 282, y, width - 300)

    y -= 27
    pdf.setFont("Helvetica-Bold", 7.2)
    pdf.drawString(left, y, "Identification")
    next_x = draw_checkbox(pdf, left + 68, y - 1, "Personal knowledge")
    next_x = draw_checkbox(pdf, next_x, y - 1, "Government ID")
    draw_checkbox(pdf, next_x, y - 1, "Credible witness")
    y -= 18
    line_field(pdf, "ID type", left, y, 160)
    line_field(pdf, "Issuer / state", left + 172, y, 160)
    line_field(pdf, "Expiration", left + 344, y, width - 362)
    y -= 17
    line_field(pdf, "Credible witness name (if used)", left, y, width - 18)

    y -= 25
    pdf.setFont("Helvetica-Bold", 7.2)
    pdf.drawString(left, y, "Confirmed")
    next_x = draw_checkbox(pdf, left + 55, y - 1, "Personal appearance")
    next_x = draw_checkbox(pdf, next_x, y - 1, "Identity satisfactory")
    draw_checkbox(pdf, next_x, y - 1, "Willing and aware")
    y -= 17
    next_x = draw_checkbox(pdf, left + 55, y - 1, "Document appears complete")
    next_x = draw_checkbox(pdf, next_x, y - 1, "Signed in my presence if required")
    draw_checkbox(pdf, next_x, y - 1, "Certificate completed")

    y -= 24
    line_field(pdf, "Signer journal signature", left, y, 344)
    line_field(pdf, "Notary initials", left + 356, y, width - 374)

    y -= 25
    line_field(pdf, "Notarial fee $", left, y, 130)
    line_field(pdf, "Agreed travel fee $", left + 142, y, 160)
    line_field(pdf, "Total $", left + 314, y, 95)
    draw_checkbox(pdf, left + 425, y - 1, "Receipt")

    y -= 24
    line_field(pdf, "Notes", left, y, width - 18)
    y -= 14
    pdf.setStrokeColor(MARBLE)
    pdf.setLineWidth(0.45)
    pdf.line(left, y, right, y)


def draw_entry_page(pdf: canvas.Canvas, page_number: int, first_entry: int) -> None:
    draw_brand_header(
        pdf,
        "OHIO TRADITIONAL NOTARY JOURNAL",
        "One signer and one notarial act per entry",
    )
    pdf.setFillColor(CHARCOAL)
    pdf.setFont("Helvetica", 7)
    pdf.drawString(MARGIN, PAGE_HEIGHT - 79, "Journal volume / date range:")
    pdf.setStrokeColor(MARBLE)
    pdf.line(MARGIN + 92, PAGE_HEIGHT - 81, 258, PAGE_HEIGHT - 81)
    pdf.drawRightString(
        PAGE_WIDTH - MARGIN,
        PAGE_HEIGHT - 79,
        "Avoid recording full ID numbers or sensitive document contents.",
    )

    draw_entry(pdf, MARGIN, 696, PAGE_WIDTH - (2 * MARGIN), first_entry)
    draw_entry(pdf, MARGIN, 367, PAGE_WIDTH - (2 * MARGIN), first_entry + 1)
    draw_footer(pdf, page_number)


def build(output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(
        str(output),
        pagesize=LETTER,
        pageCompression=1,
        invariant=1,
    )
    pdf.setTitle("Ohio Traditional Notary Journal")
    pdf.setAuthor("Cincinnati Document Services")
    pdf.setSubject("Printable journal for traditional in-person notarial acts in Ohio")
    draw_cover(pdf)
    pdf.showPage()
    for page_offset in range(ENTRY_PAGE_COUNT):
        page_number = page_offset + 2
        first_entry = (page_offset * 2) + 1
        draw_entry_page(pdf, page_number, first_entry)
        pdf.showPage()
    pdf.save()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("forms_library/assets/cds-ohio-notary-journal.pdf"),
    )
    args = parser.parse_args()
    build(args.output)
    print(args.output.resolve())


if __name__ == "__main__":
    main()
