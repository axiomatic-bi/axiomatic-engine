# Axiomatic Engine

Axiomatic Engine orchestrates ingestion and transformation pipelines while keeping domain logic in project folders.

## Quick Start

Install the package:

- `uv add axiomatic-engine`

Or with pip:

- `pip install axiomatic-engine`

Run a project entrypoint:

- copy `projects/fake_store/.env.example` to `projects/fake_store/.env`
- set required environment variables for your target warehouse and storage
- run `uv run python projects/fake_store/run_pipeline.py`

This gives a working reference for a REST ingestion source and transformation flow using the engine contracts.

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

Source implementations now expose specific source kinds:

- `rest_api`
- `http_file`

The standard project path is typed source definitions routed through `axiomatic_engine.sources.factory` via `build_source(...)`.

Direct source constructors remain supported for advanced project-specific customisation.

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
