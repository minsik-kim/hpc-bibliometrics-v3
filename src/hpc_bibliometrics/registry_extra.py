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
