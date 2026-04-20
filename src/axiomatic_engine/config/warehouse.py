from __future__ import annotations

from dataclasses import dataclass

from axiomatic_engine.contracts.warehouse import WarehouseKind


@dataclass(frozen=True)
class WarehouseSettings:
    """
    Typed settings for warehouse adapter selection and credentials.
    """

    kind: WarehouseKind = "duckdb"
    path: str = "./data/warehouse.duckdb"
    schema_name: str = "bronze"
    motherduck_access_token: str | None = None
