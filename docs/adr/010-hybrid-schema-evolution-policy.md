# ADR 010: Hybrid Schema Evolution Policy

## Status

Accepted

## Context

Client and project requirements differ on schema drift:

- some pipelines should auto-accept new source fields
- others require strict failure when unexpected fields appear
- some require value-discard behaviour to keep rows but ignore untrusted additions

The engine needed one policy model that can be configured per resource while preserving source-agnostic contracts.

## Decision

Adopt a hybrid schema evolution contract with explicit per-resource modes:

- engine contract values:
  - `auto`
  - `strict`
  - `discard`
- map contract values to dlt runtime values in the source bridge:
  - `auto -> evolve`
  - `strict -> freeze`
  - `discard -> discard_value`

Default guidance is permissive evolution (`auto`) unless a project/resource explicitly opts into strict behaviour.

## Consequences

### Positive

- one consistent contract across projects and source types
- stricter data governance available where required
- safer incremental adoption: permissive default, explicit tightening per resource
- no project-specific branching in core ingestion flow

### Trade-offs

- mapping layer must track destination semantics and naming changes
- strict mode can increase operational incidents if upstream schemas change frequently
- discard mode may hide useful new fields unless monitored

## Operational Notes

- schema mode is declared by resource through `ResourceLoadHints`
- schema semantics are enforced at extraction/load boundary (source bridge)
- projects remain responsible for monitoring and surfacing drift events in their runbooks
