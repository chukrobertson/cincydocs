# Cincinnati Document Services

Documentation, SOPs, writing, fillable forms, data organization, research, dashboards, photo restoration, and document services for Cincinnati-area individuals and small organizations. Ohio notary by appointment is a secondary offering.

**Website:** [cincydocs.com](https://cincydocs.com) | **Call/Text:** 513 580 4150

---

## Repository Structure

| Directory | Purpose |
|-----------|---------|
| `docs/`   | GitHub Pages website (deployed to cincydocs.com) |
| `forms_library/` | Python CLI and templates for the retained local forms library |
| `data/` | Form manifests, downloads, and extracted text |
| `tests/` | Test suite |

The site is a static HTML/CSS site deployed from the `docs/` folder via GitHub Pages. The forms library is retained in the repository but is not published. Its generator writes an ignored local preview to `build/forms-library-preview/`.

---

## Forms Library

A searchable directory of official public forms with plain-language descriptions. The library is currently available only as a local preview and is not served from cincydocs.com.

**No runtime server required.** Run the CLI locally when adding, updating, or previewing forms.

### Currently in the Local Library

#### Bundled in the Preview (4)
Forms copied into the generated local preview with direct PDF download:

| Form | Agency | Notes |
|------|--------|-------|
| W-9 (Taxpayer ID) | IRS | 6 pages, fillable |
| W-4 (Withholding) | IRS | 5 pages, fillable |
| SS-4 (Employer ID) | IRS | 2 pages, fillable |
| SS-5 (Social Security Card) | SSA | 5 pages, fillable |

#### Agency-Link Only (11)
Forms linked to official sources:

| Form | Agency |
|------|--------|
| 1040 (Income Tax) | IRS |
| BMV 3771 (Power of Attorney) | Ohio BMV |
| BMV 3774 (Certificate of Title) | Ohio BMV |
| BMV 3770 (Casual Sale Title) | Ohio BMV |
| BMV 3811 (Beneficiary Designation) | Ohio BMV |
| SSA-1-BK (Retirement Benefits) | SSA |
| SSA-16-BK (Disability Benefits) | SSA |
| SSA-827 (Disclose Information) | SSA |
| Auditor Forms Directory | Hamilton County |
| Vital Records Requests | Hamilton County |
| Notary FAQ | Ohio Secretary of State |

### Quick Start

```bash
# Create an isolated environment (Python 3.12+; do not copy .venv between machines)
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[dev,pdf]"

# Validate all manifest files
.venv/bin/python -m forms_library validate

# Build the local, non-published preview
.venv/bin/python -m forms_library build

# Check internal HTML, CSS, and asset references
.venv/bin/python tools/check_static_site.py

# Run tests
.venv/bin/python -m pytest tests/ -v
```

### CLI Commands

| Command | Description |
|---------|-------------|
| `validate` | Validate all manifest YAML files |
| `import-manifest <file>` | Validate and preview a manifest |
| `fetch <slug>` | Download a form PDF from its official URL |
| `register <slug> <file>` | Register a manually downloaded PDF |
| `build` | Generate a local preview in `build/forms-library-preview/` |
| `verify --all` | Check all form URLs for broken links (HEAD with GET fallback); saves a Cincinnati-time run timestamp |
| `report` | Generate a maintenance report (broken links, stale verifications) |
| `list-forms` | List forms, filterable by status, category, or jurisdiction |

### Adding a New Form

1. Create or edit a YAML manifest in `data/manifests/`:

```yaml
forms:
  - slug: example-form
    title: Example Official Form
    form_number: FORM-123
    agency: Example Agency
    jurisdiction: Ohio
    category: Motor vehicles
    official_page_url: https://example.gov/form-page
    official_download_url: https://example.gov/form.pdf
    description: Brief description of the form.
    plain_language_summary: Plain-English explanation of what this form is for.
    redistribution_status: review_required
    publication_status: hidden
    review_level: standard
    tags:
      - example
      - plain-language phrase
```

2. Validate:

```bash
python3 -m forms_library validate
```

3. Download the PDF and record metadata (or skip for link-only forms):

```bash
python3 -m forms_library fetch example-form
# OR for manually downloaded files:
python3 -m forms_library register example-form ~/Downloads/form.pdf
```

4. For locally hosted forms, update the manifest with the fetch output:
   - Set `publication_status: locally_hosted`
   - Set `locally_stored: true`
   - Set `local_file_path: data/downloads/<dir>/<filename>`
   - Set `page_count`, `file_size`, `sha256`, `fillable` from the fetch output
   - Set `last_verified_at` to today's date

5. For link-only forms, change `publication_status: hidden` to `link_only`.

6. Build the local preview:

```bash
python3 -m forms_library build
```

### Publication Statuses

| Status | Included in preview? | Description |
|--------|-------------------|-------------|
| `hidden` | No | Not yet reviewed |
| `internal_only` | No | Internal templates only |
| `link_only` | Yes | Links to official source only |
| `locally_hosted` | Yes | PDF copied into the generated local preview |
| `archived` | No | No longer current |
| `superseded` | No | Replaced by newer version |

Only `link_only` and `locally_hosted` forms are included in the generated local preview. The preview output is ignored by Git and is not part of the deployed `docs/` site.

### Review Levels

Forms in sensitive categories (courts, probate, immigration, family, tax, benefits) are automatically assigned `elevated` review level. Review before publication.

### Security

- URL validation blocks private IPs, localhost, and metadata services (SSRF protection)
- Only HTTPS (and explicitly approved HTTP) schemes allowed
- Downloaded files are content-type validated and SHA-256 hashed
- Form filenames are sanitized
- No server-side attack surface (static site)

### Legal and Content Safety

- Every public form page displays issuing agency, jurisdiction, official source, and verification date
- Disclaimers are included on all form detail pages
- Requirements (notarization, witnesses, fees) are only displayed when verified with a source citation
- Cincinnati Document Services is clearly distinguished from government agencies and law firms

### Directory Layout

```
data/
  manifests/          # YAML form manifests (source of truth, committed to git)
    irs.yaml          # IRS forms (W-9, W-4, SS-4, 1040)
    ssa.yaml          # SSA forms (SS-5, SSA-827, SSA-1, SSA-16)
    ohio_bmv.yaml     # Ohio BMV forms (3770, 3771, 3774, 3811)
    ohio_local.yaml   # Hamilton County, Ohio SOS
    internal_templates.yaml  # Internal CDS forms (not public)
  downloads/          # Fetched form PDFs (gitignored — copied into local previews)
    federal/
    ohio/
  extracted_text/     # Extracted PDF text (gitignored)
  reports/            # Generated verify/report output (gitignored)

build/forms-library-preview/  # Generated local preview (gitignored)
  style.css
  forms-search.js
  forms/
    index.html        # Search/browse page
    forms.json        # Client-side search index
    irs-form-w9/      # Per-form directory
      index.html      # Form detail page
      irs-form-w9.pdf # PDF (locally_hosted only)
```

## License

This repository's source code is licensed under the MIT License. The website content in `docs/` is copyright Cincinnati Document Services.
