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

## Extensibility Principles

All improvements must keep the engine **source-agnostic, warehouse-agnostic, and storage-agnostic**. The declarative layer is a thin convenience on top of the existing adapter protocol — not a replacement for it.

- **Source kinds are pluggable via `kind:` in `pipeline.yml`** — new sources (Kafka, SFTP, Snowflake export) are added by implementing a `SourceDefinition` adapter and registering a YAML kind. No engine core changes needed.
- **Warehouse and transform adapters remain protocols** — `pipeline.yml` does not hardcode DuckDB or dbt. `warehouse.kind: bigquery` routes to the BigQuery adapter; `transform.adapter: sqlmesh` would route to a future adapter.
- **Escape hatch always exists** — if a client's source logic exceeds the declarative patterns, a `custom` template generates a skeleton `run_pipeline.py`. They lose the generator commands but gain full flexibility.
- **When adding any declarative feature, check**: Does it assume DuckDB? → belongs in the DuckDB adapter. Does it assume dbt? → belongs in the dbt adapter. Does it assume a specific source type? → make it a per-`kind` field, not a core YAML field.

---

## Proposed Improvements

### 1. Client Onboarding Command (`axiomatic_engine init`) — Critical

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
│   ├── context.md    # FILL IN — domain context for AI
│   ├── checklist.md  # pre-filled with step-by-step procedures
│   └── reference.md  # pre-filled with naming conventions, errors, and fixes
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

### 2. Declarative `pipeline.yml` Entrypoint — Critical

Replace `run_pipeline.py` with a YAML config as the standard client entrypoint. A client project should contain zero Python for the common case.

**Full example (NHS-style HTTP ZIP source, DuckDB, dbt):**

```yaml
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

**Run commands:**

```bash
axiomatic-engine run --config pipeline.yml
axiomatic-engine run --config pipeline.yml --skip-transforms
axiomatic-engine run --config pipeline.yml --force-reload
```

**Bulk resource generation** via `url_pattern` / `date_range` is deferred to a future release. For now, list all resources explicitly — AI can generate the list trivially from a prompt like "add all months April 2024 to March 2025."

**Escape hatch**: If source logic exceeds declarative patterns, use the `custom` template. The declarative path does not support arbitrary Python to keep it AI-safe and client-safe.

**Status**: Planning
**Estimated Effort**: Medium

---

### 3. AI Context Files (`.ai/`) — High Priority

Every client project includes four files that an AI reads on first contact, generated by `init` with sensible defaults and clear prompts to fill in.

```
.ai/
├── context.md    # domain context: what the project does, business terms, data sources
├── checklist.md  # step-by-step procedures for common tasks (pre-filled by engine)
└── reference.md  # naming conventions, common errors, and fixes (pre-filled by engine)
```

**`checklist.md` is the key file — it tells AI exactly what to do for each task:**

```markdown
## Starting work on this project (read first)
1. Read `.ai/context.md`
2. Read `pipeline.yml`
3. Check `.ai/reference.md` for naming conventions and common errors

## Adding a new data source
1. Read `.ai/context.md` and `pipeline.yml`
2. Add the new `resources:` entry to the `source:` block in `pipeline.yml`
3. Rewrite `dbt_project/models/sources.yml` to match — one `tables:` entry per resource
4. Run: `axiomatic-engine run --config pipeline.yml --skip-transforms`
5. Run: `axiomatic-engine generate-staging --config pipeline.yml --source <name>`
6. Review generated model in `dbt_project/models/silver/`
7. Write intermediate and gold models manually
8. Run: `axiomatic-engine run --config pipeline.yml`

## Do NOT
- Hand-edit `dbt_project/models/sources.yml` — ask AI to regenerate it from `pipeline.yml` instead
- Write run_pipeline.py from scratch (use `axiomatic-engine init --template custom`)
- Edit files in `src/axiomatic_engine/` (that's the engine, not the project)
```

**`context.md` template prompts the user to fill in:**
- What the project does
- Client's business terms and domain vocabulary
- Data sources table (name, type, URL/location, update frequency)
- Analysis questions this project answers
- Extension plans / deferred work

**Benefit:** AI reads ~100 lines (three files) instead of 10+ engine source files. Context is written once per project and reused across every AI session. Three files instead of four keeps per-session token cost low.

**Status**: Planning
**Estimated Effort**: Low (generated by `init`)

---

### 4. Bronze-to-Silver Staging Generator — High Priority

The single biggest time cost on every client engagement. Writing `stg_*.sql` with messy source column names (e.g. `"0 To 1 Weeks SUM 1"`) is fully manual today.

```bash
axiomatic-engine generate-staging --config pipeline.yml --source nhs_rtt_bronze_ingest
```

**Behaviour:**
- Introspects bronze table schema from the warehouse
- Generates snake_case aliases, casts, and `_dlt_*` metadata handling
- Writes to `dbt_project/models/silver/stg_<source>.sql` for review
- If file exists, shows a diff instead of overwriting (`--diff` flag)
- Flags ambiguous type inferences with a `-- TODO` comment for human review

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

**Schema drift** is handled by re-running this command: if columns have changed since last generation, `--diff` shows what's new, missing, or changed. No separate drift-detection command needed.

**Benefit:** Turns 181 lines of manual SQL into a review-and-commit workflow. On a new client engagement this alone saves hours.

**Status**: Planning
**Estimated Effort**: Medium

---

### 5. Fix Storage Cache Bug — High Priority

`should_run_ingestion()` checks `LocalStorage.list_files()` but HTTP sources never write there. Every HTTP pipeline currently either always re-downloads or always skips — there is no working incremental logic.

**Fix**: Skip the storage cache check entirely for source kinds that don't write to local storage. Return `True` (always ingest) until the proper checkpoint system (Item #6) is in place.

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

### 6. Incremental Checkpoint System — Medium Priority

Replace the broken file-name cache with warehouse-level checkpoint metadata. Critical for client projects where re-downloading months of data per run is unacceptable.

**Approach**: Store checkpoint state in the warehouse (e.g. `_axiomatic_state.checkpoints` table):

| source_name | resource_name | last_loaded_at | etag | content_hash |
|-------------|--------------|---------------|------|--------------|
| nhs_rtt_bronze_ingest | rtt_commissioner_apr24 | 2025-05-01 | "abc123" | null |

- **HTTP sources**: check `ETag` / `Last-Modified` headers before downloading
- **REST API sources**: track last successful fetch timestamp
- **File sources**: track file mtime or hash

**Benefit:** `--force-reload` works as expected. Incremental client runs complete in seconds.

> **Phase escalation note:** If a client has 10+ resources and the storage cache bug fix (#5) means every run re-downloads everything, this moves to Phase 2 immediately.

**Status**: Planning
**Estimated Effort**: Medium-High

---

### 7. Pipeline Report — Medium Priority

Every run should produce a unified summary instead of scattered dlt logs. Important for client deliverables.

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

When dbt or dlt fails, surface dbt's own `run_results.json` rather than parsing raw stderr. This gives AI structured output to work with without building a custom error parser.

**Status**: Planning
**Estimated Effort**: Medium

---

### 8. Integration Cookbook — Phase 2

Copy-pasteable patterns in `docs/cookbook/`. The NHS `http-csv-zip.md` pattern is written immediately after Phase 1 ships (30 minutes of work, highest AI asset value per hour spent). Further patterns added after each engagement.

- `http-csv-zip.md` — ZIP + CSV (NHS-style)
- `http-csv-direct.md` — flat CSV over HTTP
- `rest-api-pagination.md` — page-based, cursor-based, offset-based
- `rest-api-auth.md` — Bearer token, API key, OAuth2
- `s3-parquet.md` — S3 Parquet files
- `bigquery-export.md` — BigQuery as warehouse target

Each pattern includes: complete `pipeline.yml`, expected bronze schema, generated staging model snippet, common errors and fixes.

**Benefit:** AI copies a working pattern instead of inventing one. A single well-documented example is worth more than several CLI commands for reducing AI token cost.

**Status**: Planning (NHS pattern) / Continuous (subsequent patterns)
**Estimated Effort**: Low per pattern

---

## What Was Cut

| Item | Why |
|------|-----|
| `CHANGELOG.md` | Git tags and GitHub releases are sufficient for a solo-maintained package |
| `schema_version` runtime validation | Over-engineering for a solo user — semver tags are enough; add only if versioning actually causes a client breakage |
| `sync-sources` command | AI regenerates `sources.yml` from `pipeline.yml` in one shot given a `checklist.md` instruction — a dedicated command adds maintenance for no meaningful gain |
| Four `.ai/` files | `conventions.md` and `known-issues.md` merged into `reference.md` — three files reduces per-session token overhead |
| `computed_fields` in `pipeline.yml` | Reinvents dbt's job inside YAML — column transforms belong in staging SQL models |
| `url_pattern` / `date_range` bulk generation | Design rabbit hole — defer until the explicit resource list proves too painful; AI can generate verbose lists trivially |
| Auto-test generation command | AI already writes good dbt tests when `.ai/conventions.md` tells it the rules — a dedicated command adds maintenance for marginal benefit |
| Standalone `check-drift` command | Folded into `generate-staging --diff` — same problem, one tool instead of two |
| Structured error parser | Fragile (dbt output format changes between versions) — surfacing dbt's native `run_results.json` is simpler and more robust |
| Engine-level IDE rules file | Already covered by `.ai/checklist.md` in each client project — a separate engine-level file is redundant |

## Decision Record

| Decision | Status |
|----------|--------|
| Engine published on PyPI; client projects install it as a pinned versioned dependency | Accepted |
| `projects/` in engine repo are development examples only; real client projects are separate repos | Accepted |
| Declarative `pipeline.yml` is the primary client entrypoint; `run_pipeline.py` is escape hatch only | Proposed |
| No Jinja2 or arbitrary Python in `pipeline.yml` | Proposed |
| Storage cache removed for HTTP sources pending proper checkpoint system | Proposed |

## Phases

| Phase | Item | Why now |
|-------|------|---------|
| 1 | `init` command (#1) | Enables the correct client project model from day one |
| 1 | Declarative `pipeline.yml` (#2) | Zero-Python client projects |
| 1 | `.ai/` context files (#3) | Generated by `init` — low effort, high AI impact |
| 2 | Staging generator (#4) | Biggest time saving per engagement |
| 2 | Fix storage cache bug (#5) | Correctness fix — dead code in every HTTP project |
| 2 | Cookbook NHS pattern (#8) | 30 min effort, immediate AI value |
| 3 | Checkpoint system (#6) | Performance — may escalate to Phase 2 if client has 10+ resources |
| 3 | Pipeline report (#7) | Client-facing output quality |

## Success Criteria

- [ ] A new client project is scaffolded with `axiomatic-engine init` in under 2 minutes.
- [ ] A client pipeline runs end-to-end in under 5 minutes without writing any Python.
- [ ] An AI assistant can add a new source to a client project by editing only `pipeline.yml` and dbt models.
- [ ] Bronze-to-silver staging model for a 100+ column source is generated and reviewed in under 5 minutes.
- [ ] Re-running a pipeline with no source changes completes in under 10 seconds (checkpoint cache hit).
- [ ] When dbt or dlt fails, the run report surfaces dbt's `run_results.json` for AI diagnosis.

## Related

- `docs/architecture.md` — protocol layer and adapter hierarchy
- `docs/plans/decisions/` — ADRs
- `projects/nhs_inequality/`, `projects/fake_store/` — development examples (not client project templates)
