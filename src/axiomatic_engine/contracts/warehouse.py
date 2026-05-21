from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol, Any, runtime_checkable, Literal
from axiomatic_engine.contracts.storage import RawFileRef

WarehouseKind = Literal["duckdb", "motherduck", "bigquery"]


@dataclass(frozen=True)
class ColumnInfo:
    """
    Metadata for a single column returned by schema introspection.
    """

    name: str
    data_type: str
    is_nullable: bool = True


@runtime_checkable
class WarehouseProtocol(Protocol):
    """
    The Axiomatic Contract for analytical warehouses.
    This defines the 'how' of interacting with any database implementation.
    """

    def get_connection_uri(self) -> str:
        """
        Return the standardised connection string.
        Essential for tools like 'dlt' or 'dbt' to find the warehouse.
        """
        ...

    def get_dlt_destination(self) -> Any:
        """
        Return the dlt destination reference or configured destination object
        for this warehouse adapter.
        """
        ...

    def get_dlt_credentials(self) -> Any | None:
        """
        Return dlt credentials payload for this warehouse adapter, if required.
        """
        ...

    def execute(self, query: str, parameters: Any = None) -> Any:
        """
        Execute a raw SQL command.
        Used for schema management, testing, or ad-hoc analytics.
        """
        ...

    def load_from_references(
        self,
        references: list[RawFileRef],
        target_schema: str = "bronze"
    ) -> dict[str, int]:
        """
        A high-level method to move data from Storage to Warehouse.
        Replaces 'load_bronze_tables' with a general-purpose loader.
        """
        ...

    def introspect_schema(
        self,
        schema: str,
        table: str,
    ) -> list[ColumnInfo]:
        """
        Return column metadata for a table in the given schema.

        Raises ValueError if the table does not exist.
        """
        ...
