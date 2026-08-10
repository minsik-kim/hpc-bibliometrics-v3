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


def test_get_venue_rejects_unknown_key() -> None:
    with pytest.raises(ValueError, match="Available venues: ipdps, sc"):
        get_venue("unknown")
