from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import polars as pl

from .manual_enrichment import apply_manual_enrichment
from .openalex import OpenAlexClient, OpenAlexError


@dataclass(frozen=True, slots=True)
class EnrichResult:
    venue: str
    total: int
    matched: int
    missing_doi: int
    unmatched: int
    manually_enriched: int
    path: Path


def _normalize_doi(value: Any) -> str | None:
    if value is None:
        return None
    doi = str(value).strip().lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if doi.startswith(prefix):
            doi = doi[len(prefix):]
            break
    return doi or None


def _institution_rows(work: dict[str, Any]) -> tuple[str, str]:
    authors: list[dict[str, Any]] = []
    institutions: dict[str, dict[str, Any]] = {}
    for authorship in work.get("authorships") or []:
        if not isinstance(authorship, dict):
            continue
        author = authorship.get("author") or {}
        author_institutions: list[dict[str, Any]] = []
        for institution in authorship.get("institutions") or []:
            if not isinstance(institution, dict):
                continue
            item = {
                "id": institution.get("id"),
                "display_name": institution.get("display_name"),
                "country_code": institution.get("country_code"),
                "type": institution.get("type"),
                "ror": institution.get("ror"),
            }
            key = str(item.get("id") or item.get("ror") or item.get("display_name") or "")
            if key:
                institutions[key] = item
            author_institutions.append(item)
        authors.append({
            "id": author.get("id"),
            "display_name": author.get("display_name"),
            "institutions": author_institutions,
        })
    return (
        json.dumps(authors, ensure_ascii=False),
        json.dumps(list(institutions.values()), ensure_ascii=False),
    )


def _apply_manual_enrichments(frame: pl.DataFrame) -> tuple[pl.DataFrame, int]:
    rows: list[dict[str, Any]] = []
    applied = 0
    for row in frame.to_dicts():
        updated, did_apply = apply_manual_enrichment(row)
        rows.append(updated)
        applied += int(did_apply)
    return (
        pl.DataFrame(rows, strict=False, infer_schema_length=None).sort(
            ["publication_year", "dblp_key"]
        ),
        applied,
    )


def _write_enrichment(frame: pl.DataFrame, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(f".{output.name}.tmp")
    frame.write_parquet(temporary, compression="zstd", statistics=True)
    temporary.replace(output)


def enrich_venue(
    venue: str,
    *,
    from_year: int,
    to_year: int,
    cache_root: Path = Path("cache"),
    workers: int = 4,
    refresh: bool = False,
) -> EnrichResult:
    if from_year > to_year:
        raise ValueError("from_year must be less than or equal to to_year")
    roster_paths = [cache_root / venue / f"{year}.parquet" for year in range(from_year, to_year + 1)]
    missing = [str(path) for path in roster_paths if not path.exists()]
    if missing:
        raise RuntimeError("Collect DBLP roster first; missing: " + ", ".join(missing))

    output = cache_root / venue / f"openalex-{from_year}-{to_year}.parquet"
    if output.exists() and not refresh:
        cached = pl.read_parquet(output)
        frame, applied = _apply_manual_enrichments(cached)
        if not cached.equals(frame):
            _write_enrichment(frame, output)
        return EnrichResult(
            venue, frame.height,
            frame.filter(pl.col("status") == "matched").height,
            frame.filter(pl.col("status") == "missing_doi").height,
            frame.filter(pl.col("status") == "unmatched").height,
            frame.filter(pl.col("metadata_source") == "manual").height,
            output,
        )

    roster = pl.concat([pl.read_parquet(path) for path in roster_paths], how="vertical")
    records = roster.to_dicts()

    reusable: dict[str, dict[str, Any]] = {}
    if not refresh:
        for candidate in sorted((cache_root / venue).glob("openalex-*.parquet")):
            if candidate == output:
                continue
            for cached_row in pl.read_parquet(candidate).to_dicts():
                key = str(cached_row.get("dblp_key") or "")
                if key:
                    reusable[key] = cached_row

    def lookup(row: dict[str, Any]) -> dict[str, Any]:
        doi = _normalize_doi(row.get("doi"))
        base = {
            "dblp_key": row.get("dblp_key"),
            "doi": doi,
            "title": row.get("title"),
            "publication_year": row.get("publication_year"),
        }
        if not doi:
            return {**base, "status": "missing_doi", "openalex_id": None,
                    "authorships_json": "[]", "institutions_json": "[]",
                    "metadata_source": None, "metadata_source_url": None,
                    "metadata_verified_on": None}
        try:
            with OpenAlexClient() as client:
                work = client.get_work_by_doi(doi)
        except OpenAlexError as exc:
            if exc.status_code == 404:
                unmatched = {**base, "status": "unmatched", "openalex_id": None,
                             "authorships_json": "[]", "institutions_json": "[]",
                             "metadata_source": None, "metadata_source_url": None,
                             "metadata_verified_on": None}
                return apply_manual_enrichment(unmatched)[0]
            raise
        authorships_json, institutions_json = _institution_rows(work)
        return {**base, "status": "matched", "openalex_id": work.get("id"),
                "authorships_json": authorships_json, "institutions_json": institutions_json,
                "metadata_source": "openalex", "metadata_source_url": work.get("id"),
                "metadata_verified_on": None}

    rows: list[dict[str, Any]] = []
    to_fetch: list[dict[str, Any]] = []
    for row in records:
        cached_row = reusable.get(str(row.get("dblp_key") or ""))
        if cached_row is not None and _normalize_doi(cached_row.get("doi")) == _normalize_doi(row.get("doi")):
            rows.append(cached_row)
        else:
            to_fetch.append(row)

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(lookup, row) for row in to_fetch]
        for future in as_completed(futures):
            rows.append(future.result())

    combined = pl.DataFrame(rows, strict=False, infer_schema_length=None).sort(["publication_year", "dblp_key"])
    result, _ = _apply_manual_enrichments(combined)
    _write_enrichment(result, output)
    return EnrichResult(
        venue, result.height,
        result.filter(pl.col("status") == "matched").height,
        result.filter(pl.col("status") == "missing_doi").height,
        result.filter(pl.col("status") == "unmatched").height,
        result.filter(pl.col("metadata_source") == "manual").height,
        output,
    )
