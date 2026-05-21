from __future__ import annotations

from abc import ABC
from pathlib import Path
from typing import Any

import duckdb

from axiomatic_engine.contracts.storage import RawFileRef
from axiomatic_engine.contracts.warehouse import ColumnInfo, WarehouseProtocol


class DuckCompatibleWarehouseBase(WarehouseProtocol, ABC):
    """
    Shared implementation for DuckDB-compatible warehouse adapters.

    Concrete adapters own URI and credentials semantics while this base owns
    common query execution and file-loading behaviour.
    """

    def __init__(self, path: str):
        self.path = path

    def get_dlt_destination(self) -> str:
        """
        Return the dlt destination identifier for DuckDB-compatible backends.
        """
        return "duckdb"

    def _prepare_connection_target(self) -> None:
        """
        Hook for adapter-specific filesystem or remote validation before connect.
        """

    def execute(self, query: str, parameters: Any = None) -> Any:
        """
        Execute raw SQL and return fetched rows.
        """
        self._prepare_connection_target()
        with duckdb.connect(self.path) as conn:
            if parameters is not None:
                return conn.execute(query, parameters).fetchall()
            return conn.execute(query).fetchall()

    def load_from_references(
        self,
        references: list[RawFileRef],
        target_schema: str = "bronze",
    ) -> dict[str, int]:
        """
        Bulk-load files from storage references into DuckDB-compatible tables.
        """
        counts: dict[str, int] = {}
        schema_identifier = _quote_identifier(target_schema)

        self._prepare_connection_target()
        with duckdb.connect(self.path) as conn:
            conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_identifier}")

            for ref in references:
                table_name = Path(ref.file_name).stem
                table_identifier = _quote_identifier(table_name)
                normalised_read_uri = _normalise_read_uri(ref.read_uri)

                conn.execute(
                    f"""
                    CREATE OR REPLACE TABLE {schema_identifier}.{table_identifier} AS
                    SELECT * FROM read_auto(?)
                    """,
                    [normalised_read_uri],
                )
                row = conn.execute(
                    f"SELECT count(*) FROM {schema_identifier}.{table_identifier}"
                ).fetchone()
                counts[table_name] = row[0] if row else 0

        return counts

    def introspect_schema(
        self,
        schema: str,
        table: str,
    ) -> list[ColumnInfo]:
        """
        Return column metadata for a table using DuckDB DESCRIBE.

        DuckDB DESCRIBE returns rows: (column_name, column_type, null, key, default, extra)
        Raises ValueError if the table does not exist.
        """
        schema_id = _quote_identifier(schema)
        table_id = _quote_identifier(table)

        self._prepare_connection_target()
        with duckdb.connect(self.path) as conn:
            try:
                rows = conn.execute(
                    f"DESCRIBE {schema_id}.{table_id}"
                ).fetchall()
            except duckdb.CatalogException as exc:
                raise ValueError(
                    f"Table '{schema}.{table}' does not exist in warehouse at '{self.path}'. "
                    "Run ingestion first."
                ) from exc

        return [
            ColumnInfo(
                name=row[0],
                data_type=row[1],
                is_nullable=(str(row[2]).upper() == "YES"),
            )
            for row in rows
        ]


def _quote_identifier(identifier: str) -> str:
    return f"\"{identifier.replace('\"', '\"\"')}\""


def _normalise_read_uri(read_uri: str) -> str:
    """
    Resolve local relative paths while preserving explicit URI schemes.
    """
    if _looks_like_uri(read_uri):
        return read_uri
    return str(Path(read_uri).expanduser().resolve())


def _looks_like_uri(value: str) -> bool:
    if "://" in value:
        return True
    if value.startswith("md:"):
        return True
    if len(value) >= 3 and value[1] == ":" and value[2] in {"\\", "/"}:
        # Windows absolute path (for example C:\\data\\input.parquet)
        return False
    return False
