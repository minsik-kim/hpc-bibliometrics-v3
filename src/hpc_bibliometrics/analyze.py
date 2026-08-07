from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import polars as pl

# Conservative curated registry: only organizations that are clearly public/national
# research institutes or national supercomputing centers. Do not classify parent
# academies wholesale (for example, CAS); match institute/center-level affiliations.
RESEARCH_LABS: dict[str, dict[str, Any]] = {
    # United States - DOE national laboratories
    "ANL": {"country": "US", "aliases": ("argonne national laboratory",)},
    "BNL": {"country": "US", "aliases": ("brookhaven national laboratory",)},
    "FNAL": {"country": "US", "aliases": ("fermi national accelerator laboratory", "fermilab")},
    "INL": {"country": "US", "aliases": ("idaho national laboratory",)},
    "LANL": {"country": "US", "aliases": ("los alamos national laboratory",)},
    "LBNL": {"country": "US", "aliases": ("lawrence berkeley national laboratory", "lawrence berkeley lab")},
    "LLNL": {"country": "US", "aliases": ("lawrence livermore national laboratory",)},
    "NETL": {"country": "US", "aliases": ("national energy technology laboratory",)},
    "NREL": {"country": "US", "aliases": ("national renewable energy laboratory",)},
    "ORNL": {"country": "US", "aliases": ("oak ridge national laboratory",)},
    "PNNL": {"country": "US", "aliases": ("pacific northwest national laboratory",)},
    "PPPL": {"country": "US", "aliases": ("princeton plasma physics laboratory",)},
    "SNL": {"country": "US", "aliases": ("sandia national laboratories", "sandia national laboratory")},
    "SLAC": {"country": "US", "aliases": ("slac national accelerator laboratory",)},
    "SRNL": {"country": "US", "aliases": ("savannah river national laboratory",)},
    # China - institute/center level, intentionally not all of CAS
    "CAS-ICT": {"country": "CN", "aliases": ("institute of computing technology, chinese academy of sciences", "institute of computing technology chinese academy of sciences")},
    "CAS-SIAT": {"country": "CN", "aliases": ("shenzhen institutes of advanced technology, chinese academy of sciences", "shenzhen institute of advanced technology, chinese academy of sciences")},
    "CAS-ISCAS": {"country": "CN", "aliases": ("institute of software, chinese academy of sciences",)},
    "NSCC-TJ": {"country": "CN", "aliases": ("national supercomputing center in tianjin", "national supercomputer center in tianjin")},
    "NSCC-WX": {"country": "CN", "aliases": ("national supercomputing center in wuxi", "national supercomputer center in wuxi")},
    "NSCC-GZ": {"country": "CN", "aliases": ("national supercomputing center in guangzhou", "national supercomputer center in guangzhou")},
    "NSCC-CS": {"country": "CN", "aliases": ("national supercomputing center in changsha", "national supercomputer center in changsha")},
    "NSCC-JN": {"country": "CN", "aliases": ("national supercomputing center in jinan", "national supercomputer center in jinan")},
    # Japan - national/public research agencies with HPC relevance
    "RIKEN": {"country": "JP", "aliases": ("riken", "riken center for computational science")},
    "AIST": {"country": "JP", "aliases": ("national institute of advanced industrial science and technology", "advanced industrial science and technology")},
    "JAEA": {"country": "JP", "aliases": ("japan atomic energy agency",)},
    "JAMSTEC": {"country": "JP", "aliases": ("japan agency for marine-earth science and technology", "japan agency for marine earth science and technology")},
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


def _lab_match(name: str) -> tuple[str, str] | None:
    normalized = " ".join(name.lower().replace("&", "and").split())
    for code, spec in RESEARCH_LABS.items():
        if any(alias in normalized for alias in spec["aliases"]):
            return code, str(spec["country"])
    return None


def _lab_code(name: str) -> str | None:
    match = _lab_match(name)
    return match[0] if match else None


def _classify(inst: dict[str, Any]) -> tuple[str, str | None]:
    name = str(inst.get("display_name") or "")
    match = _lab_match(name)
    if match:
        return "national_lab", match[0]
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
    institution_counts: dict[tuple[str, str, str, str], int] = {}
    for row in frame.to_dicts():
        institutions = json.loads(row.get("institutions_json") or "[]")
        categories: set[str] = set(); labs: set[str] = set(); countries: set[str] = set(); names: set[str] = set()
        for inst in institutions:
            if not isinstance(inst, dict): continue
            category, lab = _classify(inst); categories.add(category)
            country = ""
            if lab:
                labs.add(lab); country = str(RESEARCH_LABS[lab]["country"]); countries.add(country)
            name = str(inst.get("display_name") or "").strip()
            if name:
                names.add(name); key = (category, country, lab or "", name)
                institution_counts[key] = institution_counts.get(key, 0) + 1
        has_lab = "national_lab" in categories; has_university = "university" in categories
        paper_rows.append({"dblp_key": row.get("dblp_key"), "doi": row.get("doi"), "title": row.get("title"),
            "publication_year": row.get("publication_year"), "openalex_status": row.get("status"),
            "has_national_lab": has_lab, "has_university": has_university, "has_industry": "industry" in categories,
            "lab_university_collaboration": has_lab and has_university,
            "national_lab_countries": ";".join(sorted(countries)), "national_labs": ";".join(sorted(labs)),
            "institutions": ";".join(sorted(names))})
    papers = pl.DataFrame(paper_rows, strict=False).sort(["publication_year", "dblp_key"])
    yearly = (papers.group_by("publication_year").agg(pl.len().alias("papers"),
        pl.col("has_national_lab").sum().alias("national_lab_papers"),
        pl.col("lab_university_collaboration").sum().alias("lab_university_papers"),
        pl.col("has_industry").sum().alias("industry_papers")).sort("publication_year").with_columns(
        (pl.col("national_lab_papers") / pl.col("papers") * 100).round(2).alias("national_lab_pct"),
        (pl.col("lab_university_papers") / pl.col("papers") * 100).round(2).alias("lab_university_pct")))
    inst_rows = [{"category": k[0], "country": k[1] or None, "lab_code": k[2] or None, "institution": k[3], "papers": v}
                 for k, v in institution_counts.items()]
    institutions = pl.DataFrame(inst_rows, strict=False).sort("papers", descending=True) if inst_rows else pl.DataFrame()
    out_dir = cache_root / venue / "analysis"; out_dir.mkdir(parents=True, exist_ok=True)
    papers_path = out_dir / f"papers-{from_year}-{to_year}.parquet"; yearly_path = out_dir / f"yearly-{from_year}-{to_year}.csv"
    institutions_path = out_dir / f"institutions-{from_year}-{to_year}.csv"
    papers.write_parquet(papers_path, compression="zstd"); yearly.write_csv(yearly_path); institutions.write_csv(institutions_path)
    return AnalysisResult(papers_path, yearly_path, institutions_path, papers.height,
        papers.filter(pl.col("has_national_lab")).height, papers.filter(pl.col("lab_university_collaboration")).height)
