# ADR 003: Source Contract Boundary

## Status

Accepted

## Context

The engine is intended to remain domain-agnostic while allowing projects to implement source-specific extraction logic.

Without an explicit boundary, source behaviour, orchestration concerns, and destination mapping could become tightly coupled and difficult to extend.

## Decision

Use `SourceProtocol` and `ResourceProtocol` as the stable extension boundary:

- project or adapter code implements source/resource behaviour
- `core/pipeline.py` and `core/ingestion.py` orchestrate execution only
- `BaseSource` bridges source contracts into dlt-compatible resources

The engine does not import project modules. Projects import engine contracts and implementations.

## Consequences

### Positive

- clear separation between orchestration and source logic
- safer extensibility for new source types
- preserves engine-agnostic dependency direction

### Trade-offs

- protocol and bridge layers add abstraction overhead
- source implementers must conform to explicit contracts
