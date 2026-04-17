from __future__ import annotations

from axiomatic_engine.contracts.storage import RawStorageProtocol, RawStorageKind
from axiomatic_engine.contracts.warehouse import WarehouseProtocol, WarehouseKind

from axiomatic_engine.adapters.storage.local import LocalStorage
from axiomatic_engine.adapters.warehouse.duckdb import DuckDBWarehouse

def get_storage_adapter(kind: RawStorageKind, base_uri: str) -> RawStorageProtocol:
    """Returns the requested storage implementation."""
    if kind == "local":
        return LocalStorage(base_path=base_uri)
    if kind == "gcs":
        raise NotImplementedError("GCS storage is not implemented yet")
    if kind == "s3":
        raise NotImplementedError("S3 storage is not implemented yet")
    raise ValueError(f"Unsupported storage kind: {kind}")

def get_warehouse_adapter(kind: WarehouseKind, warehouse_path: str) -> WarehouseProtocol:
    """
    Returns the requested warehouse implementation.
    This allows the engine to switch between local DuckDB and Cloud warehouses.
    """
    if kind == "duckdb":
        return DuckDBWarehouse(path=warehouse_path)
    if kind == "motherduck":
        raise NotImplementedError("MotherDuck is not implemented yet")
    if kind == "bigquery":
        raise NotImplementedError("BigQuery is not implemented yet")
    raise ValueError(f"Unsupported warehouse kind: {kind}")