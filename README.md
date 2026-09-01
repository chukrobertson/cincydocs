# Cincinnati Document Services

Mobile notary, photo restoration, document scanning, digitizing, printing, and digital archival services in Greater Cincinnati. We bring the office to you.

**Website:** [cincydocs.com](https://cincydocs.com) | **Call/Text:** 513 580 4150

---

## Repository Structure

| Directory | Purpose |
|-----------|---------|
| `docs/`   | GitHub Pages website (deployed to cincydocs.com) |
| `forms_library/` | Python CLI for managing the public forms library |
| `data/` | Form manifests, downloads, and extracted text |
| `tests/` | Test suite |

The site is a static HTML/CSS site deployed from the `docs/` folder via GitHub Pages. The forms library generates static HTML pages into `docs/forms/`.

---

## Forms Library

A searchable directory of official public forms with plain-language descriptions. 15 forms live at [cincydocs.com/forms/](https://cincydocs.com/forms/).

**No runtime server required.** The public site is static HTML served by GitHub Pages. You run the CLI locally when adding or updating forms.

### Currently Published

#### Locally Hosted (4)
Forms stored on cincydocs.com with direct PDF download:

| Form | Agency | Notes |
|------|--------|-------|
| W-9 (Taxpayer ID) | IRS | 6 pages, fillable |
| W-4 (Withholding) | IRS | 5 pages, fillable |
| SS-4 (Employer ID) | IRS | 2 pages, fillable |
| SS-5 (Social Security Card) | SSA | 5 pages, fillable |

#### Link-Only (11)
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

# Build the static public site
.venv/bin/python -m forms_library build

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
| `build` | Generate static HTML pages into `docs/forms/` |
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

6. Build and deploy:

```bash
python3 -m forms_library build
git add docs/forms/ data/manifests/
git commit -m "Add example form"
git push
```

### Publication Statuses

| Status | Publicly visible? | Description |
|--------|-------------------|-------------|
| `hidden` | No | Not yet reviewed |
| `internal_only` | No | Internal templates only |
| `link_only` | Yes | Links to official source only |
| `locally_hosted` | Yes | PDF copied into docs/forms/, served from cincydocs.com |
| `archived` | No | No longer current |
| `superseded` | No | Replaced by newer version |

Only `link_only` and `locally_hosted` forms are included in the public site output.

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
  downloads/          # Fetched form PDFs (gitignored — copies go to docs/forms/)
    federal/
    ohio/
  extracted_text/     # Extracted PDF text (gitignored)
  reports/            # Generated verify/report output (gitignored)

docs/forms/           # Generated static site (committed for GitHub Pages)
  index.html          # Search/browse page
  forms.json          # Client-side search index
  irs-form-w9/        # Per-form directory
    index.html         #   Form detail page
    irs-form-w9.pdf    #   PDF (locally_hosted only)
```

## License

This repository's source code is licensed under the MIT License. The website content in `docs/` is copyright Cincinnati Document Services.
