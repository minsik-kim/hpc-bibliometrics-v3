# hpc-bibliometrics-v3

Fast, reproducible bibliometric collection for HPC conferences.

The first milestone collects main-conference OpenAlex records by a stable source identifier and writes one compressed Parquet cache per year. It does not use broad full-text work search, and it does not issue one request per author or institution.

## Current scope

- IPDPS main proceedings
- Source resolution by ISSN (`1530-2075`)
- Cursor-based OpenAlex pagination
- Parallel year collection
- Atomic, resumable Parquet caches
- Native macOS/system certificate trust through `truststore`

DOE National Lab statistics and Excel reports will be added after the collector is validated.

## Install on macOS

```bash
cd hpc-bibliometrics-v3
/usr/local/bin/python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Apple Silicon Homebrew commonly installs Python under `/opt/homebrew/bin/python3.12`; use that path when applicable.

OpenAlex can use an email and, where required, an API key:

```bash
export OPENALEX_EMAIL="you@example.com"
# Optional, depending on the current OpenAlex access policy:
export OPENALEX_API_KEY="..."
```

## Collect IPDPS 2016-2025

```bash
hpc-bib collect ipdps --from 2016 --to 2025
```

Equivalent module invocation:

```bash
python -m hpc_bibliometrics collect ipdps --from 2016 --to 2025
```

Outputs:

```text
cache/
├── sources.json
└── ipdps/
    ├── 2016.parquet
    ├── ...
    ├── 2025.parquet
    └── manifest.json
```

Existing yearly files are reused. To replace them:

```bash
hpc-bib collect ipdps --from 2016 --to 2025 --refresh
```

Control parallelism with `--workers`/`-j`:

```bash
hpc-bib collect ipdps --from 2016 --to 2025 -j 4
```

## Test

```bash
python -m pytest
```
