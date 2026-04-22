# ADR 013: Specific Source Kinds And Source Factory Routing

## Status

Accepted

## Context

The engine historically exposed generic source kinds and relied on project entrypoints
to instantiate concrete source classes directly.

As packaging readiness improved, two needs became clearer:

- source-kind values should route to concrete source logic without ambiguity
- common source construction should be reusable across projects while keeping an
  escape hatch for bespoke client behaviour

## Decision

Adopt specific source-kind values for currently implemented source families:

- `rest_api`
- `http_file`

Add a dedicated source factory in `sources/factory.py` with typed definitions:

- `RestApiSourceDefinition` routes to `RestApiSource`
- `HttpFileSourceDefinition` routes to `HttpStreamSource`

Harden `HttpStream` to align with source quality conventions:

- explicit constructor return typing (`-> None`)
- per-resource `timeout_seconds`
- URL-path-based compression inference (ignores query strings)
- optional `ResourceLoadHints` passthrough

Project entrypoints should prefer `build_source(definition=...)` as the standard
construction path, while direct source class construction remains supported.

## Consequences

### Positive

- source-kind values now carry deterministic routing semantics
- source construction is repeatable and easier to validate across projects
- future file-source expansions can follow typed-definition patterns
- projects retain flexibility through direct constructor escape hatches

### Trade-offs

- adding new source families requires updating literals, factory routing, and docs
- source-definition models introduce additional types to maintain
- projects migrating from direct constructors to factory definitions incur small
  refactor overhead

## Operational Notes

- `sources/factory.py` is the canonical routing layer for source definitions
- adapter factory remains scoped to storage, warehouse, and transformation adapters
- additional source kinds should be introduced only when concrete implementations
  and tests are added in the same change
