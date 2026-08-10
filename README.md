# hpc-bibliometrics-v3

Fast, reproducible bibliometric analysis for HPC conferences.

The pipeline builds an exact main-conference paper roster from DBLP, enriches those papers with OpenAlex institution metadata, and then produces collaboration statistics for universities, industry, and curated public research institutions.

## Current scope

- IPDPS, SC, and ICS main conferences, 2016-2025
- Exact main-conference roster from DBLP TOC pages
- Parallel collection with resumable local caches
- DOI-based OpenAlex enrichment
- Curated public research institution registry using OpenAlex IDs, RORs, and aliases
- Paper-level deduplication for institution, subtype, country, and collaboration statistics
- Auditing of still-unclassified institutions by country

The public research institution registry currently spans organizations in the United States, China, Japan, Korea, Germany, France, the United Kingdom, the Netherlands, Australia, Spain, Taiwan, Switzerland, Italy, and Norway. Broad parent organizations such as CAS and CNRS are intentionally not classified wholesale when that would overstate institution-level participation.

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

Use `ipdps`, `sc`, or `ics` as the venue argument. For SC, the DBLP roster uses the main
proceedings pages and excludes the separately indexed workshop proceedings.
SC 2018 is a documented publisher-link exception: DBLP exposes legacy ACM links
rather than DOI links, so the collector recovers the IEEE DOI from the proceeding's
article pagination before OpenAlex enrichment.

ICS uses the ACM International Conference on Supercomputing main-proceedings TOCs
under DBLP's `conf/ics` series. It is distinct from ISC High Performance, which DBLP
indexes under `conf/supercomputer`.

### 1. Collect the DBLP roster

```bash
hpc-bib collect ipdps --from 2016 --to 2025 --workers 4
# SC: hpc-bib collect sc --from 2016 --to 2025 --workers 4
# ICS: hpc-bib collect ics --from 2016 --to 2025 --workers 4
```

Use `--refresh` to rebuild cached yearly rosters.

### 2. Enrich with OpenAlex

```bash
hpc-bib enrich ipdps --from 2016 --to 2025 --workers 4
# SC: hpc-bib enrich sc --from 2016 --to 2025 --workers 4
# ICS: hpc-bib enrich ics --from 2016 --to 2025 --workers 4
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

## Validated 2016-2025 snapshots

These snapshots use the same global registry for every venue. Adding a conservatively
verified institution can therefore update earlier venue totals as well as the new venue.

| Metric | IPDPS | SC | ICS |
| --- | ---: | ---: | ---: |
| DBLP main-conference papers | 1,097 | 994 | 440 |
| OpenAlex matched papers | 1,096 | 991 | 440 |
| Public research institution papers | 353 | 449 | 127 |
| Public research institution + university papers | 283 | 356 | 117 |
| Public research institutions | 53 | 57 | 31 |
| Universities | 461 | 387 | 265 |
| Institution-university pairs | 391 | 648 | 193 |
| Multi-subtype papers | 16 | 41 | 9 |
| US `national_lab` papers | 223 | 307 | 79 |
| US `national_lab` + university papers | 171 | 232 | 72 |

For all three venues, the exclusive subtype-combination `papers` sum equals the unique
public-research paper count. ICS has complete DOI coverage and all 440 papers currently
match OpenAlex. SC has three DOI-bearing papers that OpenAlex does not currently match
(two from 2021 and one from 2023); they remain in the DBLP roster with an explicit
`unmatched` status.

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
