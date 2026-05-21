# Engine Usability Improvements Plan

**Date**: 2026-05-21
**Status**: Planning
**Priority**: High

## Context and Goal

`axiomatic-engine` is published on PyPI and installed as a versioned dependency in each client project. The engine's job is to abstract dlt + dbt across different warehouses (DuckDB, MotherDuck, BigQuery), storage backends (local, S3, GCS), and source types (HTTP, REST API, file) so that onboarding a new client is fast, consistent, and AI-assisted.

Each client engagement looks like:

```
Client project (separate repo)
├── pipeline.yml          ← describes the client's sources and warehouse
├── .ai/                  ← domain context for AI assistants
├── dbt_project/          ← client's SQL models
├── env-template          ← client's env vars
└── pyproject.toml        ← pins axiomatic-engine==x.y.z
```

**The engine itself is never modified per-client.** Only `pipeline.yml` and dbt models change.

## Current Problems

The engine's architecture is correct for this goal, but the tooling is not there yet:

1. **No client onboarding command.** There is no `axiomatic_engine init` — every new client project is copy-pasted from `nhs_inequality` or `fake_store`, both of which live inside the engine repo (wrong model).
2. **No declarative entrypoint.** Every client project currently requires a Python developer to write `run_pipeline.py` (~150–230 lines of engine-specific wiring). This blocks AI-only onboarding.
3. **The hard parts are manual.** Writing `stg_*.sql` with 100+ column casts is still fully manual. This is the biggest time cost on every engagement.
4. **Storage cache is broken for HTTP sources.** `should_run_ingestion()` checks `LocalStorage.list_files()` but HTTP sources never write there. Dead code in production.
5. **No AI orientation layer.** AI assistants have to read ~10 source files across `contracts/`, `config/`, `adapters/`, and `core/` to understand how to build a pipeline. No project-level context files exist.
6. **No PyPI release or version contract.** The engine has not been published and there is no `CHANGELOG` or versioning discipline. Client projects cannot pin a stable version.

## Extensibility Principles

All improvements must keep the engine **source-agnostic, warehouse-agnostic, and storage-agnostic**. The declarative layer is a thin convenience on top of the existing adapter protocol — not a replacement for it.

- **Source kinds are pluggable via `kind:` in `pipeline.yml`** — new sources (Kafka, SFTP, Snowflake export) are added by implementing a `SourceDefinition` adapter and registering a YAML kind. No engine core changes needed.
- **Warehouse and transform adapters remain protocols** — `pipeline.yml` does not hardcode DuckDB or dbt. `warehouse.kind: bigquery` routes to the BigQuery adapter; `transform.adapter: sqlmesh` would route to a future adapter.
- **Escape hatch always exists** — if a client's source logic exceeds the declarative patterns, a `custom` template generates a skeleton `run_pipeline.py`. They lose the generator commands but gain full flexibility.
- **When adding any declarative feature, check**: Does it assume DuckDB? → belongs in the DuckDB adapter. Does it assume dbt? → belongs in the dbt adapter. Does it assume a specific source type? → make it a per-`kind` field, not a core YAML field.

---

## Proposed Improvements

### 1. Versioning Discipline & `schema_version` Contract — High Priority

The engine is already on PyPI. What's missing is a stable contract between the engine and client `pipeline.yml` files so that engine upgrades don't silently break existing clients.

**Required:**
- Add a `CHANGELOG.md` with entries from the current version onwards
- Establish semantic versioning discipline: minor version = backwards-compatible YAML additions, major version = breaking `pipeline.yml` schema or `EngineSettings` API changes
- Add `schema_version: "1"` as a required top-level field in `pipeline.yml`; the engine validates this at startup and raises a clear error if the version is unsupported
- Document the version contract in `docs/versioning.md`

**Status**: Not started
**Estimated Effort**: Low

---

### 2. Client Onboarding Command (`axiomatic_engine init`) — Critical

The primary client onboarding action. Replaces "copy-paste from `nhs_inequality`" with a single command.

**Command:**

```bash
uvx axiomatic-engine init --template minimal --project my_client
```

**Creates a complete, runnable project:**

```
my_client/
├── pipeline.yml              # REQUIRED — fill in source URLs and warehouse
├── pyproject.toml            # pins axiomatic-engine==<current version>
├── .ai/
│   ├── context.md            # FILL IN — domain context for AI
│   ├── conventions.md        # pre-filled with engine conventions
│   ├── known-issues.md       # pre-filled with common errors and fixes
│   └── checklist.md          # pre-filled with step-by-step procedures
├── dbt_project/
│   ├── dbt_project.yml       # medallion schema, env_var references
│   ├── profiles.yml          # warehouse connection
│   └── models/
│       ├── sources.yml       # AUTO-GENERATED — do not hand-edit
│       ├── silver/           # empty, ready for generated staging models
│       └── gold/             # empty, ready for fact/dimension models
├── env-template              # all AXIOMATIC_* vars pre-populated
├── .gitignore
└── README.md                 # includes "Working with AI Assistants" section
```

**Templates:**
- `minimal` (default): HTTP file or REST API source + DuckDB + dbt. The preferred path for all client projects.
- `api`: REST API source with pagination pattern examples.
- `custom` (escape hatch): Skeleton `run_pipeline.py` — documented as "use only when declarative patterns are insufficient."

**Status**: Planning
**Estimated Effort**: Low-Medium

---

### 3. Declarative `pipeline.yml` Entrypoint — Critical

Replace `run_pipeline.py` with a YAML config as the standard client entrypoint. A client project should contain zero Python for the common case.

**Full example (NHS-style HTTP ZIP source, DuckDB, dbt):**

```yaml
schema_version: "1"

source:
  kind: http_file
  name: nhs_rtt_bronze_ingest
  resources:
    - name: rtt_commissioner_apr24
      url: https://www.england.nhs.uk/.../Full-CSV-data-file-Apr24-ZIP-4M-revised.zip
      archive_format: zip
      archive_member: 20240430-RTT-April-2024-full-extract-revised.csv
      delimiter: ","

warehouse:
  kind: duckdb
  path: "${AXIOMATIC_WAREHOUSE_PATH}"

schema:
  bronze: "${AXIOMATIC_SCHEMA_BRONZE:bronze}"
  silver: "${AXIOMATIC_SCHEMA_SILVER:silver}"
  gold: "${AXIOMATIC_SCHEMA_GOLD:gold}"

transform:
  enabled: true
  dbt_project_dir: ./dbt_project
  dbt_profiles_dir: ./dbt_project
  dbt_profile_name: my_client
```

**Bulk resource generation (no Python, no Jinja2):**

```yaml
source:
  kind: http_file
  name: nhs_rtt_bronze_ingest
  resources:
    - name_pattern: "rtt_commissioner_{mon}{yy}"
      url_pattern: "https://.../Full-CSV-data-file-{Mon}{YY}-ZIP-4M-revised.zip"
      archive_member_pattern: "{YYYYMMDD}-RTT-{Month}-{YYYY}-full-extract-revised.csv"
      date_range:
        from: "2024-04"
        to: "2025-03"
        frequency: monthly
```

**Run commands:**

```bash
axiomatic-engine run --config pipeline.yml
axiomatic-engine run --config pipeline.yml --skip-transforms
axiomatic-engine run --config pipeline.yml --force-reload
```

**Escape hatch**: If source logic exceeds declarative patterns, use the `custom` template. The declarative path does not support arbitrary Python to keep it AI-safe and client-safe.

**Status**: Planning
**Estimated Effort**: Medium

---

### 4. AI Context Files (`.ai/`) — High Priority

Every client project includes four files that an AI reads on first contact, generated by `init` with sensible defaults and clear prompts to fill in.

```
.ai/
├── context.md       # domain context: what the project does, business terms, data sources
├── conventions.md   # naming rules, file layout, design patterns (pre-filled by engine)
├── known-issues.md  # common errors and fixes (pre-filled by engine, extended per-project)
└── checklist.md     # step-by-step procedures for common tasks (pre-filled by engine)
```

**`checklist.md` is the key file — it tells AI exactly what to do for each task:**

```markdown
## Starting work on this project (read first)
1. Read `.ai/context.md`
2. Read `.ai/conventions.md`
3. Read `pipeline.yml`

## Adding a new data source
1. Read `.ai/context.md` and `pipeline.yml`
2. Add the new source block to `pipeline.yml`
3. Run: `axiomatic-engine sync-sources --config pipeline.yml`
4. Run: `axiomatic-engine generate-staging --config pipeline.yml --source <name>`
5. Review generated model in `dbt_project/models/silver/`
6. Write intermediate and gold models manually
7. Run: `axiomatic-engine run --config pipeline.yml --run-transforms`

## Do NOT
- Edit `dbt_project/models/sources.yml` by hand (use sync-sources)
- Write run_pipeline.py from scratch (use `axiomatic-engine init --template custom`)
- Edit files in `src/axiomatic_engine/` (that's the engine, not the project)
```

**`context.md` template prompts the user to fill in:**
- What the project does
- Client's business terms and domain vocabulary
- Data sources table (name, type, URL/location, update frequency)
- Analysis questions this project answers
- Extension plans / deferred work

**Benefit:** AI reads ~100 lines instead of 10+ engine source files. Context is written once per project and reused across every AI session.

**Status**: Planning
**Estimated Effort**: Low (generated by `init`)

---

### 5. `sync-sources` Command — High Priority

Keeps `pipeline.yml` source definitions in sync with `dbt_project/models/sources.yml`. Currently this is hand-edited and error-prone.

```bash
axiomatic-engine sync-sources --config pipeline.yml
```

**Behaviour:**
1. Reads source name and resource list from `pipeline.yml`
2. Generates or updates `sources.yml` with correct table names, schema `env_var` references, and column stubs
3. If `sources.yml` already exists, shows a diff and asks before overwriting
4. Optionally validates against actual bronze tables in the warehouse: `--validate`

**Status**: Planning
**Estimated Effort**: Medium

---

### 6. Bronze-to-Silver Staging Generator — High Priority

The single biggest time cost on every client engagement. Writing `stg_*.sql` with messy source column names (e.g. `"0 To 1 Weeks SUM 1"`) is fully manual today.

```bash
axiomatic-engine generate-staging --config pipeline.yml --source nhs_rtt_bronze_ingest
```

**Behaviour:**
- Introspects bronze table schema from the warehouse
- Generates snake_case aliases, casts, and `_dlt_*` metadata handling
- Writes to `dbt_project/models/silver/stg_<source>.sql` for review
- If file exists, shows a diff instead of overwriting
- Flags ambiguous type inferences with a comment for human review

**Example output:**

```sql
-- auto-generated by axiomatic-engine generate-staging
-- Review before committing. Flagged columns marked with TODO.
{{ config(materialized='view', schema=env_var('AXIOMATIC_SCHEMA_SILVER', 'silver')) }}

select
    cast("Period" as date)                     as period,
    cast("Commissioner Org Code" as varchar)   as commissioner_org_code,
    cast("0 To 1 Weeks SUM 1" as integer)      as weeks_0_to_1,  -- TODO: verify type
    ...
    _dlt_load_id                               as load_id
from {{ source('nhs_rtt_bronze_ingest', 'rtt_commissioner_apr24') }}
```

**Benefit:** Turns 181 lines of manual SQL into a review-and-commit workflow. On a new client engagement this alone saves hours.

**Status**: Planning
**Estimated Effort**: Medium

---

### 7. Fix Storage Cache Bug — High Priority

`should_run_ingestion()` checks `LocalStorage.list_files()` but HTTP sources never write there. Every HTTP pipeline currently either always re-downloads or always skips — there is no working incremental logic.

**Fix**: Skip the storage cache check entirely for source kinds that don't write to local storage. Return `True` (always ingest) until the proper checkpoint system (Item #8) is in place.

```python
# pipeline.py - minimal fix
def should_run_ingestion(self, source: BaseSource, force_reload: bool) -> bool:
    if force_reload:
        return True
    if not source.supports_storage_cache():
        LOGGER.info("Source does not use storage cache. Ingestion will run.")
        return True
    # existing file-based cache logic...
```

**Status**: Planning
**Estimated Effort**: Low

---

### 8. Incremental Checkpoint System — Medium Priority

Replace the broken file-name cache with warehouse-level checkpoint metadata. Critical for client projects where re-downloading months of data per run is unacceptable.

**Approach**: Store checkpoint state in the warehouse (e.g. `_axiomatic_state.checkpoints` table):

| source_name | resource_name | last_loaded_at | etag | content_hash |
|-------------|--------------|---------------|------|--------------|
| nhs_rtt_bronze_ingest | rtt_commissioner_apr24 | 2025-05-01 | "abc123" | null |

- **HTTP sources**: check `ETag` / `Last-Modified` headers before downloading
- **REST API sources**: track last successful fetch timestamp
- **File sources**: track file mtime or hash

**Benefit:** `--force-reload` works as expected. Incremental client runs complete in seconds.

**Status**: Planning
**Estimated Effort**: Medium-High

---

### 9. Pipeline Report & Diagnostics — Medium Priority

Three related features sharing the same dlt/dbt output-parsing infrastructure. Important for client deliverables.

**a. Run report** — printed after every run:

```
Axiomatic Pipeline Report — my_client
======================================
Ingestion:
  nhs_rtt_bronze_ingest
    rtt_commissioner_apr24  185,101 rows  12.3s  loaded
    rtt_commissioner_may24  187,432 rows  11.8s  skipped (cached)

Transform:
  dbt run   passed  45.2s
  dbt test  12 passed, 0 failed  8.1s

Warehouse: DuckDB at ./data/warehouse.duckdb
```

**b. Structured error output** — when dbt or dlt fails, emit structured JSON that AI can parse in one shot:

```json
{
  "stage": "transform",
  "step": "dbt_test",
  "error_type": "relationships_test_failed",
  "model": "fct_icb_waiting_times",
  "details": "47 rows have icb_code not in dim_icb",
  "affected_models": ["fct_icb_waiting_times", "int_icb_waiting_metrics"]
}
```

**c. Schema drift detection** — warns when a source schema has changed relative to committed staging models:

```bash
axiomatic-engine check-drift --config pipeline.yml
```

```
Schema drift in 'nhs_rtt_bronze_ingest':
  NEW   "Gt 104 Weeks SUM 1" (integer) — not in stg_rtt_commissioner.sql
  GONE  "Commissioner Org Name" — in model but not in source
```

**Status**: Planning
**Estimated Effort**: Medium

---

### 10. Integration Cookbook — Continuous

A library of copy-pasteable patterns in `docs/cookbook/`. Built up as client engagements happen.

- `http-csv-zip.md` — ZIP + CSV (NHS-style)
- `http-csv-direct.md` — flat CSV over HTTP
- `rest-api-pagination.md` — page-based, cursor-based, offset-based
- `rest-api-auth.md` — Bearer token, API key, OAuth2
- `s3-parquet.md` — S3 Parquet files
- `bigquery-export.md` — BigQuery as warehouse target

Each pattern includes: complete `pipeline.yml`, expected bronze schema, generated staging model snippet, common errors and fixes.

**Benefit:** AI copies a working pattern for the client's source type instead of inventing one.

**Status**: Continuous
**Estimated Effort**: Low per pattern (grows with each engagement)

---

### 11. Engine-Level IDE Rules — Low Priority

A `.windsurf/rules/` or `.cursorrules` file in the engine repo that tells AI assistants the correct way to work with any client project built on this engine. Useful for contributors to the engine itself.

A separate, minimal version is included in every client project by `init`:

```markdown
# AI Rules: <client> (Axiomatic Engine project)

Read `.ai/checklist.md` before doing anything.
Do not edit `dbt_project/models/sources.yml` by hand.
Do not write `run_pipeline.py` unless using the custom template.
Do not edit anything in `src/axiomatic_engine/`.
```

**Status**: Continuous
**Estimated Effort**: Low

---

## Decision Record

| Decision | Status |
|----------|--------|
| Engine published on PyPI; client projects install it as a pinned versioned dependency | Accepted |
| `projects/` in engine repo are development examples only; real client projects are separate repos | Accepted |
| Declarative `pipeline.yml` is the primary client entrypoint; `run_pipeline.py` is escape hatch only | Proposed |
| No Jinja2 or arbitrary Python in `pipeline.yml` | Proposed |
| Storage cache removed for HTTP sources pending proper checkpoint system | Proposed |
| `schema_version` field added to `pipeline.yml` for breaking change detection | Proposed |

## Phases

| Phase | Item | Why now |
|-------|------|---------|
| 1 | Versioning discipline & `schema_version` (#1) | Protects existing clients before more changes ship |
| 1 | `init` command (#2) | Enables the correct client project model from day one |
| 1 | Declarative `pipeline.yml` (#3) | Zero-Python client projects |
| 1 | `.ai/` context files (#4) | Generated by `init` — low effort, high AI impact |
| 2 | `sync-sources` (#5) | Unblocks dbt model development after ingestion |
| 2 | Staging generator (#6) | Biggest time saving per engagement |
| 2 | Fix storage cache bug (#7) | Correctness fix — dead code in every HTTP project |
| 3 | Checkpoint system (#8) | Performance — incremental loads for repeat client runs |
| 3 | Pipeline report & diagnostics (#9) | Client-facing output quality |
| Continuous | Cookbook (#10) | One pattern per engagement |
| Continuous | IDE rules (#11) | Low effort, maintained alongside engine |

## Success Criteria

- [ ] A new client project is scaffolded with `axiomatic-engine init` in under 2 minutes.
- [ ] A client pipeline runs end-to-end in under 5 minutes without writing any Python.
- [ ] An AI assistant can add a new source to a client project by editing only `pipeline.yml` and dbt models.
- [ ] Bronze-to-silver staging model for a 100+ column source is generated and reviewed in under 5 minutes.
- [ ] Re-running a pipeline with no source changes completes in under 10 seconds (checkpoint cache hit).
- [ ] When dbt or dlt fails, the structured error allows an AI to diagnose and fix in one chat turn.
- [ ] Client projects pin `axiomatic-engine==x.y.z`; engine validates `schema_version` at startup and raises a clear error on incompatibility.

## Related

- `docs/architecture.md` — protocol layer and adapter hierarchy
- `docs/plans/decisions/` — ADRs
- `projects/nhs_inequality/`, `projects/fake_store/` — development examples (not client project templates)
