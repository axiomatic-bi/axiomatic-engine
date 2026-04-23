from __future__ import annotations

import unittest

from axiomatic_engine.adapters.factory import (
    get_storage_adapter,
    get_transformation_adapter,
    get_warehouse_adapter,
)
from axiomatic_engine.adapters.storage.local import LocalStorage
from axiomatic_engine.adapters.transformation.dbt_adapter import DbtTransformationAdapter
from axiomatic_engine.adapters.warehouse.duckdb import DuckDBWarehouse
from axiomatic_engine.adapters.warehouse.motherduck import MotherDuckWarehouse
from axiomatic_engine.config.storage import LocalStorageSettings
from axiomatic_engine.config.transform import TransformSettings
from axiomatic_engine.config.warehouse import (
    BigQueryWarehouseSettings,
    DuckDBWarehouseSettings,
    MotherDuckWarehouseSettings,
)


class FactoryTests(unittest.TestCase):
    def test_get_storage_adapter_returns_local_storage(self) -> None:
        adapter = get_storage_adapter(
            settings=LocalStorageSettings(path="./data/raw_vault")
        )
        self.assertIsInstance(adapter, LocalStorage)

    def test_get_warehouse_adapter_returns_duckdb_warehouse(self) -> None:
        adapter = get_warehouse_adapter(
            settings=DuckDBWarehouseSettings(path="./data/local.duckdb")
        )
        self.assertIsInstance(adapter, DuckDBWarehouse)

    def test_get_warehouse_adapter_returns_motherduck_warehouse(self) -> None:
        adapter = get_warehouse_adapter(
            settings=MotherDuckWarehouseSettings(
                path="md:analytics",
                access_token="token",
            )
        )
        self.assertIsInstance(adapter, MotherDuckWarehouse)

    def test_get_transformation_adapter_returns_dbt_adapter_for_motherduck(self) -> None:
        adapter = get_transformation_adapter(
            transform_settings=TransformSettings(
                enabled=True,
                kind="dbt",
                dbt_project_dir="./projects/fake-store/dbt",
                dbt_profiles_dir="./projects/fake-store/dbt",
                dbt_profile_name="fake_store",
                dbt_target="dev",
                dbt_run_tests=True,
            ),
            warehouse_settings=MotherDuckWarehouseSettings(
                path="md:analytics",
                access_token="token",
            ),
        )
        self.assertIsInstance(adapter, DbtTransformationAdapter)

    def test_get_transformation_adapter_returns_dbt_adapter_for_duckdb(self) -> None:
        adapter = get_transformation_adapter(
            transform_settings=TransformSettings(
                enabled=True,
                kind="dbt",
                dbt_project_dir="./projects/fake-store/dbt",
                dbt_profiles_dir="./projects/fake-store/dbt",
                dbt_profile_name="fake_store",
                dbt_target=None,
                dbt_run_tests=True,
            ),
            warehouse_settings=DuckDBWarehouseSettings(
                path="./data/local.duckdb",
            ),
        )
        self.assertIsInstance(adapter, DbtTransformationAdapter)

    def test_get_transformation_adapter_rejects_not_enabled_warehouses(self) -> None:
        with self.assertRaises(NotImplementedError):
            get_transformation_adapter(
                transform_settings=TransformSettings(
                    enabled=True,
                    kind="dbt",
                    dbt_project_dir="./projects/fake-store/dbt",
                    dbt_profiles_dir="./projects/fake-store/dbt",
                    dbt_profile_name="fake_store",
                    dbt_target=None,
                    dbt_run_tests=True,
                ),
                warehouse_settings=BigQueryWarehouseSettings(
                    path="project.dataset",
                ),
            )


if __name__ == "__main__":
    unittest.main()
