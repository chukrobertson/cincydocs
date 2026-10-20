from __future__ import annotations

from pathlib import Path

from forms_library.manifest import load_manifest
from forms_library.models import PublicationStatus, compute_sha256
from forms_library.pdf_utils import extract_pdf_info

ROOT = Path(__file__).parents[1]
MANIFEST_PATH = ROOT / "data" / "manifests" / "cincydocs_notary.yaml"
JOURNAL_PATH = ROOT / "forms_library" / "assets" / "cds-ohio-notary-journal.pdf"


def test_notary_journal_matches_manifest_metadata():
    form = load_manifest(MANIFEST_PATH).forms[0]

    assert form.publication_status == PublicationStatus.locally_hosted
    assert form.locally_stored is True
    assert ROOT / form.local_file_path == JOURNAL_PATH
    assert JOURNAL_PATH.stat().st_size == form.file_size
    assert compute_sha256(JOURNAL_PATH) == form.sha256

    pdf_info = extract_pdf_info(JOURNAL_PATH)
    assert pdf_info.error == ""
    assert pdf_info.page_count == form.page_count == 9
    assert pdf_info.fillable is False
    assert (
        pdf_info.revision_label
        == "Printable journal for traditional in-person notarial acts in Ohio"
    )
