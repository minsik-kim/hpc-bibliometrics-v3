from __future__ import annotations

import httpx
import pytest

from hpc_bibliometrics.config import get_venue
from hpc_bibliometrics.dblp import DblpClient, DblpError


HTML = '''
<ul class="publ-list">
<li id="conf/ipps/Example24" class="entry inproceedings toc" data-key="conf/ipps/Example24">
  <cite class="data tts-content">
    <span itemprop="author"><span itemprop="name">Ada Example</span></span>
    <span class="title" itemprop="name">Fast &amp; Correct HPC.</span>
    <a href="https://doi.org/10.1109/IPDPS.2024.123">DOI</a>
  </cite>
</li>
<li class="entry proceedings" data-key="conf/ipps/2024"><span class="title">Proceedings</span></li>
</ul>
'''


def test_dblp_parses_live_style_html_without_attribute_order_dependency() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/db/conf/ipps/ipdps2024.html"
        return httpx.Response(200, text=HTML)

    with DblpClient(transport=httpx.MockTransport(handler)) as client:
        rows = list(client.iter_proceedings(get_venue("ipdps"), 2024))

    assert len(rows) == 1
    assert rows[0]["dblp_key"] == "conf/ipps/Example24"
    assert rows[0]["doi"] == "10.1109/ipdps.2024.123"
    assert rows[0]["title"] == "Fast & Correct HPC"
    assert rows[0]["authors"] == ["Ada Example"]


def test_dblp_refuses_empty_roster() -> None:
    with DblpClient(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, text="<html></html>"))
    ) as client:
        with pytest.raises(DblpError, match="refusing to cache an empty roster"):
            list(client.iter_proceedings(get_venue("ipdps"), 2024))


def test_sc_uses_main_proceedings_page() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/db/conf/sc/sc2024.html"
        return httpx.Response(200, text=HTML.replace("conf/ipps", "conf/sc"))

    with DblpClient(transport=httpx.MockTransport(handler)) as client:
        rows = list(client.iter_proceedings(get_venue("sc"), 2024))

    assert len(rows) == 1
    assert rows[0]["dblp_key"] == "conf/sc/Example24"
    assert rows[0]["dblp_url"] == "https://dblp.org/db/conf/sc/sc2024.html"


def test_ics_uses_main_proceedings_page() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/db/conf/ics/ics2024.html"
        return httpx.Response(200, text=HTML.replace("conf/ipps", "conf/ics"))

    with DblpClient(transport=httpx.MockTransport(handler)) as client:
        rows = list(client.iter_proceedings(get_venue("ics"), 2024))

    assert len(rows) == 1
    assert rows[0]["dblp_key"] == "conf/ics/Example24"
    assert rows[0]["dblp_url"] == "https://dblp.org/db/conf/ics/ics2024.html"


def test_sc_2018_recovers_ieee_doi_from_article_pagination() -> None:
    html = HTML.replace("conf/ipps", "conf/sc").replace(
        '<a href="https://doi.org/10.1109/IPDPS.2024.123">DOI</a>',
        '<a href="http://dl.acm.org/citation.cfm?id=3291659">ACM</a>'
        '<span itemprop="pagination">2:1-2:16</span>',
    )

    with DblpClient(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, text=html))
    ) as client:
        rows = list(client.iter_proceedings(get_venue("sc"), 2018))

    assert rows[0]["doi"] == "10.1109/sc.2018.00005"
