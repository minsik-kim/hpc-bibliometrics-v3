from hpc_bibliometrics.cache import load_json, write_json_atomic


def test_json_cache_round_trip(tmp_path) -> None:
    path = tmp_path / "nested" / "cache.json"
    write_json_atomic(path, {"ipdps": {"id": "S123"}})
    assert load_json(path, {}) == {"ipdps": {"id": "S123"}}


def test_manifest_merges_years(tmp_path) -> None:
    from hpc_bibliometrics.cache import update_manifest

    update_manifest(
        tmp_path,
        "ipdps",
        source={"id": "S123"},
        years={2023: 10},
    )
    path = update_manifest(
        tmp_path,
        "ipdps",
        source={"id": "S123"},
        years={2024: 11},
    )

    assert load_json(path, {})["years"] == {"2023": 10, "2024": 11}


def test_parquet_round_trip_when_polars_is_available(tmp_path) -> None:
    import pytest

    pytest.importorskip("polars")
    from hpc_bibliometrics.cache import parquet_row_count, write_parquet_atomic

    path = tmp_path / "works.parquet"
    count = write_parquet_atomic(
        [
            {"openalex_id": "W1", "title": "One", "publication_year": 2024},
            {"openalex_id": "W2", "title": "Two", "publication_year": 2024},
        ],
        path,
    )

    assert count == 2
    assert parquet_row_count(path) == 2
