from __future__ import annotations

import json

import polars as pl

from hpc_bibliometrics.report import build_validation_report


def test_subtype_reports_deduplicate_per_paper(tmp_path) -> None:
    venue = "ipdps"
    source_dir = tmp_path / venue
    source_dir.mkdir(parents=True)
    source = source_dir / "openalex-2024-2024.parquet"

    institutions = [
        {"display_name": "Argonne National Laboratory", "type": "facility"},
        {"display_name": "Oak Ridge National Laboratory", "type": "facility"},
        {"display_name": "Example University", "type": "education"},
    ]
    pl.DataFrame([
        {
            "publication_year": 2024,
            "institutions_json": json.dumps(institutions),
        }
    ]).write_parquet(source)

    result = build_validation_report(
        venue,
        from_year=2024,
        to_year=2024,
        cache_root=tmp_path,
    )

    subtype = pl.read_csv(result.subtype_yearly_path)
    national_lab = subtype.filter(pl.col("subtype") == "national_lab")
    assert national_lab.height == 1
    assert national_lab["papers"][0] == 1
    assert national_lab["university_collaboration_papers"][0] == 1
    assert national_lab["university_collaboration_pct"][0] == 100.0

    country = pl.read_csv(result.country_subtype_path)
    us_national_lab = country.filter(
        (pl.col("country") == "US") & (pl.col("subtype") == "national_lab")
    )
    assert us_national_lab.height == 1
    assert us_national_lab["papers"][0] == 1
    assert us_national_lab["university_collaboration_papers"][0] == 1
