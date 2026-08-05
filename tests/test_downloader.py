from __future__ import annotations

import hashlib

import httpx
import pytest

from forms_library.downloader import (
    DownloadError,
    _safe_filename,
    _validate_url,
    download_file,
)


class TestURLValidation:
    def test_https_url(self):
        url = "https://example.gov/form.pdf"
        assert _validate_url(url) == url

    def test_http_url(self):
        url = "http://example.gov/form.pdf"
        assert _validate_url(url) == url

    def test_blocks_file_url(self):
        with pytest.raises(DownloadError, match="Blocked URL scheme"):
            _validate_url("file:///etc/passwd")

    def test_blocks_ftp_url(self):
        with pytest.raises(DownloadError, match="Blocked URL scheme"):
            _validate_url("ftp://example.com/file.pdf")

    def test_blocks_localhost(self):
        with pytest.raises(DownloadError, match="Blocked"):
            _validate_url("http://localhost:8080/admin")

    def test_blocks_127_0_0_1(self):
        with pytest.raises(DownloadError, match="Blocked"):
            _validate_url("http://127.0.0.1:8080/form.pdf")

    def test_blocks_private_ip(self):
        with pytest.raises(DownloadError, match="Blocked"):
            _validate_url("http://192.168.1.1/form.pdf")

    def test_blocks_metadata_service(self):
        with pytest.raises(DownloadError, match="Blocked"):
            _validate_url("http://169.254.169.254/latest/meta-data")

    def test_blocks_no_hostname(self):
        with pytest.raises(DownloadError, match="no hostname"):
            _validate_url("https://")


class TestSafeFilename:
    def test_pdf_filename(self):
        assert _safe_filename("my-form", "application/pdf") == "my-form.pdf"

    def test_unknown_type(self):
        assert _safe_filename("my-form", "application/octet-stream") == "my-form.pdf"

    def test_other_type(self):
        assert _safe_filename("test", "image/png") == "test.bin"

    def test_sanitize_special_chars(self):
        name = _safe_filename("form with spaces & symbols!", "application/pdf")
        assert " " not in name
        assert "&" not in name

    def test_truncate_long(self):
        long_slug = "a" * 200
        name = _safe_filename(long_slug, "application/pdf")
        assert len(name) <= 151


class TestDownloadFile:
    def test_download_pdf(self, tmp_path):
        content = b"%PDF-1.4 fake pdf content"
        url = "https://example.gov/form.pdf"

        with httpx.Client(
            transport=httpx.MockTransport(
                lambda req: httpx.Response(
                    200,
                    content=content,
                    headers={"content-type": "application/pdf"},
                )
            )
        ) as client:
            path, sha, size, mime = download_file(url, "test-form", tmp_path, client=client)

        assert path.exists()
        assert path.read_bytes() == content
        assert size == len(content)
        assert sha == hashlib.sha256(content).hexdigest()
        assert mime == "application/pdf"

    def test_follow_redirects(self, tmp_path):
        content = b"%PDF-1.5 redirected pdf"

        def handler(request):
            if request.url.path == "/old":
                return httpx.Response(301, headers={"location": "https://example.gov/new.pdf"})
            return httpx.Response(200, content=content, headers={"content-type": "application/pdf"})

        with httpx.Client(
            transport=httpx.MockTransport(handler),
            follow_redirects=True,
        ) as client:
            path, sha, size, _ = download_file(
                "https://example.gov/old", "test-form", tmp_path, client=client
            )

        assert path.read_bytes() == content
        assert sha == hashlib.sha256(content).hexdigest()

    def test_rejects_html_content(self, tmp_path):
        html_content = b"<!DOCTYPE html><html>Login page</html>"

        with httpx.Client(
            transport=httpx.MockTransport(
                lambda req: httpx.Response(
                    200,
                    content=html_content,
                    headers={"content-type": "text/html"},
                )
            )
        ) as client:
            with pytest.raises(DownloadError, match="HTML content"):
                download_file("https://example.gov/form", "test-form", tmp_path, client=client)

    def test_http_error(self, tmp_path):
        with httpx.Client(
            transport=httpx.MockTransport(
                lambda req: httpx.Response(404)
            )
        ) as client:
            with pytest.raises(DownloadError, match="Download failed"):
                download_file(
                    "https://example.gov/missing.pdf",
                    "test-form",
                    tmp_path,
                    client=client,
                )
