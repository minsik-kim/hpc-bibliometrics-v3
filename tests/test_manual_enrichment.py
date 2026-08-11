from __future__ import annotations

import json

import polars as pl

from hpc_bibliometrics.enrich import _apply_manual_enrichments, enrich_venue
from hpc_bibliometrics.manual_enrichment import (
    MANUAL_ENRICHMENTS,
    apply_manual_enrichment,
)


def _unmatched_row(dblp_key: str, doi: str) -> dict[str, object]:
    return {
        "dblp_key": dblp_key,
        "doi": doi,
        "title": "Example",
        "publication_year": 2023,
        "status": "unmatched",
        "openalex_id": None,
        "authorships_json": "[]",
        "institutions_json": "[]",
    }


def test_all_manual_enrichments_preserve_unmatched_status_and_provenance() -> None:
    assert len(MANUAL_ENRICHMENTS) == 6

    for dblp_key, override in MANUAL_ENRICHMENTS.items():
        row, applied = apply_manual_enrichment(
            _unmatched_row(dblp_key, override.doi)
        )
        institutions = json.loads(str(row["institutions_json"]))

        assert applied
        assert row["status"] == "unmatched"
        assert row["openalex_id"] is None
        assert row["metadata_source"] == "manual"
        assert row["metadata_source_url"] == override.source_url
        assert row["metadata_verified_on"] == "2026-08-11"
        assert institutions


def test_manual_enrichment_requires_exact_unmatched_dblp_and_doi_pair() -> None:
    key = "conf/hpdc/Movsowitz-Davidow23"
    override = MANUAL_ENRICHMENTS[key]

    wrong_doi, wrong_doi_applied = apply_manual_enrichment(
        _unmatched_row(key, "10.0000/wrong")
    )
    matched, matched_applied = apply_manual_enrichment(
        {**_unmatched_row(key, override.doi), "status": "matched"}
    )

    assert not wrong_doi_applied
    assert wrong_doi["institutions_json"] == "[]"
    assert not matched_applied
    assert matched["metadata_source"] == "openalex"


def test_existing_cache_is_backfilled_without_openalex_request(tmp_path) -> None:
    venue_dir = tmp_path / "hpdc"
    venue_dir.mkdir()
    key = "conf/hpdc/Movsowitz-Davidow23"
    override = MANUAL_ENRICHMENTS[key]

    pl.DataFrame(
        {
            "dblp_key": [key],
            "doi": [override.doi],
            "title": ["Deconstructing Alibaba Cloud's Preemptible Instance Pricing"],
            "publication_year": [2023],
            "authors_json": ['["A"]'],
            "dblp_url": ["https://dblp.org/example"],
        }
    ).write_parquet(venue_dir / "2023.parquet")
    pl.DataFrame([_unmatched_row(key, override.doi)]).write_parquet(
        venue_dir / "openalex-2023-2023.parquet"
    )

    result = enrich_venue(
        "hpdc",
        from_year=2023,
        to_year=2023,
        cache_root=tmp_path,
    )
    cached = pl.read_parquet(result.path)

    assert result.unmatched == 1
    assert result.manually_enriched == 1
    assert cached["metadata_source"].to_list() == ["manual"]
    assert json.loads(cached["institutions_json"][0])[0]["display_name"] == (
        "University of Haifa"
    )


def test_manual_provenance_schema_is_inferred_beyond_first_hundred_rows() -> None:
    ordinary = [
        {
            **_unmatched_row(f"conf/example/{index}", f"10.0000/{index}"),
            "publication_year": 2022,
        }
        for index in range(110)
    ]
    key = "conf/hpdc/Movsowitz-Davidow23"
    override = MANUAL_ENRICHMENTS[key]

    frame, applied = _apply_manual_enrichments(
        pl.DataFrame(ordinary + [_unmatched_row(key, override.doi)])
    )

    assert applied == 1
    assert frame.schema["metadata_verified_on"] == pl.String
