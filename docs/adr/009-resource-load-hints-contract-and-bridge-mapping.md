# ADR 009: Resource Load Hints Contract And Source Bridge Mapping

## Status

Accepted

## Context

The engine required deterministic rerun control per resource (for example `merge` for keyed entities, `replace` for snapshot-like entities) without embedding project-specific logic into core orchestration.

Before this decision:

- `BaseSource.to_dlt()` always created `dlt.resource(...)` with only a name
- source implementations had no typed way to declare load behaviour
- rerun semantics depended on destination defaults

We needed a source-agnostic contract that:

- works across source types
- keeps policy declaration close to resource definitions
- preserves engine boundaries and factory isolation

## Decision

Introduce a typed resource-level hint contract and map it centrally in the source bridge:

- add `ResourceLoadHints` to `contracts/source.py`
  - `write_disposition`
  - `primary_key`
  - `schema_evolution_mode`
- extend `ResourceProtocol` with optional `get_load_hints()`
- read hints in `sources/base.py` and pass mapped kwargs to `dlt.resource(...)`
- keep default behaviour unchanged when hints are absent
- enforce minimal guardrail: `merge` requires `primary_key`

## Consequences

### Positive

- deterministic resource-level rerun policy without project hardcoding in core
- reusable across REST and future source implementations
- clearer ownership: project/source declares intent, bridge maps to runtime semantics
- backwards-compatible default path for resources with no hints

### Trade-offs

- additional contract surface to maintain
- source-bridge now carries destination-specific mapping responsibilities
- stricter validation can fail earlier than previous permissive behaviour

## Boundary Notes

- `core/ingestion.py` remains orchestration-only
- `BaseSource` remains the sole source-to-dlt translation boundary
- project code can opt into hints without modifying engine internals
