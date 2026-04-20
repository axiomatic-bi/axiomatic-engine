# ADR 001: Duck-Compatible Warehouse Adapter Hierarchy

## Status

Accepted

## Context

The engine needs first-class support for both local DuckDB and MotherDuck while keeping warehouse behaviour behind `WarehouseProtocol`.

A single universal adapter was possible because both backends are DuckDB-compatible. However, this would push backend-specific branching (for example `md:` validation and token checks) into one class and blur capability boundaries defined by `WarehouseKind`.

The project is still in build phase, so we can establish stable conventions now:

- namespaced `AXIOMATIC_*` environment variables
- typed settings objects for storage and warehouse configuration
- central adapter construction in `adapters/factory.py`

## Decision

Use a shared base class plus separate concrete warehouse adapters:

- `DuckCompatibleWarehouseBase` contains shared DuckDB-compatible behaviour (`execute`, `load_from_references`, `dlt` destination)
- `DuckDBWarehouse` handles local DuckDB semantics
- `MotherDuckWarehouse` handles MotherDuck semantics

MotherDuck paths remain `md:<database_name>` only. Tokens are not appended to URI paths.

## Consequences

### Positive

- Clear capability boundaries for `duckdb` and `motherduck`
- Shared logic is centralised without coupling backend-specific concerns
- Safer secret handling by keeping tokens out of connection URIs
- Cleaner extension path for future warehouses

### Trade-offs

- One additional abstraction layer to maintain
- Factory wiring and settings propagation become slightly more explicit

## Security Notes

- MotherDuck access tokens are sourced from `AXIOMATIC_MOTHERDUCK_ACCESS_TOKEN`
- Token presence is validated by the MotherDuck adapter
- Token values are not embedded into `warehouse_path`
