# Axiomatic Engine

Axiomatic Engine orchestrates ingestion and transformation pipelines while keeping domain logic in project folders.

## Quick Start

Install the package:

```bash
uv add axiomatic-engine
```

Or with pip:

```bash
pip install axiomatic-engine
```

### New Project (Declarative Workflow)

Scaffold a new client project:

```bash
axiomatic-engine init --project my_client --template minimal
cd my_client
# Edit pipeline.yml to add your source URLs
axiomatic-engine run --config pipeline.yml
```

### Example Projects

Reference implementations in `projects/` show both workflows:

**Declarative (NEW)** — zero Python required:
```bash
cd projects/fake_store
axiomatic-engine run --config pipeline.yml
```

**Imperative (Legacy)** — for advanced customization:
```bash
cd projects/fake_store
python run_pipeline.py
```

## Contributor Quickstart

The project standardises on `uv` for local quality checks and packaging workflows.

- Install hooks once:
  - `uv run --group dev pre-commit install`
- Run hooks across the repository:
  - `uv run --group dev pre-commit run --all-files`
- Run the full package quality gate:
  - `uv run --group dev --group test python scripts/quality_gate.py`

## Runtime Configuration Contract

The engine reads typed runtime settings from `AXIOMATIC_*` environment variables, with project entrypoints able to override values via CLI flags.

Schema layers are configured independently:

- `AXIOMATIC_SCHEMA_BRONZE`
- `AXIOMATIC_SCHEMA_SILVER`
- `AXIOMATIC_SCHEMA_GOLD`
- `AXIOMATIC_SCHEMA_ANALYTICS`

This keeps medallion naming explicit and consistent across ingestion and dbt model targets.

## Source Routing Contract

Source implementations expose specific source kinds for declarative configuration:

- `rest_api` — JSON REST endpoints with pagination support
- `http_file` — HTTP file downloads (CSV, ZIP archives)

### Declarative Configuration (pipeline.yml)

```yaml
source:
  kind: http_file
  name: my_source
  resources:
    - name: data_file
      url: https://example.com/data.csv
      archive_format: zip
      archive_member: data.csv

warehouse:
  kind: duckdb
  path: "${AXIOMATIC_WAREHOUSE_PATH:./data/warehouse.duckdb}"

transform:
  enabled: true
  dbt_project_dir: ./dbt_project
  dbt_profile_name: my_project
```

### Imperative Construction (Python)

Direct source constructors remain supported for advanced use cases:

```python
from axiomatic_engine.sources.factory import build_source, HttpFileSourceDefinition

source = build_source(HttpFileSourceDefinition(...))
```

## CLI Commands

The engine provides a unified CLI for pipeline operations:

### `init` — Scaffold New Project

```bash
axiomatic-engine init --project my_client --template minimal
```

Creates a complete project with `pipeline.yml`, dbt structure, and `.ai/` context files.

### `run` — Execute Pipeline

```bash
# Full pipeline (ingestion + transforms)
axiomatic-engine run --config pipeline.yml

# Ingestion only
axiomatic-engine run --config pipeline.yml --skip-transforms

# Force re-download (ignore cache)
axiomatic-engine run --config pipeline.yml --force-reload
```

### `generate-staging` — Create Silver Models

```bash
# Generate staging model for a resource
axiomatic-engine generate-staging --config pipeline.yml --source my_source --resource my_table

# Show diff against existing file
axiomatic-engine generate-staging --config pipeline.yml --source my_source --diff
```

## Ingestion Resource Load Hints

Sources can provide optional per-resource hints through `ResourceLoadHints`:

- `write_disposition`: `append`, `replace`, or `merge`
- `primary_key`: key used by merge semantics
- `schema_evolution_mode`: `auto`, `strict`, or `discard`

These hints are source-agnostic contracts and are mapped by the source bridge when building `dlt.resource(...)`.

## Schema Evolution Policy

The engine supports a hybrid schema evolution policy:

- `auto`: evolve bronze schema when new fields appear
- `strict`: freeze schema and fail on drift
- `discard`: discard unexpected values while keeping rows

Projects can set this per resource so strictness can vary by endpoint.

## Rerun Semantics

Replay behaviour depends on per-resource load hints:

- `merge` with a primary key provides idempotent upsert behaviour
- `replace` gives deterministic snapshot tables on rerun
- `append` preserves full arrival history

Choose by resource based on analytical needs and source stability.

Operationally, ingestion stage gating also considers:

- `force_reload=True` always triggers ingestion
- otherwise storage-cache heuristics decide whether ingestion should run

## Security Defaults

Current security defaults prioritise secret-safe runtime surfaces:

- dbt command environments are filtered to an allowlist instead of forwarding the full process environment
- token-like values in dbt stderr are redacted before being returned in transformation failure details
- ingestion logs avoid dumping raw loader result objects

## Package Quality Gate

The package quality gate is standardised on `uv` and runs the same checks you should later enforce in CI:

- pre-commit checks across the repository
- unit tests
- distribution build (wheel + source distribution)
- distribution metadata checks
- wheel content validation for `src`-layout packaging boundaries

Run it with both dependency groups enabled:

`uv run --group dev --group test python scripts/quality_gate.py`

## Pre-commit Checks

Use pre-commit for fast local feedback before commits.

Install the hooks:

`uv run --group dev pre-commit install`

Run hooks on all files:

`uv run --group dev pre-commit run --all-files`

## Release Publishing

Release publishing is handled by `.github/workflows/release.yml`.

- Trigger: push a tag matching `v*` (for example `v0.1.1`)
- Required PyPI setup: configure a Trusted Publisher for this GitHub repository
- Workflow behaviour:
  - runs the same quality gate command used locally and in CI
  - builds release distributions
  - uploads `dist/*` as workflow artefacts
  - publishes with `pypa/gh-action-pypi-publish` via OIDC
