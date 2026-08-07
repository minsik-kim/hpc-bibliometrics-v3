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


_ENTRY_RE = re.compile(r'<li class="entry (?:inproceedings|proceedings)".*?</li>', re.S)
_TITLE_RE = re.compile(r'<span class="title" itemprop="name">(.*?)</span>', re.S)
_DOI_RE = re.compile(r'href="https?://doi\.org/([^"?#]+)"')
_KEY_RE = re.compile(r'data-key="([^"]+)"')
_AUTHOR_RE = re.compile(r'<span itemprop="author".*?<span itemprop="name">(.*?)</span>', re.S)
_TAG_RE = re.compile(r'<[^>]+>')


def _text(value: str) -> str:
    return html.unescape(_TAG_RE.sub("", value)).strip()


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
        for entry in _ENTRY_RE.findall(page):
            # The volume-level proceedings entry is not a paper.
            if 'class="entry proceedings"' in entry:
                continue
            title_match = _TITLE_RE.search(entry)
            key_match = _KEY_RE.search(entry)
            if not title_match or not key_match:
                continue
            doi_match = _DOI_RE.search(entry)
            authors = [_text(value) for value in _AUTHOR_RE.findall(entry)]
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
