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
projects/fake-store/
├── sql/
│   ├── .env.example
│   ├── silver/
│   ├── gold/
│   └── analytics/
├── src/
│   ├── definitions.py
│   └── normalisers.py
└── run_pipeline.py
```

## Runtime Contract

The project stays domain-aware while the engine stays domain-agnostic:

- project code defines API resources and normalisation hooks
- engine code handles ingestion orchestration and transformation orchestration
- sensitive values come from environment variables, not hardcoded paths or tokens

## Environment Variables

Copy `sql/.env.example` to a local `.env` file and set values for your environment.

Key variables:

- warehouse: `AXIOMATIC_WAREHOUSE_KIND`, `AXIOMATIC_WAREHOUSE_PATH`, `AXIOMATIC_WAREHOUSE_SCHEMA`
- MotherDuck auth: `AXIOMATIC_MOTHERDUCK_ACCESS_TOKEN`
- transformation: `AXIOMATIC_TRANSFORM_ENABLED`, `AXIOMATIC_TRANSFORM_BACKEND`
- dbt: `AXIOMATIC_DBT_PROJECT_DIR`, `AXIOMATIC_DBT_PROFILES_DIR`, `AXIOMATIC_DBT_PROFILE_NAME`, `AXIOMATIC_DBT_TARGET`, `AXIOMATIC_DBT_RUN_TESTS`

## Usage

Run the pipeline from the project root:

```bash
python run_pipeline.py
```

When enabled, the pipeline performs ingestion first, then runs dbt transformations.

## Development Notes

- Use British English in user-facing docs and comments.
- Keep API-specific logic in project files, not in `src/axiomatic_engine/`.
- Keep secrets in local env files and CI secret stores, never in committed source files.