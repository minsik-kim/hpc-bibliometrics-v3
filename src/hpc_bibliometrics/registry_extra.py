from __future__ import annotations

from .analyze import RESEARCH_LABS

# Additional research-infrastructure institutions discovered by audit. Keep this
# separate from the core registry so country expansion does not churn analyze.py.
RESEARCH_LABS.update({
    "NLESC": {"country": "NL", "subtype": "public_research_institute", "openalex_ids": ("I4210095242",), "rors": ("00rbjv475",), "aliases": ("netherlands escience center", "netherlands e-science center")},
    "ASTRON": {"country": "NL", "subtype": "public_research_institute", "openalex_ids": ("I922237871",), "rors": ("000k1q888",), "aliases": ("netherlands institute for radio astronomy", "astron")},
    "CWI": {"country": "NL", "subtype": "public_research_institute", "openalex_ids": ("I1341640284",), "rors": ("00x7ekv49",), "aliases": ("centrum wiskunde & informatica", "centrum wiskunde en informatica")},
    "PAWSEY": {"country": "AU", "subtype": "national_compute_center", "openalex_ids": ("I2801909468",), "rors": ("04f2f0537",), "aliases": ("pawsey supercomputing research centre", "pawsey supercomputing research center")},
    "BSC": {"country": "ES", "subtype": "national_compute_center", "openalex_ids": ("I2799803557",), "rors": ("05sd8tv96",), "aliases": ("barcelona supercomputing center", "barcelona supercomputing centre")},
    "AS-IIS": {"country": "TW", "subtype": "public_research_institute", "openalex_ids": ("I4210098366",), "rors": ("00z83z196",), "aliases": ("institute of information science, academia sinica", "institute of information science academia sinica")},
    "CSCS": {"country": "CH", "subtype": "national_compute_center", "openalex_ids": ("I4391767926",), "rors": ("04rzmms09",), "aliases": ("cscs - swiss national supercomputing centre", "swiss national supercomputing centre", "swiss national supercomputing center")},
    "CINECA": {"country": "IT", "subtype": "national_compute_center", "openalex_ids": ("I4210119786",), "rors": ("02f013h18",), "aliases": ("cineca",)},
    "NERSC": {"country": "US", "subtype": "national_compute_center", "openalex_ids": ("I4210151627",), "rors": ("05v3mvq14",), "aliases": ("national energy research scientific computing center", "nersc")},
    "TACC": {"country": "US", "subtype": "national_compute_center", "openalex_ids": ("I4388891828",), "rors": ("00xg4bh43",), "aliases": ("texas advanced computing center", "texas advanced computing centre")},
    "FZJ": {"country": "DE", "subtype": "public_research_institute", "openalex_ids": ("I171892758",), "rors": ("02nv7yv05",), "aliases": ("forschungszentrum jülich", "forschungszentrum julich", "julich research centre", "julich research center")},
    "SIMULA": {"country": "NO", "subtype": "public_research_institute", "openalex_ids": ("I2799829267",), "rors": ("00vn06n10",), "aliases": ("simula research laboratory",)},
    "MIT-LL": {"country": "US", "subtype": "government_research_institute", "openalex_ids": ("I4210122954",), "rors": ("022z6jk58",), "aliases": ("mit lincoln laboratory", "massachusetts institute of technology lincoln laboratory")},
    "JLAB": {"country": "US", "subtype": "national_lab", "openalex_ids": ("I29801172",), "rors": ("02vwzrd76",), "aliases": ("thomas jefferson national accelerator facility", "jefferson lab")},
    "JGI": {"country": "US", "subtype": "public_research_institute", "openalex_ids": ("I196679689",), "rors": ("04xm1d337",), "aliases": ("joint genome institute", "doe joint genome institute")},
    "NCSA": {"country": "US", "subtype": "national_compute_center", "openalex_ids": ("I4210135837",), "rors": ("03r10zj06",), "aliases": ("national center for supercomputing applications", "national centre for supercomputing applications")},
    "DKRZ": {"country": "DE", "subtype": "national_compute_center", "openalex_ids": ("I2800289517",), "rors": ("03ztgj037",), "aliases": ("german climate computing centre", "german climate computing center", "deutsches klimarechenzentrum")},
    "NCAR": {"country": "US", "subtype": "government_research_institute", "openalex_ids": ("I107766831",), "rors": ("05cvfcr44",), "aliases": ("nsf national center for atmospheric research", "national center for atmospheric research", "national centre for atmospheric research")},
})

# Identifier/name updates for existing entries discovered in the SC audit.
RESEARCH_LABS["NREL"].update({
    "openalex_ids": ("I1297288678",),
    "rors": ("036266993",),
    "aliases": RESEARCH_LABS["NREL"]["aliases"] + ("national laboratory of the rockies",),
})
RESEARCH_LABS["NSCC-TJ"].update({
    "openalex_ids": ("I4210165734",),
    "rors": ("05tngxm14",),
    "aliases": RESEARCH_LABS["NSCC-TJ"]["aliases"] + ("national supercomputing center of tianjin",),
})

# Backward-compatible metadata layer. The existing `national_lab` category remains
# unchanged; subtype is additive and can be consumed by newer reports.
_NATIONAL_COMPUTE_CENTERS = {"NSCC-TJ", "NSCC-WX", "NSCC-GZ", "NSCC-CS", "NSCC-JN", "MPCDF", "LRZ"}
_GOVERNMENT_RESEARCH_INSTITUTES = {"AIST", "NICT", "JAEA", "JAMSTEC", "KISTI", "ETRI", "INRIA", "INRIA-BORDEAUX", "INRIA-RENNES", "INRIA-GRENOBLE", "CEA", "CEA-GRENOBLE", "CEA-CESTA", "CEA-SACLAY", "RAL", "ECMWF"}
_PUBLIC_RESEARCH_INSTITUTES = {"CAS-ICT", "CAS-SIAT", "CAS-ISCAS", "CAS-IIE", "CAS-CNIC", "WNLO", "PCL", "ZJLAB", "PML", "RIKEN", "NII", "ZIB", "HZDR", "CASUS", "MAISON-SIM"}

for _code, _spec in RESEARCH_LABS.items():
    if "subtype" in _spec:
        continue
    if _code in _NATIONAL_COMPUTE_CENTERS:
        _spec["subtype"] = "national_compute_center"
    elif _code in _GOVERNMENT_RESEARCH_INSTITUTES:
        _spec["subtype"] = "government_research_institute"
    elif _code in _PUBLIC_RESEARCH_INSTITUTES:
        _spec["subtype"] = "public_research_institute"
    else:
        # Core US DOE/NNSA labs and similar explicitly named national laboratories.
        _spec["subtype"] = "national_lab"
