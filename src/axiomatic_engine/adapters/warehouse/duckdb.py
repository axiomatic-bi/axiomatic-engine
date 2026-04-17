from __future__ import annotations
import duckdb
from typing import Any
from axiomatic_engine.contracts.warehouse import WarehouseProtocol
from axiomatic_engine.contracts.storage import RawFileRef

class DuckDBWarehouse(WarehouseProtocol):
    """
    Adapter for DuckDB (Local or MotherDuck).
    Provides the compute environment for the Axiomatic Engine.
    """
    def __init__(self, path: str):
        self.path = path

    def get_connection_uri(self) -> str:
        """
        Returns the URI required by dlt and other tools.
        For DuckDB, this is usually 'duckdb:///path/to/file.db'.
        """
        if self.path.startswith("md:"):
            return self.path # MotherDuck handles its own URI format
        return f"duckdb:///{self.path}"

    def get_dlt_destination(self) -> str:
        """
        Return the dlt destination identifier for DuckDB-compatible backends.
        """
        return "duckdb"

    def get_dlt_credentials(self) -> Any:
        """
        Return destination credentials expected by dlt for DuckDB loaders.
        """
        return self.path

    def execute(self, query: str, parameters: Any = None) -> Any:
        """
        Executes raw SQL. Useful for maintenance, testing, and 
        running dbt-style transformations.
        """
        with duckdb.connect(self.path) as conn:
            if parameters:
                return conn.execute(query, parameters).fetchall()
            return conn.execute(query).fetchall()

    def load_from_references(
        self, 
        references: list[RawFileRef], 
        target_schema: str = "bronze"
    ) -> dict[str, int]:
        """
        An optimised loader for bulk-moving files into DuckDB.
        Leverages DuckDB's native Parquet/CSV reading capabilities.
        """
        counts: dict[str, int] = {}
        with duckdb.connect(self.path) as conn:
            conn.execute(f"CREATE SCHEMA IF NOT EXISTS {target_schema}")
            
            for ref in references:
                table_name = ref.file_name.split('.')[0] # Basic naming logic
                # DuckDB's secret weapon: reading remote/local files directly in SQL
                conn.execute(f"""
                    CREATE OR REPLACE TABLE {target_schema}.{table_name} AS 
                    SELECT * FROM read_auto('{ref.read_uri}')
                """)
                res = conn.execute(f"SELECT count(*) FROM {target_schema}.{table_name}").fetchone()
                counts[table_name] = res[0] if res else 0
                
        return counts