from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from forms_library.models import Form, Manifest, PublicationStatus

DISCLAIMER = (
    "Cincinnati Document Services is not a law firm or government agency. "
    "This page provides general document information and links to official sources. "
    "It does not provide legal, tax, financial, medical, or eligibility advice. "
    "Requirements can change. Review the issuing agency&rsquo;s current instructions "
    "before relying on a form."
)
PUBLIC_PUBLICATION_STATUSES = {
    PublicationStatus.link_only,
    PublicationStatus.locally_hosted,
}


def _json_default(obj: object) -> str:
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    raise TypeError(f"Cannot serialize {type(obj)}")


def _form_to_dict(form: Form) -> dict:
    data = form.model_dump()
    for field in ("created_at", "updated_at", "revision_date", "effective_date",
                  "expiration_date", "last_checked_at", "last_verified_at"):
        val = data.get(field)
        if isinstance(val, datetime):
            data[field] = val.date().isoformat()
        elif isinstance(val, date):
            data[field] = val.isoformat()
    for citation in data.get("source_citations", []):
        v = citation.get("verified_at")
        if isinstance(v, datetime):
            citation["verified_at"] = v.date().isoformat()
        elif isinstance(v, date):
            citation["verified_at"] = v.isoformat()
    if data.get("local_file_path"):
        data["local_filename"] = Path(data["local_file_path"]).name
    return data


class Builder:
    def __init__(self, output_dir: Path, templates_dir: Path, data_dir: Path) -> None:
        self.output_dir = output_dir
        self.data_dir = data_dir
        self.env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            autoescape=select_autoescape(["html", "xml"]),
        )
        self.env.globals["disclaimer"] = DISCLAIMER
        self.env.globals["pub_status"] = PublicationStatus

    def build(self, manifests: list[Manifest]) -> None:
        forms = self._collect_forms(manifests)
        if not forms:
            return

        public_forms = [f for f in forms if f.publication_status in PUBLIC_PUBLICATION_STATUSES]

        forms_dir = self.output_dir / "forms"
        forms_dir.mkdir(parents=True, exist_ok=True)

        self._clean_non_public_dirs(forms, public_forms, forms_dir)
        self._build_form_pages(public_forms, forms_dir)
        self._copy_local_files(public_forms, forms_dir)
        self._build_search_index(public_forms, forms_dir)
        self._build_browse_page(public_forms, forms_dir)

    def _clean_non_public_dirs(
        self, all_forms: list[Form], public_forms: list[Form], forms_dir: Path
    ) -> None:
        public_slugs = {f.slug for f in public_forms}
        for child in forms_dir.iterdir():
            if child.is_dir() and child.name not in public_slugs:
                import shutil
                shutil.rmtree(child)

    def _collect_forms(self, manifests: list[Manifest]) -> list[Form]:
        seen: set[str] = set()
        forms: list[Form] = []
        for m in manifests:
            for f in m.forms:
                if f.slug not in seen:
                    seen.add(f.slug)
                    forms.append(f)
        return forms

    def _build_form_pages(self, forms: list[Form], forms_dir: Path) -> None:
        template = self.env.get_template("form_detail.html")
        for form in forms:
            slug_dir = forms_dir / form.slug
            slug_dir.mkdir(parents=True, exist_ok=True)
            html = template.render(form=_form_to_dict(form))
            (slug_dir / "index.html").write_text(html)

    def _copy_local_files(self, forms: list[Form], forms_dir: Path) -> None:
        import shutil

        for form in forms:
            if not form.locally_stored or not form.local_file_path:
                continue
            src = self.data_dir.parent / form.local_file_path
            if not src.exists():
                continue
            slug_dir = forms_dir / form.slug
            slug_dir.mkdir(parents=True, exist_ok=True)
            dest = slug_dir / src.name
            shutil.copy2(src, dest)

    def _build_search_index(self, forms: list[Form], forms_dir: Path) -> None:
        index = []
        for form in forms:
            item = {
                "slug": form.slug,
                "title": form.title,
                "form_number": form.form_number,
                "agency": form.agency,
                "jurisdiction": form.jurisdiction,
                "category": form.category,
                "description": form.description,
                "summary": form.plain_language_summary,
                "tags": form.tags,
                "last_verified_at": (
                    form.last_verified_at.isoformat() if form.last_verified_at else None
                ),
                "publication_status": form.publication_status.value,
                "locally_stored": form.locally_stored,
            }
            index.append(item)
        (forms_dir / "forms.json").write_text(
            json.dumps(index, indent=2, default=_json_default)
        )

    def _build_browse_page(self, forms: list[Form], forms_dir: Path) -> None:
        template = self.env.get_template("forms_browse.html")
        html = template.render(forms=[_form_to_dict(f) for f in forms])
        (forms_dir / "index.html").write_text(html)
