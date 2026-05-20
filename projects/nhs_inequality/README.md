# NHS Inequality Analysis Project

Analysing how NHS waiting times (RTT) patterns vary across commissioners/ICBs and deprivation context over the last 12 months.

## Overview

This portfolio project demonstrates the Axiomatic Engine's capabilities for public health data engineering, using real-world NHS England data.

## Data Sources

### RTT (Referral to Treatment) Waiting Times
- **Source**: NHS England Statistics (CSV in ZIP via HTTP)
- **URL**: `https://www.england.nhs.uk/statistics/wp-content/uploads/sites/2/2025/07/Full-CSV-data-file-Mar25-ZIP-4M-revised.zip`
- **Data**: Monthly snapshots, commissioner-level aggregation
- **Key Fields**: Organisation code, treatment function code, waiting time bands, patient counts

## Project Structure

```
projects/nhs_inequality/
├── run_pipeline.py               # Entrypoint for ingestion
├── dbt_project/
│   ├── dbt_project.yml          # dbt configuration
│   ├── profiles.yml             # DuckDB connection
│   └── models/
│       ├── sources.yml          # Source definitions
│       └── bronze/
│           └── stg_rtt_commissioner.sql
└── README.md                    # This file
```

## Usage

Run the pipeline (ingestion only):
```bash
uv run projects/nhs_inequality/run_pipeline.py --skip-transforms
```

Run with dbt transforms:
```bash
uv run projects/nhs_inequality/run_pipeline.py --run-transforms \
  --dbt-project-dir ./projects/nhs_inequality/dbt_project \
  --dbt-profiles-dir ./projects/nhs_inequality/dbt_project \
  --dbt-profile-name nhs_inequality
```

## Analytical Approach

This project uses NHS England RTT full-extract data which contains both provider and commissioner context. The commissioner fields allow analysis at ICB/sub-ICB/region/England grains without requiring separate ODS lookups.

## Phase Status

- **Phase 1**: ✅ Complete - Engine ZIP streaming support in `http_stream.py`
- **Phase 2**: ✅ Complete - RTT single month ingestion (185,101 rows ingested to bronze)
- **Phase 3**: In Progress - dbt models and analysis
- **Phase 4+**: Deferred - ODS & IMD integration (v1.1)
