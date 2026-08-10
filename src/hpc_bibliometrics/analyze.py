from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import polars as pl

# Conservative curated registry: public/national research institutes and national
# supercomputing centers only. Parent academies (for example CAS/CNRS) are not
# classified wholesale. OpenAlex IDs/RORs take precedence over name aliases.
RESEARCH_LABS: dict[str, dict[str, Any]] = {
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

    # China: institute/center-level entries only. CAS itself is intentionally excluded.
    "CAS-ICT": {"country": "CN", "openalex_ids": ("I4210090176",), "rors": ("0090r4d87",),
        "aliases": ("institute of computing technology", "institute of computing technology, chinese academy of sciences")},
    "CAS-SIAT": {"country": "CN", "openalex_ids": ("I4210145761",), "rors": ("04gh4er46",),
        "aliases": ("shenzhen institutes of advanced technology", "shenzhen institute of advanced technology")},
    "CAS-ISCAS": {"country": "CN", "openalex_ids": ("I4210128818",), "rors": ("033dfsn42",),
        "aliases": ("institute of software, chinese academy of sciences", "institute of software")},
    "CAS-IIE": {"country": "CN", "openalex_ids": ("I4210156404",), "rors": ("04r53se39",),
        "aliases": ("institute of information engineering",)},
    "CAS-CNIC": {"country": "CN", "openalex_ids": ("I4210108629",), "rors": ("01s0wyf50",),
        "aliases": ("computer network information center",)},
    "WNLO": {"country": "CN", "openalex_ids": ("I4210138186",), "rors": ("03c9ncn37",),
        "aliases": ("wuhan national laboratory for optoelectronics",)},
    "PCL": {"country": "CN", "openalex_ids": ("I4210136793",), "rors": ("03qdqbt06",),
        "aliases": ("peng cheng laboratory",)},
    "ZJLAB": {"country": "CN", "openalex_ids": ("I4210123185",), "rors": ("02m2h7991",),
        "aliases": ("zhejiang lab",)},
    "PML": {"country": "CN", "openalex_ids": ("I4210155350",), "rors": ("04zcbk583",),
        "aliases": ("purple mountain laboratories", "purple mountain laboratory")},
    "NSCC-TJ": {"country": "CN", "aliases": ("national supercomputing center in tianjin", "national supercomputer center in tianjin")},
    "NSCC-WX": {"country": "CN", "aliases": ("national supercomputing center in wuxi", "national supercomputer center in wuxi")},
    "NSCC-GZ": {"country": "CN", "aliases": ("national supercomputing center in guangzhou", "national supercomputer center in guangzhou")},
    "NSCC-CS": {"country": "CN", "aliases": ("national supercomputing center in changsha", "national supercomputer center in changsha")},
    "NSCC-JN": {"country": "CN", "aliases": ("national supercomputing center in jinan", "national supercomputer center in jinan")},

    # Japan: national/public research agencies and inter-university research institutes.
    "RIKEN": {"country": "JP", "aliases": ("riken center for computational science", "riken")},
    "AIST": {"country": "JP", "openalex_ids": ("I138495182",),
        "aliases": ("national institute of advanced industrial science and technology", "advanced industrial science and technology")},
    "NII": {"country": "JP", "openalex_ids": ("I184597095",), "rors": ("04ksd4g47",),
        "aliases": ("national institute of informatics",)},
    "NICT": {"country": "JP", "openalex_ids": ("I90023481",), "rors": ("016bgq349",),
        "aliases": ("national institute of information and communications technology",)},
    "JAEA": {"country": "JP", "aliases": ("japan atomic energy agency",)},
    "JAMSTEC": {"country": "JP", "aliases": ("japan agency for marine-earth science and technology", "japan agency for marine earth science and technology")},

    # Korea
    "KISTI": {"country": "KR", "openalex_ids": ("I878022262",), "rors": ("01k4yrm29",),
        "aliases": ("korea institute of science and technology information",)},
    "ETRI": {"country": "KR", "openalex_ids": ("I142401562",), "rors": ("03ysstz10",),
        "aliases": ("electronics and telecommunications research institute",)},

    # Germany
    "ZIB": {"country": "DE", "openalex_ids": ("I195893171",), "rors": ("02eva5865",),
        "aliases": ("zuse institute berlin",)},
    "MPCDF": {"country": "DE", "openalex_ids": ("I4210132734",), "rors": ("03e21z229",),
        "aliases": ("max planck computing and data facility",)},
    "LRZ": {"country": "DE", "openalex_ids": ("I4210163716",), "rors": ("05558nw16",),
        "aliases": ("leibniz supercomputing centre", "leibniz supercomputing center")},
    "HZDR": {"country": "DE", "openalex_ids": ("I2801798921",), "rors": ("01zy2cs03",),
        "aliases": ("helmholtz-zentrum dresden-rossendorf", "helmholtz zentrum dresden rossendorf")},
    "CASUS": {"country": "DE", "openalex_ids": ("I4210133756",), "rors": ("042b69396",),
        "aliases": ("center for advanced systems understanding",)},

    # France: national research organizations/centers. CNRS as a whole is excluded.
    "INRIA": {"country": "FR", "openalex_ids": ("I1326498283",), "rors": ("02kvxyf05",),
        "aliases": ("institut national de recherche en sciences et technologies du numérique", "inria")},
    "INRIA-BORDEAUX": {"country": "FR", "openalex_ids": ("I4210131512",), "rors": ("03tjcj052",),
        "aliases": ("centre inria de l'université de bordeaux", "centre inria de l'universite de bordeaux")},
    "INRIA-RENNES": {"country": "FR", "openalex_ids": ("I4210133778",), "rors": ("04040yw90",),
        "aliases": ("centre inria de l'université de rennes", "centre inria de l'universite de rennes")},
    "INRIA-GRENOBLE": {"country": "FR", "openalex_ids": ("I4210101348",), "rors": ("00n8d6z93",),
        "aliases": ("centre inria de l'université grenoble alpes", "centre inria de l'universite grenoble alpes")},
    "CEA": {"country": "FR", "openalex_ids": ("I2738703131",), "rors": ("00jjx8s55",),
        "aliases": ("commissariat à l'énergie atomique et aux énergies alternatives", "commissariat a l'energie atomique et aux energies alternatives")},
    "CEA-GRENOBLE": {"country": "FR", "openalex_ids": ("I3020098449",), "rors": ("02mg6n827",),
        "aliases": ("cea grenoble",)},
    "CEA-CESTA": {"country": "FR", "openalex_ids": ("I129235615",), "rors": ("026ma2c10",),
        "aliases": ("cea cesta",)},
    "CEA-SACLAY": {"country": "FR", "openalex_ids": ("I4210128565",), "rors": ("03n15ch10",),
        "aliases": ("cea paris-saclay", "cea paris saclay")},
    "MAISON-SIM": {"country": "FR", "openalex_ids": ("I4210125654",), "rors": ("03jv6w209",),
        "aliases": ("maison de la simulation",)},

    # United Kingdom
    "RAL": {"country": "GB", "openalex_ids": ("I1286704778",), "rors": ("03gq8fr08",),
        "aliases": ("rutherford appleton laboratory",)},
    "ECMWF": {"country": "GB", "openalex_ids": ("I154986956",), "rors": ("014w0fd65",),
        "aliases": ("european centre for medium-range weather forecasts", "european centre for medium range weather forecasts")},
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


def _short_id(value: Any) -> str:
    return str(value or "").rstrip("/").rsplit("/", 1)[-1]


def _normalize_institution_name(value: Any) -> str:
    return " ".join(str(value or "").lower().replace("&", "and").split())


def _lab_match(inst: dict[str, Any]) -> tuple[str, str] | None:
    name = _normalize_institution_name(inst.get("display_name"))
    openalex_id = _short_id(inst.get("id"))
    ror = _short_id(inst.get("ror"))
    for code, spec in RESEARCH_LABS.items():
        if openalex_id and openalex_id in spec.get("openalex_ids", ()):
            return code, str(spec["country"])
        if ror and ror in spec.get("rors", ()):
            return code, str(spec["country"])
        aliases = (_normalize_institution_name(alias) for alias in spec.get("aliases", ()))
        if name and any(alias in name for alias in aliases):
            return code, str(spec["country"])
    return None


def _lab_code(name: str) -> str | None:
    match = _lab_match({"display_name": name})
    return match[0] if match else None


def _classify(inst: dict[str, Any]) -> tuple[str, str | None]:
    match = _lab_match(inst)
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
