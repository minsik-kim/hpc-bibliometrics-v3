from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class VenueSpec:
    """Stable metadata used to resolve an OpenAlex source."""

    key: str
    display_name: str
    source_lookup: str
    expected_name_tokens: tuple[str, ...]


VENUES: dict[str, VenueSpec] = {
    "ipdps": VenueSpec(
        key="ipdps",
        display_name="IEEE International Parallel and Distributed Processing Symposium",
        # The main IPDPS proceedings use this ISSN. IPDPS Workshops use a
        # different proceedings record and are therefore not selected here.
        source_lookup="issn:1530-2075",
        expected_name_tokens=("parallel", "distributed", "processing"),
    ),
}


def get_venue(key: str) -> VenueSpec:
    normalized = key.strip().lower()
    try:
        return VENUES[normalized]
    except KeyError as exc:
        choices = ", ".join(sorted(VENUES))
        raise ValueError(f"Unknown venue {key!r}. Available venues: {choices}") from exc
