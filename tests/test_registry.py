from __future__ import annotations

import pytest

from hpc_bibliometrics.analyze import RESEARCH_LABS, _classify


@pytest.mark.parametrize(
    ("institution", "expected_code", "expected_subtype"),
    [
        ({"id": "https://openalex.org/I4391767926"}, "CSCS", "national_compute_center"),
        ({"display_name": "National Energy Research Scientific Computing Center"}, "NERSC", "national_compute_center"),
        ({"ror": "https://ror.org/02nv7yv05"}, "FZJ", "public_research_institute"),
        ({"display_name": "Simula Research Laboratory"}, "SIMULA", "public_research_institute"),
        ({"display_name": "MIT Lincoln Laboratory"}, "MIT-LL", "government_research_institute"),
        ({"display_name": "Thomas Jefferson National Accelerator Facility"}, "JLAB", "national_lab"),
        ({"display_name": "National Laboratory of the Rockies"}, "NREL", "national_lab"),
        ({"id": "I4210165734"}, "NSCC-TJ", "national_compute_center"),
        ({"display_name": "DOE Joint Genome Institute"}, "JGI", "public_research_institute"),
        ({"id": "I4210135837"}, "NCSA", "national_compute_center"),
        ({"ror": "03ztgj037"}, "DKRZ", "national_compute_center"),
        ({"display_name": "NSF National Center for Atmospheric Research"}, "NCAR", "government_research_institute"),
    ],
)
def test_audited_registry_entries(
    institution: dict[str, str], expected_code: str, expected_subtype: str
) -> None:
    category, code = _classify(institution)
    assert category == "national_lab"
    assert code == expected_code
    assert RESEARCH_LABS[code]["subtype"] == expected_subtype
