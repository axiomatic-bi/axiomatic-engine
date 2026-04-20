from __future__ import annotations

from typing import Any

from axiomatic_engine.adapters.warehouse.base_duck import DuckCompatibleWarehouseBase


class MotherDuckWarehouse(DuckCompatibleWarehouseBase):
    """
    Adapter for MotherDuck warehouse execution using DuckDB compatibility.
    """

    def __init__(self, path: str, access_token: str | None):
        super().__init__(path=path)
        self.access_token = access_token
        self._validate_path()

    def _validate_path(self) -> None:
        if not self.path.startswith("md:"):
            raise ValueError(
                "MotherDuck warehouse_path must use md:<database_name> format."
            )
        if self.path == "md:":
            raise ValueError(
                "MotherDuck warehouse_path must include a database name after md:."
            )

    def get_connection_uri(self) -> str:
        """
        Return MotherDuck connection path.
        """
        return self.path

    def get_dlt_credentials(self) -> Any:
        """
        Return dlt credentials for MotherDuck without embedding token in URI.
        """
        if not self.access_token:
            raise ValueError(
                "Missing AXIOMATIC_MOTHERDUCK_ACCESS_TOKEN for motherduck warehouse."
            )
        return self.path
