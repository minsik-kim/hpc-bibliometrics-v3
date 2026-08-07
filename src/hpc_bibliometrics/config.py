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
        # DBLP's main IPDPS table of contents uses ipdpsYYYY. Workshop
        # proceedings use a different key and are intentionally excluded.
        dblp_toc_pattern="db/conf/ipps/ipdps{year}.bht",
    ),
}


def get_venue(key: str) -> VenueSpec:
    normalized = key.strip().lower()
    try:
        return VENUES[normalized]
    except KeyError as exc:
        choices = ", ".join(sorted(VENUES))
        raise ValueError(f"Unknown venue {key!r}. Available venues: {choices}") from exc
