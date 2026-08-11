from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ManualEnrichment:
    doi: str
    institutions: tuple[dict[str, str | None], ...]
    source_url: str
    verified_on: str


def _institution(
    display_name: str,
    country_code: str,
    institution_type: str,
) -> dict[str, str | None]:
    return {
        "id": None,
        "display_name": display_name,
        "country_code": country_code,
        "type": institution_type,
        "ror": None,
    }


# OpenAlex currently returns 404 for these DOI-bearing DBLP papers. Affiliations
# are transcribed from the linked proceedings, author manuscript, or institutional
# publication record. Status remains `unmatched`; this data is a transparent
# analysis fallback rather than a fabricated OpenAlex match.
MANUAL_ENRICHMENTS: dict[str, ManualEnrichment] = {
    "conf/hpdc/Movsowitz-Davidow23": ManualEnrichment(
        doi="10.1145/3588195.3593001",
        institutions=(
            _institution("University of Haifa", "IL", "education"),
        ),
        source_url=(
            "https://cris.haifa.ac.il/en/publications/"
            "deconstructing-alibaba-clouds-preemptible-instance-pricing/"
        ),
        verified_on="2026-08-11",
    ),
    "conf/ccgrid/LiuA17": ManualEnrichment(
        doi="10.1109/ccgrid.2017.95",
        institutions=(
            _institution("The Ohio State University", "US", "education"),
        ),
        source_url=(
            "https://etd.ohiolink.edu/acprod/odb_etd/ws/send_file/"
            "send?accession=osu1483632126075067&disposition=inline"
        ),
        verified_on="2026-08-11",
    ),
    "conf/ipps/FunkeL00SL18": ManualEnrichment(
        doi="10.1109/ipdps.2018.00043",
        institutions=(
            _institution("Karlsruhe Institute of Technology", "DE", "education"),
        ),
        source_url="https://www.proceedings.com/content/040/040569webtoc.pdf",
        verified_on="2026-08-11",
    ),
    "conf/sc/GaihreZWLSDLL21": ManualEnrichment(
        doi="10.1145/3458817.3476141",
        institutions=(
            _institution("Johns Hopkins University", "US", "education"),
            _institution("Stevens Institute of Technology", "US", "education"),
            _institution("Brookhaven National Laboratory", "US", "government"),
            _institution(
                "Lawrence Berkeley National Laboratory", "US", "government"
            ),
            _institution("University of Sydney", "AU", "education"),
            _institution("University of Washington", "US", "education"),
            _institution("University of Connecticut", "US", "education"),
        ),
        source_url="https://anil-gaihre.github.io/files/DrTopk.pdf",
        verified_on="2026-08-11",
    ),
    "conf/sc/KwasniewskiKBZS21": ManualEnrichment(
        doi="10.1145/3458817.3476167",
        institutions=(
            _institution("ETH Zurich", "CH", "education"),
            _institution(
                "CSCS - Swiss National Supercomputing Centre", "CH", "facility"
            ),
        ),
        source_url="https://spcl.inf.ethz.ch/Publications/.pdf/SC_factorization.pdf",
        verified_on="2026-08-11",
    ),
    "conf/sc/TaylorCBCDFGHKK23": ManualEnrichment(
        doi="10.1145/3581784.3627044",
        institutions=(
            _institution("Sandia National Laboratories", "US", "government"),
            _institution(
                "Lawrence Livermore National Laboratory", "US", "government"
            ),
            _institution(
                "Lawrence Berkeley National Laboratory", "US", "government"
            ),
            _institution("Argonne National Laboratory", "US", "government"),
            _institution("Oak Ridge National Laboratory", "US", "government"),
            _institution("Hewlett Packard Enterprise", "US", "company"),
            _institution(
                "Pacific Northwest National Laboratory", "US", "government"
            ),
        ),
        source_url=(
            "https://sc23.supercomputing.org/proceedings/tech_paper/"
            "tech_paper_pages/gbv102.html"
        ),
        verified_on="2026-08-11",
    ),
}


def apply_manual_enrichment(row: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    """Apply a verified fallback only to the exact still-unmatched DBLP/DOI pair."""
    updated = dict(row)
    updated.setdefault(
        "metadata_source", "openalex" if row.get("status") == "matched" else None
    )
    updated.setdefault("metadata_source_url", row.get("openalex_id"))
    updated.setdefault("metadata_verified_on", None)

    override = MANUAL_ENRICHMENTS.get(str(row.get("dblp_key") or ""))
    if override is None or row.get("status") != "unmatched":
        return updated, False
    if str(row.get("doi") or "").strip().lower() != override.doi:
        return updated, False

    updated["institutions_json"] = json.dumps(
        override.institutions, ensure_ascii=False
    )
    updated["metadata_source"] = "manual"
    updated["metadata_source_url"] = override.source_url
    updated["metadata_verified_on"] = override.verified_on
    return updated, True
