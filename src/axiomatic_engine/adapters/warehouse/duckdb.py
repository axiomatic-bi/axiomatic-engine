from __future__ import annotations

from pathlib import Path
from typing import Any
from axiomatic_engine.adapters.warehouse.base_duck import DuckCompatibleWarehouseBase


class DuckDBWarehouse(DuckCompatibleWarehouseBase):
    """
    Adapter for local DuckDB environments.
    Provides the compute environment for the Axiomatic Engine.
    """

    def __init__(self, path: str):
        super().__init__(path=path)

    def _prepare_connection_target(self) -> None:
        """
        Ensure local DuckDB file destinations have an existing parent directory.
        """
        if self.path == ":memory:":
            return
        Path(self.path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)

    def get_connection_uri(self) -> str:
        """
        Returns the URI required by dlt and other tools.
        For DuckDB, this is usually 'duckdb:///path/to/file.db'.
        """
        return f"duckdb:///{self.path}"

    def get_dlt_credentials(self) -> Any:
        """
        Return destination credentials expected by dlt for DuckDB loaders.
        """
        self._prepare_connection_target()
        return self.path