# Axiomatic Engine

Axiomatic Engine orchestrates ingestion and transformation pipelines while keeping domain logic in project folders.

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
