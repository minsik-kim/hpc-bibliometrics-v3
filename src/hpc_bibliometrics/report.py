from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import polars as pl

from .analyze import RESEARCH_LABS, _classify

@dataclass(frozen=True, slots=True)
class ReportResult:
    labs_path: Path
    universities_path: Path
    pairs_path: Path
    subtype_yearly_path: Path
    labs: int
    universities: int
    pairs: int

@dataclass(frozen=True, slots=True)
class AuditResult:
    path: Path
    institutions: int


def build_validation_report(venue: str, *, from_year: int, to_year: int, cache_root: Path = Path("cache")) -> ReportResult:
    source = cache_root / venue / f"openalex-{from_year}-{to_year}.parquet"
    if not source.exists():
        raise RuntimeError(f"Run `hpc-bib enrich {venue} --from {from_year} --to {to_year}` first")

    lab_papers: Counter[str] = Counter()
    university_papers: Counter[str] = Counter()
    pair_papers: Counter[tuple[str, str]] = Counter()
    subtype_yearly: Counter[tuple[int, str, str]] = Counter()

    for row in pl.read_parquet(source).to_dicts():
        institutions = json.loads(row.get("institutions_json") or "[]")
        labs: set[str] = set()
        universities: set[str] = set()
        year = int(row.get("publication_year") or 0)

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

        subtypes = {str(RESEARCH_LABS[lab].get("subtype", "national_lab")) for lab in labs}
        for subtype in subtypes:
            subtype_yearly[(year, subtype, "papers")] += 1
            if universities:
                subtype_yearly[(year, subtype, "university_collaboration_papers")] += 1

    labs_rows = [
        {"country": RESEARCH_LABS[lab]["country"], "lab_code": lab,
         "subtype": RESEARCH_LABS[lab].get("subtype", "national_lab"), "papers": count}
        for lab, count in lab_papers.most_common()
    ]
    university_rows = [{"university": name, "papers": count} for name, count in university_papers.most_common()]
    pair_rows = [
        {"country": RESEARCH_LABS[lab]["country"], "lab_code": lab,
         "subtype": RESEARCH_LABS[lab].get("subtype", "national_lab"),
         "university": university, "papers": count}
        for (lab, university), count in pair_papers.most_common()
    ]

    subtype_keys = sorted({(year, subtype) for year, subtype, _metric in subtype_yearly})
    subtype_rows = []
    for year, subtype in subtype_keys:
        papers = subtype_yearly[(year, subtype, "papers")]
        collab = subtype_yearly[(year, subtype, "university_collaboration_papers")]
        subtype_rows.append({
            "publication_year": year,
            "subtype": subtype,
            "papers": papers,
            "university_collaboration_papers": collab,
            "university_collaboration_pct": round((collab / papers * 100) if papers else 0.0, 2),
        })

    out_dir = cache_root / venue / "analysis"
    out_dir.mkdir(parents=True, exist_ok=True)
    labs_path = out_dir / f"labs-{from_year}-{to_year}.csv"
    universities_path = out_dir / f"universities-{from_year}-{to_year}.csv"
    pairs_path = out_dir / f"lab-university-pairs-{from_year}-{to_year}.csv"
    subtype_yearly_path = out_dir / f"public-research-subtypes-yearly-{from_year}-{to_year}.csv"

    pl.DataFrame(labs_rows, schema={"country": pl.String, "lab_code": pl.String, "subtype": pl.String, "papers": pl.Int64}).write_csv(labs_path)
    pl.DataFrame(university_rows, schema={"university": pl.String, "papers": pl.Int64}).write_csv(universities_path)
    pl.DataFrame(pair_rows, schema={"country": pl.String, "lab_code": pl.String, "subtype": pl.String, "university": pl.String, "papers": pl.Int64}).write_csv(pairs_path)
    pl.DataFrame(subtype_rows, schema={"publication_year": pl.Int64, "subtype": pl.String, "papers": pl.Int64, "university_collaboration_papers": pl.Int64, "university_collaboration_pct": pl.Float64}).write_csv(subtype_yearly_path)

    return ReportResult(labs_path, universities_path, pairs_path, subtype_yearly_path, len(lab_papers), len(university_papers), len(pair_papers))


def audit_other_institutions(venue: str, *, from_year: int, to_year: int, countries: set[str] | None = None, cache_root: Path = Path("cache")) -> AuditResult:
    source = cache_root / venue / f"openalex-{from_year}-{to_year}.parquet"
    if not source.exists():
        raise RuntimeError(f"Run `hpc-bib enrich {venue} --from {from_year} --to {to_year}` first")
    counts: Counter[tuple[str, str, str, str, str]] = Counter()
    for row in pl.read_parquet(source).to_dicts():
        seen: set[tuple[str, str, str, str, str]] = set()
        for inst in json.loads(row.get("institutions_json") or "[]"):
            if not isinstance(inst, dict):
                continue
            category, _ = _classify(inst)
            if category != "other":
                continue
            country = str(inst.get("country_code") or "").upper()
            if countries and country not in countries:
                continue
            name = str(inst.get("display_name") or "").strip()
            if not name:
                continue
            key = (country, name, str(inst.get("type") or ""), str(inst.get("id") or ""), str(inst.get("ror") or ""))
            seen.add(key)
        for key in seen:
            counts[key] += 1
    rows = [{"country": k[0], "institution": k[1], "openalex_type": k[2], "openalex_id": k[3], "ror": k[4], "papers": v} for k, v in counts.most_common()]
    out_dir = cache_root / venue / "analysis"
    out_dir.mkdir(parents=True, exist_ok=True)
    suffix = "-".join(sorted(countries)) if countries else "all"
    path = out_dir / f"other-institutions-{suffix}-{from_year}-{to_year}.csv"
    schema = {"country": pl.String, "institution": pl.String, "openalex_type": pl.String, "openalex_id": pl.String, "ror": pl.String, "papers": pl.Int64}
    pl.DataFrame(rows, schema=schema).write_csv(path)
    return AuditResult(path, len(rows))
