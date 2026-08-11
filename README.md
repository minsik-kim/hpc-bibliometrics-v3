# hpc-bibliometrics-v3

Fast, reproducible bibliometric analysis for HPC conferences.

The pipeline builds an exact main-conference paper roster from DBLP, enriches those papers with OpenAlex institution metadata, and then produces collaboration statistics for universities, industry, and curated public research institutions.

## Current scope

- IPDPS, SC, ICS, PPoPP, HPDC, ISC, CLUSTER, ICPP, Euro-Par, and HiPC
  main conferences, 2016-2025
- CCGrid main conference, 2016-2024 (DBLP does not yet list a 2025 proceedings
  roster as of 2026-08-11)
- Exact main-conference roster from DBLP TOC pages
- Parallel collection with resumable local caches
- DOI-based OpenAlex enrichment
- Curated public research institution registry using OpenAlex IDs, RORs, and aliases
- Paper-level deduplication for institution, subtype, country, and collaboration statistics
- Auditing of still-unclassified institutions by country

The public research institution registry currently spans organizations in the United States, China, Japan, Korea, Germany, France, the United Kingdom, the Netherlands, Australia, Spain, Taiwan, Switzerland, Italy, Norway, Poland, Portugal, Greece, Singapore, and Costa Rica. Broad parent organizations such as CAS, CNRS, CSIRO, and A*STAR are intentionally not classified wholesale when that would overstate institution-level participation. Their specifically audited institutes and centers can still be registered.

## Install on macOS

```bash
cd hpc-bibliometrics-v3
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

OpenAlex requires an API key:

```bash
export OPENALEX_API_KEY="your-key"
hpc-bib check-auth
```

The key is passed only to OpenAlex and is not written to the cache.

## End-to-end workflow

Use any key printed by `hpc-bib list-venues` as the venue argument. For SC, CLUSTER,
and CCGrid, the DBLP roster uses the main proceedings pages and excludes the
separately indexed workshop proceedings.
SC 2018 is a documented publisher-link exception: DBLP exposes legacy ACM links
rather than DOI links, so the collector recovers the IEEE DOI from the proceeding's
article pagination before OpenAlex enrichment.

ICS uses the ACM International Conference on Supercomputing main-proceedings TOCs
under DBLP's `conf/ics` series. It is distinct from ISC High Performance, which DBLP
indexes under `conf/supercomputer`.

Euro-Par 2024 and 2025 each have three DBLP main-proceedings volumes. The collector
requires all three, combines them, and deduplicates by DBLP publication key. CCGrid
2025 is not substituted from another source: until DBLP publishes its roster, use
`--to 2024` for CCGrid.

### 1. Collect the DBLP roster

```bash
hpc-bib collect ipdps --from 2016 --to 2025 --workers 4
# Replace ipdps with another venue key.
# CCGrid currently uses: hpc-bib collect ccgrid --from 2016 --to 2024 --workers 4
```

Use `--refresh` to rebuild cached yearly rosters.

### 2. Enrich with OpenAlex

```bash
hpc-bib enrich ipdps --from 2016 --to 2025 --workers 4
# CCGrid currently uses: hpc-bib enrich ccgrid --from 2016 --to 2024 --workers 4
```

This matches the DBLP roster to OpenAlex and writes:

```text
cache/ipdps/openalex-2016-2025.parquet
```

### 3. Analyze collaboration

```bash
hpc-bib analyze ipdps --from 2016 --to 2025
```

Primary outputs:

```text
cache/ipdps/analysis/yearly-2016-2025.csv
cache/ipdps/analysis/institutions-2016-2025.csv
cache/ipdps/analysis/papers-2016-2025.parquet
```

The CLI uses the term `Public research institution`. Legacy CSV fields containing `national_lab` are retained for compatibility with earlier versions.

### 4. Build validation and collaboration reports

```bash
hpc-bib report ipdps --from 2016 --to 2025
```

Outputs include:

```text
cache/ipdps/analysis/labs-2016-2025.csv
cache/ipdps/analysis/universities-2016-2025.csv
cache/ipdps/analysis/lab-university-pairs-2016-2025.csv
cache/ipdps/analysis/public-research-subtypes-yearly-2016-2025.csv
cache/ipdps/analysis/public-research-country-subtypes-2016-2025.csv
cache/ipdps/analysis/public-research-subtype-combinations-2016-2025.csv
```

`labs-*.csv` and `lab-university-pairs-*.csv` include a `subtype` column. Current subtypes are:

- `national_lab`
- `national_compute_center`
- `government_research_institute`
- `public_research_institute`

The yearly and country subtype reports use overlapping participation counts. A paper with multiple public-research subtypes contributes once to every subtype represented, while duplicate institutions of the same subtype or country/subtype combination still count only once.

The subtype-combination report is exclusive. Every public-research paper belongs to exactly one sorted subtype combination. Therefore, the sum of its `papers` column equals the unique public-research paper count, and the sum for rows where `subtype_count > 1` equals the multi-subtype paper count. The report command validates both invariants before writing any CSV output.

## Validated snapshots

These snapshots use the same global registry for every venue. Adding a conservatively
verified institution can therefore update earlier venue totals as well as the new venue.

All columns below cover 2016-2025 except CCGrid, which covers 2016-2024.

| Metric | IPDPS | SC | ICS | PPoPP | HPDC |
| --- | ---: | ---: | ---: | ---: | ---: |
| DBLP main-conference papers | 1,097 | 994 | 440 | 490 | 333 |
| OpenAlex matched papers | 1,096 | 991 | 440 | 490 | 332 |
| Public research institution papers | 370 | 451 | 127 | 100 | 128 |
| Public research institution + university papers | 298 | 358 | 117 | 91 | 105 |
| Public research institutions | 65 | 65 | 31 | 30 | 28 |
| Universities | 461 | 387 | 265 | 239 | 189 |
| Institution-university pairs | 447 | 675 | 193 | 150 | 139 |
| Multi-subtype papers | 32 | 50 | 9 | 8 | 6 |
| US `national_lab` papers | 223 | 307 | 79 | 49 | 95 |
| US `national_lab` + university papers | 171 | 232 | 72 | 45 | 79 |

| Metric | ISC | CLUSTER | CCGrid | ICPP | Euro-Par | HiPC |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| DBLP main-conference papers | 226 | 686 | 850 | 864 | 511 | 397 |
| OpenAlex matched papers | 226 | 686 | 849 | 864 | 511 | 397 |
| Public research institution papers | 95 | 303 | 209 | 235 | 167 | 105 |
| Public research institution + university papers | 69 | 222 | 179 | 199 | 148 | 88 |
| Public research institutions | 32 | 63 | 57 | 45 | 53 | 36 |
| Universities | 129 | 339 | 501 | 401 | 331 | 234 |
| Institution-university pairs | 105 | 381 | 292 | 314 | 289 | 156 |
| Multi-subtype papers | 8 | 38 | 25 | 22 | 43 | 12 |
| US `national_lab` papers | 62 | 171 | 79 | 88 | 35 | 67 |
| US `national_lab` + university papers | 42 | 120 | 68 | 66 | 31 | 53 |

For every venue, the exclusive subtype-combination `papers` sum equals the unique
public-research paper count, and its multi-subtype rows equal the independently
reconstructed multi-subtype count. Every DBLP paper has a DOI. OpenAlex currently
does not match one HPDC paper, one CCGrid paper, one IPDPS paper, and three SC papers;
they remain in the exact DBLP roster with an explicit `unmatched` status.

## Audit unclassified institutions

Use the audit command to discover institutions that remain outside the curated registry:

```bash
hpc-bib audit-institutions ipdps \
  --from 2016 --to 2025 \
  -c KR -c DE -c FR
```

The output CSV contains country, institution name, OpenAlex type, OpenAlex ID, ROR, and paper count. This is intended for conservative registry expansion based on institutions that actually appear in the conference dataset.

## Classification policy

The registry prefers stable OpenAlex IDs and ROR identifiers, then falls back to curated name aliases. It intentionally distinguishes specific research institutes and computing centers from broad parent academies or ministries.

The umbrella analysis category remains backward-compatible as `national_lab` internally, but it should be interpreted as the broader concept of a public research institution. The subtype column provides the more precise classification for newer analyses.

## Tests

```bash
python -m pytest
```

Tests cover collection/cache behavior, OpenAlex handling, and paper-level deduplication in subtype and country/subtype reports.
