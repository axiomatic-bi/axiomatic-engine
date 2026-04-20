from __future__ import annotations

from axiomatic_engine.config.storage import StorageSettings
from axiomatic_engine.config.warehouse import WarehouseSettings
from axiomatic_engine.contracts.storage import RawStorageProtocol
from axiomatic_engine.contracts.warehouse import WarehouseProtocol

from axiomatic_engine.adapters.storage.local import LocalStorage
from axiomatic_engine.adapters.warehouse.duckdb import DuckDBWarehouse
from axiomatic_engine.adapters.warehouse.motherduck import MotherDuckWarehouse

def get_storage_adapter(settings: StorageSettings) -> RawStorageProtocol:
    """Returns the requested storage implementation."""
    if settings.kind == "local":
        return LocalStorage(base_path=settings.path)
    if settings.kind == "gcs":
        raise NotImplementedError("GCS storage is not implemented yet")
    if settings.kind == "s3":
        raise NotImplementedError("S3 storage is not implemented yet")
    raise ValueError(f"Unsupported storage kind: {settings.kind}")

def get_warehouse_adapter(settings: WarehouseSettings) -> WarehouseProtocol:
    """
    Returns the requested warehouse implementation.
    This allows the engine to switch between local DuckDB and Cloud warehouses.
    """
    if settings.kind == "duckdb":
        return DuckDBWarehouse(path=settings.path)
    if settings.kind == "motherduck":
        return MotherDuckWarehouse(
            path=settings.path,
            access_token=settings.motherduck_access_token,
        )
    if settings.kind == "bigquery":
        raise NotImplementedError("BigQuery is not implemented yet")
    raise ValueError(f"Unsupported warehouse kind: {settings.kind}")