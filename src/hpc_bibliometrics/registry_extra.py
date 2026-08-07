from __future__ import annotations

from .analyze import RESEARCH_LABS

# Additional research-infrastructure institutions discovered by audit. Keep this
# separate from the core registry so country expansion does not churn analyze.py.
RESEARCH_LABS.update({
    "NLESC": {
        "country": "NL",
        "openalex_ids": ("I4210095242",),
        "rors": ("00rbjv475",),
        "aliases": ("netherlands escience center", "netherlands e-science center"),
    },
    "ASTRON": {
        "country": "NL",
        "openalex_ids": ("I922237871",),
        "rors": ("000k1q888",),
        "aliases": ("netherlands institute for radio astronomy", "astron"),
    },
    "CWI": {
        "country": "NL",
        "openalex_ids": ("I1341640284",),
        "rors": ("00x7ekv49",),
        "aliases": ("centrum wiskunde & informatica", "centrum wiskunde en informatica"),
    },
    "PAWSEY": {
        "country": "AU",
        "openalex_ids": ("I2801909468",),
        "rors": ("04f2f0537",),
        "aliases": ("pawsey supercomputing research centre", "pawsey supercomputing research center"),
    },
})
