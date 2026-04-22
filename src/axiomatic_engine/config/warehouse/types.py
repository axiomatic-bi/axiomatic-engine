from __future__ import annotations

from axiomatic_engine.config.warehouse.bigquery import BigQueryWarehouseSettings
from axiomatic_engine.config.warehouse.duckdb import DuckDBWarehouseSettings
from axiomatic_engine.config.warehouse.motherduck import MotherDuckWarehouseSettings

WarehouseSettings = (
    DuckDBWarehouseSettings | MotherDuckWarehouseSettings | BigQueryWarehouseSettings
)
