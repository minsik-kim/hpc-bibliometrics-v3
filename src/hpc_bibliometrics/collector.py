from __future__ import annotations

import json
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .cache import (
    CACHE_FORMAT_VERSION,
    load_json,
    parquet_row_count,
    update_manifest,
    write_parquet_atomic,
    year_cache_path,
)
from .config import VenueSpec
from .dblp import DblpClient


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


def _collect_year(
    client: DblpClient,
    venue: VenueSpec,
    year: int,
    cache_root: Path,
    refresh: bool,
) -> YearResult:
    path = year_cache_path(cache_root, venue.key, year)
    if path.exists() and not refresh:
        return YearResult(year=year, path=path, count=0, cached=True)

    def rows():
        for paper in client.iter_proceedings(venue, year):
            yield {
                "dblp_key": paper["dblp_key"],
                "doi": paper["doi"],
                "title": paper["title"],
                "publication_year": paper["publication_year"],
                "authors_json": json.dumps(paper["authors"], ensure_ascii=False),
                "dblp_url": paper["dblp_url"],
            }

    count = write_parquet_atomic(rows(), path)
    if count == 0:
        # Defensive guard: an empty roster must never become a valid cache.
        path.unlink(missing_ok=True)
        raise RuntimeError(f"Refusing to cache zero papers for {venue.key.upper()} {year}")
    return YearResult(year=year, path=path, count=count, cached=False)


def _manifest_format_version(manifest: Any) -> int:
    if not isinstance(manifest, dict):
        return 0
    try:
        return int(manifest.get("format_version") or 0)
    except (TypeError, ValueError):
        return 0


def collect_venue(
    venue: VenueSpec,
    *,
    from_year: int,
    to_year: int,
    cache_root: Path = Path("cache"),
    workers: int = 4,
    refresh: bool = False,
    client: DblpClient | None = None,
    on_year: Callable[[YearResult], None] | None = None,
) -> CollectionResult:
    if from_year > to_year:
        raise ValueError("from_year must be less than or equal to to_year")
    if workers < 1:
        raise ValueError("workers must be at least 1")

    owns_client = client is None
    api = client or DblpClient()
    source = {
        "provider": "DBLP",
        "display_name": venue.display_name,
        "toc_pattern": venue.dblp_toc_pattern,
    }
    try:
        old_manifest = load_json(cache_root / venue.key / "manifest.json", {})
        cache_compatible = _manifest_format_version(old_manifest) >= CACHE_FORMAT_VERSION
        effective_refresh = refresh or not cache_compatible
        old_counts = old_manifest.get("years", {}) if cache_compatible and isinstance(old_manifest, dict) else {}

        futures = {}
        results: list[YearResult] = []
        with ThreadPoolExecutor(max_workers=min(workers, to_year - from_year + 1)) as executor:
            for year in range(from_year, to_year + 1):
                future = executor.submit(_collect_year, api, venue, year, cache_root, effective_refresh)
                futures[future] = year

            for future in as_completed(futures):
                item = future.result()
                if item.cached:
                    cached_value = old_counts.get(str(item.year))
                    cached_count = int(cached_value) if cached_value is not None else parquet_row_count(item.path)
                    item = YearResult(item.year, item.path, cached_count, True)
                results.append(item)
                if on_year is not None:
                    on_year(item)

        ordered = tuple(sorted(results, key=lambda item: item.year))
        manifest = update_manifest(
            cache_root,
            venue.key,
            source=source,
            years={item.year: item.count for item in ordered},
        )
        return CollectionResult(venue.key, source, ordered, manifest)
    finally:
        if owns_client:
            api.close()
