from __future__ import annotations

import httpx

from hpc_bibliometrics.openalex import OpenAlexClient, work_to_row


def test_check_auth_uses_minimal_works_request() -> None:
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(
            200,
            json={"results": [{"id": "https://openalex.org/W1"}], "meta": {}},
        )

    client = OpenAlexClient(
        api_key="test-key",
        transport=httpx.MockTransport(handler),
        max_retries=1,
    )
    try:
        client.check_auth()
    finally:
        client.close()

    assert len(calls) == 1
    assert calls[0].url.path == "/works"
    assert calls[0].url.params.get("select") == "id"
    assert calls[0].url.params.get("per_page") == "1"


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


def test_api_key_is_trimmed_and_unquoted() -> None:
    client = OpenAlexClient(
        api_key='  "copied-key"  ',
        transport=httpx.MockTransport(
            lambda request: httpx.Response(200, json={"results": [], "meta": {}})
        ),
        max_retries=1,
    )
    try:
        assert client.api_key == "copied-key"
    finally:
        client.close()


def test_unauthorized_error_is_actionable_and_hides_key() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "unauthorized"})

    import pytest
    from hpc_bibliometrics.openalex import OpenAlexError

    client = OpenAlexClient(
        api_key="super-secret-key",
        transport=httpx.MockTransport(handler),
        max_retries=1,
    )
    try:
        with pytest.raises(OpenAlexError) as captured:
            client.check_auth()
    finally:
        client.close()

    message = str(captured.value)
    assert "HTTP 401" in message
    assert "hpc-bib check-auth" in message
    assert "super-secret-key" not in message


def test_http_error_does_not_expose_api_key() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, json={"error": "forbidden"})

    import pytest
    from hpc_bibliometrics.openalex import OpenAlexError

    client = OpenAlexClient(
        api_key="super-secret-key",
        transport=httpx.MockTransport(handler),
        max_retries=1,
    )
    try:
        with pytest.raises(OpenAlexError) as captured:
            client.check_auth()
    finally:
        client.close()

    assert "HTTP 403" in str(captured.value)
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
            client.check_auth()
    finally:
        client.close()

    assert captured.value.__cause__ is None
    assert "super-secret-key" not in str(captured.value)
