from __future__ import annotations

import unittest

from axiomatic_engine.config.engine import EngineSettings


class EngineSettingsTests(unittest.TestCase):
    def test_from_env_uses_expected_axiomatic_variables(self) -> None:
        settings = EngineSettings.from_env(
            {
                "AXIOMATIC_STORAGE_KIND": "local",
                "AXIOMATIC_STORAGE_PATH": "./data/raw_vault",
                "AXIOMATIC_WAREHOUSE_KIND": "motherduck",
                "AXIOMATIC_WAREHOUSE_PATH": "md:analytics",
                "AXIOMATIC_WAREHOUSE_SCHEMA": "bronze",
                "AXIOMATIC_MOTHERDUCK_ACCESS_TOKEN": "secret-token",
            }
        )

        self.assertEqual(settings.storage.kind, "local")
        self.assertEqual(settings.storage.path, "./data/raw_vault")
        self.assertEqual(settings.warehouse.kind, "motherduck")
        self.assertEqual(settings.warehouse.path, "md:analytics")
        self.assertEqual(settings.warehouse.schema_name, "bronze")
        self.assertEqual(settings.warehouse.motherduck_access_token, "secret-token")

    def test_from_env_uses_defaults_when_values_missing(self) -> None:
        settings = EngineSettings.from_env({})

        self.assertEqual(settings.storage.kind, "local")
        self.assertEqual(settings.storage.path, "./data/raw_vault")
        self.assertEqual(settings.warehouse.kind, "duckdb")
        self.assertEqual(settings.warehouse.path, "./data/warehouse.duckdb")
        self.assertEqual(settings.warehouse.schema_name, "bronze")
        self.assertIsNone(settings.warehouse.motherduck_access_token)

    def test_from_env_rejects_unknown_kinds(self) -> None:
        with self.assertRaises(ValueError):
            EngineSettings.from_env({"AXIOMATIC_STORAGE_KIND": "filesystem"})

        with self.assertRaises(ValueError):
            EngineSettings.from_env({"AXIOMATIC_WAREHOUSE_KIND": "snowflake"})

    def test_with_overrides_updates_selected_fields_only(self) -> None:
        base = EngineSettings.from_env(
            {
                "AXIOMATIC_STORAGE_KIND": "local",
                "AXIOMATIC_STORAGE_PATH": "./data/raw_vault",
                "AXIOMATIC_WAREHOUSE_KIND": "duckdb",
                "AXIOMATIC_WAREHOUSE_PATH": "./data/local.duckdb",
                "AXIOMATIC_MOTHERDUCK_ACCESS_TOKEN": "secret-token",
            }
        )

        overridden = base.with_overrides(
            warehouse_kind="motherduck",
            warehouse_path="md:analytics",
        )

        self.assertEqual(overridden.storage.kind, "local")
        self.assertEqual(overridden.storage.path, "./data/raw_vault")
        self.assertEqual(overridden.warehouse.kind, "motherduck")
        self.assertEqual(overridden.warehouse.path, "md:analytics")
        self.assertEqual(
            overridden.warehouse.motherduck_access_token,
            "secret-token",
        )


if __name__ == "__main__":
    unittest.main()
