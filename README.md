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

A searchable directory of official public forms, plain-language descriptions, and links to authoritative sources. Built as a static site with a Python management CLI.

**No runtime server required.** The public site is static HTML served by GitHub Pages. You run the CLI locally when adding or updating forms.

### Quick Start

```bash
# Install dependencies (Python 3.12+)
pip install --break-system-packages pydantic pyyaml httpx jinja2 typer rich pymupdf

# Validate all manifest files
python3 -m forms_library validate

# Build the static public site
python3 -m forms_library build

# Run tests
python3 -m pytest tests/ -v
```

### CLI Commands

| Command | Description |
|---------|-------------|
| `validate` | Validate all manifest YAML files |
| `import-manifest <file>` | Validate and preview a manifest |
| `fetch --slug <slug>` | Download a form PDF from its official URL |
| `register --slug <slug> --file <path>` | Register a manually downloaded PDF |
| `build` | Generate static HTML pages into `docs/forms/` |
| `verify --all` | Check all form URLs for broken links |
| `report` | Generate a maintenance report (broken links, stale verifications) |
| `list-forms --status hidden` | List forms filtered by status, category, or jurisdiction |

### Adding a New Form

1. Edit or create a YAML manifest in `data/manifests/`:

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

3. Download the PDF (if direct URL is available) or manually download and register:

```bash
python3 -m forms_library fetch --slug example-form
# OR
python3 -m forms_library register --slug example-form --file ~/Downloads/form.pdf
```

4. Review and approve by changing `publication_status: hidden` to `link_only` or `locally_hosted` in the manifest.

5. Build and deploy:

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
| `locally_hosted` | Yes | Form hosted on cincydocs.com |
| `archived` | No | No longer current |
| `superseded` | No | Replaced by newer version |

### Review Levels

Forms in sensitive categories (courts, probate, immigration, family, tax, benefits) are automatically assigned `elevated` review level. These must be reviewed before publication.

### Security

- URL validation blocks private IPs, localhost, and metadata services (SSRF protection)
- Only HTTPS (and explicitly approved HTTP) schemes allowed
- Downloaded files are content-type validated
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
    ohio_bmv.yaml
    irs.yaml
    ssa.yaml
    ohio_local.yaml
    internal_templates.yaml
  downloads/          # Fetched form PDFs (gitignored)
    federal/
    ohio/
    hamilton-county/
    cincinnati/
  extracted_text/     # Extracted PDF text (gitignored)
  reports/            # Generated reports (gitignored)
```

## License

This repository's source code is licensed under the MIT License. The website content in `docs/` is copyright Cincinnati Document Services.
