from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping


PAPER_COLUMNS = (
    "openalex_id",
    "doi",
    "title",
    "publication_year",
    "publication_date",
    "work_type",
    "cited_by_count",
    "source_id",
    "source_name",
    "authorships_json",
    "topics_json",
    "keywords_json",
)


def venue_cache_dir(cache_root: Path, venue_key: str) -> Path:
    return cache_root / venue_key.lower()


def year_cache_path(cache_root: Path, venue_key: str, year: int) -> Path:
    return venue_cache_dir(cache_root, venue_key) / f"{year}.parquet"


def source_cache_path(cache_root: Path) -> Path:
    return cache_root / "sources.json"


def manifest_path(cache_root: Path, venue_key: str) -> Path:
    return venue_cache_dir(cache_root, venue_key) / "manifest.json"


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json_atomic(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
    os.replace(temporary, path)


def write_parquet_atomic(rows: Iterable[Mapping[str, Any]], path: Path) -> int:
    """Write one year's works atomically and return the row count.

    Polars is imported lazily so configuration and API tests can run without
    loading the native dataframe extension.
    """

    import polars as pl

    materialized = list(rows)
    normalized = [{column: row.get(column) for column in PAPER_COLUMNS} for row in materialized]

    if normalized:
        frame = pl.DataFrame(normalized, strict=False).select(list(PAPER_COLUMNS))
    else:
        frame = pl.DataFrame(
            {
                "openalex_id": pl.Series([], dtype=pl.String),
                "doi": pl.Series([], dtype=pl.String),
                "title": pl.Series([], dtype=pl.String),
                "publication_year": pl.Series([], dtype=pl.Int64),
                "publication_date": pl.Series([], dtype=pl.String),
                "work_type": pl.Series([], dtype=pl.String),
                "cited_by_count": pl.Series([], dtype=pl.Int64),
                "source_id": pl.Series([], dtype=pl.String),
                "source_name": pl.Series([], dtype=pl.String),
                "authorships_json": pl.Series([], dtype=pl.String),
                "topics_json": pl.Series([], dtype=pl.String),
                "keywords_json": pl.Series([], dtype=pl.String),
            }
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    frame.write_parquet(temporary, compression="zstd", statistics=True)
    os.replace(temporary, path)
    return frame.height


def parquet_row_count(path: Path) -> int:
    """Return a cached Parquet file's row count."""

    import polars as pl

    return int(pl.scan_parquet(path).select(pl.len()).collect().item())


def update_manifest(
    cache_root: Path,
    venue_key: str,
    *,
    source: Mapping[str, Any],
    years: Mapping[int, int],
) -> Path:
    path = manifest_path(cache_root, venue_key)
    current = load_json(path, {})
    previous_years = current.get("years", {}) if isinstance(current, dict) else {}
    merged_years = dict(previous_years) if isinstance(previous_years, dict) else {}
    merged_years.update({str(year): count for year, count in years.items()})
    current.update(
        {
            "venue": venue_key,
            "source": dict(source),
            "years": dict(sorted(merged_years.items(), key=lambda item: int(item[0]))),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "format_version": 1,
        }
    )
    write_json_atomic(path, current)
    return path
