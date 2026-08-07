from __future__ import annotations

import json
from pathlib import Path

from hpc_bibliometrics.cache import CACHE_FORMAT_VERSION
from hpc_bibliometrics.collector import collect_venue
from hpc_bibliometrics.config import get_venue


class FakeClient:
    def __init__(self) -> None:
        self.years: list[int] = []

    def resolve_source(self, venue):
        return {"id": "S123", "display_name": venue.display_name, "issn_l": "1530-2075"}

    def iter_works(self, source_id: str, year: int):
        self.years.append(year)
        yield {
            "id": f"https://openalex.org/W{year}",
            "title": f"Paper {year}",
            "publication_year": year,
            "primary_location": {
                "source": {"id": "https://openalex.org/S123", "display_name": "IPDPS"}
            },
        }


def test_collect_venue_uses_year_cache(monkeypatch, tmp_path: Path) -> None:
    written: list[Path] = []

    def fake_write(rows, path: Path) -> int:
        materialized = list(rows)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("placeholder", encoding="utf-8")
        written.append(path)
        return len(materialized)

    monkeypatch.setattr("hpc_bibliometrics.collector.write_parquet_atomic", fake_write)
    client = FakeClient()

    progress = []
    first = collect_venue(
        get_venue("ipdps"),
        from_year=2023,
        to_year=2024,
        cache_root=tmp_path,
        workers=2,
        client=client,
        on_year=progress.append,
    )
    second = collect_venue(
        get_venue("ipdps"),
        from_year=2023,
        to_year=2024,
        cache_root=tmp_path,
        workers=2,
        client=client,
    )

    assert first.total_count == 2
    assert {item.year for item in progress} == {2023, 2024}
    assert second.total_count == 2
    assert len(written) == 2
    assert all(item.cached for item in second.years)


def test_collect_venue_rebuilds_legacy_zero_result_cache(monkeypatch, tmp_path: Path) -> None:
    venue_dir = tmp_path / "ipdps"
    venue_dir.mkdir(parents=True)
    (venue_dir / "2024.parquet").write_text("stale zero-result cache", encoding="utf-8")
    (venue_dir / "manifest.json").write_text(
        json.dumps(
            {
                "venue": "ipdps",
                "format_version": 1,
                "years": {"2024": 0},
            }
        ),
        encoding="utf-8",
    )

    writes: list[Path] = []

    def fake_write(rows, path: Path) -> int:
        materialized = list(rows)
        path.write_text("rebuilt", encoding="utf-8")
        writes.append(path)
        return len(materialized)

    monkeypatch.setattr("hpc_bibliometrics.collector.write_parquet_atomic", fake_write)
    client = FakeClient()

    result = collect_venue(
        get_venue("ipdps"),
        from_year=2024,
        to_year=2024,
        cache_root=tmp_path,
        workers=1,
        client=client,
    )

    manifest = json.loads((venue_dir / "manifest.json").read_text(encoding="utf-8"))
    assert result.total_count == 1
    assert result.years[0].cached is False
    assert client.years == [2024]
    assert writes == [venue_dir / "2024.parquet"]
    assert manifest["format_version"] == CACHE_FORMAT_VERSION
    assert manifest["years"]["2024"] == 1
