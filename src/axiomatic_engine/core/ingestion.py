import dlt
from axiomatic_engine.contracts.warehouse import WarehouseProtocol
from axiomatic_engine.sources.base import BaseSource
import logging
from time import perf_counter

LOGGER = logging.getLogger(__name__)

class Ingestor:
    """
    The Axiomatic worker responsible for executing data movement.
    
    It orchestrates the flow from a BaseSource implementation into 
     a WarehouseProtocol implementation using dlt.
    """
    
    def __init__(self, warehouse: WarehouseProtocol):
        self.warehouse = warehouse

    def run(self, source: BaseSource, dataset_name: str):
        """
        Executes the ingestion pipeline.
        
        Triggers dlt loading using destination config from the warehouse adapter.
        """
        LOGGER.info("Starting ingestion for source: %s", source.name)

        pipeline = dlt.pipeline(
            pipeline_name=source.name,
            dataset_name=dataset_name,
            progress="log",
        )
        LOGGER.info(
            "Starting dlt pipeline run for source: %s (extract, normalise, load)",
            source.name,
        )
        load_start = perf_counter()
        load_info = pipeline.run(
            source.to_dlt(),
            destination=self.warehouse.get_dlt_destination(),
            credentials=self.warehouse.get_dlt_credentials(),
        )
        duration_s = perf_counter() - load_start
        LOGGER.info(
            "Ingestion complete for %s in %.1fs.",
            source.name,
            duration_s,
        )
        return load_info
