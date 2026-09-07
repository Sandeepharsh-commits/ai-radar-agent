"""URL normalization and domain allowlist."""
from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from config import ALLOWED_DOMAINS, TRACKING_PARAMS


def hostname_of(url: str) -> str:
    host = (urlparse(url).hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    return host


def is_allowed_url(url: str) -> bool:
    host = hostname_of(url)
    if not host:
        return False
    for allowed in ALLOWED_DOMAINS:
        allowed = allowed.lower().removeprefix("www.")
        if host == allowed or host.endswith("." + allowed):
            return True
    return False


def normalize_url(url: str) -> str:
    if not url:
        return ""
    parsed = urlparse(url.strip())
    scheme = (parsed.scheme or "https").lower()
    if scheme not in {"http", "https"}:
        return url.strip()
    if scheme == "http":
        scheme = "https"

    host = (parsed.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]

    path = parsed.path or "/"
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")

    query_pairs = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if key.lower() not in TRACKING_PARAMS
    ]
    query_pairs.sort()
    query = urlencode(query_pairs, doseq=True)

    return urlunparse((scheme, host, path, "", query, ""))


def seen_key(url: str) -> str:
    return normalize_url(url) or url
