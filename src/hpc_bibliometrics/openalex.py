from __future__ import annotations

import os
import random
import ssl
import time
from typing import Any, Mapping
from urllib.parse import quote

import httpx


class OpenAlexError(RuntimeError):
    """Raised when OpenAlex cannot satisfy a request."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


def _clean_api_key(value: str | None) -> str:
    key = (value or "").strip()
    if len(key) >= 2 and key[0] == key[-1] and key[0] in {"'", '"'}:
        key = key[1:-1].strip()
    return key


class OpenAlexClient:
    def __init__(self, *, api_key: str | None = None, timeout: float = 45.0,
                 max_retries: int = 5, transport: httpx.BaseTransport | None = None) -> None:
        resolved_key = _clean_api_key(api_key if api_key is not None else os.getenv("OPENALEX_API_KEY"))
        if not resolved_key and transport is None:
            raise OpenAlexError(
                "OPENALEX_API_KEY is required. Create a free key at "
                "https://openalex.org/settings/api and export it before collecting."
            )
        self.api_key = resolved_key or "test-key"
        self.max_retries = max_retries
        verify: ssl.SSLContext | bool = True
        if transport is None:
            try:
                import truststore
                verify = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            except ImportError:
                verify = True
        self._client = httpx.Client(base_url="https://api.openalex.org", timeout=timeout,
                                    follow_redirects=True, transport=transport, verify=verify,
                                    headers={"User-Agent": "hpc-bibliometrics-v3/0.1"})

    def __enter__(self) -> "OpenAlexClient": return self
    def __exit__(self, *_: object) -> None: self.close()
    def close(self) -> None: self._client.close()

    def _request(self, path: str, params: Mapping[str, Any] | None = None) -> dict[str, Any]:
        query = dict(params or {})
        query["api_key"] = self.api_key
        for attempt in range(self.max_retries):
            try:
                response = self._client.get(path, params=query)
                if response.status_code in {429, 500, 502, 503, 504}:
                    retry_after = response.headers.get("Retry-After")
                    delay = float(retry_after) if retry_after and retry_after.isdigit() else min(30.0, (2**attempt) + random.random())
                    time.sleep(delay); continue
                if response.status_code == 401:
                    raise OpenAlexError("OpenAlex rejected OPENALEX_API_KEY (HTTP 401). Use a current OpenAlex key from https://openalex.org/settings/api; re-export the key, then run `hpc-bib check-auth`.", status_code=401)
                if response.status_code == 403:
                    raise OpenAlexError("OpenAlex denied the request (HTTP 403). Check the account's API access and usage dashboard.", status_code=403)
                if response.status_code == 404:
                    raise OpenAlexError(f"OpenAlex returned HTTP 404 for {path}", status_code=404)
                if response.is_error:
                    raise OpenAlexError(f"OpenAlex returned HTTP {response.status_code} for {path}", status_code=response.status_code)
                payload = response.json()
                if not isinstance(payload, dict):
                    raise OpenAlexError(f"Unexpected OpenAlex response type for {path}")
                return payload
            except OpenAlexError:
                raise
            except (httpx.HTTPError, ValueError):
                if attempt + 1 < self.max_retries:
                    time.sleep(min(30.0, (2**attempt) + random.random()))
        raise OpenAlexError(f"OpenAlex request failed for {path}") from None

    def check_auth(self) -> dict[str, Any]:
        return self._request("/works", {"select": "id", "per_page": 1})

    def get_work_by_doi(self, doi: str) -> dict[str, Any]:
        normalized = doi.strip().lower()
        for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
            if normalized.startswith(prefix):
                normalized = normalized[len(prefix):]
                break
        return self._request(f"/works/https://doi.org/{quote(normalized, safe='/')}", {
            "select": "id,doi,title,publication_year,authorships,cited_by_count"
        })


def _short_openalex_id(value: Any) -> str | None:
    if not value: return None
    return str(value).rstrip("/").rsplit("/", 1)[-1]


def work_to_row(work: Mapping[str, Any]) -> dict[str, Any]:
    primary_location = work.get("primary_location")
    source: Mapping[str, Any] = {}
    if isinstance(primary_location, Mapping):
        maybe_source = primary_location.get("source")
        if isinstance(maybe_source, Mapping): source = maybe_source
    import json
    title = work.get("title") or work.get("display_name") or ""
    return {"openalex_id": _short_openalex_id(work.get("id")), "doi": work.get("doi"),
            "title": str(title), "publication_year": work.get("publication_year"),
            "publication_date": work.get("publication_date"), "work_type": work.get("type"),
            "cited_by_count": int(work.get("cited_by_count") or 0),
            "source_id": _short_openalex_id(source.get("id")), "source_name": source.get("display_name"),
            "authorships_json": json.dumps(work.get("authorships") or [], ensure_ascii=False),
            "topics_json": json.dumps(work.get("topics") or [], ensure_ascii=False),
            "keywords_json": json.dumps(work.get("keywords") or [], ensure_ascii=False)}
