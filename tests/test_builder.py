from __future__ import annotations

import json

from forms_library.builder import Builder
from forms_library.models import Form, Manifest


class TestBuilder:
    def test_collect_forms_deduplication(self):
        builder = Builder(None, None, None)  # type: ignore[arg-type]
        manifest1 = Manifest(forms=[
            Form(slug="form-a", title="Form A"),
            Form(slug="form-b", title="Form B"),
        ])
        manifest2 = Manifest(forms=[
            Form(slug="form-a", title="Form A Duplicate"),
            Form(slug="form-c", title="Form C"),
        ])
        forms = builder._collect_forms([manifest1, manifest2])
        slugs = [f.slug for f in forms]
        assert slugs == ["form-a", "form-b", "form-c"]

    def test_build_form_pages(self, tmp_path):
        output_dir = tmp_path / "output"
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        (templates_dir / "form_detail.html").write_text(
            "<html><body>{{ form.title }} - {{ form.slug }}</body></html>"
        )
        (templates_dir / "forms_browse.html").write_text("{{ forms | length }}")

        builder = Builder(output_dir, templates_dir, tmp_path)
        manifest = Manifest(forms=[
            Form(
                slug="test-form",
                title="Test Form",
                agency="Agency",
                publication_status="link_only",
            ),
        ])
        builder.build([manifest])

        page = (output_dir / "forms" / "test-form" / "index.html").read_text()
        assert "Test Form" in page
        assert "test-form" in page

    def test_search_index(self, tmp_path):
        output_dir = tmp_path / "output"
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        (templates_dir / "form_detail.html").write_text("{{ form.title }}")
        (templates_dir / "forms_browse.html").write_text("{{ forms | length }}")

        builder = Builder(output_dir, templates_dir, tmp_path)
        manifest = Manifest(forms=[
            Form(slug="form-a", title="Form A", tags=["tag1"], publication_status="link_only"),
            Form(slug="form-b", title="Form B", tags=["tag2"], publication_status="link_only"),
        ])
        builder.build([manifest])

        index_data = json.loads((output_dir / "forms" / "forms.json").read_text())
        assert len(index_data) == 2
        assert index_data[0]["slug"] == "form-a"
        assert index_data[1]["tags"] == ["tag2"]

    def test_form_slug_in_url(self, tmp_path):
        output_dir = tmp_path / "output"
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        (templates_dir / "form_detail.html").write_text("{{ form.title }}")
        (templates_dir / "forms_browse.html").write_text("browse")

        builder = Builder(output_dir, templates_dir, tmp_path)
        manifest = Manifest(forms=[
            Form(slug="irs-form-w9", title="W-9 Form", publication_status="link_only"),
        ])
        builder.build([manifest])

        assert (output_dir / "forms" / "irs-form-w9" / "index.html").exists()
        assert (output_dir / "forms" / "index.html").exists()
