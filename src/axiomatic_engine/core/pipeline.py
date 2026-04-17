from __future__ import annotations
import logging
from axiomatic_engine.contracts.storage import RawStorageKind
from axiomatic_engine.contracts.warehouse import WarehouseKind
from axiomatic_engine.sources.base import BaseSource
from axiomatic_engine.adapters.factory import get_storage_adapter, get_warehouse_adapter
from axiomatic_engine.core.ingestion import Ingestor

LOGGER = logging.getLogger(__name__)

class Pipeline:
    """
    The central orchestrator of the Axiomatic Engine.
    
    It manages the two-step dance of modern data engineering:
    1. Landing: Extracting raw files to the Storage Layer (Non-Custodial).
    2. Loading: Moving data from Storage to the Warehouse Layer (Compute).
    """
    
    def __init__(
        self, 
        storage_kind: RawStorageKind, 
        storage_path: str, 
        warehouse_kind: WarehouseKind, 
        warehouse_path: str
    ):
        self.storage = get_storage_adapter(kind=storage_kind, base_uri=storage_path)
        self.warehouse = get_warehouse_adapter(kind=warehouse_kind, warehouse_path=warehouse_path)
        self.ingestor = Ingestor(warehouse=self.warehouse)

    def land_raw_data(self, source: BaseSource) -> bool:
        """
        Ensures all source resources are present in the Storage Layer.
        Returns True if new data was landed, False if everything was already cached.
        """
        existing_files = {f.file_name for f in self.storage.list_files()}
        resources_to_fetch = [
            res for res in source.get_resources() 
            if res.name not in existing_files
        ]

        if not resources_to_fetch:
            LOGGER.info("All resources already landed in storage")
            return False

        LOGGER.info("Landing %d new resources to storage", len(resources_to_fetch))
        return True

    def run(self, source: BaseSource, force_reload: bool = False):
        """
        The main execution loop. Orchestrates 'Landing' then 'Loading'.
        """
        LOGGER.info("Initialising Axiomatic Pipeline: %s", source.name)
        
        data_was_landed = self.land_raw_data(source)

        if data_was_landed or force_reload:
            LOGGER.info("Ingesting data into the warehouse")
            load_info = self.ingestor.run(source=source)
            LOGGER.info("Pipeline completed: %s", load_info)
        else:
            LOGGER.info("Warehouse is already up to date. Skipping load.")