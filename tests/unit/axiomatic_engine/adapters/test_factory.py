from __future__ import annotations

import unittest

from axiomatic_engine.adapters.factory import get_storage_adapter, get_warehouse_adapter
from axiomatic_engine.adapters.storage.local import LocalStorage
from axiomatic_engine.adapters.warehouse.duckdb import DuckDBWarehouse
from axiomatic_engine.adapters.warehouse.motherduck import MotherDuckWarehouse
from axiomatic_engine.config.storage import StorageSettings
from axiomatic_engine.config.warehouse import WarehouseSettings


class FactoryTests(unittest.TestCase):
    def test_get_storage_adapter_returns_local_storage(self) -> None:
        adapter = get_storage_adapter(
            settings=StorageSettings(kind="local", path="./data/raw_vault")
        )
        self.assertIsInstance(adapter, LocalStorage)

    def test_get_warehouse_adapter_returns_duckdb_warehouse(self) -> None:
        adapter = get_warehouse_adapter(
            settings=WarehouseSettings(kind="duckdb", path="./data/local.duckdb")
        )
        self.assertIsInstance(adapter, DuckDBWarehouse)

    def test_get_warehouse_adapter_returns_motherduck_warehouse(self) -> None:
        adapter = get_warehouse_adapter(
            settings=WarehouseSettings(
                kind="motherduck",
                path="md:analytics",
                motherduck_access_token="token",
            )
        )
        self.assertIsInstance(adapter, MotherDuckWarehouse)


if __name__ == "__main__":
    unittest.main()
