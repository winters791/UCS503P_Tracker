"""Build report.pdf from report.html using headless Chrome.

Pass 1: render, find which page each section lands on.
Pass 2: fill in TOC page numbers and re-render.
Pass 3: overlay running header + page numbers (skipping the cover page).
"""
import re
import subprocess
import tempfile
from pathlib import Path

import pdfplumber
from pypdf import PdfReader, PdfWriter

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
HERE = Path(__file__).parent
SRC = HERE / "report.html"
OUT = HERE / "OPS_System_Tracker_Report.pdf"

# TOC placeholder -> heading text to search for in the rendered PDF
HEADINGS = {
    "__P_1__": "1. Project Selection Phase",
    "__P_1_1__": "1.1 Software Bid",
    "__P_1_2__": "1.2 Project Overview",
    "__P_2__": "2. Analysis Phase",
    "__P_2_1__": "2.1 Use Cases",
    "__P_2_1_1__": "2.1.1 Use-Case Diagram",
    "__P_2_1_2__": "2.1.2 Use Case Templates",
    "__P_2_2__": "2.2 Activity Diagram and Swimlane Diagram",
    "__P_2_2_1__": "2.2.1 Activity Diagram",
    "__P_2_2_2__": "2.2.2 Swimlane Diagram",
    "__P_2_3__": "2.3 Sequence and Collaboration Diagrams",
    "__P_2_3_1__": "2.3.1 Sequence Diagram",
    "__P_2_3_2__": "2.3.2 Collaboration Diagram",
    "__P_2_4__": "2.4 Software Requirement Specification in IEEE Format",
    "__P_2_5__": "2.5 User Stories and Story Cards",
}


def render(html: Path, pdf: Path) -> None:
    subprocess.run(
        [CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
         f"--print-to-pdf={pdf}", html.as_uri()],
        check=True, capture_output=True,
    )


def find_pages(pdf: Path) -> dict[str, int]:
    found: dict[str, int] = {}
    with pdfplumber.open(pdf) as doc:
        for i, page in enumerate(doc.pages):
            text = page.extract_text() or ""
            if i < 2:  # skip cover and TOC pages
                continue
            for key, heading in HEADINGS.items():
                if key not in found and heading in text:
                    found[key] = i + 1
    return found


def overlay_header(pdf_in: Path, pdf_out: Path) -> None:
    reader = PdfReader(pdf_in)
    n = len(reader.pages)
    # Build an overlay PDF with the same page count via Chrome.
    pages_html = "".join(
        '<div class="pg">'
        + ("" if i == 0 else '<div class="hdr">UCS503- Software Engineering Lab</div>'
                              f'<div class="num">{i + 1}</div>')
        + "</div>"
        for i in range(n)
    )
    overlay_html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
    @page {{ size: A4; margin: 0; }}
    body {{ margin: 0; font-family: "Times New Roman", serif; }}
    .pg {{ width: 210mm; height: 297mm; position: relative; page-break-after: always; }}
    .pg:last-child {{ page-break-after: auto; }}
    .hdr {{ position: absolute; top: 10mm; right: 22mm; font-size: 10pt; font-weight: bold; }}
    .num {{ position: absolute; bottom: 10mm; left: 0; right: 0; text-align: center; font-size: 11pt; }}
    </style></head><body>{pages_html}</body></html>"""
    with tempfile.TemporaryDirectory() as td:
        ov_html = Path(td) / "overlay.html"
        ov_pdf = Path(td) / "overlay.pdf"
        ov_html.write_text(overlay_html)
        render(ov_html, ov_pdf)
        overlay = PdfReader(ov_pdf)
        assert len(overlay.pages) == n, (len(overlay.pages), n)
        writer = PdfWriter()
        for page, ov in zip(reader.pages, overlay.pages):
            page.merge_page(ov)
            writer.add_page(page)
        writer.write(pdf_out)


def main() -> None:
    html = SRC.read_text()
    with tempfile.TemporaryDirectory() as td:
        pass1 = Path(td) / "pass1.pdf"
        render(SRC, pass1)
        pages = find_pages(pass1)
        missing = [k for k in HEADINGS if k not in pages]
        if missing:
            raise SystemExit(f"headings not found: {missing}")
        filled = html
        for key, pg in pages.items():
            filled = filled.replace(key, str(pg))
        tmp_html = HERE / "_report_filled.html"
        tmp_html.write_text(filled)
        pass2 = Path(td) / "pass2.pdf"
        try:
            render(tmp_html, pass2)
        finally:
            tmp_html.unlink()
        overlay_header(pass2, OUT)
    print(f"wrote {OUT} ({len(PdfReader(OUT).pages)} pages)")
    for key, pg in pages.items():
        print(f"  {HEADINGS[key]:<55} p.{pg}")


if __name__ == "__main__":
    main()
