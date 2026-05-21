# Fake Store Data Pipeline

This project is a reference consumer of `axiomatic_engine`. It ingests retail data from the [Fake Store API](https://fakestoreapi.com/) and runs transformations with a dbt-first workflow.

## Architecture

The pipeline follows a medallion flow:

- Bronze: raw API records loaded by the engine via `dlt`
- Silver: cleaned and typed staging models
- Gold: dimensional and fact models for analytics
- Analytics: optional denormalised views for BI and AI use cases

## Project Structure

```text
projects/fake_store/
├── pipeline.yml              # Declarative pipeline config (NEW)
├── .env.example
├── dbt_project/
│   └── models/
│       ├── sources.yml
│       ├── silver/
│       ├── gold/
│       └── analytics/
├── src/
│   ├── definitions.py
│   └── normalisers.py
└── run_pipeline.py           # Legacy Python entrypoint (escape hatch)
```

## Runtime Contract

The project stays domain-aware while the engine stays domain-agnostic:

- project code defines API resources and normalisation hooks
- engine code handles ingestion orchestration and transformation orchestration
- sensitive values come from environment variables, not hardcoded paths or tokens

## Bronze Load Policies

This project configures resource-level ingestion hints for deterministic reruns:

- `products`: `merge` on primary key `id`
- `users`: `merge` on primary key `id`
- `carts`: `replace`

Schema evolution is set to `auto` for all three resources. New source fields are accepted in bronze and can be promoted through silver/gold when needed.

Because `merge` and `replace` are used, dlt also creates a transient/staging schema (for example `bronze_staging`) in MotherDuck while applying load operations. This is expected engine behaviour and supports safe upsert/replace semantics into the final `bronze` tables.

## Environment Variables

Copy `.env.example` to a local `.env` file and set values for your environment.

Key variables:

- warehouse: `AXIOMATIC_WAREHOUSE_KIND`, `AXIOMATIC_WAREHOUSE_PATH`
- dlt runtime: `AXIOMATIC_DLT_PIPELINES_DIR`
- schemas: `AXIOMATIC_SCHEMA_BRONZE`, `AXIOMATIC_SCHEMA_SILVER`, `AXIOMATIC_SCHEMA_GOLD`, `AXIOMATIC_SCHEMA_ANALYTICS`
- storage: `AXIOMATIC_STORAGE_KIND`, `AXIOMATIC_STORAGE_PATH`
- MotherDuck auth: `AXIOMATIC_MOTHERDUCK_ACCESS_TOKEN`
- transformation: `AXIOMATIC_TRANSFORM_ENABLED`, `AXIOMATIC_TRANSFORM_BACKEND`
- dbt: `AXIOMATIC_DBT_PROJECT_DIR`, `AXIOMATIC_DBT_PROFILES_DIR`, `AXIOMATIC_DBT_PROFILE_NAME`, `AXIOMATIC_DBT_TARGET`, `AXIOMATIC_DBT_RUN_TESTS`
- project source: `FAKE_STORE_API_URL`, `LOG_LEVEL`

## Usage

This project uses the declarative `pipeline.yml` workflow.

Run the full pipeline (ingestion + transforms):
```bash
axiomatic-engine run --config pipeline.yml
```

Run ingestion only:
```bash
axiomatic-engine run --config pipeline.yml --skip-transforms
```

Force re-download all data:
```bash
axiomatic-engine run --config pipeline.yml --force-reload
```

Generate staging model:
```bash
axiomatic-engine generate-staging --config pipeline.yml --source fake_store_bronze_ingest --resource products
```

### Legacy Python Script (Escape Hatch)

The original `run_pipeline.py` is preserved as an example of imperative pipeline construction for advanced use cases requiring programmatic control or custom authentication hooks.

## Development Notes

- Use British English in user-facing docs and comments.
- Keep API-specific logic in project files, not in `src/axiomatic_engine/`.
- Keep secrets in local env files and CI secret stores, never in committed source files.
