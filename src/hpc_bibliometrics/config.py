from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class VenueSpec:
    """Stable metadata used to collect an exact conference roster."""

    key: str
    display_name: str
    dblp_toc_pattern: str


VENUES: dict[str, VenueSpec] = {
    "ipdps": VenueSpec(
        key="ipdps",
        display_name="IEEE International Parallel and Distributed Processing Symposium",
        # DBLP exposes the main-conference table of contents as an HTML page.
        # The displayed BHT key is an internal DBLP key, not a fetchable URL.
        # Workshop proceedings use a distinct key and are intentionally excluded.
        dblp_toc_pattern="db/conf/ipps/ipdps{year}.html",
    ),
}


def get_venue(key: str) -> VenueSpec:
    normalized = key.strip().lower()
    try:
        return VENUES[normalized]
    except KeyError as exc:
        choices = ", ".join(sorted(VENUES))
        raise ValueError(f"Unknown venue {key!r}. Available venues: {choices}") from exc
