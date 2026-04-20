from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from typing import cast

from axiomatic_engine.config.storage import StorageSettings
from axiomatic_engine.config.warehouse import WarehouseSettings
from axiomatic_engine.contracts.storage import RawStorageKind
from axiomatic_engine.contracts.warehouse import WarehouseKind


@dataclass(frozen=True)
class EngineSettings:
    """
    Composite settings object for pipeline runtime configuration.
    """

    storage: StorageSettings
    warehouse: WarehouseSettings

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
        )

    def with_overrides(
        self,
        storage_kind: RawStorageKind | None = None,
        storage_path: str | None = None,
        warehouse_kind: WarehouseKind | None = None,
        warehouse_path: str | None = None,
        warehouse_schema_name: str | None = None,
    ) -> EngineSettings:
        """
        Return a copy with explicit overrides applied.
        """

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
