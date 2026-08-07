from __future__ import annotations

import json
import os
import random
import ssl
import time
from collections.abc import Iterator, Mapping
from typing import Any
from urllib.parse import quote

import httpx

from .config import VenueSpec


DEFAULT_SELECT = ",".join(
    (
        "id",
        "doi",
        "title",
        "display_name",
        "publication_year",
        "publication_date",
        "type",
        "cited_by_count",
        "primary_location",
        "authorships",
        "topics",
        "keywords",
    )
)


class OpenAlexError(RuntimeError):
    """Raised when OpenAlex cannot satisfy a request."""


def _clean_api_key(value: str | None) -> str:
    """Normalize a copied key without ever logging its contents."""

    key = (value or "").strip()
    if len(key) >= 2 and key[0] == key[-1] and key[0] in {"'", '"'}:
        key = key[1:-1].strip()
    return key


class OpenAlexClient:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        timeout: float = 45.0,
        max_retries: int = 5,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        raw_key = api_key if api_key is not None else os.getenv("OPENALEX_API_KEY")
        resolved_key = _clean_api_key(raw_key)
        if not resolved_key and transport is None:
            raise OpenAlexError(
                "OPENALEX_API_KEY is required. Create a free key at "
                "https://openalex.org/settings/api and export it before collecting."
            )

        # Mock transports do not contact OpenAlex but still exercise request
        # construction, so use a harmless placeholder in tests.
        self.api_key = resolved_key or "test-key"
        self.max_retries = max_retries

        verify: ssl.SSLContext | bool = True
        if transport is None:
            try:
                import truststore

                verify = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            except ImportError:
                # truststore is a runtime dependency. This fallback keeps
                # source-tree unit tests usable before dependencies are installed.
                verify = True

        self._client = httpx.Client(
            base_url="https://api.openalex.org",
            timeout=timeout,
            follow_redirects=True,
            transport=transport,
            verify=verify,
            headers={"User-Agent": "hpc-bibliometrics-v3/0.1"},
        )

    def __enter__(self) -> "OpenAlexClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        self._client.close()

    def _request(self, path: str, params: Mapping[str, Any] | None = None) -> dict[str, Any]:
        query = dict(params or {})
        query["api_key"] = self.api_key

        for attempt in range(self.max_retries):
            try:
                response = self._client.get(path, params=query)
                if response.status_code in {429, 500, 502, 503, 504}:
                    retry_after = response.headers.get("Retry-After")
                    if retry_after and retry_after.isdigit():
                        delay = float(retry_after)
                    else:
                        delay = min(30.0, (2**attempt) + random.random())
                    time.sleep(delay)
                    continue

                if response.status_code == 401:
                    raise OpenAlexError(
                        "OpenAlex rejected OPENALEX_API_KEY (HTTP 401). "
                        "Use a current OpenAlex key from "
                        "https://openalex.org/settings/api; an IEEE key will not work. "
                        "Re-export the key, then run `hpc-bib check-auth`."
                    )

                if response.status_code == 403:
                    raise OpenAlexError(
                        "OpenAlex denied the request (HTTP 403). Check the account's "
                        "API access and usage dashboard."
                    )

                if response.is_error:
                    raise OpenAlexError(
                        f"OpenAlex returned HTTP {response.status_code} for {path}"
                    )

                payload = response.json()
                if not isinstance(payload, dict):
                    raise OpenAlexError(f"Unexpected OpenAlex response type for {path}")
                return payload
            except OpenAlexError:
                raise
            except (httpx.HTTPError, ValueError):
                if attempt + 1 < self.max_retries:
                    time.sleep(min(30.0, (2**attempt) + random.random()))

        # Suppress the underlying httpx exception because it retains the full
        # request URL, including the API key query parameter.
        raise OpenAlexError(f"OpenAlex request failed for {path}") from None

    def check_auth(self) -> dict[str, Any]:
        """Validate the configured API key without exposing it."""

        return self._request("/rate-limit")

    def resolve_source(self, venue: VenueSpec) -> dict[str, Any]:
        payload = self._request(f"/sources/{quote(venue.source_lookup, safe=':')}")
        display_name = str(payload.get("display_name") or "")
        lowered = display_name.lower()
        if not all(token in lowered for token in venue.expected_name_tokens):
            expected = ", ".join(venue.expected_name_tokens)
            raise OpenAlexError(
                f"Resolved source {display_name!r} does not contain expected tokens: {expected}"
            )

        source_id = _short_openalex_id(payload.get("id"))
        if not source_id:
            raise OpenAlexError("Resolved source has no OpenAlex ID")

        return {
            "id": source_id,
            "display_name": display_name,
            "issn_l": payload.get("issn_l"),
            "type": payload.get("type"),
        }

    def iter_works(
        self,
        source_id: str,
        year: int,
        *,
        per_page: int = 100,
    ) -> Iterator[dict[str, Any]]:
        cursor = "*"
        while cursor:
            payload = self._request(
                "/works",
                {
                    "filter": (
                        f"primary_location.source.id:{source_id},"
                        f"from_publication_date:{year}-01-01,"
                        f"to_publication_date:{year}-12-31"
                    ),
                    # The current OpenAlex Walden index excludes XPAC records by
                    # default. Conference proceedings such as IPDPS can be XPAC-
                    # only, so source queries must opt in explicitly. OpenAlex's
                    # own GUI does the same when linking a Source to its Works.
                    "include_xpac": "true",
                    "select": DEFAULT_SELECT,
                    "cursor": cursor,
                    "per_page": per_page,
                },
            )
            results = payload.get("results") or []
            if not isinstance(results, list):
                raise OpenAlexError("OpenAlex works response has a non-list results field")
            for work in results:
                if isinstance(work, dict):
                    yield work

            meta = payload.get("meta") or {}
            next_cursor = meta.get("next_cursor") if isinstance(meta, dict) else None
            cursor = str(next_cursor) if next_cursor else ""


def _short_openalex_id(value: Any) -> str | None:
    if not value:
        return None
    text = str(value).rstrip("/")
    return text.rsplit("/", 1)[-1]


def work_to_row(work: Mapping[str, Any]) -> dict[str, Any]:
    primary_location = work.get("primary_location")
    source: Mapping[str, Any] = {}
    if isinstance(primary_location, Mapping):
        maybe_source = primary_location.get("source")
        if isinstance(maybe_source, Mapping):
            source = maybe_source

    title = work.get("title") or work.get("display_name") or ""
    return {
        "openalex_id": _short_openalex_id(work.get("id")),
        "doi": work.get("doi"),
        "title": str(title),
        "publication_year": work.get("publication_year"),
        "publication_date": work.get("publication_date"),
        "work_type": work.get("type"),
        "cited_by_count": int(work.get("cited_by_count") or 0),
        "source_id": _short_openalex_id(source.get("id")),
        "source_name": source.get("display_name"),
        "authorships_json": json.dumps(work.get("authorships") or [], ensure_ascii=False),
        "topics_json": json.dumps(work.get("topics") or [], ensure_ascii=False),
        "keywords_json": json.dumps(work.get("keywords") or [], ensure_ascii=False),
    }
