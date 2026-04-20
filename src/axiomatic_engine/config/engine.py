from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import cast

from axiomatic_engine.config.storage import StorageSettings
from axiomatic_engine.config.warehouse import WarehouseSettings
from axiomatic_engine.contracts.storage import RawStorageKind
from axiomatic_engine.contracts.transformation import TransformationKind
from axiomatic_engine.contracts.warehouse import WarehouseKind


@dataclass(frozen=True)
class TransformSettings:
    """
    Typed configuration for the transformation stage.
    """

    enabled: bool = False
    kind: TransformationKind = "dbt"
    dbt_project_dir: str | None = None
    dbt_profiles_dir: str | None = None
    dbt_profile_name: str | None = None
    dbt_target: str | None = None
    dbt_run_tests: bool = True


@dataclass(frozen=True)
class EngineSettings:
    """
    Composite settings object for pipeline runtime configuration.
    """

    storage: StorageSettings
    warehouse: WarehouseSettings
    transform: TransformSettings = field(default_factory=TransformSettings)

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> EngineSettings:
        """
        Build a typed settings object from AXIOMATIC-prefixed environment variables.

        The caller controls .env loading at application entry points.
        """

        source = environ if environ is not None else os.environ

        storage_kind = _parse_storage_kind(source.get("AXIOMATIC_STORAGE_KIND", "local"))
        storage_path = source.get("AXIOMATIC_STORAGE_PATH", "./data/raw_vault")

        warehouse_kind = _parse_warehouse_kind(source.get("AXIOMATIC_WAREHOUSE_KIND", "duckdb"))
        warehouse_path = source.get("AXIOMATIC_WAREHOUSE_PATH", "./data/warehouse.duckdb")
        warehouse_schema = source.get("AXIOMATIC_WAREHOUSE_SCHEMA", "bronze")
        motherduck_access_token = source.get("AXIOMATIC_MOTHERDUCK_ACCESS_TOKEN")
        transform_enabled = _parse_bool(source.get("AXIOMATIC_TRANSFORM_ENABLED", "false"))
        transform_kind = _parse_transform_kind(source.get("AXIOMATIC_TRANSFORM_BACKEND", "dbt"))
        dbt_project_dir = source.get("AXIOMATIC_DBT_PROJECT_DIR")
        dbt_profiles_dir = source.get("AXIOMATIC_DBT_PROFILES_DIR")
        dbt_profile_name = source.get("AXIOMATIC_DBT_PROFILE_NAME")
        dbt_target = source.get("AXIOMATIC_DBT_TARGET")
        dbt_run_tests = _parse_bool(source.get("AXIOMATIC_DBT_RUN_TESTS", "true"))

        transform_settings = TransformSettings(
            enabled=transform_enabled,
            kind=transform_kind,
            dbt_project_dir=dbt_project_dir,
            dbt_profiles_dir=dbt_profiles_dir,
            dbt_profile_name=dbt_profile_name,
            dbt_target=dbt_target,
            dbt_run_tests=dbt_run_tests,
        )
        _validate_transform_settings(transform_settings=transform_settings)

        return cls(
            storage=StorageSettings(
                kind=storage_kind,
                path=storage_path,
            ),
            warehouse=WarehouseSettings(
                kind=warehouse_kind,
                path=warehouse_path,
                schema_name=warehouse_schema,
                motherduck_access_token=motherduck_access_token,
            ),
            transform=transform_settings,
        )

    def with_overrides(
        self,
        storage_kind: RawStorageKind | None = None,
        storage_path: str | None = None,
        warehouse_kind: WarehouseKind | None = None,
        warehouse_path: str | None = None,
        warehouse_schema_name: str | None = None,
        transform_enabled: bool | None = None,
        transform_kind: TransformationKind | None = None,
        dbt_project_dir: str | None = None,
        dbt_profiles_dir: str | None = None,
        dbt_profile_name: str | None = None,
        dbt_target: str | None = None,
        dbt_run_tests: bool | None = None,
    ) -> EngineSettings:
        """
        Return a copy with explicit overrides applied.
        """

        transform_settings = TransformSettings(
            enabled=transform_enabled
            if transform_enabled is not None
            else self.transform.enabled,
            kind=transform_kind if transform_kind is not None else self.transform.kind,
            dbt_project_dir=dbt_project_dir
            if dbt_project_dir is not None
            else self.transform.dbt_project_dir,
            dbt_profiles_dir=dbt_profiles_dir
            if dbt_profiles_dir is not None
            else self.transform.dbt_profiles_dir,
            dbt_profile_name=dbt_profile_name
            if dbt_profile_name is not None
            else self.transform.dbt_profile_name,
            dbt_target=dbt_target if dbt_target is not None else self.transform.dbt_target,
            dbt_run_tests=dbt_run_tests
            if dbt_run_tests is not None
            else self.transform.dbt_run_tests,
        )
        _validate_transform_settings(transform_settings=transform_settings)

        return EngineSettings(
            storage=StorageSettings(
                kind=storage_kind if storage_kind is not None else self.storage.kind,
                path=storage_path if storage_path is not None else self.storage.path,
            ),
            warehouse=WarehouseSettings(
                kind=warehouse_kind if warehouse_kind is not None else self.warehouse.kind,
                path=warehouse_path if warehouse_path is not None else self.warehouse.path,
                schema_name=warehouse_schema_name
                if warehouse_schema_name is not None
                else self.warehouse.schema_name,
                motherduck_access_token=self.warehouse.motherduck_access_token,
            ),
            transform=transform_settings,
        )


def _parse_storage_kind(value: str) -> RawStorageKind:
    if value not in {"local", "gcs", "s3"}:
        raise ValueError(
            "Unsupported AXIOMATIC_STORAGE_KIND. "
            "Expected one of: local, gcs, s3."
        )
    return cast(RawStorageKind, value)


def _parse_warehouse_kind(value: str) -> WarehouseKind:
    if value not in {"duckdb", "motherduck", "bigquery"}:
        raise ValueError(
            "Unsupported AXIOMATIC_WAREHOUSE_KIND. "
            "Expected one of: duckdb, motherduck, bigquery."
        )
    return cast(WarehouseKind, value)


def _parse_transform_kind(value: str) -> TransformationKind:
    if value not in {"dbt", "sql_file"}:
        raise ValueError(
            "Unsupported AXIOMATIC_TRANSFORM_BACKEND. "
            "Expected one of: dbt, sql_file."
        )
    return cast(TransformationKind, value)


def _parse_bool(value: str) -> bool:
    normalised = value.strip().lower()
    if normalised in {"1", "true", "yes", "on"}:
        return True
    if normalised in {"0", "false", "no", "off"}:
        return False
    raise ValueError(
        f"Unsupported boolean value: {value}. "
        "Expected one of: 1, true, yes, on, 0, false, no, off."
    )


def _validate_transform_settings(transform_settings: TransformSettings) -> None:
    if not transform_settings.enabled:
        return
    if transform_settings.kind == "dbt" and not transform_settings.dbt_project_dir:
        raise ValueError(
            "AXIOMATIC_DBT_PROJECT_DIR is required when transformations are enabled "
            "with AXIOMATIC_TRANSFORM_BACKEND=dbt."
        )
