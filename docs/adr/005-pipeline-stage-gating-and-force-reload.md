# ADR 005: Pipeline Stage Gating And Force Reload

## Status

Accepted

## Context

The pipeline includes landing, ingestion, and optional transformation stages. Re-running all stages unconditionally can increase cost and runtime.

A lightweight gating strategy was needed to avoid unnecessary loads while keeping a manual override for deterministic reruns.

## Decision

Use stage gating in `Pipeline.run(...)`:

- evaluate ingestion necessity through `should_run_ingestion(...)`:
  - run ingestion immediately when `force_reload=True`
  - otherwise use storage-cache heuristics to detect missing resources
- run ingestion when gating returns true
- run transformations according to transform settings after ingestion stage decision

`force_reload` remains the explicit operator control for full reruns.

## Consequences

### Positive

- reduced unnecessary ingestion runs
- clear operator override behaviour
- predictable orchestration flow in one entrypoint

### Trade-offs

- storage-cache heuristics may not capture all upstream-change scenarios
- incorrect assumptions in cache state can cause skipped loads unless force reload is used
