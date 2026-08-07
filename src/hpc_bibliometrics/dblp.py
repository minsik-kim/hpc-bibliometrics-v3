from __future__ import annotations

import html
import re
import ssl
import time
from collections.abc import Iterator
from typing import Any
from urllib.parse import urljoin

import httpx

from .config import VenueSpec


class DblpError(RuntimeError):
    """Raised when DBLP cannot provide a conference roster."""


# DBLP's HTML evolves over time. Do not require a specific class ordering or
# exact attribute set: first isolate every <li>, then retain entries whose
# class list contains "entry" and "inproceedings".
_LI_RE = re.compile(r"<li\b(?P<attrs>[^>]*)>(?P<body>.*?)</li>", re.S | re.I)
_CLASS_RE = re.compile(r'''\bclass\s*=\s*["']([^"']*)["']''', re.I)
_TITLE_RE = re.compile(
    r'''<span\b(?=[^>]*\bclass\s*=\s*["'][^"']*\btitle\b[^"']*["'])(?=[^>]*\bitemprop\s*=\s*["']name["'])[^>]*>(.*?)</span>''',
    re.S | re.I,
)
_DOI_RE = re.compile(r'''href\s*=\s*["']https?://doi\.org/([^"'?#]+)["']''', re.I)
_KEY_RE = re.compile(r'''\bdata-key\s*=\s*["']([^"']+)["']''', re.I)
_ID_RE = re.compile(r'''\bid\s*=\s*["']([^"']+)["']''', re.I)
_AUTHOR_RE = re.compile(
    r'''<span\b(?=[^>]*\bitemprop\s*=\s*["']author["'])[^>]*>.*?<span\b(?=[^>]*\bitemprop\s*=\s*["']name["'])[^>]*>(.*?)</span>''',
    re.S | re.I,
)
_TAG_RE = re.compile(r"<[^>]+>")


def _text(value: str) -> str:
    return html.unescape(_TAG_RE.sub("", value)).strip()


def _paper_entries(page: str) -> Iterator[tuple[str, str]]:
    for match in _LI_RE.finditer(page):
        attrs = match.group("attrs")
        class_match = _CLASS_RE.search(attrs)
        classes = set(class_match.group(1).split()) if class_match else set()
        if "entry" in classes and "inproceedings" in classes:
            yield attrs, match.group("body")


class DblpClient:
    def __init__(
        self,
        *,
        timeout: float = 45.0,
        max_retries: int = 4,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        verify: ssl.SSLContext | bool = True
        if transport is None:
            try:
                import truststore

                verify = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            except ImportError:
                verify = True
        self.max_retries = max_retries
        self._client = httpx.Client(
            base_url="https://dblp.org/",
            timeout=timeout,
            follow_redirects=True,
            transport=transport,
            verify=verify,
            headers={"User-Agent": "hpc-bibliometrics-v3/0.1 (bibliometric research)"},
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "DblpClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def _get_text(self, path: str) -> str:
        for attempt in range(self.max_retries):
            try:
                response = self._client.get(path)
                if response.status_code in {429, 500, 502, 503, 504}:
                    time.sleep(min(8.0, 2**attempt))
                    continue
                if response.is_error:
                    raise DblpError(f"DBLP returned HTTP {response.status_code} for {path}")
                return response.text
            except DblpError:
                raise
            except httpx.HTTPError:
                if attempt + 1 < self.max_retries:
                    time.sleep(min(8.0, 2**attempt))
        raise DblpError(f"DBLP request failed for {path}") from None

    def iter_proceedings(self, venue: VenueSpec, year: int) -> Iterator[dict[str, Any]]:
        path = venue.dblp_toc_pattern.format(year=year)
        page = self._get_text(path)
        found = 0
        for attrs, body in _paper_entries(page):
            title_match = _TITLE_RE.search(body)
            key_match = _KEY_RE.search(attrs) or _ID_RE.search(attrs)
            if not title_match or not key_match:
                continue
            doi_match = _DOI_RE.search(body)
            authors = [_text(value) for value in _AUTHOR_RE.findall(body)]
            found += 1
            yield {
                "dblp_key": html.unescape(key_match.group(1)),
                "doi": html.unescape(doi_match.group(1)).lower() if doi_match else None,
                "title": _text(title_match.group(1)),
                "publication_year": year,
                "authors": authors,
                "dblp_url": urljoin("https://dblp.org/", path),
            }
        if found == 0:
            raise DblpError(
                f"DBLP returned no main-conference papers for {venue.key.upper()} {year}; "
                "refusing to cache an empty roster."
            )
