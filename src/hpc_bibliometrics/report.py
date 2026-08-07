from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import polars as pl

from .analyze import _classify


@dataclass(frozen=True, slots=True)
class ReportResult:
    labs_path: Path
    universities_path: Path
    pairs_path: Path
    labs: int
    universities: int
    pairs: int


def build_validation_report(venue: str, *, from_year: int, to_year: int,
                            cache_root: Path = Path("cache")) -> ReportResult:
    source = cache_root / venue / f"openalex-{from_year}-{to_year}.parquet"
    if not source.exists():
        raise RuntimeError(f"Run `hpc-bib enrich {venue} --from {from_year} --to {to_year}` first")

    lab_papers: Counter[str] = Counter()
    university_papers: Counter[str] = Counter()
    pair_papers: Counter[tuple[str, str]] = Counter()

    for row in pl.read_parquet(source).to_dicts():
        institutions = json.loads(row.get("institutions_json") or "[]")
        labs: set[str] = set()
        universities: set[str] = set()
        for inst in institutions:
            if not isinstance(inst, dict):
                continue
            category, lab = _classify(inst)
            name = str(inst.get("display_name") or "").strip()
            if category == "national_lab" and lab:
                labs.add(lab)
            elif category == "university" and name:
                universities.add(name)
        for lab in labs:
            lab_papers[lab] += 1
        for university in universities:
            university_papers[university] += 1
        for lab in labs:
            for university in universities:
                pair_papers[(lab, university)] += 1

    labs_rows = [{"lab_code": lab, "papers": count} for lab, count in lab_papers.most_common()]
    university_rows = [{"university": name, "papers": count} for name, count in university_papers.most_common()]
    pair_rows = [{"lab_code": lab, "university": university, "papers": count}
                 for (lab, university), count in pair_papers.most_common()]

    out_dir = cache_root / venue / "analysis"
    out_dir.mkdir(parents=True, exist_ok=True)
    labs_path = out_dir / f"labs-{from_year}-{to_year}.csv"
    universities_path = out_dir / f"universities-{from_year}-{to_year}.csv"
    pairs_path = out_dir / f"lab-university-pairs-{from_year}-{to_year}.csv"

    pl.DataFrame(labs_rows, schema={"lab_code": pl.String, "papers": pl.Int64}).write_csv(labs_path)
    pl.DataFrame(university_rows, schema={"university": pl.String, "papers": pl.Int64}).write_csv(universities_path)
    pl.DataFrame(pair_rows, schema={"lab_code": pl.String, "university": pl.String, "papers": pl.Int64}).write_csv(pairs_path)

    return ReportResult(labs_path, universities_path, pairs_path,
                        len(lab_papers), len(university_papers), len(pair_papers))
