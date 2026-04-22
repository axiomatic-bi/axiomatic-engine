# ADR 007: dbt Project And Profiles Path Resolution

## Status

Accepted

## Context

Transformation runs can be triggered from different working directories and environments.

Relative dbt paths are error-prone in subprocess execution and can fail with invalid-directory errors when resolved from unexpected current directories.

## Decision

Resolve dbt project and profiles paths to absolute paths in the transformation adapter before subprocess invocation.

- accept configured paths as input
- resolve to absolute paths in `_build_command(...)`
- pass resolved values to dbt CLI invocation

## Consequences

### Positive

- more reliable cross-environment dbt execution
- fewer path-dependent runtime failures
- clearer diagnostics in command output

### Trade-offs

- path resolution behaviour must be consistent across OS environments
- debugging still depends on correct initial config values
