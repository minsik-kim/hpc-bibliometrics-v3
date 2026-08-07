import pytest

from hpc_bibliometrics.config import get_venue


def test_get_venue_is_case_insensitive() -> None:
    venue = get_venue(" IPDPS ")
    assert venue.key == "ipdps"
    assert venue.dblp_toc_pattern == "db/conf/ipps/ipdps{year}.html"


def test_get_venue_rejects_unknown_key() -> None:
    with pytest.raises(ValueError, match="Available venues: ipdps"):
        get_venue("unknown")
