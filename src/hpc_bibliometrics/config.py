from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class VenueSpec:
    """Stable metadata used to collect an exact conference roster."""

    key: str
    display_name: str
    dblp_toc_pattern: str


VENUES: dict[str, VenueSpec] = {
    "ics": VenueSpec(
        key="ics",
        display_name="ACM International Conference on Supercomputing",
        # Main proceedings only. Co-located workshops use separate DBLP pages/keys.
        dblp_toc_pattern="db/conf/ics/ics{year}.html",
    ),
    "ipdps": VenueSpec(
        key="ipdps",
        display_name="IEEE International Parallel and Distributed Processing Symposium",
        # Main-conference TOC. Workshops use a separate DBLP page/key.
        dblp_toc_pattern="db/conf/ipps/ipdps{year}.html",
    ),
    "sc": VenueSpec(
        key="sc",
        display_name=(
            "International Conference for High Performance Computing, Networking, "
            "Storage, and Analysis"
        ),
        # Main proceedings only. SC workshops use separate pages such as sc2024w.html.
        dblp_toc_pattern="db/conf/sc/sc{year}.html",
    ),
}


def get_venue(key: str) -> VenueSpec:
    normalized = key.strip().lower()
    try:
        return VENUES[normalized]
    except KeyError as exc:
        choices = ", ".join(sorted(VENUES))
        raise ValueError(f"Unknown venue {key!r}. Available venues: {choices}") from exc
