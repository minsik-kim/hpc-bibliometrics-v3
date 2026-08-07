from __future__ import annotations

import httpx

from hpc_bibliometrics.config import get_venue
from hpc_bibliometrics.openalex import OpenAlexClient, work_to_row


def test_resolve_source_and_paginate_works() -> None:
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        if request.url.path == "/sources/issn:1530-2075":
            return httpx.Response(
                200,
                json={
                    "id": "https://openalex.org/S123",
                    "display_name": "Proceedings - IEEE International Parallel and Distributed Processing Symposium",
                    "issn_l": "1530-2075",
                    "type": "conference",
                },
            )
        cursor = request.url.params.get("cursor")
        if cursor == "*":
            return httpx.Response(
                200,
                json={
                    "results": [{"id": "https://openalex.org/W1", "title": "A paper"}],
                    "meta": {"next_cursor": "next"},
                },
            )
        return httpx.Response(200, json={"results": [], "meta": {"next_cursor": None}})

    client = OpenAlexClient(transport=httpx.MockTransport(handler), max_retries=1)
    try:
        source = client.resolve_source(get_venue("ipdps"))
        works = list(client.iter_works(source["id"], 2024))
    finally:
        client.close()

    assert source["id"] == "S123"
    assert [work["id"] for work in works] == ["https://openalex.org/W1"]
    assert len(calls) == 3
    assert "primary_location.source.id%3AS123" in calls[1]
    assert "per_page=100" in calls[1]


def test_work_to_row_flattens_nested_metadata() -> None:
    row = work_to_row(
        {
            "id": "https://openalex.org/W42",
            "doi": "https://doi.org/10.1/example",
            "display_name": "Example",
            "publication_year": 2024,
            "publication_date": "2024-05-01",
            "type": "proceedings-article",
            "cited_by_count": 7,
            "primary_location": {
                "source": {
                    "id": "https://openalex.org/S123",
                    "display_name": "IPDPS",
                }
            },
            "authorships": [{"author": {"display_name": "A"}}],
        }
    )

    assert row["openalex_id"] == "W42"
    assert row["source_id"] == "S123"
    assert row["title"] == "Example"
    assert '"display_name": "A"' in row["authorships_json"]


def test_live_client_requires_api_key(monkeypatch) -> None:
    monkeypatch.delenv("OPENALEX_API_KEY", raising=False)
    import pytest
    from hpc_bibliometrics.openalex import OpenAlexError

    with pytest.raises(OpenAlexError, match="OPENALEX_API_KEY is required"):
        OpenAlexClient()


def test_http_error_does_not_expose_api_key() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, json={"error": "forbidden"})

    from hpc_bibliometrics.openalex import OpenAlexError

    client = OpenAlexClient(
        api_key="super-secret-key",
        transport=httpx.MockTransport(handler),
        max_retries=1,
    )
    try:
        import pytest

        with pytest.raises(OpenAlexError) as captured:
            client.resolve_source(get_venue("ipdps"))
    finally:
        client.close()

    assert "super-secret-key" not in str(captured.value)


def test_network_error_suppresses_request_url_and_api_key() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("network unavailable", request=request)

    import pytest
    from hpc_bibliometrics.openalex import OpenAlexError

    client = OpenAlexClient(
        api_key="super-secret-key",
        transport=httpx.MockTransport(handler),
        max_retries=1,
    )
    try:
        with pytest.raises(OpenAlexError) as captured:
            client.resolve_source(get_venue("ipdps"))
    finally:
        client.close()

    assert captured.value.__cause__ is None
    assert "super-secret-key" not in str(captured.value)
