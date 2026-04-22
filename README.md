# Axiomatic Engine

Axiomatic Engine orchestrates ingestion and transformation pipelines while keeping domain logic in project folders.

## Runtime Configuration Contract

The engine reads typed runtime settings from `AXIOMATIC_*` environment variables, with project entrypoints able to override values via CLI flags.

Schema layers are configured independently:

- `AXIOMATIC_SCHEMA_BRONZE`
- `AXIOMATIC_SCHEMA_SILVER`
- `AXIOMATIC_SCHEMA_GOLD`
- `AXIOMATIC_SCHEMA_ANALYTICS`

This keeps medallion naming explicit and consistent across ingestion and dbt model targets.

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
