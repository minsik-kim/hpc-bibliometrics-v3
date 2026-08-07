from __future__ import annotations

import httpx
import pytest

from hpc_bibliometrics.config import get_venue
from hpc_bibliometrics.dblp import DblpClient, DblpError


PAYLOAD = {
    "result": {
        "hits": {
            "hit": [
                {
                    "info": {
                        "authors": {"author": [{"text": "Ada Example"}]},
                        "title": "Fast &amp; Correct HPC.",
                        "year": "2024",
                        "key": "conf/ipps/Example24",
                        "doi": "10.1109/IPDPS.2024.123",
                    }
                },
                {
                    "info": {
                        "title": "Proceedings of IPDPS 2024",
                        "year": "2024",
                        "key": "conf/ipps/2024",
                    }
                },
            ]
        }
    }
}


def test_dblp_uses_toc_json_export_and_parses_paper() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/search/publ/api"
        assert request.url.params.get("format") == "json"
        assert request.url.params.get("h") == "1000"
        assert request.url.params.get("q") == "toc:db/conf/ipps/ipdps2024.bht:"
        return httpx.Response(200, json=PAYLOAD)

    with DblpClient(transport=httpx.MockTransport(handler)) as client:
        rows = list(client.iter_proceedings(get_venue("ipdps"), 2024))

    assert len(rows) == 1
    assert rows[0]["dblp_key"] == "conf/ipps/Example24"
    assert rows[0]["doi"] == "10.1109/ipdps.2024.123"
    assert rows[0]["title"] == "Fast & Correct HPC"
    assert rows[0]["authors"] == ["Ada Example"]


def test_dblp_accepts_single_hit_and_single_author_objects() -> None:
    payload = {
        "result": {
            "hits": {
                "hit": {
                    "info": {
                        "authors": {"author": {"text": "Grace Hopper"}},
                        "title": "One paper",
                        "year": "2018",
                        "key": "conf/ipps/Hopper18",
                        "ee": "https://doi.org/10.1109/IPDPS.2018.1",
                    }
                }
            }
        }
    }

    with DblpClient(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json=payload))
    ) as client:
        rows = list(client.iter_proceedings(get_venue("ipdps"), 2018))

    assert rows[0]["authors"] == ["Grace Hopper"]
    assert rows[0]["doi"] == "10.1109/ipdps.2018.1"


def test_dblp_refuses_empty_roster() -> None:
    payload = {"result": {"hits": {"hit": []}}}
    with DblpClient(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json=payload))
    ) as client:
        with pytest.raises(DblpError, match="refusing to cache an empty roster"):
            list(client.iter_proceedings(get_venue("ipdps"), 2024))
