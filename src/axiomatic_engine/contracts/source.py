from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Iterable, Literal, Protocol, runtime_checkable

SourceKind = Literal["rest_api", "http_file"]
WriteDisposition = Literal["append", "replace", "merge"]
SchemaEvolutionMode = Literal["auto", "strict", "discard"]


@dataclass(frozen=True)
class ResourceLoadHints:
    """
    Optional ingestion hints for a single resource.

    These values are source-agnostic contracts that adapters may map onto
    destination-specific capabilities.
    """

    write_disposition: WriteDisposition | None = None
    primary_key: str | list[str] | None = None
    schema_evolution_mode: SchemaEvolutionMode | None = None

@runtime_checkable
class ResourceProtocol(Protocol):
    """
    Represents a single stream of data (a table) from a source.
    """
    name: str  # e.g., "title_basics"

    def read(self) -> Iterable[dict[str, Any]]:
        """
        Yields raw records from the source.
        Explicitly returns a dictionary to ensure compatibility with dlt.
        """
        ...

    def get_load_hints(self) -> ResourceLoadHints | None:
        """
        Optionally returns resource-level ingestion hints.
        """
        ...

@runtime_checkable
class SourceProtocol(Protocol):
    """
    The Axiomatic Contract for data ingestion.
    A Source is a collection of one or more Resources.
    """
    name: str  # e.g., "imdb_dataset"
    kind: SourceKind

    def get_resources(self) -> list[ResourceProtocol]:
        """
        Returns the list of resources available for this source.
        Allows the engine to orchestrate parallel loading.
        """
        ...

    def get_incremental_key(self) -> str | None:
        """
        Returns the column name used for incremental loading (e.g., 'updated_at').
        Returns None if the source only supports 'Full Refresh'.
        """
        ...
