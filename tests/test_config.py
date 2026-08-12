import pytest

from hpc_bibliometrics.config import get_venue


def test_get_venue_is_case_insensitive() -> None:
    venue = get_venue(" IPDPS ")
    assert venue.key == "ipdps"
    assert venue.dblp_toc_pattern == "db/conf/ipps/ipdps{year}.html"


def test_get_sc_venue_uses_main_proceedings_toc() -> None:
    venue = get_venue(" SC ")
    assert venue.key == "sc"
    assert venue.dblp_toc_pattern == "db/conf/sc/sc{year}.html"
    assert "High Performance Computing" in venue.display_name


def test_get_ics_venue_uses_main_proceedings_toc() -> None:
    venue = get_venue(" ICS ")
    assert venue.key == "ics"
    assert venue.dblp_toc_pattern == "db/conf/ics/ics{year}.html"
    assert venue.display_name == "ACM International Conference on Supercomputing"


@pytest.mark.parametrize(
    ("key", "pattern"),
    [
        ("ccgrid", "db/conf/ccgrid/ccgrid{year}.html"),
        ("cluster", "db/conf/cluster/cluster{year}.html"),
        ("hipc", "db/conf/hipc/hipc{year}.html"),
        ("hpdc", "db/conf/hpdc/hpdc{year}.html"),
        ("icpp", "db/conf/icpp/icpp{year}.html"),
        ("isc", "db/conf/supercomputer/isc{year}.html"),
        ("ppopp", "db/conf/ppopp/ppopp{year}.html"),
        ("cgo", "db/conf/cgo/cgo{year}.html"),
        ("eurosys", "db/conf/eurosys/eurosys{year}.html"),
        ("asplos", "db/conf/asplos/asplos{year}.html"),
    ],
)
def test_additional_venues_use_main_proceedings_toc(key: str, pattern: str) -> None:
    assert get_venue(key).dblp_toc_pattern == pattern


def test_asplos_expands_quarterly_pacmpl_volumes() -> None:
    venue = get_venue("asplos")
    assert venue.dblp_toc_paths(2022) == ("db/conf/asplos/asplos2022.html",)
    assert venue.dblp_toc_paths(2023) == tuple(
        f"db/conf/asplos/asplos2023-{part}.html" for part in range(1, 5)
    )
    assert venue.dblp_toc_paths(2024) == tuple(
        f"db/conf/asplos/asplos2024-{part}.html" for part in range(1, 5)
    )
    assert venue.dblp_toc_paths(2025) == tuple(
        f"db/conf/asplos/asplos2025-{part}.html" for part in range(1, 4)
    )


def test_europar_expands_recent_main_proceedings_volumes() -> None:
    venue = get_venue("europar")
    assert venue.dblp_toc_paths(2023) == (
        "db/conf/europar/europar2023.html",
    )
    assert venue.dblp_toc_paths(2024) == tuple(
        f"db/conf/europar/europar2024-{part}.html" for part in range(1, 4)
    )
    assert all("w" not in path for path in venue.dblp_toc_paths(2025))


def test_get_venue_rejects_unknown_key() -> None:
    with pytest.raises(ValueError, match="Available venues: asplos, ccgrid, cgo, cluster"):
        get_venue("unknown")
