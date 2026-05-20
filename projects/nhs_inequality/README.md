# NHS Inequality Analysis Project

Analysing how NHS waiting times (RTT) patterns vary across commissioners/ICBs and deprivation context over the last 12 months.

## Overview

This portfolio project demonstrates the Axiomatic Engine's capabilities for public health data engineering, using real-world NHS England data.

## Data Sources

### RTT (Referral to Treatment) Waiting Times
- **Source**: NHS England Statistics (CSV in ZIP via HTTP)
- **URL pattern**: `https://www.england.nhs.uk/statistics/wp-content/uploads/sites/2/{publish_year}/{publish_month}/Full-CSV-data-file-{Mon}{YY}-ZIP-{size}-revised.zip`
- **Coverage**: 12 months — April 2024 to March 2025 (full 2024-25 NHS fiscal year)
- **Data**: Monthly snapshots, commissioner-level aggregation
- **Key Fields**: Organisation code, treatment function code, waiting time bands, patient counts

## Project Structure

```
projects/nhs_inequality/
├── run_pipeline.py               # Entrypoint for ingestion
├── dbt_project/
│   ├── dbt_project.yml            # dbt configuration
│   ├── profiles.yml               # DuckDB connection
│   └── models/
│       ├── sources.yml            # Source definitions + tests
│       ├── silver/
│       │   ├── stg_rtt_commissioner.sql       # Bronze→Silver staging
│       │   ├── int_rtt_metrics_by_commissioner.sql  # Derived breach counts
│       │   ├── int_icb_waiting_metrics.sql    # ICB-level aggregation
│       │   └── int_icb_benchmarks.sql         # England/regional official totals
│       └── gold/
│           ├── dim_icb.sql        # ICB dimension (SK=BK pattern)
│           ├── dim_period.sql     # Period dimension (SK=BK pattern)
│           ├── dim_rtt_pathway.sql  # Pathway type dimension
│           ├── fct_icb_waiting_times.sql  # Star schema fact table
│           └── fct_waiting_times_by_icb.sql  # Original benchmark fact table
└── README.md                      # This file
```

## Star Schema Design

### Fact Table: `fct_icb_waiting_times`
**Grain:** ICB × Period × RTT Part Type

| Column | Description |
|--------|-------------|
| `period` | Period dimension FK (degenerate) |
| `icb_code` | ICB dimension FK (degenerate) |
| `rtt_part_type` | Pathway dimension FK (degenerate) |
| `total_waiting_list` | Total patients on list |
| `count_over_52_weeks` | Patients 52+ weeks (inequity signal) |
| `pct_over_52_weeks` | % over 52 weeks |
| `long_wait_tail_index` | Custom metric: (pct_52+)^2 - emphasizes tail concentration |
| `variance_from_england_18wk` | Deviation from official England benchmark |
| `performance_vs_england` | Categorical performance assessment |

### Dimension Tables
- **`dim_icb`** (SK=BK: `icb_code`) - ICB attributes with v1.1 extension points for deprivation data
- **`dim_period`** (SK=BK: `period`) - Calendar attributes with NHS fiscal year
- **`dim_rtt_pathway`** (SK=BK: `rtt_part_type`) - Pathway type descriptions and categories

### Key Design Principles
- **SK=BK Pattern:** Business keys = surrogate keys (stable, meaningful identifiers)
- **Honest Benchmark Naming:** `england_*` = official NHS England totals from source (not peer averages)
- **Long-Wait Focus:** 52+, 65+, 78+, 104+ week metrics prioritized for inequity analysis
- **Extension Ready:** Business key pattern enables trivial v1.1 deprivation enrichment

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

Run with dbt tests:
```bash
uv run projects/nhs_inequality/run_pipeline.py --run-transforms \
  --dbt-project-dir ./projects/nhs_inequality/dbt_project \
  --dbt-profiles-dir ./projects/nhs_inequality/dbt_project \
  --dbt-profile-name nhs_inequality \
  --dbt-run-tests
```

## Phase Status

- **Phase 1**: ✅ Complete - Engine ZIP streaming support in `http_stream.py`
- **Phase 2**: ✅ Complete - RTT ingestion (185,101 rows for March 2025 to bronze)
- **Phase 3**: ✅ Complete - Star schema dbt models (gold layer with degenerate dimension keys)
- **Phase 6**: ✅ Complete - 12-month time series (Apr 2024–Mar 2025); separate bronze table per month; `--months` CLI flag for selective reload; UNION ALL staging; composite grain tests
- **Phase 4+**: Deferred - ODS & IMD integration (v1.1)
