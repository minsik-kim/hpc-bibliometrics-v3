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
        ({"id": "I4210109712"}, "MPI-INF", "public_research_institute"),
        ({"ror": "04d23a975"}, "US-NRL", "government_research_institute"),
        (
            {"display_name": "Shanghai Artificial Intelligence Laboratory"},
            "SHLAB",
            "public_research_institute",
        ),
        ({"id": "I67311998"}, "CERN", "public_research_institute"),
        ({"ror": "04nytyj38"}, "CAS-SIMIT", "public_research_institute"),
        (
            {"display_name": "Beijing Institute of Big Data Research"},
            "BIBDR",
            "public_research_institute",
        ),
        ({"id": "I4210127509"}, "VECTOR", "public_research_institute"),
        ({"ror": "04mqy3p58"}, "INESC-ID", "public_research_institute"),
        (
            {"display_name": "Advanced Digital Sciences Centre"},
            "ADSC",
            "public_research_institute",
        ),
        ({"id": "I1309980932"}, "ORNL", "national_lab"),
        ({"ror": "02pq9w205"}, "CAS-ICT", "public_research_institute"),
        (
            {"display_name": "State Key Laboratory of Computer Science"},
            "CAS-ISCAS",
            "public_research_institute",
        ),
        ({"id": "I4210101455"}, "CEA-DIF", "government_research_institute"),
        ({"ror": "00myn0z94"}, "IRISA", "public_research_institute"),
        ({"display_name": "LIP6"}, "LIP6", "public_research_institute"),
        ({"id": "I42894916"}, "DATA61", "government_research_institute"),
        ({"ror": "03ajsaw82"}, "NASK", "government_research_institute"),
        ({"id": "I166416128"}, "DEVCOM-ARL", "government_research_institute"),
        ({"display_name": "Air Force Research Laboratory"}, "AFRL", "government_research_institute"),
        ({"ror": "05fa8ka61"}, "INESC-TEC", "public_research_institute"),
        ({"id": "I3004594783"}, "A-STAR-IHPC", "government_research_institute"),
        ({"ror": "04dcc3438"}, "CC-IN2P3", "national_compute_center"),
        ({"id": "I4210112812"}, "NSCC-SZ", "national_compute_center"),
        ({"display_name": "San Diego Supercomputer Center"}, "SDSC", "national_compute_center"),
        ({"ror": "02pe2kf23"}, "MPI-SWS", "public_research_institute"),
    ],
)
def test_audited_registry_entries(
    institution: dict[str, str], expected_code: str, expected_subtype: str
) -> None:
    category, code = _classify(institution)
    assert category == "national_lab"
    assert code == expected_code
    assert RESEARCH_LABS[code]["subtype"] == expected_subtype


@pytest.mark.parametrize(
    "institution",
    [
        {
            "id": "I1294671590",
            "display_name": "Centre National de la Recherche Scientifique",
            "type": "government",
        },
        {
            "id": "I19820366",
            "display_name": "Chinese Academy of Sciences",
            "type": "government",
        },
        {
            "id": "I1292875679",
            "display_name": "Commonwealth Scientific and Industrial Research Organisation",
            "type": "government",
        },
        {
            "id": "I115228651",
            "display_name": "Agency for Science, Technology and Research",
            "type": "government",
        },
    ],
)
def test_umbrella_organizations_remain_unclassified(
    institution: dict[str, str]
) -> None:
    assert _classify(institution) == ("other", None)
