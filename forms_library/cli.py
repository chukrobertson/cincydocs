from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from forms_library.builder import Builder
from forms_library.clock import CINCINNATI_TIMEZONE, current_datetime
from forms_library.downloader import DownloadError, download_file
from forms_library.manifest import ManifestError, load_all_manifests, load_manifest
from forms_library.models import (
    Form,
    Manifest,
    compute_sha256,
)
from forms_library.pdf_utils import extract_pdf_info

app = typer.Typer(
    name="forms-library",
    help="CincyDocs Forms Library management CLI",
    no_args_is_help=True,
)

console = Console()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
MANIFESTS_DIR = DATA_DIR / "manifests"
DOWNLOADS_DIR = DATA_DIR / "downloads"
EXTRACTED_DIR = DATA_DIR / "extracted_text"
DOCS_DIR = PROJECT_ROOT / "docs"
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"


def _find_form(slug: str) -> Form:
    manifests = load_all_manifests(MANIFESTS_DIR)
    for m in manifests:
        for f in m.forms:
            if f.slug == slug:
                return f
    raise typer.BadParameter(f"Form not found in any manifest: {slug}")


def _save_manifest(manifest: Manifest | None = None, forms: list[Form] | None = None) -> None:
    pass


def _jurisdiction_dir(jurisdiction: str) -> Path:
    mapping = {
        "united states": "federal",
        "federal": "federal",
        "ohio": "ohio",
        "hamilton county": "hamilton-county",
        "cincinnati": "cincinnati",
    }
    key = jurisdiction.lower().strip()
    dirname = mapping.get(key, key.replace(" ", "-").lower())
    return DOWNLOADS_DIR / dirname


def _form_dest_dir(form: Form) -> Path:
    if form.jurisdiction:
        return _jurisdiction_dir(form.jurisdiction)
    if "irs" in form.agency.lower() or "social security" in form.agency.lower():
        return DOWNLOADS_DIR / "federal"
    return DOWNLOADS_DIR / "other"


@app.command()
def validate(
    manifest: Path | None = typer.Option(None, help="Validate a specific manifest file"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed output"),
) -> None:
    manifests_dir = MANIFESTS_DIR

    if manifest:
        try:
            m = load_manifest(manifest)
            console.print(f"[green]Valid:[/green] {manifest} ({len(m.forms)} forms)")
            if verbose:
                for f in m.forms:
                    console.print(f"  - {f.slug}: {f.title[:60]}")
        except ManifestError as e:
            console.print(f"[red]Invalid:[/red] {manifest}")
            for err in e.errors:
                console.print(f"  [yellow]- {err}[/yellow]")
            raise typer.Exit(code=1)
        return

    errors: list[str] = []
    for path in sorted(manifests_dir.glob("*.yaml")):
        try:
            m = load_manifest(path)
            console.print(f"[green]Valid:[/green] {path.name} ({len(m.forms)} forms)")
        except ManifestError as e:
            console.print(f"[red]Invalid:[/red] {path.name}")
            for err in e.errors:
                console.print(f"  [yellow]- {err}[/yellow]")
            errors.append(str(e))

    if errors:
        console.print(f"\n[yellow]{len(errors)} manifest(s) have errors[/yellow]")
        raise typer.Exit(code=1)


@app.command(name="import-manifest")
def import_manifest(
    manifest_path: Path = typer.Argument(..., help="Path to the manifest YAML file"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Validate only, do not import"),
) -> None:
    try:
        m = load_manifest(manifest_path)
    except ManifestError as e:
        console.print(f"[red]Validation failed:[/red] {manifest_path}")
        for err in e.errors:
            console.print(f"  [yellow]- {err}[/yellow]")
        raise typer.Exit(code=1)

    console.print(f"[green]Manifest validated:[/green] {len(m.forms)} form(s)")

    table = Table(title="Forms")
    table.add_column("Slug", style="cyan")
    table.add_column("Title")
    table.add_column("Status", style="yellow")
    for f in m.forms:
        elevated = " [red](ELEVATED)[/red]" if f.review_level.value == "elevated" else ""
        table.add_row(f.slug, f.title[:60], f.publication_status.value + elevated)

    console.print(table)

    if dry_run:
        console.print("[dim]Dry run — no changes made[/dim]")
        return

    console.print("[green]Manifest imported successfully[/green]")


@app.command()
def fetch(
    slug: str = typer.Argument(..., help="Form slug to download"),
    all_: bool = typer.Option(False, "--all", help="Fetch all forms with download URLs"),
) -> None:
    try:
        import fitz
    except ImportError:
        console.print("[red]PyMuPDF not installed. Install with: pip install pymupdf[/red]")
        raise typer.Exit(code=1)

    if all_:
        manifests = load_all_manifests(MANIFESTS_DIR)
        fetched = 0
        failed = 0
        for m in manifests:
            for form in m.forms:
                if not form.official_download_url:
                    continue
                try:
                    _do_fetch(form)
                    fetched += 1
                except (DownloadError, typer.Exit):
                    failed += 1
        console.print(f"\nFetched: {fetched}, Failed: {failed}")
        return

    form = _find_form(slug)
    _do_fetch(form)


def _do_fetch(form: Form) -> None:
    if not form.official_download_url:
        console.print(f"[yellow]No download URL for: {form.slug}[/yellow]")
        return

    dest_dir = _form_dest_dir(form)
    console.print(f"Downloading [cyan]{form.slug}[/cyan] from {form.official_download_url}")

    try:
        filepath, sha256, size, mime_type = download_file(
            form.official_download_url, form.slug, dest_dir
        )
    except DownloadError as e:
        console.print(f"[red]Download failed:[/red] {e}")
        raise typer.Exit(code=1)

    console.print(f"  Saved: {filepath}")
    console.print(f"  Size: {size:,} bytes")
    console.print(f"  SHA-256: {sha256}")

    pdf_info = extract_pdf_info(filepath)
    if pdf_info.page_count:
        console.print(f"  Pages: {pdf_info.page_count}")
    if pdf_info.fillable:
        console.print("  Fillable: yes")
    if pdf_info.error:
        console.print(f"  [yellow]PDF parse note: {pdf_info.error}[/yellow]")

    console.print("[green]Download complete[/green]")
    console.print("[dim]Run 'forms-library build' to regenerate the public site[/dim]")


@app.command()
def register(
    slug: str = typer.Argument(..., help="Form slug"),
    file: Path = typer.Argument(..., help="Path to the downloaded PDF file", exists=True),
) -> None:
    try:
        import fitz
    except ImportError:
        console.print("[red]PyMuPDF not installed. Install with: pip install pymupdf[/red]")
        raise typer.Exit(code=1)

    form = _find_form(slug)
    dest_dir = _form_dest_dir(form)
    dest_dir.mkdir(parents=True, exist_ok=True)

    sha256 = compute_sha256(file)
    size = file.stat().st_size

    dest_path = dest_dir / file.name
    dest_path.write_bytes(file.read_bytes())

    console.print(f"[green]Registered:[/green] {slug}")
    console.print(f"  Saved: {dest_path}")
    console.print(f"  Size: {size:,} bytes")
    console.print(f"  SHA-256: {sha256}")

    pdf_info = extract_pdf_info(dest_path)
    if pdf_info.page_count:
        console.print(f"  Pages: {pdf_info.page_count}")
    if pdf_info.fillable:
        console.print("  Fillable: yes")

    console.print("[dim]Run 'forms-library build' to regenerate the public site[/dim]")


@app.command()
def build(
    output: Path | None = typer.Option(None, help="Output directory (default: docs/)"),
) -> None:
    output_dir = output or DOCS_DIR

    try:
        manifests = load_all_manifests(MANIFESTS_DIR)
    except ManifestError as e:
        console.print("[red]Manifest errors:[/red]")
        for err in e.errors:
            console.print(f"  [yellow]- {err}[/yellow]")
        raise typer.Exit(code=1)

    forms_count = sum(len(m.forms) for m in manifests)
    if forms_count == 0:
        console.print("[yellow]No forms found in manifests[/yellow]")
        return

    builder = Builder(output_dir=output_dir, templates_dir=TEMPLATES_DIR, data_dir=DATA_DIR)
    builder.build(manifests)

    console.print(f"[green]Built {forms_count} form(s) to {output_dir / 'forms'}[/green]")


@app.command()
def verify(
    slug: str | None = typer.Option(None, help="Verify a specific form's links"),
    all_: bool = typer.Option(False, "--all", help="Verify all forms with URLs"),
    timeout: float = typer.Option(15.0, "--timeout", help="Request timeout in seconds"),
) -> None:
    import httpx

    if slug:
        manifests = load_all_manifests(MANIFESTS_DIR)
        form = None
        for m in manifests:
            for f in m.forms:
                if f.slug == slug:
                    form = f
                    break
        if form is None:
            console.print(f"[red]Form not found: {slug}[/red]")
            raise typer.Exit(code=1)
        forms = [form]
    elif all_:
        manifests = load_all_manifests(MANIFESTS_DIR)
        forms = [f for m in manifests for f in m.forms]
    else:
        console.print("[yellow]Use --slug or --all[/yellow]")
        return

    results = []
    with httpx.Client(
        follow_redirects=True,
        timeout=timeout,
        headers={"User-Agent": "Mozilla/5.0 (compatible; CincyDocsForms/1.0)"},
    ) as client:
        for form in forms:
            urls = [u for u in (form.official_page_url, form.official_download_url) if u]
            for url in urls:
                try:
                    resp = client.head(url)
                    if resp.status_code not in (200, 301, 302, 307, 308):
                        resp = client.get(url)
                    status = resp.status_code
                    final_url = str(resp.url)
                    redirected = final_url != url
                except Exception as e:
                    status = 0
                    final_url = ""
                    redirected = False
                    console.print(f"[red]{form.slug}: {url} — {e}[/red]")
                    results.append({"slug": form.slug, "url": url, "status": 0, "error": str(e)})
                    continue

                color = "green" if 200 <= status < 400 else "red"
                redirect_note = f" -> {final_url}" if redirected else ""
                console.print(f"[{color}]{form.slug}[/{color}]: {url} [{status}]{redirect_note}")
                results.append({
                    "slug": form.slug,
                    "url": url,
                    "status": status,
                    "final_url": final_url,
                    "redirected": redirected,
                })

    generated_at = current_datetime()
    report_data = {
        "generated_at": generated_at.isoformat(),
        "timezone": CINCINNATI_TIMEZONE.key,
        "results": results,
    }
    report_path = DATA_DIR / "reports" / "verify_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report_data, indent=2, default=str))
    console.print(f"\n[dim]Report saved: {report_path}[/dim]")


@app.command()
def report(
    format: str = typer.Option(
        "markdown", "--format", "-f", help="Output format: markdown or json"
    ),
    stale_days: int = typer.Option(
        90, "--stale-days", help="Days before a verification is considered stale"
    ),
) -> None:
    try:
        manifests = load_all_manifests(MANIFESTS_DIR)
    except ManifestError:
        console.print("[red]Manifest errors[/red]")
        raise typer.Exit(code=1)

    forms = [f for m in manifests for f in m.forms]
    generated_at = current_datetime()
    today = generated_at.date()
    report_items: list[dict] = []

    for form in forms:
        issues: list[str] = []

        if not form.official_page_url and not form.official_download_url:
            issues.append("no_official_url")

        if form.last_verified_at:
            age = (today - form.last_verified_at).days
            if age > stale_days:
                issues.append(f"verification_stale_{age}d")
        elif form.publication_status.value not in ("hidden", "draft", "internal_only"):
            issues.append("never_verified_but_public")

        if (
            form.review_level.value == "elevated"
            and form.publication_status.value not in ("hidden", "draft")
        ):
            if not form.last_verified_at:
                issues.append("elevated_no_review")

        for c in form.source_citations:
            if c.verification_status.value == "unverified":
                issues.append(f"unverified_citation:{c.claim_type.value}")

        if issues:
            report_items.append({
                "slug": form.slug,
                "title": form.title,
                "issues": issues,
                "last_verified": (
                    form.last_verified_at.isoformat() if form.last_verified_at else None
                ),
                "publication_status": form.publication_status.value,
                "review_level": form.review_level.value,
            })

    if format == "json":
        report_data = {
            "generated_at": generated_at.isoformat(),
            "timezone": CINCINNATI_TIMEZONE.key,
            "results": report_items,
        }
        console.print_json(json.dumps(report_data, indent=2, default=str))
        return

    console.print(f"# Forms Library Report — {today}\n")
    console.print(f"Generated: {generated_at.isoformat()}\n")
    console.print(f"Total forms: {len(forms)}")
    console.print(f"Forms with issues: {len(report_items)}\n")

    if not report_items:
        console.print("[green]No issues found[/green]")
        return

    for item in report_items:
        console.print(f"## {item['title']} (`{item['slug']}`)")
        console.print(f"- Status: {item['publication_status']} | Review: {item['review_level']}")
        console.print(f"- Last verified: {item['last_verified'] or 'never'}")
        for issue in item["issues"]:
            console.print(f"  - [yellow]{issue}[/yellow]")
        console.print()

    report_path = DATA_DIR / "reports" / f"report_{today.isoformat()}.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    console.print(f"[dim]Report saved: {report_path}[/dim]")


@app.command()
def list_forms(
    category: str | None = typer.Option(None, "--category", "-c", help="Filter by category"),
    jurisdiction: str | None = typer.Option(
        None, "--jurisdiction", "-j", help="Filter by jurisdiction"
    ),
    status: str | None = typer.Option(
        None, "--status", "-s", help="Filter by publication status"
    ),
) -> None:
    try:
        manifests = load_all_manifests(MANIFESTS_DIR)
    except ManifestError:
        console.print("[red]Manifest errors[/red]")
        raise typer.Exit(code=1)

    forms = [f for m in manifests for f in m.forms]

    if category:
        forms = [f for f in forms if f.category.lower() == category.lower()]
    if jurisdiction:
        forms = [f for f in forms if jurisdiction.lower() in f.jurisdiction.lower()]
    if status:
        forms = [f for f in forms if f.publication_status.value == status.lower()]

    if not forms:
        console.print("[dim]No forms match filters[/dim]")
        return

    table = Table(title=f"Forms ({len(forms)})")
    table.add_column("Slug", style="cyan")
    table.add_column("Title")
    table.add_column("Agency")
    table.add_column("Status", style="yellow")
    table.add_column("Verified")

    for f in sorted(forms, key=lambda x: x.slug):
        verified = f.last_verified_at.isoformat() if f.last_verified_at else "—"
        table.add_row(f.slug, f.title[:60], f.agency[:30], f.publication_status.value, verified)

    console.print(table)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
