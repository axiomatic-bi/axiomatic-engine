# ADR 005: Pipeline Stage Gating And Force Reload

## Status

Accepted

## Context

The pipeline includes landing, ingestion, and optional transformation stages. Re-running all stages unconditionally can increase cost and runtime.

A lightweight gating strategy was needed to avoid unnecessary loads while keeping a manual override for deterministic reruns.

## Decision

Use stage gating in `Pipeline.run(...)`:

- land resources and detect whether new data was landed
- run ingestion when data was landed or when `force_reload=True`
- run transformations according to transform settings after ingestion stage decision

`force_reload` remains the explicit operator control for full reruns.

## Consequences

### Positive

- reduced unnecessary ingestion runs
- clear operator override behaviour
- predictable orchestration flow in one entrypoint

### Trade-offs

- landing heuristics may not capture all upstream-change scenarios
- incorrect assumptions in storage state can cause skipped loads unless force reload is used
