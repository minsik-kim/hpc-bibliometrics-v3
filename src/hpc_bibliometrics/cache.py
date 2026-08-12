from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping


# Version 3 changes the authoritative conference roster from OpenAlex Source-ID
# queries to DBLP proceedings. Older zero-result caches must be rebuilt.
CACHE_FORMAT_VERSION = 3

PAPER_COLUMNS = (
    "dblp_key",
    "doi",
    "title",
    "publication_year",
    "authors_json",
    "dblp_url",
)


def venue_cache_dir(cache_root: Path, venue_key: str) -> Path:
    return cache_root / venue_key.lower()


def year_cache_path(cache_root: Path, venue_key: str, year: int) -> Path:
    return venue_cache_dir(cache_root, venue_key) / f"{year}.parquet"


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
    import polars as pl

    materialized = list(rows)
    normalized = [{column: row.get(column) for column in PAPER_COLUMNS} for row in materialized]
    if normalized:
        frame = pl.DataFrame(normalized, strict=False).select(list(PAPER_COLUMNS))
    else:
        frame = pl.DataFrame({column: pl.Series([], dtype=pl.String) for column in PAPER_COLUMNS})
        frame = frame.with_columns(pl.col("publication_year").cast(pl.Int64))

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    frame.write_parquet(temporary, compression="zstd", statistics=True)
    os.replace(temporary, path)
    return frame.height


def parquet_row_count(path: Path) -> int:
    import polars as pl

    return int(pl.scan_parquet(path).select(pl.len()).collect().item())


def is_current_paper_cache(path: Path) -> bool:
    """Return whether a partial cache is a non-empty DBLP roster in v3 schema."""
    import polars as pl

    try:
        schema = pl.scan_parquet(path).collect_schema()
        return tuple(schema.names()) == PAPER_COLUMNS and parquet_row_count(path) > 0
    except (OSError, pl.exceptions.PolarsError):
        return False


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
            "format_version": CACHE_FORMAT_VERSION,
        }
    )
    write_json_atomic(path, current)
    return path
