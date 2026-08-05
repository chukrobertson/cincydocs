from __future__ import annotations

import pytest
import yaml
from pydantic import ValidationError

from forms_library.manifest import ManifestError, load_manifest
from forms_library.models import (
    ClaimType,
    Form,
    FormVersion,
    PublicationStatus,
    RelatedForm,
    RelationshipType,
    ReviewLevel,
    SourceCitation,
    VerificationStatus,
    compute_sha256,
)


class TestFormModel:
    def test_valid_form(self):
        form = Form(
            slug="test-form",
            title="Test Form",
            agency="Test Agency",
            jurisdiction="Ohio",
            category="Motor vehicles",
        )
        assert form.slug == "test-form"
        assert form.publication_status == PublicationStatus.hidden
        assert form.form_status.value == "draft"

    def test_slug_validation(self):
        with pytest.raises(ValidationError):
            Form(slug="!!!", title="Test")

        with pytest.raises(ValidationError):
            Form(slug="", title="Test")

        with pytest.raises(ValidationError):
            Form(slug="   ", title="Test")

    def test_slug_auto_clean(self):
        form = Form(
            slug=" Ohio-BMV-Vehicle-Power-of-Attorney ",
            title="Ohio BMV Vehicle Power of Attorney",
        )
        assert form.slug == "ohio-bmv-vehicle-power-of-attorney"

    def test_elevated_review_court_category(self):
        form = Form(
            slug="court-form",
            title="Some Court Form",
            category="Courts",
        )
        assert form.review_level == ReviewLevel.elevated

    def test_elevated_review_immigration(self):
        form = Form(
            slug="immigration-form",
            title="Immigration Form I-130",
            category="Immigration",
        )
        assert form.review_level == ReviewLevel.elevated

    def test_elevated_review_tax_keyword(self):
        form = Form(
            slug="some-tax-form",
            title="Tax Form 1040",
            category="Taxes",
        )
        assert form.review_level == ReviewLevel.elevated

    def test_elevated_review_keywords(self):
        for kw in ["court", "probate", "immigration", "bankruptcy",
                     "estate-planning", "custody", "divorce", "criminal",
                     "tax", "benefits"]:
            form = Form(slug=f"test-{kw}", title=f"{kw} form")
            assert (
                form.review_level == ReviewLevel.elevated
            ), f"Keyword '{kw}' should trigger elevated review"

    def test_standard_review_motor_vehicles(self):
        form = Form(
            slug="bmv-form",
            title="BMV Power of Attorney",
            category="Motor vehicles",
        )
        assert form.review_level == ReviewLevel.standard

    def test_default_values(self):
        form = Form(slug="test", title="Test")
        assert form.publication_status == PublicationStatus.hidden
        assert form.form_status.value == "draft"
        assert form.language == "en"
        assert form.review_level == ReviewLevel.standard
        assert form.tags == []
        assert form.source_citations == []
        assert form.versions == []
        assert form.related_forms == []

    def test_source_citation(self):
        citation = SourceCitation(
            claim_type=ClaimType.notarization,
            claim_text="This form requires notarization",
            source_title="Ohio BMV Instructions",
            source_url="https://example.com",
            source_agency="Ohio BMV",
            verification_status=VerificationStatus.verified,
        )
        assert citation.claim_type == ClaimType.notarization

    def test_form_version(self):
        version = FormVersion(
            revision_label="2024-01",
            sha256="abc123",
        )
        assert version.revision_label == "2024-01"

    def test_related_form(self):
        rel = RelatedForm(
            target_slug="other-form",
            relationship_type=RelationshipType.instruction_for,
            notes="Provides instructions",
        )
        assert rel.target_slug == "other-form"


class TestComputeSHA256:
    def test_sha256(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_bytes(b"hello world")
        sha = compute_sha256(f)
        expected = "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
        assert sha == expected

    def test_sha256_large_file(self, tmp_path):
        f = tmp_path / "large.bin"
        f.write_bytes(b"x" * 100000)
        sha = compute_sha256(f)
        assert len(sha) == 64


class TestPublicationStatusRules:
    def test_new_form_defaults_to_hidden(self):
        form = Form(slug="test", title="Test")
        assert form.publication_status == PublicationStatus.hidden

    def test_can_set_to_locally_hosted(self):
        form = Form(
            slug="test",
            title="Test",
            publication_status=PublicationStatus.locally_hosted,
            locally_stored=True,
        )
        assert form.publication_status == PublicationStatus.locally_hosted

    def test_can_set_to_link_only(self):
        form = Form(
            slug="test",
            title="Test",
            publication_status=PublicationStatus.link_only,
        )
        assert form.publication_status == PublicationStatus.link_only

    def test_superseded_form(self):
        form = Form(
            slug="test",
            title="Test",
            publication_status=PublicationStatus.superseded,
        )
        assert form.publication_status == PublicationStatus.superseded


class TestManifestValidation:
    def test_load_valid_manifest(self, tmp_path):
        data = {
            "forms": [
                {
                    "slug": "test-form",
                    "title": "Test Form",
                    "agency": "Test Agency",
                    "jurisdiction": "Ohio",
                    "category": "Motor vehicles",
                }
            ]
        }
        manifest_path = tmp_path / "test.yaml"
        manifest_path.write_text(yaml.dump(data))
        m = load_manifest(manifest_path)
        assert len(m.forms) == 1
        assert m.forms[0].slug == "test-form"

    def test_empty_manifest(self, tmp_path):
        data = {"forms": []}
        manifest_path = tmp_path / "empty.yaml"
        manifest_path.write_text(yaml.dump(data))
        with pytest.raises(ManifestError, match="no forms"):
            load_manifest(manifest_path)

    def test_missing_forms_key(self, tmp_path):
        data = {"agencies": []}
        manifest_path = tmp_path / "bad.yaml"
        manifest_path.write_text(yaml.dump(data))
        with pytest.raises(ManifestError, match="contains no forms"):
            load_manifest(manifest_path)

    def test_invalid_yaml(self, tmp_path):
        manifest_path = tmp_path / "bad.yaml"
        manifest_path.write_text("forms: [invalid: yaml: :::")
        with pytest.raises(ManifestError, match="Invalid YAML"):
            load_manifest(manifest_path)

    def test_missing_file(self, tmp_path):
        manifest_path = tmp_path / "nonexistent.yaml"
        with pytest.raises(ManifestError, match="not found"):
            load_manifest(manifest_path)

    def test_invalid_form_data(self, tmp_path):
        data = {
            "forms": [
                {"slug": "", "title": ""}  # empty slug
            ]
        }
        manifest_path = tmp_path / "bad_form.yaml"
        manifest_path.write_text(yaml.dump(data))
        with pytest.raises(ManifestError, match="validation error"):
            load_manifest(manifest_path)

    def test_multiple_forms(self, tmp_path):
        data = {
            "forms": [
                {"slug": "form-a", "title": "Form A", "agency": "Agency"},
                {"slug": "form-b", "title": "Form B", "agency": "Agency"},
            ]
        }
        manifest_path = tmp_path / "multi.yaml"
        manifest_path.write_text(yaml.dump(data))
        m = load_manifest(manifest_path)
        assert len(m.forms) == 2

    def test_form_with_all_fields(self, tmp_path):
        data = {
            "forms": [
                {
                    "slug": "complete-form",
                    "title": "Complete Form",
                    "form_number": "ABC-123",
                    "alternate_titles": ["Alt Title"],
                    "description": "A test form",
                    "plain_language_summary": "Plain English summary",
                    "agency": "Test Agency",
                    "jurisdiction": "Ohio",
                    "category": "Motor vehicles",
                    "subcategory": "Title transfers",
                    "official_page_url": "https://example.gov/page",
                    "official_download_url": "https://example.gov/form.pdf",
                    "locally_stored": False,
                    "local_file_path": "",
                    "redistribution_status": "permitted",
                    "publication_status": "hidden",
                    "form_status": "draft",
                    "language": "en",
                    "page_count": 2,
                    "file_size": 102400,
                    "mime_type": "application/pdf",
                    "sha256": "abc123",
                    "revision_label": "2024-01",
                    "revision_date": "2024-01-15",
                    "fillable": True,
                    "requires_notarization": True,
                    "requires_witnesses": False,
                    "filing_fee_summary": "$20 fee required",
                    "filing_location_summary": "Any BMV office",
                    "instructions_summary": "Complete and sign",
                    "accessibility_notes": "Large print available",
                    "review_level": "standard",
                    "tags": ["vehicle", "title"],
                    "source_citations": [
                        {
                            "claim_type": "notarization",
                            "claim_text": "Must be notarized",
                            "source_title": "BMV Instructions",
                            "source_url": "https://example.gov",
                            "source_agency": "Ohio BMV",
                            "verification_status": "verified",
                        }
                    ],
                    "versions": [
                        {
                            "revision_label": "2023-06",
                            "sha256": "def456",
                        }
                    ],
                    "related_forms": [
                        {
                            "target_slug": "other-form",
                            "relationship_type": "commonly-used-with",
                            "notes": "",
                        }
                    ],
                }
            ]
        }
        manifest_path = tmp_path / "complete.yaml"
        manifest_path.write_text(yaml.dump(data))
        m = load_manifest(manifest_path)
        assert len(m.forms) == 1
        f = m.forms[0]
        assert f.form_number == "ABC-123"
        assert f.page_count == 2
        assert f.fillable is True
        assert f.requires_notarization is True
        assert len(f.source_citations) == 1
        assert len(f.versions) == 1
        assert len(f.related_forms) == 1
