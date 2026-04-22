from __future__ import annotations

from pathlib import Path

from axiomatic_engine.config.transform import TransformSettings
from axiomatic_engine.config.storage import StorageSettings
from axiomatic_engine.config.warehouse import MotherDuckWarehouseSettings, WarehouseSettings
from axiomatic_engine.contracts.transformation import TransformationProtocol
from axiomatic_engine.contracts.storage import RawStorageProtocol
from axiomatic_engine.contracts.warehouse import WarehouseProtocol

from axiomatic_engine.adapters.transformation.dbt_adapter import DbtTransformationAdapter
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
        access_token = (
            settings.access_token
            if isinstance(settings, MotherDuckWarehouseSettings)
            else None
        )
        return MotherDuckWarehouse(
            path=settings.path,
            access_token=access_token,
        )
    if settings.kind == "bigquery":
        raise NotImplementedError("BigQuery is not implemented yet")
    raise ValueError(f"Unsupported warehouse kind: {settings.kind}")


def get_transformation_adapter(
    transform_settings: TransformSettings,
    warehouse_settings: WarehouseSettings,
) -> TransformationProtocol:
    """
    Return the requested transformation adapter.
    """
    if transform_settings.kind != "dbt":
        raise ValueError(f"Unsupported transformation kind: {transform_settings.kind}")
    return _build_dbt_transformation_adapter(
        transform_settings=transform_settings,
        warehouse_settings=warehouse_settings,
    )


def _build_dbt_transformation_adapter(
    transform_settings: TransformSettings,
    warehouse_settings: WarehouseSettings,
) -> DbtTransformationAdapter:
    if warehouse_settings.kind == "motherduck":
        return DbtTransformationAdapter(
            project_dir=Path(_require_value(transform_settings.dbt_project_dir, "dbt_project_dir")),
            profiles_dir=Path(
                _require_value(transform_settings.dbt_profiles_dir, "dbt_profiles_dir")
            ),
            profile_name=_require_value(transform_settings.dbt_profile_name, "dbt_profile_name"),
            target=transform_settings.dbt_target,
            run_tests=transform_settings.dbt_run_tests,
            adapter_package="dbt-duckdb",
            expected_profile_type="duckdb",
        )

    if warehouse_settings.kind == "duckdb":
        raise NotImplementedError(
            "dbt transformations for duckdb warehouse are planned but not enabled yet."
        )
    if warehouse_settings.kind == "bigquery":
        raise NotImplementedError(
            "dbt transformations for bigquery warehouse are planned but not enabled yet."
        )
    raise ValueError(f"Unsupported warehouse kind for dbt transformations: {warehouse_settings.kind}")


def _require_value(value: str | None, field_name: str) -> str:
    if value is None or value.strip() == "":
        raise ValueError(f"Missing required transformation setting: {field_name}")
    return value
