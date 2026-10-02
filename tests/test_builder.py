from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from forms_library.builder import Builder
from forms_library.models import Form, Manifest, PublicationStatus

TEMPLATES_DIR = Path(__file__).parents[1] / "forms_library" / "templates"


def build_real_page(tmp_path, form: Form) -> str:
    output_dir = tmp_path / "output"
    builder = Builder(output_dir, TEMPLATES_DIR, tmp_path)
    builder.build([Manifest(forms=[form])])
    return (output_dir / "forms" / form.slug / "index.html").read_text()


class TestBuilder:
    def test_undated_form_has_no_false_updated_date(self, tmp_path):
        html = build_real_page(
            tmp_path,
            Form(slug="undated-form", title="Undated Form", publication_status="link_only"),
        )

        assert "Last Updated" not in html
        assert "Content Updated" not in html
        assert "Last Verified" not in html
        assert "Source verification date not recorded." in html

    def test_explicit_verification_date_is_displayed(self, tmp_path):
        html = build_real_page(
            tmp_path,
            Form(
                slug="verified-form",
                title="Verified Form",
                publication_status="link_only",
                last_verified_at=date(2025, 4, 12),
            ),
        )

        assert "<th>Last Checked</th><td>April 12, 2025</td>" in html
        assert "Source verification date not recorded." not in html

    def test_explicit_content_update_date_is_displayed_as_content_update(self, tmp_path):
        html = build_real_page(
            tmp_path,
            Form(
                slug="updated-form",
                title="Updated Form",
                publication_status="link_only",
                updated_at=date(2025, 4, 12),
            ),
        )

        assert "<th>Content Updated</th><td>April 12, 2025</td>" in html
        assert "Last Verified" not in html

    def test_rebuilding_unchanged_content_is_deterministic(self, tmp_path):
        output_dir = tmp_path / "output"
        builder = Builder(output_dir, TEMPLATES_DIR, tmp_path)
        manifest = Manifest(forms=[
            Form(slug="stable-form", title="Stable Form", publication_status="link_only"),
        ])

        builder.build([manifest])
        first = {
            path.relative_to(output_dir): path.read_bytes()
            for path in output_dir.rglob("*")
            if path.is_file()
        }
        builder.build([manifest])
        second = {
            path.relative_to(output_dir): path.read_bytes()
            for path in output_dir.rglob("*")
            if path.is_file()
        }

        assert first == second

    def test_build_excludes_non_public_forms(self, tmp_path):
        output_dir = tmp_path / "output"
        builder = Builder(output_dir, TEMPLATES_DIR, tmp_path)
        manifest = Manifest(forms=[
            Form(
                slug="public-link-form",
                title="Public Link Form",
                publication_status=PublicationStatus.link_only,
            ),
            Form(
                slug="public-local-form",
                title="Public Local Form",
                publication_status=PublicationStatus.locally_hosted,
            ),
            Form(
                slug="hidden-form",
                title="Hidden Form",
                publication_status=PublicationStatus.hidden,
            ),
            Form(
                slug="internal-form",
                title="Internal Form",
                publication_status=PublicationStatus.internal_only,
            ),
            Form(
                slug="archived-form",
                title="Archived Form",
                publication_status=PublicationStatus.archived,
            ),
            Form(
                slug="superseded-form",
                title="Superseded Form",
                publication_status=PublicationStatus.superseded,
            ),
        ])

        builder.build([manifest])

        forms_dir = output_dir / "forms"
        assert (forms_dir / "public-link-form" / "index.html").exists()
        assert (forms_dir / "public-local-form" / "index.html").exists()
        for slug in ("hidden-form", "internal-form", "archived-form", "superseded-form"):
            assert not (forms_dir / slug).exists()

        search_index = json.loads((forms_dir / "forms.json").read_text())
        assert {item["slug"] for item in search_index} == {
            "public-link-form",
            "public-local-form",
        }
        browse_page = (forms_dir / "index.html").read_text()
        assert "Internal Form" not in browse_page

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

    def test_build_copies_local_preview_assets(self, tmp_path):
        output_dir = tmp_path / "output"
        builder = Builder(output_dir, TEMPLATES_DIR, tmp_path)
        manifest = Manifest(forms=[
            Form(
                slug="public-form",
                title="Public Form",
                publication_status="link_only",
            ),
        ])

        builder.build([manifest])

        assert (output_dir / "index.html").is_file()
        assert (output_dir / "style.css").is_file()
        assert (output_dir / "forms-search.js").is_file()
        assert (output_dir / "assets" / "img" / "logo.svg").is_file()

    def test_disclaimer_apostrophe_is_not_double_escaped(self, tmp_path):
        html = build_real_page(
            tmp_path,
            Form(slug="form", title="Form", publication_status="link_only"),
        )

        assert "agency&#39;s current instructions" in html
        assert "&amp;rsquo;" not in html
