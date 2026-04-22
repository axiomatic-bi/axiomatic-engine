# ADR 006: Environment-First Configuration With CLI Overrides

## Status

Accepted

## Context

Pipeline execution must work across local development, CI, and deployment environments while supporting project-specific runtime overrides.

Purely code-based configuration increases coupling and deployment friction. Purely environment-based configuration can be inflexible for ad hoc runs.

## Decision

Adopt environment-first configuration with explicit CLI override support:

- load defaults from `EngineSettings.from_env()`
- apply runtime override values through `.with_overrides(...)`
- keep precedence explicit: CLI override values take priority over environment values

## Consequences

### Positive

- reproducible config in CI and deployment
- practical local ergonomics for one-off runs
- centralised typed settings model

### Trade-offs

- path assumptions can differ by working directory and must be documented
- override surfaces increase validation and testing requirements
