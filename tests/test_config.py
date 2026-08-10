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


def test_get_venue_rejects_unknown_key() -> None:
    with pytest.raises(ValueError, match="Available venues: ics, ipdps, sc"):
        get_venue("unknown")
