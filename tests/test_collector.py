from __future__ import annotations

from pathlib import Path

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
