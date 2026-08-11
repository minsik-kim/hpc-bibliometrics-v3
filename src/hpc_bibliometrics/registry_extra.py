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
    "MPI-INF": {
        "country": "DE",
        "subtype": "public_research_institute",
        "openalex_ids": ("I4210109712",),
        "rors": ("01w19ak89",),
        "aliases": ("max planck institute for informatics",),
    },
    "US-NRL": {
        "country": "US",
        "subtype": "government_research_institute",
        "openalex_ids": ("I1288214837",),
        "rors": ("04d23a975",),
        "aliases": (
            "united states naval research laboratory",
            "u.s. naval research laboratory",
        ),
    },
    "SHLAB": {
        "country": "CN",
        "subtype": "public_research_institute",
        "openalex_ids": ("I4391012619",),
        "rors": ("03wkvpx79",),
        "aliases": (
            "shanghai artificial intelligence laboratory",
            "shanghai ai laboratory",
        ),
    },
    "CERN": {
        "country": "CH",
        "subtype": "public_research_institute",
        "openalex_ids": ("I67311998",),
        "rors": ("01ggx4157",),
        "aliases": ("european organization for nuclear research",),
    },
    "CAS-SIMIT": {
        "country": "CN",
        "subtype": "public_research_institute",
        "openalex_ids": ("I4210147322",),
        "rors": ("04nytyj38",),
        "aliases": ("shanghai institute of microsystem and information technology",),
    },
    "BIBDR": {
        "country": "CN",
        "subtype": "public_research_institute",
        "openalex_ids": ("I4210096250",),
        "rors": ("00s1sz824",),
        "aliases": ("beijing institute of big data research",),
    },
    "VECTOR": {
        "country": "CA",
        "subtype": "public_research_institute",
        "openalex_ids": ("I4210127509",),
        "rors": ("03kqdja62",),
        "aliases": ("vector institute",),
    },
    "INESC-ID": {
        "country": "PT",
        "subtype": "public_research_institute",
        "openalex_ids": ("I121345201",),
        "rors": ("04mqy3p58",),
        "aliases": (
            "instituto de engenharia de sistemas e computadores investigação e desenvolvimento",
            "instituto de engenharia de sistemas e computadores investigacao e desenvolvimento",
            "inesc-id",
        ),
    },
    "ADSC": {
        "country": "SG",
        "subtype": "public_research_institute",
        "openalex_ids": ("I4210108443",),
        "rors": ("01xaqx887",),
        "aliases": (
            "advanced digital sciences center",
            "advanced digital sciences centre",
        ),
    },
    # Specific institutes, laboratories, and computing centers found while
    # auditing the additional HPC venues. Broad parents such as CNRS, CAS,
    # CSIRO, and A*STAR remain intentionally unclassified.
    "CEA-DIF": {
        "country": "FR",
        "subtype": "government_research_institute",
        "openalex_ids": ("I4210101455",),
        "rors": ("00kn4eb29",),
        "aliases": ("cea dam île-de-france", "cea dam ile-de-france"),
    },
    "IRISA": {
        "country": "FR",
        "subtype": "public_research_institute",
        "openalex_ids": ("I2802519937",),
        "rors": ("00myn0z94",),
        "aliases": ("institut de recherche en informatique et systèmes aléatoires",),
    },
    "LIG": {
        "country": "FR",
        "subtype": "public_research_institute",
        "openalex_ids": ("I4210104430",),
        "rors": ("01c8rcg82",),
        "aliases": ("laboratoire d'informatique de grenoble",),
    },
    "LABRI": {
        "country": "FR",
        "subtype": "public_research_institute",
        "openalex_ids": ("I4210142254",),
        "rors": ("03adqg323",),
        "aliases": ("laboratoire bordelais de recherche en informatique",),
    },
    "LIP": {
        "country": "FR",
        "subtype": "public_research_institute",
        "openalex_ids": ("I4210144566",),
        "rors": ("04msnz457",),
        "aliases": ("laboratoire de l'informatique du parallélisme",),
    },
    "FEMTO-ST": {
        "country": "FR",
        "subtype": "public_research_institute",
        "openalex_ids": ("I2802759292",),
        "rors": ("004fmxv66",),
        "aliases": (
            "franche-comté électronique mécanique thermique et optique - sciences et technologies",
        ),
    },
    "LS2N": {
        "country": "FR",
        "subtype": "public_research_institute",
        "openalex_ids": ("I4210117005",),
        "rors": ("02snf8m58",),
        "aliases": ("laboratoire des sciences du numérique de nantes",),
    },
    "IRIT": {
        "country": "FR",
        "subtype": "public_research_institute",
        "openalex_ids": ("I4210119061",),
        "rors": ("01rx4qw44",),
        "aliases": ("institut de recherche en informatique de toulouse",),
    },
    "LIP6": {
        "country": "FR",
        "subtype": "public_research_institute",
        "openalex_ids": ("I4210159731",),
        "rors": ("05krcen59",),
        "aliases": ("lip6", "laboratoire d'informatique de paris 6"),
    },
    "CRISTAL": {
        "country": "FR",
        "subtype": "public_research_institute",
        "openalex_ids": ("I4387153239",),
        "rors": ("05vrs3189",),
        "aliases": ("centre de recherche en informatique, signal et automatique de lille",),
    },
    "ICUBE": {
        "country": "FR",
        "subtype": "public_research_institute",
        "openalex_ids": ("I4210100283",),
        "rors": ("00k4e5n71",),
        "aliases": ("laboratoire des sciences de l'ingénieur, de l'informatique et de l'imagerie",),
    },
    "CC-IN2P3": {
        "country": "FR",
        "subtype": "national_compute_center",
        "openalex_ids": ("I4210144793",),
        "rors": ("04dcc3438",),
        "aliases": (
            "centre de calcul de l’institut national de physique nucléaire et de physique des particules",
            "centre de calcul de l'institut national de physique nucléaire et de physique des particules",
        ),
    },
    "LIRMM": {
        "country": "FR",
        "subtype": "public_research_institute",
        "openalex_ids": ("I4210101743",),
        "rors": ("013yean28",),
        "aliases": (
            "laboratoire d'informatique, de robotique et de microélectronique de montpellier",
        ),
    },
    "DATA61": {
        "country": "AU",
        "subtype": "government_research_institute",
        "openalex_ids": ("I42894916",),
        "rors": ("03q397159",),
        "aliases": ("data61", "csiro's data61", "csiro data61"),
    },
    "NASK": {
        "country": "PL",
        "subtype": "government_research_institute",
        "openalex_ids": ("I4210136276",),
        "rors": ("03ajsaw82",),
        "aliases": ("nask national research institute",),
    },
    "DEVCOM-ARL": {
        "country": "US",
        "subtype": "government_research_institute",
        "openalex_ids": ("I166416128",),
        "rors": ("011hc8f90",),
        "aliases": ("devcom army research laboratory", "army research laboratory"),
    },
    "AFRL": {
        "country": "US",
        "subtype": "government_research_institute",
        "openalex_ids": ("I1280414376",),
        "rors": ("02e2egq70",),
        "aliases": ("united states air force research laboratory", "air force research laboratory"),
    },
    "IAPCM": {
        "country": "CN",
        "subtype": "government_research_institute",
        "openalex_ids": ("I4210145278",),
        "rors": ("03sxpbt26",),
        "aliases": ("institute of applied physics and computational mathematics",),
    },
    "INESC-TEC": {
        "country": "PT",
        "subtype": "public_research_institute",
        "openalex_ids": ("I4210166615",),
        "rors": ("05fa8ka61",),
        "aliases": ("inesc tec",),
    },
    "FORTH-ICS": {
        "country": "GR",
        "subtype": "public_research_institute",
        "openalex_ids": ("I4210121775",),
        "rors": ("02tf48g55",),
        "aliases": ("forth institute of computer science",),
    },
    "A-STAR-IHPC": {
        "country": "SG",
        "subtype": "government_research_institute",
        "openalex_ids": ("I3004594783",),
        "rors": ("02n0ejh50",),
        "aliases": ("institute of high performance computing",),
    },
    "AWE": {
        "country": "GB",
        "subtype": "government_research_institute",
        "openalex_ids": ("I2802201010",),
        "rors": ("02gv4h649",),
        "aliases": ("awe nuclear security technologies",),
    },
    "FRAUNHOFER-ITWM": {
        "country": "DE",
        "subtype": "public_research_institute",
        "openalex_ids": ("I3019415892",),
        "rors": ("019hjw009",),
        "aliases": ("fraunhofer institute for industrial mathematics",),
    },
    "IMDEA-SW": {
        "country": "ES",
        "subtype": "public_research_institute",
        "openalex_ids": ("I4210162154",),
        "rors": ("04xvfkh51",),
        "aliases": ("imdea software institute",),
    },
    "MPI-SWS": {
        "country": "DE",
        "subtype": "public_research_institute",
        "openalex_ids": ("I4210121786",),
        "rors": ("02pe2kf23",),
        "aliases": ("max planck institute for software systems",),
    },
    "ICAR-CNR": {
        "country": "IT",
        "subtype": "public_research_institute",
        "openalex_ids": ("I3005160176",),
        "rors": ("04r5fge26",),
        "aliases": ("institute for high performance computing and networking",),
    },
    "NSCC-SZ": {
        "country": "CN",
        "subtype": "national_compute_center",
        "openalex_ids": ("I4210112812",),
        "rors": ("02291hh73",),
        "aliases": ("national supercomputing center in shenzhen",),
    },
    "SDSC": {
        "country": "US",
        "subtype": "national_compute_center",
        "openalex_ids": ("I181653535",),
        "rors": ("04mg3nk07",),
        "aliases": ("san diego supercomputer center",),
    },
    "CENAT": {
        "country": "CR",
        "subtype": "national_compute_center",
        "openalex_ids": ("I4387155612",),
        "rors": ("02tkjx303",),
        "aliases": ("centro nacional de alta tecnología", "national high technology center"),
    },
    "CIEMAT": {
        "country": "ES",
        "subtype": "government_research_institute",
        "openalex_ids": ("I4210165411",),
        "rors": ("05xx77y52",),
        "aliases": (
            "centro de investigaciones energéticas, medioambientales y tecnológicas",
        ),
    },
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
RESEARCH_LABS["ORNL"].update({
    "openalex_ids": ("I1289243028", "I1309980932"),
    "rors": ("01qz5mb56", "011fc0n53"),
    "aliases": RESEARCH_LABS["ORNL"]["aliases"]
    + ("national transportation research center",),
})
RESEARCH_LABS["CAS-ICT"].update({
    "openalex_ids": RESEARCH_LABS["CAS-ICT"]["openalex_ids"] + ("I4391767888",),
    "rors": RESEARCH_LABS["CAS-ICT"]["rors"] + ("02pq9w205",),
    "aliases": RESEARCH_LABS["CAS-ICT"]["aliases"]
    + ("state key laboratory of computer architecture",),
})
RESEARCH_LABS["CAS-ISCAS"].update({
    "openalex_ids": RESEARCH_LABS["CAS-ISCAS"]["openalex_ids"] + ("I4391767820",),
    "rors": RESEARCH_LABS["CAS-ISCAS"]["rors"] + ("01hsx4r68",),
    "aliases": RESEARCH_LABS["CAS-ISCAS"]["aliases"]
    + ("state key laboratory of computer science",),
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
