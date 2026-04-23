from __future__ import annotations

import unittest

from axiomatic_engine.config.engine import EngineSettings
from axiomatic_engine.config.warehouse import MotherDuckWarehouseSettings


class EngineSettingsTests(unittest.TestCase):
    def test_from_env_uses_expected_axiomatic_variables(self) -> None:
        settings = EngineSettings.from_env(
            {
                "AXIOMATIC_STORAGE_KIND": "local",
                "AXIOMATIC_STORAGE_PATH": "./data/raw_vault",
                "AXIOMATIC_WAREHOUSE_KIND": "motherduck",
                "AXIOMATIC_WAREHOUSE_PATH": "md:analytics",
                "AXIOMATIC_DLT_PIPELINES_DIR": "./.dlt/pipelines",
                "AXIOMATIC_SCHEMA_BRONZE": "raw_zone",
                "AXIOMATIC_SCHEMA_SILVER": "refined_zone",
                "AXIOMATIC_SCHEMA_GOLD": "curated_zone",
                "AXIOMATIC_SCHEMA_ANALYTICS": "analytics_zone",
                "AXIOMATIC_MOTHERDUCK_ACCESS_TOKEN": "secret-token",
                "AXIOMATIC_TRANSFORM_ENABLED": "true",
                "AXIOMATIC_TRANSFORM_BACKEND": "dbt",
                "AXIOMATIC_DBT_PROJECT_DIR": "./projects/fake-store/dbt",
                "AXIOMATIC_DBT_PROFILES_DIR": "./projects/fake-store/dbt",
                "AXIOMATIC_DBT_PROFILE_NAME": "fake_store",
                "AXIOMATIC_DBT_TARGET": "dev",
                "AXIOMATIC_DBT_RUN_TESTS": "false",
            }
        )

        self.assertEqual(settings.storage.kind, "local")
        self.assertEqual(settings.storage.path, "./data/raw_vault")
        self.assertEqual(settings.warehouse.kind, "motherduck")
        self.assertEqual(settings.warehouse.path, "md:analytics")
        self.assertEqual(settings.dlt_pipelines_dir, "./.dlt/pipelines")
        self.assertEqual(settings.schema.bronze, "raw_zone")
        self.assertEqual(settings.schema.silver, "refined_zone")
        self.assertEqual(settings.schema.gold, "curated_zone")
        self.assertEqual(settings.schema.analytics, "analytics_zone")
        self.assertIsInstance(settings.warehouse, MotherDuckWarehouseSettings)
        self.assertEqual(settings.warehouse.access_token, "secret-token")
        self.assertTrue(settings.transform.enabled)
        self.assertEqual(settings.transform.kind, "dbt")
        self.assertEqual(settings.transform.dbt_project_dir, "./projects/fake-store/dbt")
        self.assertEqual(settings.transform.dbt_profiles_dir, "./projects/fake-store/dbt")
        self.assertEqual(settings.transform.dbt_profile_name, "fake_store")
        self.assertEqual(settings.transform.dbt_target, "dev")
        self.assertFalse(settings.transform.dbt_run_tests)

    def test_from_env_uses_defaults_when_values_missing(self) -> None:
        settings = EngineSettings.from_env({})

        self.assertEqual(settings.storage.kind, "local")
        self.assertEqual(settings.storage.path, "./data/raw_vault")
        self.assertEqual(settings.warehouse.kind, "duckdb")
        self.assertEqual(settings.warehouse.path, "./data/warehouse.duckdb")
        self.assertIsNone(settings.dlt_pipelines_dir)
        self.assertEqual(settings.schema.bronze, "bronze")
        self.assertEqual(settings.schema.silver, "silver")
        self.assertEqual(settings.schema.gold, "gold")
        self.assertEqual(settings.schema.analytics, "analytics")
        self.assertNotIsInstance(settings.warehouse, MotherDuckWarehouseSettings)
        self.assertFalse(settings.transform.enabled)
        self.assertEqual(settings.transform.kind, "dbt")
        self.assertIsNone(settings.transform.dbt_project_dir)
        self.assertIsNone(settings.transform.dbt_profiles_dir)
        self.assertIsNone(settings.transform.dbt_profile_name)
        self.assertIsNone(settings.transform.dbt_target)
        self.assertTrue(settings.transform.dbt_run_tests)

    def test_from_env_rejects_unknown_kinds(self) -> None:
        with self.assertRaises(ValueError):
            EngineSettings.from_env({"AXIOMATIC_STORAGE_KIND": "filesystem"})

        with self.assertRaises(ValueError):
            EngineSettings.from_env({"AXIOMATIC_WAREHOUSE_KIND": "snowflake"})

        with self.assertRaises(ValueError):
            EngineSettings.from_env({"AXIOMATIC_TRANSFORM_BACKEND": "airflow"})

        with self.assertRaises(ValueError):
            EngineSettings.from_env({"AXIOMATIC_TRANSFORM_ENABLED": "sometimes"})

        with self.assertRaises(ValueError):
            EngineSettings.from_env({"AXIOMATIC_TRANSFORM_ENABLED": "true"})

    def test_with_overrides_updates_selected_fields_only(self) -> None:
        base = EngineSettings.from_env(
            {
                "AXIOMATIC_STORAGE_KIND": "local",
                "AXIOMATIC_STORAGE_PATH": "./data/raw_vault",
                "AXIOMATIC_WAREHOUSE_KIND": "duckdb",
                "AXIOMATIC_WAREHOUSE_PATH": "./data/local.duckdb",
            }
        )

        overridden = base.with_overrides(
            warehouse_kind="motherduck",
            warehouse_path="md:analytics",
            dlt_pipelines_dir="./.dlt/pipelines",
            bronze_schema_name="raw_zone",
            silver_schema_name="refined_zone",
            gold_schema_name="curated_zone",
            analytics_schema_name="analytics_zone",
            transform_enabled=True,
            transform_kind="dbt",
            dbt_project_dir="./projects/fake-store/dbt",
            dbt_profiles_dir="./projects/fake-store/dbt",
            dbt_profile_name="fake_store",
            dbt_target="prod",
            dbt_run_tests=False,
        )

        self.assertEqual(overridden.storage.kind, "local")
        self.assertEqual(overridden.storage.path, "./data/raw_vault")
        self.assertEqual(overridden.warehouse.kind, "motherduck")
        self.assertEqual(overridden.warehouse.path, "md:analytics")
        self.assertEqual(overridden.dlt_pipelines_dir, "./.dlt/pipelines")
        self.assertIsInstance(overridden.warehouse, MotherDuckWarehouseSettings)
        self.assertIsNone(overridden.warehouse.access_token)
        self.assertEqual(overridden.schema.bronze, "raw_zone")
        self.assertEqual(overridden.schema.silver, "refined_zone")
        self.assertEqual(overridden.schema.gold, "curated_zone")
        self.assertEqual(overridden.schema.analytics, "analytics_zone")
        self.assertTrue(overridden.transform.enabled)
        self.assertEqual(overridden.transform.kind, "dbt")
        self.assertEqual(overridden.transform.dbt_project_dir, "./projects/fake-store/dbt")
        self.assertEqual(overridden.transform.dbt_profiles_dir, "./projects/fake-store/dbt")
        self.assertEqual(overridden.transform.dbt_profile_name, "fake_store")
        self.assertEqual(overridden.transform.dbt_target, "prod")
        self.assertFalse(overridden.transform.dbt_run_tests)


if __name__ == "__main__":
    unittest.main()
