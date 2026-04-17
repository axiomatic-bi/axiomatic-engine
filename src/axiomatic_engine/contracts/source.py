from __future__ import annotations
from typing import Literal, Protocol, Iterable, Any, runtime_checkable

SourceKind = Literal["api", "filesystem", "scraper", "sharepoint"]

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