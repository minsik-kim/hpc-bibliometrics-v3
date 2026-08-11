from __future__ import annotations

import html
import re
import ssl
import time
from collections.abc import Iterator
from typing import Any

import httpx
from bs4 import BeautifulSoup

from .config import VenueSpec


class DblpError(RuntimeError):
    """Raised when DBLP cannot provide a conference roster."""


def _strip_doi(value: str | None) -> str | None:
    if not value:
        return None
    text = html.unescape(value).strip()
    lower = text.lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if lower.startswith(prefix):
            text = text[len(prefix) :]
            break
    return text.lower() or None


def _sc_2018_doi(entry: Any, venue: VenueSpec, year: int) -> str | None:
    """Recover SC 2018's IEEE DOI from DBLP's legacy article pagination."""
    if venue.key != "sc" or year != 2018:
        return None
    pagination = entry.select_one('[itemprop="pagination"]')
    match = re.fullmatch(r"(\d+):\d+-(?:\1:)?\d+", pagination.get_text(strip=True) if pagination else "")
    if match is None:
        return None
    article = int(match.group(1))
    return f"10.1109/sc.2018.{article + 3:05d}"


def _publisher_doi(entry: Any, key: str, venue: VenueSpec, year: int) -> str | None:
    """Recover DOI values from documented publisher-link exceptions."""
    if venue.key == "isc" and year == 2025:
        link = entry.select_one('a[href*="ieeexplore.ieee.org/document/"]')
        href = str(link.get("href") or "") if link is not None else ""
        match = re.search(r"/document/(\d+)", href)
        if match is not None:
            return f"10.23919/isc.2025.{match.group(1)}"
    if key == "conf/ccgrid/LiuA17":
        return "10.1109/ccgrid.2017.95"
    return None


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
        found = 0
        seen_keys: set[str] = set()
        paths = venue.dblp_toc_paths(year)

        for path in paths:
            soup = BeautifulSoup(self._get_text(path), "html.parser")
            page_found = 0

            for entry in soup.select("li.entry.inproceedings"):
                key = entry.get("data-key") or entry.get("id")
                title_node = entry.select_one("span.title")
                if not key or title_node is None:
                    continue
                page_found += 1
                normalized_key = html.unescape(str(key))
                if normalized_key in seen_keys:
                    continue

                authors = []
                for author_node in entry.select('[itemprop="author"]'):
                    name_node = author_node.select_one('[itemprop="name"]')
                    name = (name_node or author_node).get_text(" ", strip=True)
                    if name and name not in authors:
                        authors.append(html.unescape(name))
                if not authors:
                    continue

                doi = None
                doi_link = entry.select_one(
                    'a[href^="https://doi.org/"], a[href^="http://doi.org/"]'
                )
                if doi_link is not None:
                    doi = _strip_doi(str(doi_link.get("href") or ""))
                if doi is None:
                    doi = _sc_2018_doi(entry, venue, year)
                if doi is None:
                    doi = _publisher_doi(entry, normalized_key, venue, year)

                found += 1
                seen_keys.add(normalized_key)
                yield {
                    "dblp_key": normalized_key,
                    "doi": doi,
                    "title": html.unescape(title_node.get_text(" ", strip=True)).rstrip("."),
                    "publication_year": year,
                    "authors": authors,
                    "dblp_url": f"https://dblp.org/{path}",
                }

            if page_found == 0:
                if len(paths) == 1:
                    raise DblpError(
                        f"DBLP returned no main-conference papers for "
                        f"{venue.key.upper()} {year}; refusing to cache an empty roster."
                    )
                raise DblpError(
                    f"DBLP returned no main-conference papers for {venue.key.upper()} "
                    f"{year} at {path}; refusing to cache an incomplete roster."
                )

        if found == 0:
            raise DblpError(
                f"DBLP returned no main-conference papers for {venue.key.upper()} {year}; "
                "refusing to cache an empty roster."
            )
