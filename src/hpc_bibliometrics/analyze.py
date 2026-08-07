from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import polars as pl

# Curated DOE national-lab aliases. Matching OpenAlex IDs/RORs can be added
# without changing analysis semantics; names cover the common affiliation forms.
DOE_LAB_ALIASES: dict[str, tuple[str, ...]] = {
    "ANL": ("argonne national laboratory",),
    "BNL": ("brookhaven national laboratory",),
    "FNAL": ("fermi national accelerator laboratory", "fermilab"),
    "INL": ("idaho national laboratory",),
    "LANL": ("los alamos national laboratory",),
    "LBNL": ("lawrence berkeley national laboratory", "lawrence berkeley lab"),
    "LLNL": ("lawrence livermore national laboratory",),
    "NETL": ("national energy technology laboratory",),
    "NREL": ("national renewable energy laboratory",),
    "ORNL": ("oak ridge national laboratory",),
    "PNNL": ("pacific northwest national laboratory",),
    "PPPL": ("princeton plasma physics laboratory",),
    "SNL": ("sandia national laboratories", "sandia national laboratory"),
    "SLAC": ("slac national accelerator laboratory",),
    "SRNL": ("savannah river national laboratory",),
}

UNIVERSITY_TYPES = {"education"}
INDUSTRY_TYPES = {"company"}

@dataclass(frozen=True, slots=True)
class AnalysisResult:
    papers_path: Path
    yearly_path: Path
    institutions_path: Path
    total: int
    lab_papers: int
    lab_university_papers: int


def _lab_code(name: str) -> str | None:
    normalized = " ".join(name.lower().replace("&", "and").split())
    for code, aliases in DOE_LAB_ALIASES.items():
        if any(alias in normalized for alias in aliases):
            return code
    return None


def _classify(inst: dict[str, Any]) -> tuple[str, str | None]:
    name = str(inst.get("display_name") or "")
    lab = _lab_code(name)
    if lab:
        return "national_lab", lab
    kind = str(inst.get("type") or "").lower()
    if kind in UNIVERSITY_TYPES:
        return "university", None
    if kind in INDUSTRY_TYPES:
        return "industry", None
    return "other", None


def analyze_collaboration(venue: str, *, from_year: int, to_year: int,
                          cache_root: Path = Path("cache")) -> AnalysisResult:
    source = cache_root / venue / f"openalex-{from_year}-{to_year}.parquet"
    if not source.exists():
        raise RuntimeError(f"Run `hpc-bib enrich {venue} --from {from_year} --to {to_year}` first")
    frame = pl.read_parquet(source)
    paper_rows: list[dict[str, Any]] = []
    institution_counts: dict[tuple[str, str, str], int] = {}
    for row in frame.to_dicts():
        institutions = json.loads(row.get("institutions_json") or "[]")
        categories: set[str] = set()
        labs: set[str] = set()
        names: set[str] = set()
        for inst in institutions:
            if not isinstance(inst, dict):
                continue
            category, lab = _classify(inst)
            categories.add(category)
            if lab:
                labs.add(lab)
            name = str(inst.get("display_name") or "").strip()
            if name:
                names.add(name)
                key = (category, lab or "", name)
                institution_counts[key] = institution_counts.get(key, 0) + 1
        has_lab = "national_lab" in categories
        has_university = "university" in categories
        paper_rows.append({
            "dblp_key": row.get("dblp_key"), "doi": row.get("doi"), "title": row.get("title"),
            "publication_year": row.get("publication_year"), "openalex_status": row.get("status"),
            "has_national_lab": has_lab, "has_university": has_university,
            "has_industry": "industry" in categories,
            "lab_university_collaboration": has_lab and has_university,
            "national_labs": ";".join(sorted(labs)), "institutions": ";".join(sorted(names)),
        })
    papers = pl.DataFrame(paper_rows, strict=False).sort(["publication_year", "dblp_key"])
    yearly = (papers.group_by("publication_year").agg(
        pl.len().alias("papers"),
        pl.col("has_national_lab").sum().alias("national_lab_papers"),
        pl.col("lab_university_collaboration").sum().alias("lab_university_papers"),
        pl.col("has_industry").sum().alias("industry_papers"),
    ).sort("publication_year").with_columns(
        (pl.col("national_lab_papers") / pl.col("papers") * 100).round(2).alias("national_lab_pct"),
        (pl.col("lab_university_papers") / pl.col("papers") * 100).round(2).alias("lab_university_pct"),
    ))
    inst_rows = [{"category": k[0], "lab_code": k[1] or None, "institution": k[2], "papers": v}
                 for k, v in institution_counts.items()]
    institutions = pl.DataFrame(inst_rows, strict=False).sort("papers", descending=True) if inst_rows else pl.DataFrame()
    out_dir = cache_root / venue / "analysis"
    out_dir.mkdir(parents=True, exist_ok=True)
    papers_path = out_dir / f"papers-{from_year}-{to_year}.parquet"
    yearly_path = out_dir / f"yearly-{from_year}-{to_year}.csv"
    institutions_path = out_dir / f"institutions-{from_year}-{to_year}.csv"
    papers.write_parquet(papers_path, compression="zstd")
    yearly.write_csv(yearly_path)
    institutions.write_csv(institutions_path)
    return AnalysisResult(papers_path, yearly_path, institutions_path, papers.height,
                          papers.filter(pl.col("has_national_lab")).height,
                          papers.filter(pl.col("lab_university_collaboration")).height)
