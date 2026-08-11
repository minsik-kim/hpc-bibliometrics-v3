from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class VenueSpec:
    """Stable metadata used to collect an exact conference roster."""

    key: str
    display_name: str
    dblp_toc_pattern: str
    dblp_toc_overrides: tuple[tuple[int, tuple[str, ...]], ...] = ()

    def dblp_toc_paths(self, year: int) -> tuple[str, ...]:
        for override_year, patterns in self.dblp_toc_overrides:
            if year == override_year:
                return tuple(pattern.format(year=year) for pattern in patterns)
        return (self.dblp_toc_pattern.format(year=year),)


VENUES: dict[str, VenueSpec] = {
    "ccgrid": VenueSpec(
        key="ccgrid",
        display_name=(
            "IEEE/ACM International Symposium on Cluster, Cloud and Internet Computing"
        ),
        # Main proceedings only. Workshop proceedings use ccgrid{year}w.html.
        dblp_toc_pattern="db/conf/ccgrid/ccgrid{year}.html",
    ),
    "cluster": VenueSpec(
        key="cluster",
        display_name="IEEE International Conference on Cluster Computing",
        # Main proceedings only. Workshops use clusterw{year}.html.
        dblp_toc_pattern="db/conf/cluster/cluster{year}.html",
    ),
    "europar": VenueSpec(
        key="europar",
        display_name="European Conference on Parallel and Distributed Processing",
        # Workshops use europar{year}w*.html. Main proceedings expanded to three
        # volumes in 2024; every configured volume is required and deduplicated.
        dblp_toc_pattern="db/conf/europar/europar{year}.html",
        dblp_toc_overrides=(
            (
                2024,
                tuple(f"db/conf/europar/europar{{year}}-{part}.html" for part in range(1, 4)),
            ),
            (
                2025,
                tuple(f"db/conf/europar/europar{{year}}-{part}.html" for part in range(1, 4)),
            ),
        ),
    ),
    "hipc": VenueSpec(
        key="hipc",
        display_name="IEEE International Conference on High Performance Computing",
        dblp_toc_pattern="db/conf/hipc/hipc{year}.html",
    ),
    "hpdc": VenueSpec(
        key="hpdc",
        display_name=(
            "ACM International Symposium on High-Performance Parallel and "
            "Distributed Computing"
        ),
        dblp_toc_pattern="db/conf/hpdc/hpdc{year}.html",
    ),
    "icpp": VenueSpec(
        key="icpp",
        display_name="International Conference on Parallel Processing",
        dblp_toc_pattern="db/conf/icpp/icpp{year}.html",
    ),
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
    "isc": VenueSpec(
        key="isc",
        display_name="ISC High Performance",
        dblp_toc_pattern="db/conf/supercomputer/isc{year}.html",
    ),
    "ppopp": VenueSpec(
        key="ppopp",
        display_name=(
            "ACM SIGPLAN Symposium on Principles and Practice of Parallel Programming"
        ),
        dblp_toc_pattern="db/conf/ppopp/ppopp{year}.html",
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
