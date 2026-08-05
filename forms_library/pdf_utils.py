from __future__ import annotations

from pathlib import Path


class PDFInfo:
    def __init__(
        self,
        path: Path,
        page_count: int | None = None,
        revision_label: str = "",
        fillable: bool = False,
        error: str = "",
    ) -> None:
        self.path = path
        self.page_count = page_count
        self.revision_label = revision_label
        self.fillable = fillable
        self.error = error


def extract_pdf_info(filepath: Path) -> PDFInfo:
    result = PDFInfo(path=filepath)

    if not filepath.exists():
        result.error = f"File not found: {filepath}"
        return result

    try:
        import fitz
    except ImportError:
        result.error = "PyMuPDF (fitz) not installed. Install with: pip install pymupdf"
        return result

    try:
        doc = fitz.open(str(filepath))
        result.page_count = doc.page_count

        metadata = doc.metadata or {}
        result.revision_label = (
            metadata.get("subject", "")
            or metadata.get("title", "")
        )

        for page in doc:
            for widget in page.widgets() or []:
                if widget.field_type in (
                    fitz.PDF_WIDGET_TYPE_TEXT,
                    fitz.PDF_WIDGET_TYPE_CHECKBOX,
                    fitz.PDF_WIDGET_TYPE_COMBOBOX,
                ):
                    result.fillable = True
                    break

        doc.close()
    except Exception as e:
        result.error = str(e)

    return result
