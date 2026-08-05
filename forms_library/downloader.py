from __future__ import annotations

import hashlib
import ipaddress
import socket
from pathlib import Path
from urllib.parse import urlparse

import httpx

BLOCKED_HOSTS = {
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "::1",
    "[::1]",
    "metadata.google.internal",
    "169.254.169.254",
}

BLOCKED_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
]

MAX_DOWNLOAD_SIZE = 50 * 1024 * 1024
TIMEOUT = 30.0
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/octet-stream",
}

ALLOWED_SCHEMES = {"https", "http"}


class DownloadError(Exception):
    pass


def _is_private_host(host: str) -> bool:
    host_lower = host.lower().strip("[]")
    if host_lower in BLOCKED_HOSTS:
        return True
    try:
        addr = ipaddress.ip_address(host_lower)
    except ValueError:
        try:
            resolved = socket.getaddrinfo(host_lower, None)
            for _, _, _, _, sockaddr in resolved:
                ip = sockaddr[0]
                addr = ipaddress.ip_address(ip)
                if addr.is_private or addr.is_loopback or addr.is_link_local:
                    return True
        except socket.gaierror:
            return False
        return False
    if addr.is_private or addr.is_loopback or addr.is_link_local:
        return True
    if addr.is_multicast or addr.is_reserved:
        return True
    for net in BLOCKED_NETWORKS:
        if addr in net:
            return True
    return False


def _validate_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in ALLOWED_SCHEMES:
        raise DownloadError(f"Blocked URL scheme: {parsed.scheme}")
    if parsed.scheme == "http":
        pass
    host = (parsed.hostname or "").lower()
    if not host:
        raise DownloadError("URL has no hostname")
    if _is_private_host(host):
        raise DownloadError(f"Blocked private/internal host: {host}")
    return url


def _safe_filename(slug: str, mime_type: str) -> str:
    if "pdf" in mime_type or mime_type == "application/octet-stream":
        ext = ".pdf"
    else:
        ext = ".bin"
    safe_slug = "".join(c for c in slug if c.isalnum() or c in "-_")[:100]
    return f"{safe_slug}{ext}"


def download_file(
    url: str,
    slug: str,
    dest_dir: Path,
    *,
    client: httpx.Client | None = None,
) -> tuple[Path, str, int, str]:
    url = _validate_url(url)
    dest_dir.mkdir(parents=True, exist_ok=True)

    close_client = False
    if client is None:
        client = httpx.Client(
            follow_redirects=True,
            timeout=TIMEOUT,
            headers={"User-Agent": "CincyDocsForms/1.0 (+https://cincydocs.com)"},
        )
        close_client = True

    try:
        response = client.get(url)
        response.raise_for_status()

        mime_type = response.headers.get("content-type", "").split(";")[0].strip()
        if mime_type not in ALLOWED_CONTENT_TYPES:
            if "html" in mime_type and mime_type not in ALLOWED_CONTENT_TYPES:
                raise DownloadError(
                    f"Got HTML content ({mime_type}) instead of PDF from {url}. "
                    f"Use 'register' command if downloaded manually."
                )

        content = response.read()
        if len(content) > MAX_DOWNLOAD_SIZE:
            raise DownloadError(
                f"File too large: {len(content)} bytes (max {MAX_DOWNLOAD_SIZE})"
            )

        sha256 = hashlib.sha256(content).hexdigest()
        filename = _safe_filename(slug, mime_type)
        dest = dest_dir / filename
        dest.write_bytes(content)

        return dest, sha256, len(content), mime_type or "application/pdf"
    except httpx.HTTPError as e:
        raise DownloadError(f"Download failed for {url}: {e}") from e
    finally:
        if close_client:
            client.close()
