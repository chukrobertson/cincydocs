# Cincinnati Document Services

CincyDocs is a small, mobile-notary-first website for Cincinnati and surrounding Ohio communities.

- Website: [cincydocs.com](https://cincydocs.com)
- Call or text: 513-580-4150
- Email: hello@cincydocs.com

## Public site

GitHub Pages serves the static site from `docs/`.

| File | Purpose |
|---|---|
| `docs/index.html` | Mobile notary homepage |
| `docs/notary.html` | Service details, pricing guidance, and appointment request |
| `docs/about.html` | Short local-service overview |
| `docs/services.html` | Compatibility redirect to notary services |
| `docs/projects.html` | Compatibility redirect to the homepage |
| `docs/quote.html` | Compatibility redirect to the appointment request |

The appointment form prepares an email in the visitor's browser. It does not submit data to a server, upload files, accept payment, or confirm an appointment.

Preview locally:

```bash
python3 -m http.server 8793 --directory docs
```

## Retained forms library

The Python forms library remains available for future use, but it is not published on cincydocs.com. Its generated preview is written to the ignored `build/forms-library-preview/` directory.

The tracked printable journal is:

```text
forms_library/assets/cds-ohio-notary-journal.pdf
```

Rebuild it after changing `tools/build_notary_journal.py`:

```bash
python tools/build_notary_journal.py
```

The journal is for traditional in-person notarizations. It is not an electronic journal and does not satisfy Ohio's electronic-journal requirements for online notarizations.

## Development

Python 3.12 or newer is expected.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[dev,pdf]"
.venv/bin/python -m forms_library validate
.venv/bin/python -m forms_library build
.venv/bin/python tools/check_static_site.py
.venv/bin/python -m pytest tests/ -q
.venv/bin/ruff check .
```

The forms preview includes only manifest entries marked `link_only` or `locally_hosted`. Downloads, extracted text, reports, previews, private commission records, and local print exports stay out of Git.

## License

Source code is licensed under the MIT License. Website copy and Cincinnati Document Services-branded forms are copyright Cincinnati Document Services.
