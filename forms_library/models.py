from __future__ import annotations

import hashlib
import re
from datetime import date
from enum import Enum
from pathlib import Path

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


class PublicationStatus(str, Enum):
    hidden = "hidden"
    internal_only = "internal_only"
    link_only = "link_only"
    locally_hosted = "locally_hosted"
    archived = "archived"
    superseded = "superseded"


class RedistributionStatus(str, Enum):
    permitted = "permitted"
    review_required = "review_required"
    not_permitted = "not_permitted"
    unknown = "unknown"


class FormStatus(str, Enum):
    draft = "draft"
    active = "active"
    superseded = "superseded"
    archived = "archived"


class ReviewLevel(str, Enum):
    standard = "standard"
    elevated = "elevated"


class AgencyType(str, Enum):
    federal = "federal"
    state = "state"
    county = "county"
    city = "city"
    court = "court"
    other = "other"
    internal = "internal"


class JurisdictionType(str, Enum):
    country = "country"
    state = "state"
    county = "county"
    city = "city"


class RelationshipType(str, Enum):
    commonly_used_with = "commonly-used-with"
    replaces = "replaces"
    replaced_by = "replaced-by"
    instruction_for = "instruction-for"
    attachment_to = "attachment-to"
    alternative_language = "alternative-language-version"
    related_topic = "related-topic"


class VerificationStatus(str, Enum):
    unverified = "unverified"
    verified = "verified"
    disputed = "disputed"
    outdated = "outdated"


class ClaimType(str, Enum):
    notarization = "notarization"
    witnesses = "witnesses"
    filing_fee = "filing_fee"
    filing_location = "filing_location"
    deadline = "deadline"
    instructions = "instructions"
    eligibility = "eligibility"
    supporting_documents = "supporting_documents"
    other = "other"


class Jurisdiction(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    type: JurisdictionType
    abbr: str = ""
    parent: str | None = None


class Agency(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    abbreviation: str = ""
    agency_type: AgencyType
    official_domain: str = ""
    jurisdiction: str = ""


class SourceCitation(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    claim_type: ClaimType
    claim_text: str
    source_title: str
    source_url: str = ""
    source_agency: str = ""
    verified_at: date | None = None
    verification_status: VerificationStatus = VerificationStatus.unverified
    notes: str = ""


class FormVersion(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    revision_label: str
    revision_date: date | None = None
    download_url: str = ""
    local_file_path: str = ""
    sha256: str = ""
    discovered_at: date | None = None
    superseded_at: date | None = None
    change_summary: str = ""


class RelatedForm(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    target_slug: str
    relationship_type: RelationshipType
    notes: str = ""


class Tag(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    synonyms: list[str] = Field(default_factory=list)


class Form(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    slug: str
    title: str
    form_number: str = ""
    alternate_titles: list[str] = Field(default_factory=list)
    description: str = ""
    plain_language_summary: str = ""
    agency: str = ""
    jurisdiction: str = ""
    category: str = ""
    subcategory: str = ""
    official_page_url: str = ""
    official_download_url: str = ""
    locally_stored: bool = False
    local_file_path: str = ""
    redistribution_status: RedistributionStatus = RedistributionStatus.review_required
    publication_status: PublicationStatus = PublicationStatus.hidden
    form_status: FormStatus = FormStatus.draft
    language: str = "en"
    page_count: int | None = None
    file_size: int | None = None
    mime_type: str = ""
    sha256: str = ""
    revision_label: str = ""
    revision_date: date | None = None
    effective_date: date | None = None
    expiration_date: date | None = None
    fillable: bool = False
    requires_notarization: bool | None = None
    requires_witnesses: bool | None = None
    filing_fee_summary: str = ""
    filing_location_summary: str = ""
    instructions_summary: str = ""
    accessibility_notes: str = ""
    review_level: ReviewLevel = ReviewLevel.standard
    last_checked_at: date | None = None
    last_verified_at: date | None = None
    created_at: date | None = None
    updated_at: date | None = None
    tags: list[str] = Field(default_factory=list)
    source_citations: list[SourceCitation] = Field(default_factory=list)
    versions: list[FormVersion] = Field(default_factory=list)
    related_forms: list[RelatedForm] = Field(default_factory=list)
    needs_source_verification: bool = False

    @field_validator("slug")
    @classmethod
    def clean_slug(cls, v: str) -> str:
        v = v.lower().strip()
        v = re.sub(r"[^a-z0-9]+", "-", v)
        v = v.strip("-")
        if not v:
            raise ValueError("slug is required")
        return v

    @model_validator(mode="after")
    def elevated_check(self) -> Form:
        elevated_categories = {
            "courts",
            "probate and estates",
            "family",
            "immigration",
        }
        elevated_keywords = [
            "court", "probate", "immigration", "bankruptcy",
            "estate-planning", "custody", "divorce", "criminal",
            "tax", "benefits",
        ]
        is_elevated = (
            self.category.lower() in elevated_categories
            or any(kw in self.title.lower() for kw in elevated_keywords)
        )
        if is_elevated and self.review_level != ReviewLevel.elevated:
            self.review_level = ReviewLevel.elevated
        return self


class Manifest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    forms: list[Form] = Field(default_factory=list)


def compute_sha256(filepath: Path) -> str:
    sha = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha.update(chunk)
    return sha.hexdigest()


ELEVATED_CATEGORIES = frozenset({
    "courts",
    "probate and estates",
    "family",
    "immigration",
})


ELEVATED_KEYWORDS = [
    "court", "probate", "immigration", "bankruptcy",
    "estate-planning", "custody", "divorce", "criminal",
    "tax", "benefits",
]
