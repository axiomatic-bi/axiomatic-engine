from __future__ import annotations

from axiomatic_engine.config.warehouse.bigquery import BigQueryWarehouseSettings
from axiomatic_engine.config.warehouse.duckdb import DuckDBWarehouseSettings
from axiomatic_engine.config.warehouse.motherduck import MotherDuckWarehouseSettings
from axiomatic_engine.config.warehouse.types import WarehouseSettings
from axiomatic_engine.contracts.warehouse import WarehouseKind


def build_warehouse_settings(
    kind: WarehouseKind,
    path: str,
    *,
    motherduck_access_token: str | None = None,
    existing: WarehouseSettings | None = None,
) -> WarehouseSettings:
    if kind == "duckdb":
        return DuckDBWarehouseSettings(path=path)
    if kind == "motherduck":
        token = motherduck_access_token
        if token is None and isinstance(existing, MotherDuckWarehouseSettings):
            token = existing.access_token
        return MotherDuckWarehouseSettings(path=path, access_token=token)
    if kind == "bigquery":
        return BigQueryWarehouseSettings(path=path)
    raise ValueError(f"Unsupported warehouse kind: {kind}")
