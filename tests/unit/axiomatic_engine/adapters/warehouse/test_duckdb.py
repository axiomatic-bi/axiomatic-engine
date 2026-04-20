from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from axiomatic_engine.adapters.warehouse.duckdb import DuckDBWarehouse


class DuckDBWarehouseTests(unittest.TestCase):
    def test_get_connection_uri_uses_duckdb_uri_format(self) -> None:
        warehouse = DuckDBWarehouse(path="./data/example.duckdb")
        self.assertEqual(warehouse.get_connection_uri(), "duckdb:///./data/example.duckdb")

    def test_get_dlt_credentials_creates_parent_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "nested" / "analytics.duckdb"
            warehouse = DuckDBWarehouse(path=str(db_path))

            credentials = warehouse.get_dlt_credentials()

            self.assertEqual(credentials, str(db_path))
            self.assertTrue(db_path.parent.exists())


if __name__ == "__main__":
    unittest.main()
