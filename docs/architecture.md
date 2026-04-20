# Axiomatic Engine Architecture

## Purpose
`axiomatic_engine` is a protocol-driven ingestion library that standardises how sources, storage backends, and warehouse backends interact.  
The current implementation focuses on:

- contract-first interfaces via Python `Protocol`s
- typed runtime settings loaded from `AXIOMATIC_*` environment variables
- a `dlt`-based ingestion path into a warehouse
- a DuckDB-compatible warehouse stack (local DuckDB and MotherDuck)

## Current package structure

```text
src/axiomatic_engine/
├── contracts/
│   ├── source.py      # Source and resource contracts
│   ├── storage.py     # Raw storage contracts and file reference model
│   └── warehouse.py   # Warehouse contracts
├── config/
│   ├── storage.py     # Typed storage settings
│   ├── warehouse.py   # Typed warehouse settings
│   └── engine.py      # Composite settings and env loading
├── sources/
│   ├── base.py             # Base wrappers bridging contracts to dlt
│   ├── file/
│   │   └── http_stream.py # HTTP file source (CSV/TSV, optional gzip)
│   └── rest/              # Generic REST source package
├── adapters/
│   ├── factory.py                 # Adapter selection by Literal kind
│   ├── storage/local.py           # Local filesystem storage adapter
│   └── warehouse/
│       ├── base_duck.py           # Shared Duck-compatible warehouse logic
│       ├── duckdb.py              # Local DuckDB warehouse adapter
│       └── motherduck.py          # MotherDuck warehouse adapter
└── core/
    ├── ingestion.py   # Ingestor runs dlt pipeline into warehouse
    └── pipeline.py    # Top-level orchestration
```

## Architectural layers

### 1) Contracts (engine rules)

The contracts define a stable boundary for extension:

- `SourceProtocol` and `ResourceProtocol` in `contracts/source.py`
- `RawStorageProtocol` and `RawFileRef` in `contracts/storage.py`
- `WarehouseProtocol` in `contracts/warehouse.py`

`Literal` types constrain available kinds:

- `SourceKind`: `"api" | "filesystem" | "scraper" | "sharepoint"`
- `RawStorageKind`: `"local" | "gcs" | "s3"`
- `WarehouseKind`: `"duckdb" | "motherduck" | "bigquery"`

### 2) Source bridge (contracts -> dlt resources)

`sources/base.py` provides:

- `BaseResource`: wraps each resource and injects `_axiomatic_extracted_at_utc`
- `BaseSource`: converts a `SourceProtocol` implementation into a `dlt.source`

This keeps source-specific logic separate from orchestration concerns.

### 3) Implemented source: filesystem

`sources/file/http_stream.py` implements:

- `HttpStreamResource`: streams rows from URL-backed CSV/TSV files
- delimiter inference (`.tsv` -> tab, otherwise comma)
- compression inference (`.gz` -> gzip)
- progress logging every N rows
- `HttpStreamSource`: exposes a resource map as `ResourceProtocol` instances

### 4) Settings layer

`config/engine.py` provides `EngineSettings` as the typed runtime contract.

- `EngineSettings.from_env()` reads `AXIOMATIC_*` variables
- storage and warehouse settings are modelled as dedicated dataclasses
- `with_overrides(...)` enables CLI-over-env precedence in entrypoint scripts

### 5) Adapters and factory isolation

`adapters/factory.py` is the only place that instantiates adapter implementations:

- storage: `LocalStorage` is implemented; `gcs` and `s3` are declared but not implemented
- warehouse: `DuckDBWarehouse` and `MotherDuckWarehouse` are implemented; `bigquery` remains declared but not implemented

Warehouse adapters use a shared base:

- `DuckCompatibleWarehouseBase` centralises `execute(...)`, `load_from_references(...)`, and `dlt` destination handling
- concrete adapters keep backend-specific URI and credential validation

This preserves engine-agnostic extension points while keeping current runtime narrow.

### 6) Core execution path

`core/ingestion.py`:

- `Ingestor.run()` creates a `dlt.pipeline`
- executes `pipeline.run(source.to_dlt(), destination=..., credentials=...)`
- destination and credentials come from the selected warehouse adapter

`core/pipeline.py`:

- `Pipeline` accepts `EngineSettings` and resolves storage/warehouse adapters via the factory
- `land_raw_data()` currently checks for already-landed resources by filename and returns a boolean
- `run()` triggers ingestion when data was landed or when `force_reload=True`

## Data flow in the current version

1. A source implementation yields record dictionaries through `ResourceProtocol.read()`.
2. `BaseResource` augments each record with extraction metadata.
3. `BaseSource.to_dlt()` builds a `dlt` source from wrapped resources.
4. `Ingestor` runs `dlt` into the selected warehouse destination.
5. The warehouse adapter provides connection semantics and optional direct-load utilities.

## Implemented versus planned capabilities

Implemented now:

- `HttpStreamSource` for URL-based tabular ingestion
- `RestApiSource` and `RestApiResource` for generic API ingestion flows
- `LocalStorage` file listing through canonical `RawFileRef`
- `DuckDBWarehouse` and `MotherDuckWarehouse` with shared Duck-compatible base behaviour
- scheme-aware path normalisation for `read_auto(...)` inputs
- typed `EngineSettings` with `AXIOMATIC_*` env loading and CLI override support
- end-to-end `dlt` ingestion orchestration

Declared extension points (not yet implemented):

- storage adapters for `gcs`, `s3`
- warehouse adapter for `bigquery`
- full landing/write workflow in `Pipeline.land_raw_data()` (currently detection-oriented)

## Design constraints

- engine code remains domain-agnostic (no client or dataset hardcoding in engine modules)
- adapter construction stays centralised in `adapters/factory.py`
- contracts favour explicit naming and typed boundaries for maintainability
- warehouse hierarchy decision is recorded in `docs/adr/001-warehouse-adapter-hierarchy.md`