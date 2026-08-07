from __future__ import annotations

import html
import ssl
import time
from collections.abc import Iterator, Mapping
from typing import Any

import httpx

from .config import VenueSpec


class DblpError(RuntimeError):
    """Raised when DBLP cannot provide a conference roster."""


def _author_names(value: Any) -> list[str]:
    if isinstance(value, Mapping):
        value = [value]
    if not isinstance(value, list):
        return []
    names: list[str] = []
    for author in value:
        if isinstance(author, Mapping):
            text = author.get("text")
            if text:
                names.append(html.unescape(str(text)))
        elif author:
            names.append(html.unescape(str(author)))
    return names


def _strip_doi(value: Any) -> str | None:
    if not value:
        return None
    text = html.unescape(str(value)).strip()
    lower = text.lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if lower.startswith(prefix):
            text = text[len(prefix) :]
            break
    return text.lower() or None


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

    def _get_json(self, path: str, params: Mapping[str, Any]) -> dict[str, Any]:
        for attempt in range(self.max_retries):
            try:
                response = self._client.get(path, params=params)
                if response.status_code in {429, 500, 502, 503, 504}:
                    time.sleep(min(8.0, 2**attempt))
                    continue
                if response.is_error:
                    raise DblpError(f"DBLP returned HTTP {response.status_code} for {path}")
                payload = response.json()
                if not isinstance(payload, dict):
                    raise DblpError("DBLP returned an unexpected JSON response")
                return payload
            except DblpError:
                raise
            except (httpx.HTTPError, ValueError):
                if attempt + 1 < self.max_retries:
                    time.sleep(min(8.0, 2**attempt))
        raise DblpError(f"DBLP request failed for {path}") from None

    def iter_proceedings(self, venue: VenueSpec, year: int) -> Iterator[dict[str, Any]]:
        toc_key = venue.dblp_toc_pattern.format(year=year)
        payload = self._get_json(
            "search/publ/api",
            {
                "format": "json",
                "h": 1000,
                "q": f"toc:{toc_key}:",
            },
        )

        result = payload.get("result")
        hits_container = result.get("hits") if isinstance(result, Mapping) else None
        hits = hits_container.get("hit") if isinstance(hits_container, Mapping) else None
        if isinstance(hits, Mapping):
            hits = [hits]
        if not isinstance(hits, list):
            hits = []

        found = 0
        for hit in hits:
            info = hit.get("info") if isinstance(hit, Mapping) else None
            if not isinstance(info, Mapping):
                continue
            key = info.get("key")
            title = info.get("title")
            if not key or not title:
                continue

            # The TOC export includes the proceedings/editorship record. Only
            # publication records under conf/ipps/* with authors are papers.
            authors_container = info.get("authors")
            authors_value = (
                authors_container.get("author")
                if isinstance(authors_container, Mapping)
                else None
            )
            authors = _author_names(authors_value)
            if not authors:
                continue

            doi = _strip_doi(info.get("doi"))
            if doi is None:
                ee = info.get("ee")
                if isinstance(ee, list):
                    ee = next((item for item in ee if "doi.org/" in str(item)), None)
                if ee and "doi.org/" in str(ee):
                    doi = _strip_doi(ee)

            found += 1
            yield {
                "dblp_key": html.unescape(str(key)),
                "doi": doi,
                "title": html.unescape(str(title)).rstrip("."),
                "publication_year": int(info.get("year") or year),
                "authors": authors,
                "dblp_url": f"https://dblp.org/db/conf/ipps/ipdps{year}.html",
            }

        if found == 0:
            raise DblpError(
                f"DBLP returned no main-conference papers for {venue.key.upper()} {year}; "
                "refusing to cache an empty roster."
            )
