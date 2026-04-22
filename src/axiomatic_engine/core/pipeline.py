from __future__ import annotations

import logging

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
    
    It manages the three-step dance of modern data engineering:
    1. Landing: Extracting raw files to the Storage Layer (Non-Custodial).
    2. Loading: Moving data from Storage to the Warehouse Layer (Compute).
    3. Transforming: Building analytical models in the warehouse.
    """
    
    def __init__(self, settings: EngineSettings) -> None:
        self.storage = get_storage_adapter(settings=settings.storage)
        self.warehouse = get_warehouse_adapter(settings=settings.warehouse)
        self.warehouse_kind: WarehouseKind = settings.warehouse.kind
        self.schema_settings = settings.schema
        self.ingestor = Ingestor(warehouse=self.warehouse)
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

    def land_raw_data(self, source: BaseSource) -> bool:
        """
        Ensures all source resources are present in the Storage Layer.
        Returns True if new data was landed, False if everything was already cached.
        """
        existing_files = {f.file_name for f in self.storage.list_files()}
        resources_to_fetch = [res for res in source.get_resources() if res.name not in existing_files]

        if not resources_to_fetch:
            LOGGER.info("All resources already landed in storage")
            return False

        LOGGER.info("Landing %d new resources to storage", len(resources_to_fetch))
        return True

    def run(self, source: BaseSource, force_reload: bool = False) -> None:
        """
        The main execution loop. Orchestrates 'Landing' then 'Loading'.
        """
        LOGGER.info("Initialising Axiomatic Pipeline: %s", source.name)

        data_was_landed = self.land_raw_data(source)

        if data_was_landed or force_reload:
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