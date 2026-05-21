"""
File content templates for the 'minimal' init template.

Each function returns a string ready to write to disk.
{project} is substituted with the project name supplied to init.
"""
from __future__ import annotations

import importlib.metadata


def engine_version() -> str:
    try:
        return importlib.metadata.version("axiomatic-engine")
    except importlib.metadata.PackageNotFoundError:
        return "0.1.0"


def pipeline_yml(project: str) -> str:
    return f"""\
source:
  kind: http_file
  name: {project}_bronze_ingest
  resources:
    - name: replace_with_resource_name
      url: https://example.com/replace-with-your-data-url.csv
      # archive_format: zip
      # archive_member: data.csv
      # delimiter: ","

warehouse:
  kind: duckdb
  path: "${{AXIOMATIC_WAREHOUSE_PATH}}"

schema:
  bronze: "${{AXIOMATIC_SCHEMA_BRONZE:bronze}}"
  silver: "${{AXIOMATIC_SCHEMA_SILVER:silver}}"
  gold: "${{AXIOMATIC_SCHEMA_GOLD:gold}}"

transform:
  enabled: true
  dbt_project_dir: ./dbt_project
  dbt_profiles_dir: ./dbt_project
  dbt_profile_name: {project}
"""


def pyproject_toml(project: str) -> str:
    version = engine_version()
    major_minor = ".".join(version.split(".")[:2])
    next_minor = ".".join([version.split(".")[0], str(int(version.split(".")[1]) + 1)])
    return f"""\
[project]
name = "{project}"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "axiomatic-engine>={major_minor}.0,<{next_minor}.0",
]
"""


def env_template(project: str) -> str:
    return f"""\
# Copy this file to .env and fill in the values.
# Never commit .env to version control.

AXIOMATIC_WAREHOUSE_PATH=./data/warehouse.duckdb
AXIOMATIC_STORAGE_PATH=./data/raw_vault
AXIOMATIC_SCHEMA_BRONZE=bronze
AXIOMATIC_SCHEMA_SILVER=silver
AXIOMATIC_SCHEMA_GOLD=gold

AXIOMATIC_TRANSFORM_ENABLED=true
AXIOMATIC_DBT_PROJECT_DIR=./dbt_project
AXIOMATIC_DBT_PROFILES_DIR=./dbt_project
AXIOMATIC_DBT_PROFILE_NAME={project}
AXIOMATIC_DBT_TARGET=dev

# Uncomment for MotherDuck:
# AXIOMATIC_WAREHOUSE_KIND=motherduck
# AXIOMATIC_MOTHERDUCK_ACCESS_TOKEN=your_token_here
"""


def gitignore() -> str:
    return """\
.env
data/
.dlt/
dbt_project/target/
dbt_project/dbt_packages/
dbt_project/logs/
__pycache__/
*.py[cod]
.venv/
"""


def readme(project: str) -> str:
    version = engine_version()
    return f"""\
# {project}

A data pipeline project built on [axiomatic-engine](https://pypi.org/project/axiomatic-engine/) v{version}.

## Quick start

```bash
cp env-template .env
# Edit .env with your warehouse path and credentials

axiomatic-engine run --config pipeline.yml
```

## Project layout

```
{project}/
├── pipeline.yml          # Declarative pipeline config — edit this
├── .ai/                  # AI assistant context — read context.md first
├── dbt_project/          # dbt SQL models
├── env-template          # Copy to .env and fill in
└── pyproject.toml        # Pins axiomatic-engine version
```

## Working with AI assistants

Tell your AI assistant: *"Read `.ai/checklist.md` before doing anything."*

The `.ai/` folder contains:
- `context.md` — fill in your domain context and data sources
- `checklist.md` — step-by-step procedures for every common task
- `reference.md` — naming conventions, common errors, and fixes

## Running the pipeline

```bash
# Full run (ingest + transform)
axiomatic-engine run --config pipeline.yml

# Ingest only
axiomatic-engine run --config pipeline.yml --skip-transforms

# Force re-download all sources
axiomatic-engine run --config pipeline.yml --force-reload
```
"""


def dbt_project_yml(project: str) -> str:
    return f"""\
name: '{project}'
version: '0.1.0'
config-version: 2

profile: '{project}'

model-paths: ["models"]
analysis-paths: ["analyses"]
test-paths: ["tests"]
seed-paths: ["seeds"]
macro-paths: ["macros"]
snapshot-paths: ["snapshots"]

target-path: "target"
clean-targets:
  - "target"
  - "dbt_packages"

models:
  {project}:
    silver:
      +materialized: view
      +schema: "{{{{ env_var('AXIOMATIC_SCHEMA_SILVER', 'silver') }}}}"
    gold:
      +materialized: table
      +schema: "{{{{ env_var('AXIOMATIC_SCHEMA_GOLD', 'gold') }}}}"
"""


def dbt_profiles_yml(project: str) -> str:
    return f"""\
{project}:
  target: dev
  outputs:
    dev:
      type: duckdb
      path: "{{{{ env_var('AXIOMATIC_WAREHOUSE_PATH', './data/warehouse.duckdb') }}}}"
      threads: 4
"""


def sources_yml(project: str) -> str:
    return f"""\
# AUTO-GENERATED — do not edit by hand.
# To regenerate: ask AI to re-read pipeline.yml and rewrite this file.

version: 2

sources:
  - name: {project}_bronze_ingest
    schema: "{{{{ env_var('AXIOMATIC_SCHEMA_BRONZE', 'bronze') }}}}"
    tables:
      - name: replace_with_resource_name
"""


def ai_context_md(project: str) -> str:
    return f"""\
# {project} — Project Context

> Fill in this file. It is the first thing an AI assistant should read.

## What this project does

<!-- One paragraph: what business question does this pipeline answer? -->

## Data sources

| Name | Type | URL / location | Update frequency |
|------|------|---------------|-----------------|
| <!-- source name --> | http_file | <!-- url --> | <!-- frequency --> |

## Business terms and domain vocabulary

<!-- List key terms that are specific to this domain and not obvious -->

## Analysis questions this project answers

<!-- What does a stakeholder want to know from the final gold models? -->

## Extension plans / deferred work

<!-- What is explicitly out of scope for now? -->
"""


def ai_reference_md(project: str) -> str:
    return f"""\
# {project} — Reference

## Project layout

```
{project}/
├── pipeline.yml          # Source and warehouse config (edit this)
├── .ai/                  # AI context files (read these)
├── dbt_project/
│   ├── models/
│   │   ├── sources.yml   # AUTO-GENERATED — do not hand-edit
│   │   ├── silver/       # stg_*.sql and int_*.sql
│   │   └── gold/         # fct_*.sql and dim_*.sql
│   ├── dbt_project.yml
│   └── profiles.yml
├── env-template
└── pyproject.toml
```

## dbt naming conventions (medallion)

| Layer | Prefix | Purpose |
|-------|--------|----------|
| Silver | `stg_` | Cast and rename from bronze source |
| Silver | `int_` | Business logic, aggregations |
| Gold | `fct_` | Fact tables (metrics, events) |
| Gold | `dim_` | Dimension tables (descriptive attributes) |

## Bronze references

Always reference bronze tables via `source()`, not `ref()`:

```sql
from {{{{ source('{project}_bronze_ingest', 'table_name') }}}}
```

## Schema names

Always resolve schema names via `env_var()` — never hardcode:

```sql
{{{{ config(schema=env_var('AXIOMATIC_SCHEMA_SILVER', 'silver')) }}}}
```

## Common errors and fixes

**`Could not find profile named '<project>'`**
Ensure `dbt_profile_name` in `pipeline.yml` matches the profile key in `dbt_project/profiles.yml`.

**`IO Error: Could not set lock on file`**
Another process has the DuckDB file open. Close it and re-run.

**`Relation "bronze.table_name" does not exist`**
Run ingestion first: `axiomatic-engine run --config pipeline.yml --skip-transforms`, then check that the source name and table name in `sources.yml` match exactly.

**`requests.exceptions.HTTPError: 404`**
The URL in `pipeline.yml` is wrong or the file has moved. Check the URL directly in a browser.

**`KeyError: 'filename.csv'` (ZIP extraction)**
The `archive_member` value in `pipeline.yml` does not match the filename inside the ZIP.
Inspect with: `python -c "import zipfile; print(zipfile.ZipFile('file.zip').namelist())"`
"""


def ai_checklist_md(project: str) -> str:
    return f"""\
# {project} — AI Assistant Checklist

> Read this file before doing anything else in this project.

## Starting work on this project

1. Read `.ai/context.md`
2. Read `pipeline.yml`
3. Check `.ai/reference.md` for naming conventions and common errors

## Adding a new data source

1. Read `.ai/context.md` and `pipeline.yml`
2. Add the new `resources:` entry to the `source:` block in `pipeline.yml`
3. Run: `axiomatic-engine run --config pipeline.yml --skip-transforms`
   (confirms ingestion works before writing any SQL)
4. Write the staging model in `dbt_project/models/silver/stg_<name>.sql`
5. Write intermediate and gold models as needed
6. Run: `axiomatic-engine run --config pipeline.yml`

## Running the pipeline

```bash
axiomatic-engine run --config pipeline.yml                 # full run
axiomatic-engine run --config pipeline.yml --skip-transforms  # ingest only
axiomatic-engine run --config pipeline.yml --force-reload  # force re-download
```

## Writing a staging model

```sql
{{{{ config(materialized='view', schema=env_var('AXIOMATIC_SCHEMA_SILVER', 'silver')) }}}}

select
    cast("SourceColumn" as varchar)  as snake_case_name,
    -- ... more columns
    _dlt_load_id                     as load_id
from {{{{ source('{project}_bronze_ingest', 'resource_name') }}}}
```

## Updating sources.yml

`sources.yml` is auto-generated. To regenerate it after adding a source to `pipeline.yml`:
1. Read the updated `pipeline.yml`
2. Rewrite `dbt_project/models/sources.yml` to match — one `tables:` entry per resource

## DO NOT

- Edit `dbt_project/models/sources.yml` by hand
- Write `run_pipeline.py` from scratch (use `axiomatic-engine init --template custom` if needed)
- Edit files in `src/axiomatic_engine/` (that is the engine, not this project)
- Commit `.env` to version control
"""
