from __future__ import annotations

import unittest

from axiomatic_engine.adapters.warehouse.motherduck import MotherDuckWarehouse


class MotherDuckWarehouseTests(unittest.TestCase):
    def test_requires_md_path_prefix(self) -> None:
        with self.assertRaises(ValueError):
            MotherDuckWarehouse(path="analytics.duckdb", access_token="token")

    def test_requires_database_name_after_prefix(self) -> None:
        with self.assertRaises(ValueError):
            MotherDuckWarehouse(path="md:", access_token="token")

    def test_requires_token_for_dlt_credentials(self) -> None:
        warehouse = MotherDuckWarehouse(path="md:analytics", access_token=None)

        with self.assertRaises(ValueError):
            warehouse.get_dlt_credentials()

    def test_get_connection_uri_and_credentials_use_md_path(self) -> None:
        warehouse = MotherDuckWarehouse(path="md:analytics", access_token="token")

        self.assertEqual(warehouse.get_connection_uri(), "md:analytics")
        self.assertEqual(warehouse.get_dlt_credentials(), "md:analytics")


if __name__ == "__main__":
    unittest.main()
