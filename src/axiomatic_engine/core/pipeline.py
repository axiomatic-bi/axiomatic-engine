from __future__ import annotations

import logging
from pathlib import Path

from axiomatic_engine.adapters.factory import (
    get_storage_adapter,
    get_transformation_adapter,
    get_warehouse_adapter,
)
from axiomatic_engine.config.engine import EngineSettings
from axiomatic_engine.contracts.warehouse import WarehouseKind
from axiomatic_engine.core.ingestion import Ingestor
from axiomatic_engine.core.transformation import Transformer
from axiomatic_engine.sources.base import BaseSource

LOGGER = logging.getLogger(__name__)


class Pipeline:
    """
    The central orchestrator of the Axiomatic Engine.

    It manages the ingestion and optional transformation stages.
    """

    def __init__(self, settings: EngineSettings) -> None:
        self.storage = get_storage_adapter(settings=settings.storage)
        self.warehouse = get_warehouse_adapter(settings=settings.warehouse)
        self.warehouse_kind: WarehouseKind = settings.warehouse.kind
        self.warehouse_path = settings.warehouse.path
        self.schema_settings = settings.schema
        self.ingestor = Ingestor(
            warehouse=self.warehouse,
            dlt_pipelines_dir=settings.dlt_pipelines_dir,
        )
        self.transform_settings = settings.transform
        self.transformer: Transformer | None = None

        if self.transform_settings.enabled:
            transformation_adapter = get_transformation_adapter(
                transform_settings=self.transform_settings,
                warehouse_settings=settings.warehouse,
            )
            dbt_project_dir = self.transform_settings.dbt_project_dir
            if dbt_project_dir is None:
                raise ValueError("dbt_project_dir must be set before running transformations.")
            self.transformer = Transformer(
                adapter=transformation_adapter,
                warehouse_kind=self.warehouse_kind,
                project_dir=dbt_project_dir,
            )

    def _existing_storage_resource_names(self) -> set[str]:
        names: set[str] = set()
        for file_ref in self.storage.list_files():
            names.add(file_ref.file_name)
            names.add(Path(file_ref.file_name).stem)
        return names

    def should_run_ingestion(self, source: BaseSource, force_reload: bool) -> bool:
        if force_reload:
            LOGGER.info("Force reload enabled. Ingestion will run.")
            return True

        existing_resource_names = self._existing_storage_resource_names()
        missing_resources = [
            resource.name
            for resource in source.get_resources()
            if resource.name not in existing_resource_names
        ]

        if missing_resources:
            LOGGER.info(
                "Ingestion will run. Resources not detected in storage cache: %s",
                ", ".join(missing_resources),
            )
            return True

        LOGGER.info("Ingestion skipped. Storage cache suggests no new resources.")
        return False

    def run(self, source: BaseSource, force_reload: bool = False) -> None:
        """
        The main execution loop.
        """
        LOGGER.info("Initialising Axiomatic Pipeline: %s", source.name)

        if self.should_run_ingestion(source=source, force_reload=force_reload):
            LOGGER.info("Ingesting data into the warehouse")
            self.ingestor.run(
                source=source,
                dataset_name=self.schema_settings.bronze,
            )
            LOGGER.info("Ingestion completed successfully.")
        else:
            LOGGER.info("Warehouse is already up to date. Skipping load.")

        if self.transformer is not None:
            self.transformer.run()
            LOGGER.info("Pipeline completed with transformations.")
        else:
            LOGGER.info("Pipeline completed without transformations.")

        LOGGER.info("Warehouse location: %s", self._warehouse_location_label())

    def _warehouse_location_label(self) -> str:
        if self.warehouse_kind == "duckdb":
            if self.warehouse_path == ":memory:":
                return "DuckDB in-memory database (:memory:)"
            resolved_path = Path(self.warehouse_path).expanduser().resolve()
            return f"DuckDB file at {resolved_path}"
        if self.warehouse_kind == "motherduck":
            return f"MotherDuck database {self.warehouse_path}"
        return f"{self.warehouse_kind} warehouse at {self.warehouse_path}"
