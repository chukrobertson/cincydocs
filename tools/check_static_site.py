"""Check local HTML and CSS references against the committed docs site."""

from __future__ import annotations

import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1] / "docs"
CSS_URL_RE = re.compile(r"url\(\s*(['\"]?)(.*?)\1\s*\)")
IGNORED_SCHEMES = {"data", "http", "https", "mailto", "sms", "tel", "javascript"}


class ReferenceParser(HTMLParser):
    def __init__(self, source: Path) -> None:
        super().__init__(convert_charrefs=True)
        self.source = source
        self.references: list[tuple[str, str]] = []
        self.ids: set[str] = set()

    def handle_starttag(self, _tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for name, value in attrs:
            if name in {"id", "name"} and value:
                self.ids.add(value)
            if name in {"href", "src"} and value:
                self.references.append((name, value))


def local_target(source: Path, reference: str) -> Path | None:
    parsed = urlsplit(reference)
    if parsed.scheme.lower() in IGNORED_SCHEMES or parsed.netloc:
        return None
    if not parsed.path:
        return None

    path = Path(unquote(parsed.path.lstrip("/"))) if parsed.path.startswith("/") else Path(
        unquote(parsed.path)
    )
    target = ROOT / path if parsed.path.startswith("/") else source.parent / path
    if target.suffix == "" or reference.endswith("/"):
        target /= "index.html"
    return target.resolve()


def check_html(path: Path, page_ids: dict[Path, set[str]], missing: list[str]) -> None:
    parser = ReferenceParser(path)
    parser.feed(path.read_text(encoding="utf-8"))
    page_ids[path.resolve()] = parser.ids
    for attribute, reference in parser.references:
        parsed = urlsplit(reference)
        target = local_target(path, reference)
        if target is None:
            if parsed.fragment and not parsed.scheme and not parsed.netloc and not parsed.path:
                fragment = unquote(parsed.fragment)
                if fragment not in page_ids.get(path.resolve(), set()):
                    missing.append(f"{path}: {attribute} -> missing #{fragment} in {reference}")
            continue
        try:
            target.relative_to(ROOT.resolve())
        except ValueError:
            missing.append(f"{path}: {attribute} escapes docs/: {reference}")
            continue
        if not target.is_file():
            missing.append(f"{path}: {attribute} -> {reference}")
        elif parsed.fragment:
            fragment = unquote(parsed.fragment)
            if fragment not in page_ids.get(target, set()):
                missing.append(f"{path}: {attribute} -> missing #{fragment} in {reference}")


def check_css(path: Path, missing: list[str]) -> None:
    for match in CSS_URL_RE.finditer(path.read_text(encoding="utf-8")):
        reference = match.group(2).strip()
        target = local_target(path, reference)
        if target is None:
            continue
        if not target.is_file():
            missing.append(f"{path}: url() -> {reference}")


def main() -> int:
    missing: list[str] = []
    page_ids: dict[Path, set[str]] = {}
    html_paths = sorted(ROOT.rglob("*.html"))
    for path in html_paths:
        parser = ReferenceParser(path)
        parser.feed(path.read_text(encoding="utf-8"))
        page_ids[path.resolve()] = parser.ids
    for path in html_paths:
        check_html(path, page_ids, missing)
    for path in sorted(ROOT.rglob("*.css")):
        check_css(path, missing)

    if missing:
        print("Broken local site references:")
        print("\n".join(f"- {item}" for item in missing))
        return 1

    html_count = sum(1 for _ in ROOT.rglob("*.html"))
    print(f"Checked {html_count} HTML files and local CSS asset references.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
