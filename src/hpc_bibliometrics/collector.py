from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .cache import (
    load_json,
    parquet_row_count,
    source_cache_path,
    update_manifest,
    write_json_atomic,
    write_parquet_atomic,
    year_cache_path,
)
from .config import VenueSpec
from .openalex import OpenAlexClient, work_to_row


@dataclass(frozen=True, slots=True)
class YearResult:
    year: int
    path: Path
    count: int
    cached: bool


@dataclass(frozen=True, slots=True)
class CollectionResult:
    venue: str
    source: dict[str, Any]
    years: tuple[YearResult, ...]
    manifest: Path

    @property
    def total_count(self) -> int:
        return sum(item.count for item in self.years)


def _resolve_source(client: OpenAlexClient, venue: VenueSpec, cache_root: Path) -> dict[str, Any]:
    path = source_cache_path(cache_root)
    cache = load_json(path, {})
    cached = cache.get(venue.key) if isinstance(cache, dict) else None
    if isinstance(cached, dict) and cached.get("id"):
        return dict(cached)

    source = client.resolve_source(venue)
    if not isinstance(cache, dict):
        cache = {}
    cache[venue.key] = source
    write_json_atomic(path, cache)
    return source


def _collect_year(
    client: OpenAlexClient,
    venue: VenueSpec,
    source_id: str,
    year: int,
    cache_root: Path,
    refresh: bool,
) -> YearResult:
    path = year_cache_path(cache_root, venue.key, year)
    if path.exists() and not refresh:
        # Counts are read from the manifest by the caller when available.
        return YearResult(year=year, path=path, count=0, cached=True)

    rows = (work_to_row(work) for work in client.iter_works(source_id, year))
    count = write_parquet_atomic(rows, path)
    return YearResult(year=year, path=path, count=count, cached=False)


def collect_venue(
    venue: VenueSpec,
    *,
    from_year: int,
    to_year: int,
    cache_root: Path = Path("cache"),
    workers: int = 4,
    refresh: bool = False,
    client: OpenAlexClient | None = None,
    on_year: Callable[[YearResult], None] | None = None,
) -> CollectionResult:
    if from_year > to_year:
        raise ValueError("from_year must be less than or equal to to_year")
    if workers < 1:
        raise ValueError("workers must be at least 1")

    owns_client = client is None
    api = client or OpenAlexClient()
    try:
        source = _resolve_source(api, venue, cache_root)
        source_id = str(source["id"])
        old_manifest = load_json(cache_root / venue.key / "manifest.json", {})
        old_counts = old_manifest.get("years", {}) if isinstance(old_manifest, dict) else {}

        futures = {}
        results: list[YearResult] = []
        with ThreadPoolExecutor(max_workers=min(workers, to_year - from_year + 1)) as executor:
            for year in range(from_year, to_year + 1):
                future = executor.submit(
                    _collect_year,
                    api,
                    venue,
                    source_id,
                    year,
                    cache_root,
                    refresh,
                )
                futures[future] = year

            for future in as_completed(futures):
                item = future.result()
                if item.cached:
                    cached_value = old_counts.get(str(item.year))
                    cached_count = (
                        int(cached_value)
                        if cached_value is not None
                        else parquet_row_count(item.path)
                    )
                    item = YearResult(item.year, item.path, cached_count, True)
                results.append(item)
                if on_year is not None:
                    on_year(item)

        ordered = tuple(sorted(results, key=lambda item: item.year))
        counts = {item.year: item.count for item in ordered}
        manifest = update_manifest(
            cache_root,
            venue.key,
            source=source,
            years=counts,
        )
        return CollectionResult(
            venue=venue.key,
            source=source,
            years=ordered,
            manifest=manifest,
        )
    finally:
        if owns_client:
            api.close()
