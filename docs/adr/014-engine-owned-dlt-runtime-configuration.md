# ADR 014: Engine-Owned dlt Runtime Configuration

## Status

Accepted

## Context

Pipeline runs use `dlt` for state restoration and loading. When `dlt` runtime state is
kept in the user-global directory, historical state can survive repository path changes
and introduce stale destination paths.

In practice this creates a split configuration model:

- engine settings define warehouse destination via `AXIOMATIC_*` variables
- `dlt` runtime state can still influence destination sync behaviour before load

This undermines reproducibility and makes debugging environment issues harder across
local development and CI.

## Decision

The engine owns dlt runtime configuration explicitly.

- add `AXIOMATIC_DLT_PIPELINES_DIR` to engine settings as the canonical runtime-state
  directory override
- initialise `dlt.pipeline(...)` with the warehouse destination returned by the
  warehouse adapter
- ensure DuckDB warehouse adapters return configured destination objects, matching the
  existing MotherDuck behaviour
- continue passing explicit destination and credentials into `pipeline.run(...)` for
  deterministic load execution

## Consequences

### Positive

- pipeline runtime behaviour is driven by explicit engine configuration
- project-local dlt state is supported for portable, reproducible execution
- stale global runtime state no longer silently drives destination selection
- DuckDB and MotherDuck now follow the same destination-object pattern

### Trade-offs

- one additional environment variable is introduced for advanced runtime control
- teams relying on implicit `~/.dlt` state must set a path intentionally if they want
  project-scoped behaviour

## Operational Notes

- recommended project default: `AXIOMATIC_DLT_PIPELINES_DIR=./.dlt/pipelines`
- for existing local environments, remove stale pipeline folders under `~/.dlt/pipelines`
  when migrating from historical repository paths
