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


def test_europar_combines_and_deduplicates_main_proceedings_volumes() -> None:
    html = HTML.replace("conf/ipps", "conf/europar")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path in {
            f"/db/conf/europar/europar2024-{part}.html" for part in range(1, 4)
        }
        return httpx.Response(200, text=html)

    with DblpClient(transport=httpx.MockTransport(handler)) as client:
        rows = list(client.iter_proceedings(get_venue("europar"), 2024))

    assert len(rows) == 1
    assert rows[0]["dblp_key"] == "conf/europar/Example24"


def test_europar_rejects_an_empty_configured_volume() -> None:
    html = HTML.replace("conf/ipps", "conf/europar")

    def handler(request: httpx.Request) -> httpx.Response:
        text = "<html></html>" if request.url.path.endswith("-2.html") else html
        return httpx.Response(200, text=text)

    with DblpClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(DblpError, match="incomplete roster"):
            list(client.iter_proceedings(get_venue("europar"), 2024))


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


def test_isc_2025_recovers_doi_from_ieee_document_link() -> None:
    html = HTML.replace("conf/ipps", "conf/supercomputer").replace(
        '<a href="https://doi.org/10.1109/IPDPS.2024.123">DOI</a>',
        '<a href="https://ieeexplore.ieee.org/document/11017506">IEEE</a>',
    )
    with DblpClient(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, text=html))
    ) as client:
        rows = list(client.iter_proceedings(get_venue("isc"), 2025))

    assert rows[0]["doi"] == "10.23919/isc.2025.11017506"


def test_ccgrid_2017_recovers_known_missing_doi() -> None:
    html = HTML.replace("conf/ipps/Example24", "conf/ccgrid/LiuA17").replace(
        '<a href="https://doi.org/10.1109/IPDPS.2024.123">DOI</a>',
        "",
    )
    with DblpClient(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, text=html))
    ) as client:
        rows = list(client.iter_proceedings(get_venue("ccgrid"), 2017))

    assert rows[0]["doi"] == "10.1109/ccgrid.2017.95"
