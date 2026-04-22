# ADR 008: Observability Baseline For Pipeline Execution

## Status

Accepted

## Context

Operational users require visibility into stage progress, extraction status, and execution outcomes without introducing heavyweight observability dependencies in early engine phases.

## Decision

Establish a logging-first observability baseline:

- structured stage logs for pipeline orchestration
- resource extraction progress logs in REST source
- ingestion completion status and duration logging
- transformation success/failure status with command diagnostics

Deeper telemetry (for example central metrics/tracing) remains a future enhancement.

## Consequences

### Positive

- immediate operational visibility with minimal dependencies
- useful diagnostics for local and CI troubleshooting
- consistent baseline across pipeline stages

### Trade-offs

- logs are not a full substitute for metrics, tracing, and alerting
- output verbosity and formatting may vary by runtime environment
